__author__ = "AlecZ"

# lib imports
import os
import csv
import datetime
import random
import math
from collections import OrderedDict

# custom imports
import util
from util import verbose, info, error

# constants
DATA_DIR = "data"
KEY_CLOSE = 0
KEY_VOLUME = 1
KEY_OPEN = 2
KEY_HIGH = 3
KEY_LOW = 4
MAX_LOSS_OVERRIDE = None

class MWU:

    def __init__(self, num_experts, epsilon=0.05):
        self._weights = [1.0] * num_experts
        self._epsilon = epsilon
        self._loss = 0
        self._losses = [0.0] * num_experts

    def run_iteration(self, expert_losses, max_loss):
        for i, loss in enumerate(expert_losses):
            prob = self._weights[i] / sum(self._weights)
            e_loss = loss * prob
            if not math.isfinite(e_loss):
                error("invalid loss detected")
            self._loss += e_loss # TODO IDK about this...
            self._losses[i] += e_loss
            self._weights[i] = self._weights[i] * pow((1 - self._epsilon), loss / max_loss)

    def get_loss(self):
        return self._loss

    def get_losses(self):
        return self._losses

    def get_weights(self):
        return self._weights

def load_data(dir=DATA_DIR, short=False, whitelist=None):
    stocks = OrderedDict() # stock: tuple
    dates = set()

    def load_rows(rows):
        date_price = {} # {date: (dict with mappings for close, volume, open, high, low)}
        short_date_price = {} # {date: (dict with mappings for close, volume, open, high, low)}
        for row in rows:
            r_date, r_close, r_volume, r_open, r_high, r_low = row
            date = datetime.datetime.strptime(r_date, "%Y/%m/%d")
            dates.add(date)

            d = {
                KEY_CLOSE: float(r_close),
                KEY_VOLUME: float(r_volume),
                KEY_OPEN: float(r_open),
                KEY_HIGH: float(r_high),
                KEY_LOW: float(r_low)
            }
            date_price[date] = d

            d = {
                KEY_CLOSE: -float(r_close),
                KEY_VOLUME: float(r_volume),
                KEY_OPEN: -float(r_open),
                KEY_HIGH: -float(r_high),
                KEY_LOW: -float(r_low)
            }
            short_date_price[date] = d
        return date_price, short_date_price

    def csv_rows(fname):
        f = open(fname, "r")
        c = csv.reader(f)
        first = True
        for row in c:
            if first:
                first = False
            else:
                yield row
        f.close()

    def fake_rows(func, dates):
        for date in dates:
            r_close = func(date)
            yield date.strftime("%Y/%m/%d"), r_close, 0, 0, 0, 0

    for fname in os.listdir(dir):
        if not fname.endswith(".csv") or (whitelist is not None and whitelist not in fname):
            continue

        verbose("Opening file {}... ".format(fname), end="")
        date_price, short_date_price = load_rows(csv_rows(dir + "/" + fname))

        symbol = fname.split(".")[0]
        stocks[symbol] = date_price
        if short:
            stocks["-" + symbol] = short_date_price
        verbose("Done. Loaded {} dates.".format(len(date_price)))

    sorted_dates = sorted(dates)
    for fake_i in range(0, 0): # to add fake stocks

        def mk_trending(rate, dev=0.25):
            def trending(date):
                ret = 20 - 10 * rate * (random.random() * dev - 1.0) * \
                            float((date - sorted_dates[0]).days) / float((sorted_dates[-1] - sorted_dates[0]).days)
                return ret
            return trending

        date_price, short_date_price = load_rows(fake_rows(mk_trending(-1, dev=0.25), sorted_dates))
        stocks["fake{}".format(fake_i)] = date_price
        if short:
            stocks["-fake{}".format(fake_i)] = short_date_price

    return (stocks, sorted(dates))

def run_mwu():

    stocks, dates = load_data()
    mwu = MWU(len(stocks))
    last_close = [None] * len(stocks)

    start_money = 0.0
    first_date = dates[0]
    for i, tup in enumerate(stocks.items()):
        stock, date_price = tup
        price = date_price[first_date]
        cls, vol, op, hi, lo = price[KEY_CLOSE], price[KEY_VOLUME], price[KEY_OPEN], price[KEY_HIGH], price[KEY_LOW]
        start_money += math.fabs(cls)

    money = start_money
    iteration = 0
    for date in dates:
        losses = []
        for i, tup in enumerate(stocks.items()):
            stock, date_price = tup
            price = date_price[date]
            cls, vol, op, hi, lo = price[KEY_CLOSE], price[KEY_VOLUME], price[KEY_OPEN], price[KEY_HIGH], price[KEY_LOW]

            if last_close[i] is not None:
                loss = last_close[i] - cls
                if not math.isfinite(loss):
                    error("invalid loss detected")
                losses.append(loss)

            last_close[i] = cls

        iter_loss = 0
        weights = mwu.get_weights()
        for i, loss in enumerate(losses):
            # We're going to say that every day, we sell everything then buy everything according to weights
            iter_loss = loss * weights[i] / sum(weights) * money / start_money
        money -= iter_loss

        mwu.run_iteration(losses, max_loss=money)
        iteration += 1
        if iteration % 100 == 0:
            verbose("{} iterations done".format(iteration), end="\r")

    verbose("\n{} iterations done".format(iteration))
    info("Money: {} vs {} at start, gain = {}".format(money, start_money, (money - start_money) / start_money))
    info("MWU reported loss = {}".format(mwu.get_loss()))
    weights = mwu.get_weights()
    losses = mwu.get_losses()
    info("Stats:")
    for i, stock in enumerate(stocks.keys()):
        info("{}: weight {}, loss {}".format(stock.upper(), weights[i], losses[i]))

if __name__ == "__main__":
    run_mwu()
