import pandas_datareader as reader
import datetime
import matplotlib.pyplot as plt

start_time = datetime.datetime(2016, 2, 19)
end_time = datetime.datetime(2019, 10, 4)

gs_data = reader.DataReader("078930.KS", "yahoo", start_time, end_time)
gs_data = gs_data[gs_data["Volume"] != 0]
plt.plot(gs_data["Adj Close"])

ma5 = gs_data["Adj Close"].rolling(window=5).mean()
ma20 = gs_data["Adj Close"].rolling(window=20).mean()
ma60 = gs_data["Adj Close"].rolling(window=60).mean()
ma120 = gs_data["Adj Close"].rolling(window=120).mean()

gs_data.insert(len(gs_data.columns), "MA5", ma5)
gs_data.insert(len(gs_data.columns), "MA20", ma20)
gs_data.insert(len(gs_data.columns), "MA60", ma60)
gs_data.insert(len(gs_data.columns), "MA120", ma120)

plt.plot(gs_data["Adj Close"], label="Adj close")
plt.plot(gs_data["MA5"], label="MA5")
plt.plot(gs_data["MA20"], label="MA20")
plt.plot(gs_data["MA60"], label="MA60")
plt.plot(gs_data["MA120"], label="MA120")
plt.legend(loc="best")
plt.grid()
plt.show()
