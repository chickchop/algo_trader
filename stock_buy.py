import pandas_datareader.data as reader
import datetime
import matplotlib.pyplot as plt
from zipline.api import order, symbol
from zipline.algorithm import TradingAlgorithm

start_time = datetime.datetime(2016, 2, 19)
end_time = datetime.datetime(2019, 10, 4)

dat = reader.DataReader("078930.KS", "yahoo", start_time, end_time)
dat = dat[dat["Volume"] != 0]
dat = dat[["Adj Close"]]
dat.columns= ["078930.KS"]
dat = dat.tz_localize("UTC")

def initialize(context):
    pass

def handle_data(context, dat):
    order(symbol("078930.KS"),1)


algo = TradingAlgorithm(initialize=initialize, handle_data=handle_data)

#FIXME zipline api bug. reference -> https://stackoverflow.com/questions/56957791/getting-jsondecodeerror-expecting-value-line-1-column-1-char-0-with-python