import platform
from datetime import datetime, timedelta
import mplfinance as mpf
import pandas as pd
import matplotlib
import matplotlib.pyplot as plt
from matplotlib import font_manager, rc

from .data_reader import get_corp_data

if platform.system() == 'Windows':
    font_name = font_manager.FontProperties(fname="c:/Windows/Fonts/malgun.ttf").get_name()
    rc('font', family=font_name)
else:    
# Mac 인 경우
    rc('font', family='AppleGothic')

matplotlib.rcParams['axes.unicode_minus'] = False
defalut_option = {
    "start_date" : datetime.today() - timedelta(days=80)
}

def analysis_bollinger_bands(category, corp, start_date=defalut_option["start_date"]) :
    corp_nm, corp_code, stock_df, status = get_corp_data(category, corp, start_date)

    if status == "Sucess" :
        stock_df['ma20'] = stock_df['Close'].rolling(window=20).mean() # 20일 이동평균
        stock_df['stddev'] = stock_df['Close'].rolling(window=20).std() # 20일 이동표준편차
        stock_df['upper'] = stock_df['ma20'] + 2*stock_df['stddev'] # 상단밴드
        stock_df['lower'] = stock_df['ma20'] - 2*stock_df['stddev'] # 하단밴드
        stock_df['PB'] = (stock_df["Close"] - stock_df['lower']) / (stock_df["upper"] - stock_df['lower'])
        stock_df['bandwidth'] = (stock_df["upper"] - stock_df['lower']) / (stock_df["ma20"])
        
        # 10일(거래일 기준으로 2주 동안) 기준의 현금흐름지표를 구하는 코드
        stock_df['TP'] = (stock_df['High']+stock_df['Low']+stock_df['Close'])/3
        stock_df['PMF'] = 0
        stock_df['NMF'] = 0
        for i in range(len(stock_df['Close'])-1):
            # 당일의 중심가격이 전일의 중심가격보다 크면 긍정적 현금흐름
            if stock_df['TP'].values[i] < stock_df['TP'].values[i+1]:
                stock_df['PMF'].values[i+1] = stock_df['TP'].values[i+1]*stock_df['Volume'].values[i+1]
                stock_df['NMF'].values[i+1] = 0
            # 당일의 중심가격이 전일의 중심가격보다 작거나 같으면 부정적 현금흐름
            else:
                stock_df['NMF'].values[i+1] = stock_df['TP'].values[i+1]*stock_df['Volume'].values[i+1]
                stock_df['PMF'].values[i+1] = 0
                
        stock_df['MFR'] = stock_df['PMF'].rolling(window=10).sum()/stock_df['NMF'].rolling(window=10).sum()
        stock_df['MFI10'] = 100 - 100/(1+stock_df['MFR'])
        stock_df = stock_df[19:] # 20일 이동평균을 구했기 때문에 20번째 행부터 값이 들어가 있음

        ##### plot
        fig, axes = plt.subplots(nrows=4, ncols=1, figsize=(10, 30), sharex=True)
        axes[0].plot(stock_df.index, stock_df['Close'], label='종가')
        axes[0].plot(stock_df.index, stock_df['upper'], linestyle='dashed', label='Upper band')
        axes[0].plot(stock_df.index, stock_df['ma20'], linestyle='dashed', label='Moving Average 20')
        axes[0].plot(stock_df.index, stock_df['lower'], linestyle='dashed', label='Lower band')
        mpf.candlestick2_ohlc(axes[0],stock_df['Open'],stock_df['High'],
                  stock_df['Low'],stock_df['Close'],width=0.6)
        axes[0].set_title(f'{corp_nm}({corp_code})의 볼린저 밴드(20일, 2 표준편차)')

        for i in range(stock_df.shape[0]):
            if stock_df['PB'].values[i] > 0.8 and stock_df['MFI10'].values[i] > 80:
                axes[0].plot(stock_df.index.values[i], stock_df['Close'].values[i], 'r^')
            elif stock_df['PB'].values[i] < 0.2 and stock_df['MFI10'].values[i] < 20:
                axes[0].plot(stock_df.index.values[i], stock_df['Close'].values[i], 'bv')
        axes[0].legend(loc='best')


        axes[1].plot(stock_df.index, stock_df['PB'], label='%B', color="purple")
        axes[1].grid(True)
        axes[1].legend(loc='best')


        axes[2].plot(stock_df.index, stock_df['bandwidth'], label='밴드폭', color="brown")
        axes[2].grid(True)
        axes[2].legend(loc='best')


        axes[3].plot(stock_df.index, stock_df['MFI10'], label='MFI10', color="orange")
        axes[3].axhline(y=80, color="red", linestyle='dotted')
        axes[3].axhline(y=20, color="red", linestyle='dotted')
        axes[3].grid(True)
        axes[3].legend(loc='best')

        ##### analysis
        comment = "볼린저 벤드는 주가의 변동성을 분석하는 분석 도구입니다. 표준 편차를 이용하여 변동성을 계산합니다. \n"
        if stock_df[:int(len(stock_df)/2)]["bandwidth"].mean() > stock_df[int(len(stock_df)/2):]["bandwidth"].mean() :
            comment = comment + "볼린저 밴드의 Bandwidth 가 감소하고 있습니다. 변동성이 낮아지고 있습니다."
        else :
            comment = comment + "볼린저 밴드의 Bandwidth 가 증가하고 있습니다. 변동성이 증가하고 있습니다."
    
        return fig, 200, status
    else :
        return None, 500, status