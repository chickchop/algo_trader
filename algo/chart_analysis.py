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

def get_chart_result(category, corp, analysis_type=1, start_date=defalut_option["start_date"]) :
    corp_nm, corp_code, stock_df, status = get_corp_data(category, corp, start_date)
    if analysis_type == 1 :
        return analysis_olhc(corp_nm, corp_code, stock_df, status)
    else :
        return analysis_bollinger_bands(corp_nm, corp_code, stock_df, status)
    

def analysis_olhc(corp_nm, corp_code, stock_df, status) :
    if status == "Sucess" :
        ## plot
        comment = "차트 분석은 거래량이 많고 변동성이 큰 주식의 단타매매에 적합합니다. \n"
        comment += "기초 캔들 차트와 이동 평균선 차트 입니다. 추세매매에 사용하는 분석 도구입니다. 이동평균선간의 교차와 거래량을 이용합니다. \n"

        width = .3
        width2 = .03

        fig = plt.figure(figsize=(10,10))
        axes =  plt.subplot2grid((4,4), (0,0), rowspan=3, colspan=4)
        bottom_axes = plt.subplot2grid((4,4), (3,0), rowspan=1, colspan=4, sharex=axes)
        bottom_axes.get_yaxis().get_major_formatter().set_scientific(False)
        axes.bar(up.index, up["Close"]-up["Open"], width, bottom=up["Open"], color="red")
        axes.bar(up.index, up["High"]-up["Close"], width2, bottom=up["Close"], color="red")
        axes.bar(up.index, up["Low"]-up["Open"], width2, bottom=up["Open"], color="red")
        
        # Plotting down prices of the stock
        axes.bar(down.index, down["Close"]-down["Open"], width, bottom=down["Open"], color="blue")
        axes.bar(down.index, down["High"]-down["Close"], width2, bottom=down["Close"], color="blue")
        axes.bar(down.index, down["Low"]-down["Open"], width2, bottom=down["Open"], color="blue")

        axes.plot(stock_df.index, stock_df['Close'], label='종가', linewidth=0.7)
        axes.plot(stock_df.index, stock_df['ma5'], label='MA5', linewidth=0.7)
        axes.plot(stock_df.index, stock_df['ma20'], label='MA20', linewidth=0.7)
        axes.plot(stock_df.index, stock_df['ma60'], label='MA60', linewidth=0.7)
        axes.plot(stock_df.index, stock_df['ma120'], label='MA120', linewidth=0.7)

        tmp_comment1 = "중기 신호 없음"
        for i in range(stock_df.shape[0]):
            if stock_df['ma20'].values[i] > stock_df['ma60'].values[i] :
                axes.plot(stock_df.index.values[i], stock_df['Close'].values[i], 'r^')
                tmp_comment1 = "중기 골든 크로스. 매수 신호 발생"
            elif stock_df['ma20'].values[i] < stock_df['ma60'].values[i] :
                axes.plot(stock_df.index.values[i], stock_df['Close'].values[i], 'bv')
                tmp_comment1 = "중기 데드 크로스. 매도 신호 발생"
        comment = comment + tmp_comment1 + "\n"

        tmp_comment2 = "장기 신호 없음"
        for i in range(stock_df.shape[0]):
            if stock_df['ma60'].values[i] > stock_df['ma120'].values[i] :
                axes.plot(stock_df.index.values[i], stock_df['Close'].values[i], 'r^')
                tmp_comment2 = "장기 골든 크로스. 매수 신호 발생"
            elif stock_df['ma60'].values[i] < stock_df['ma120'].values[i] :
                axes.plot(stock_df.index.values[i], stock_df['Close'].values[i], 'bv')
                tmp_comment2 = "장기 데드 크로스. 매도 신호 발생"
        comment = comment + tmp_comment2 + "\n"

        axes.set_title(f'{corp_nm}(주가차트)')
        axes.legend(loc='best')

        # 색깔 구분을 위한 함수
        color_fuc = lambda x : 'r' if x >= 0 else 'b'

        # kospi 거래량의 차이 
        stock_df['Volume'].diff().fillna(0) ## 첫 행은 값이 Nan이므로 0으로 채워줌

        # 색깔 구분을 위한 함수를 apply 시켜 Red와 Blue를 구분한다.
        color_df = stock_df['Volume'].diff().fillna(0).apply(color_fuc)

        # 구분된 값을 list 형태로 만들어준다.
        color_list = list(color_df)

        # 거래량 그래프
        bottom_axes.bar(stock_df.index, stock_df['Volume'], color=color_list)
        bottom_axes.get_yaxis().get_major_formatter().set_scientific(False) # 거래량 값 그대로 표현

        ##### analysis
        if stock_df[-1:]["ma5"].iloc[0] > stock_df[-1:]["ma20"].iloc[0] and stock_df[-1:]["ma20"].iloc[0] > stock_df[-1:]["ma60"].iloc[0] and stock_df[-1:]["Change"] < 0 :
            comment = comment + "주가가 정배열인 상태에서 하락했습니다. 저가 매수세가 나타날 수 있습니다. \n"
        elif stock_df[-1:]["ma5"].iloc[0] < stock_df[-1:]["ma20"].iloc[0] and stock_df[-1:]["ma20"].iloc[0] < stock_df[-1:]["ma60"].iloc[0] and stock_df[-1:]["Change"] > 0 :
            comment = comment + "주가가 역배열인 상태에서 상승했습니다. 고가 매도세가 나타날 수 있습니다. \n"

        return fig, 200, status, comment
    else :
        comment = "잘못된 입력입니다."
        return None, 500, status, comment

def analysis_bollinger_bands(corp_nm, corp_code, stock_df, status) :
    print(status)
    if status == "Sucess" :
        ##### plot
        comment = "차트 분석은 거래량이 많고 변동성이 큰 주식의 단타매매에 적합합니다. \n"
        comment += "볼린저 벤드는 주가의 변동성을 이용한 추세매매에 사용하는 분석 도구입니다. 표준 편차를 이용하여 변동성을 계산합니다. \n\n"

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

        fig, axes = plt.subplots(nrows=4, ncols=1, figsize=(10, 30), sharex=True)
        axes[0].plot(stock_df.index, stock_df['Close'], label='종가')
        axes[0].plot(stock_df.index, stock_df['upper'], linestyle='dashed', label='Upper band')
        axes[0].plot(stock_df.index, stock_df['ma20'], linestyle='dashed', label='Moving Average 20')
        axes[0].plot(stock_df.index, stock_df['lower'], linestyle='dashed', label='Lower band')
        axes[0].set_title(f'{corp_nm}({corp_code})의 볼린저 밴드(20일, 2 표준편차)')
        tmp_comment = "신호 없음"
        for i in range(stock_df.shape[0]):
            if stock_df['PB'].values[i] > 0.8 and stock_df['MFI10'].values[i] > 80:
                axes[0].plot(stock_df.index.values[i], stock_df['Close'].values[i], 'r^')
                tmp_comment = "볼린저 밴드와 MFI 지수 고려한 매수 신호 발생"
            elif stock_df['PB'].values[i] < 0.2 and stock_df['MFI10'].values[i] < 20:
                axes[0].plot(stock_df.index.values[i], stock_df['Close'].values[i], 'bv')
                tmp_comment = "볼린저 밴드와 MFI 지수 고려한 매도 신호 발생"
        comment = comment + tmp_comment + "\n"
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
        if stock_df[:int(len(stock_df)/2)]["bandwidth"].mean() > stock_df[int(len(stock_df)/2):]["bandwidth"].mean() :
            comment = comment + "볼린저 밴드의 Bandwidth 가 감소하고 있습니다. 변동성이 낮아지고 있습니다. \n"
        else :
            comment = comment + "볼린저 밴드의 Bandwidth 가 증가하고 있습니다. 변동성이 증가하고 있습니다. \n"

        if stock_df[-1:]["Close"].iloc[0] < stock_df[-1:]["upper"].iloc[0] and stock_df[-1:]["Close"].iloc[0] > stock_df[-1:]["lower"].iloc[0] :
            comment = comment + "볼린저 밴드의 내부에 있습니다. 박스권 입니다. 현대 박스권 내 위치는 {} % 입니다. \n".format(round(stock_df[-1:]["PB"].iloc[0], 2)*100)
            if stock_df[:int(len(stock_df)/2)]["PB"].mean() > stock_df[int(len(stock_df)/2):]["PB"].mean() :
                comment = comment + "PB 가 감소하고 있습니다. 박스권 내에서 하락추세 입니다. \n"
            else :
                comment = comment + "PB 가 증가하고 있습니다. 박스권 내에서 상승추세 입니다. \n"
            if stock_df[-1:]["PB"].iloc[0] < 0.1 :
                comment = comment + "볼린저 밴드의 하단 입니다. MFI 지수를 고려한 후 매수를 고려하세요. \n"
            elif stock_df[-1:]["PB"].iloc[0] > 0.9 :
                comment = comment + "볼린저 밴드의 상단 입니다. MFI 지수를 고려한 후 매수를 고려하세요. \n"

        elif stock_df[-1:]["Close"].iloc[0] > stock_df[-1:]["upper"].iloc[0] and stock_df[:int(len(stock_df)/2)]["bandwidth"].mean() < stock_df[int(len(stock_df)/2):]["bandwidth"].mean() :
            comment = comment + "볼린저 밴드의 상단 이탈이지만 변동성이 큽니다. 호재가 있는지 확인 후 매수하세요. 호재가 없다면 급락할 수 있습니다. \n"
        elif stock_df[-1:]["Close"].iloc[0] > stock_df[-1:]["upper"].iloc[0] and stock_df[:int(len(stock_df)/2)]["bandwidth"].mean() > stock_df[int(len(stock_df)/2):]["bandwidth"].mean() :
            comment = comment + "볼린저 밴드의 상단 이탈이지만 변동성이 작습니다. 대세 상승일 수 있습니다. \n"
        else :
            comment = comment + "볼린저 밴드의 박스권 밖 이탈입니다. 호재, 악재 여부를 확인 후 매수 혹은 매도하세요. \n"

        if stock_df[-1:]['MFI10'].iloc[0] <= 20 :
            comment = comment + "MFI 지수가 20 아래입니다. 거래량이 죽었습니다. \n"
            if stock_df[-1:]["Close"].iloc[0] < stock_df[-1:]["ma20"].iloc[0] :
                comment = comment + "매도를 고려해야 합니다. \n"
            else :
                comment = comment + "과잉 매도입니다. \n"
        elif stock_df[-1:]['MFI10'].iloc[0] >= 80 :   
            comment = comment + "MFI 지수가 80 위입니다. 과열 되었습니다. \n"
            if stock_df[-1:]["Close"].iloc[0] > stock_df[-1:]["ma20"].iloc[0] :
                comment = comment + "추격 매수를 고려해야 합니다. \n"
            else :
                comment = comment + "과잉 매수입니다. \n"

        return fig, 200, status, comment
    else :
        comment = "잘못된 입력입니다."
        return None, 500, status, comment