__author__ = "AlecZ"

# lib imports
import os
import csv
import datetime
import math
from collections import OrderedDict

# custom imports
import util
from util import verbose, info

# constants
DATA_DIR = "data"
KEY_CLOSE = 0
KEY_VOLUME = 1
KEY_OPEN = 2
KEY_HIGH = 3
KEY_LOW = 4

class MWU:

    def __init__(self, num_experts, epsilon=0.25):
        self._weights = [1.0] * num_experts
        self._epsilon = epsilon
        self._loss = 0
        self._losses = [0.0] * num_experts

    def run_iteration(self, expert_losses):
        for i, loss in enumerate(expert_losses):
            prob = self._weights[i] / sum(self._weights)
            e_loss = loss * prob
            self._loss += e_loss # TODO IDK about this...
            self._losses[i] += e_loss
            self._weights[i] = self._weights[i] * pow((1 - self._epsilon), loss)

    def get_loss(self):
        return self._loss

    def get_losses(self):
        return self._losses

    def get_weights(self):
        return self._weights

def load_data(dir=DATA_DIR):
    stocks = OrderedDict() # stock: tuple
    dates = set()

    for fname in os.listdir(dir):
        if not fname.endswith(".csv"):
            continue

        verbose("Opening file {}... ".format(fname), end="")
        f = open(dir + "/" + fname, "r")
        c = csv.reader(f)
        date_price = {} # {date: (dict with mappings for close, volume, open, high, low)}
        short_date_price = {} # {date: (dict with mappings for close, volume, open, high, low)}
        first = True
        for row in c:
            if first:
                first = False
                continue
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
        f.close()
        symbol = fname.split(".")[0]
        stocks[symbol] = date_price
        stocks["-" + symbol] = short_date_price
        verbose("Done. Loaded {} dates.".format(len(date_price)))

    return (stocks, sorted(dates))

def run_mwu(start_money=1.0):

    stocks, dates = load_data()
    mwu = MWU(len(stocks))
    last_close = [None] * len(stocks)

    money = start_money
    iteration = 0
    for date in dates:
        losses = []
        for i, tup in enumerate(stocks.items()):
            stock, date_price = tup
            price = date_price[date]
            cls, vol, op, hi, lo = price[KEY_CLOSE], price[KEY_VOLUME], price[KEY_OPEN], price[KEY_HIGH], price[KEY_LOW]

            if last_close[i] is not None:
                abs_loss = last_close[i] - cls
                frac_loss = abs_loss / math.fabs(last_close[i])
                losses.append(frac_loss)

            last_close[i] = cls

        iter_loss = 0
        weights = mwu.get_weights()
        for i, loss in enumerate(losses):
            # We're going to say that every day, we sell everything then buy everything according to weights
            iter_loss += loss * weights[i] / sum(weights)
        money -= money * iter_loss

        mwu.run_iteration(losses)
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
