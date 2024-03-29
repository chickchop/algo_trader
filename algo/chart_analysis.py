import platform
from datetime import datetime, timedelta
import numpy as np
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
        comment += "캔들 차트와 이동 평균선 차트 입니다. 추세매매에 사용하는 분석 도구입니다. 이동평균선간의 교차와 거래량을 이용하여 추세를 나타냅니다. \n"

        up = stock_df[stock_df["Close"] >= stock_df["Open"]]
        down = stock_df[stock_df["Close"] < stock_df["Open"]]
        width = .5
        width2 = .03


        fig = plt.figure(figsize=(10,7))
        axes =  plt.subplot2grid((4,4), (0,0), rowspan=3, colspan=4)
        bottom_axes = plt.subplot2grid((4,4), (3,0), rowspan=1, colspan=4)
        bottom_axes.get_yaxis().get_major_formatter().set_scientific(False)

        axes.plot(stock_df.index.strftime("%Y-%m-%d"), stock_df['Close'], label='종가', linewidth=0.7)
        axes.plot(stock_df.index.strftime("%Y-%m-%d"), stock_df['ma5'], label='MA5', linewidth=0.7)
        axes.plot(stock_df.index.strftime("%Y-%m-%d"), stock_df['ma20'], label='MA20', linewidth=0.7)
        axes.plot(stock_df.index.strftime("%Y-%m-%d"), stock_df['ma60'], label='MA60', linewidth=0.7)
        axes.plot(stock_df.index.strftime("%Y-%m-%d"), stock_df['ma120'], label='MA120', linewidth=0.7)
        axes.bar(up.index.strftime("%Y-%m-%d"), up["Close"]-up["Open"], width, bottom=up["Open"], color="red")
        axes.bar(up.index.strftime("%Y-%m-%d"), up["High"]-up["Close"], width2, bottom=up["Close"], color="red")
        axes.bar(up.index.strftime("%Y-%m-%d"), up["Low"]-up["Open"], width2, bottom=up["Open"], color="red")
        
        # Plotting down prices of the stock
        axes.bar(down.index.strftime("%Y-%m-%d"), down["Close"]-down["Open"], width, bottom=down["Open"], color="blue")
        axes.bar(down.index.strftime("%Y-%m-%d"), down["High"]-down["Close"], width2, bottom=down["Close"], color="blue")
        axes.bar(down.index.strftime("%Y-%m-%d"), down["Low"]-down["Open"], width2, bottom=down["Open"], color="blue")

        axes.set_title(f'{corp_nm}(주가차트)')
        axes.legend(loc='best')

        tmp_comment1 = "중기 신호 없음"
        for i in range(stock_df.shape[0]):
            if i == 0 :
                continue
            if stock_df['ma20'].values[i] > stock_df['ma60'].values[i] and stock_df['ma20'].values[i-1] < stock_df['ma60'].values[i-1] :
                axes.plot(stock_df.index.strftime("%Y-%m-%d").values[i], stock_df['ma20'].values[i], 'r^')
                tmp_comment1 = "중기 골든 크로스. 매수 신호 발생"
            elif stock_df['ma20'].values[i] < stock_df['ma60'].values[i] and stock_df['ma20'].values[i-1] > stock_df['ma60'].values[i-1] :
                axes.plot(stock_df.index.strftime("%Y-%m-%d").values[i], stock_df['ma20'].values[i], 'bv')
                tmp_comment1 = "중기 데드 크로스. 매도 신호 발생"
        comment = comment + tmp_comment1 + "\n"

        tmp_comment2 = "장기 신호 없음"
        for i in range(stock_df.shape[0]):
            if i == 0 :
                continue
            if stock_df['ma60'].values[i] > stock_df['ma120'].values[i] and stock_df['ma60'].values[i-1] < stock_df['ma120'].values[i-1] :
                axes.plot(stock_df.index.strftime("%Y-%m-%d").values[i], stock_df['ma60'].values[i], 'r^')
                tmp_comment2 = "장기 골든 크로스. 매수 신호 발생"
            elif stock_df['ma60'].values[i] < stock_df['ma120'].values[i] and stock_df['ma60'].values[i-1] > stock_df['ma120'].values[i-1] :
                axes.plot(stock_df.index.strftime("%Y-%m-%d").values[i], stock_df['ma60'].values[i], 'bv')
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
        bottom_axes.bar(stock_df.index.strftime("%Y-%m-%d"), stock_df['Volume'], color=color_list)
        bottom_axes.get_yaxis().get_major_formatter().set_scientific(False) # 거래량 값 그대로 표현
        axes.get_xaxis().set_ticks([])
        bottom_axes.tick_params(axis='x', labelrotation=70)

        ##### analysis
        if stock_df[-1:]["ma5"].iloc[0] > stock_df[-1:]["ma20"].iloc[0] :
            if stock_df[-1:]["Open"].iloc[0] * 1.15 <= stock_df[-1:]["Close"].iloc[0] and stock_df[-1:]["Open"].iloc[0] == stock_df[-1:]["Low"].iloc[0] and stock_df[-1:]["Close"].iloc[0] == stock_df[-1:]["High"].iloc[0] :
                comment = comment + "상승장에서 나타난 장대 양봉입니다. 추가 상승이 예상되니 불타기(매수)를 추천합니다. \n"
            elif stock_df[-1:]["Open"].iloc[0] * 1.05 <= stock_df[-1:]["Close"].iloc[0] and stock_df[-1:]["Open"].iloc[0] != stock_df[-1:]["Low"].iloc[0] and stock_df[-1:]["Close"].iloc[0] == stock_df[-1:]["High"].iloc[0] :
                comment = comment + "상승장에서 나타난 밑꼬리 양봉입니다. 상승 추세 지속이 예상됩니다. \n"
            elif stock_df[-1:]["Open"].iloc[0] * 0.85 >= stock_df[-1:]["Close"].iloc[0] :
                if stock_df[-1:]["Open"].iloc[0] == stock_df[-1:]["High"].iloc[0] and stock_df[-1:]["Close"].iloc[0] == stock_df[-1:]["Low"].iloc[0] :
                    comment = comment + "상승장에서 나타난 장대 음봉입니다. 하락 추세 전환이 예상되니 수익실현(매도)을 추천합니다. \n"
            elif stock_df[-1:]["Open"].iloc[0] * 0.90 >= stock_df[-1:]["Low"].iloc[0] and stock_df[-1:]["Open"].iloc[0] == stock_df[-1:]["High"].iloc[0] and stock_df[-1:]["Close"].iloc[0] != stock_df[-1:]["Low"].iloc[0] :
                    comment = comment + "상승장에서 나타난 하락 샅바형입니다. 거래량이 동반된 경우 추세 전환이 예상되니 수익실현(매도)을 추천합니다. \n"
            elif stock_df[-1:]["Open"].iloc[0] * 0.95 >= stock_df[-1:]["Close"].iloc[0] and stock_df[-1:]["Open"].iloc[0] == stock_df[-1:]["High"].iloc[0] and stock_df[-2:-1]["Volume"].iloc[0] * 3 < stock_df[-1:]["Volume"].iloc[0] :
                comment = comment + "상승장에서 나타난 교수형입니다. 대량 거래가 발생했으므로 추세 전환이 예상되니 수익실현(매도)을 추천합니다. \n"
        elif stock_df[-1:]["ma5"].iloc[0] < stock_df[-1:]["ma20"].iloc[0] :
            if stock_df[-1:]["Open"].iloc[0] * 0.85 >= stock_df[-1:]["Close"].iloc[0] and stock_df[-1:]["Open"].iloc[0] == stock_df[-1:]["High"].iloc[0] and stock_df[-1:]["Clow"].iloc[0] == stock_df[-1:]["Low"].iloc[0] :
                comment = comment + "하락장에서 나타난 장대 음봉입니다. 추가 하락이 예상되니 손절(매도)를 추천합니다. \n"
            elif stock_df[-1:]["Open"].iloc[0] * 1.10 <= stock_df[-1:]["High"].iloc[0] and stock_df[-1:]["Open"].iloc[0] == stock_df[-1:]["Low"].iloc[0] :
                comment = comment + "하락장에서 나타난 상승 샅바형입니다. 기술적 반등이 예상되니 물렸다면 물타기 후 상승시 손절을 추천합니다. \n"
            elif stock_df[-1:]["Open"].iloc[0] * 1.05 <= stock_df[-1:]["Close"].iloc[0] and stock_df[-1:]["Close"].iloc[0] == stock_df[-1:]["High"].iloc[0] :
                comment = comment + "하락장에서 나타난 망치형입니다. 추가적인 하락이 나올 수 있으니 물타기를 비추천하고 손절을 추천합니다. \n"
            elif stock_df[-1:]["Open"].iloc[0] * 0.95 >= stock_df[-1:]["Close"].iloc[0] and stock_df[-1:]["Open"].iloc[0] != stock_df[-1:]["High"].iloc[0] and stock_df[-1:]["Close"].iloc[0] == stock_df[-1:]["Low"].iloc[0] :
                comment = comment + "상승장에서 나타난 윗꼬리 음봉입니다. 하락 추세 지속이 예상됩니다. \n"
            


        if stock_df[-1:]["ma5"].iloc[0] > stock_df[-1:]["ma20"].iloc[0] and stock_df[-1:]["ma20"].iloc[0] > stock_df[-1:]["ma60"].iloc[0] and stock_df[-1:]["Change"].iloc[0] < 0 :
            comment = comment + "주가가 정배열(상승추세)인 상태에서 하락했습니다. 저가 매수세가 나타날 수 있습니다. 보유중이면 추가 매수를 추천합니다. \n"
        elif stock_df[-1:]["ma5"].iloc[0] < stock_df[-1:]["ma20"].iloc[0] and stock_df[-1:]["ma20"].iloc[0] < stock_df[-1:]["ma60"].iloc[0] and stock_df[-1:]["Change"].iloc[0] > 0 :
            comment = comment + "주가가 역배열(하락추세)인 상태에서 상승했습니다. 고가 매도세가 나타날 수 있습니다. 물렸다면 손절을 할 타이밍입니다. \n"

        return fig, 200, status, comment
    else :
        comment = "잘못된 입력입니다."
        return None, 500, status, comment

def analysis_bollinger_bands(corp_nm, corp_code, stock_df, status) :
    print(status)
    if status == "Sucess" :
        ##### plot
        comment = "차트 분석은 거래량이 많고 변동성이 큰 주식의 단타매매에 적합합니다. \n"
        comment += "볼린저 벤드와 MFI 차트입니다. 변동성을 이용한 추세매매에 사용하는 분석 도구입니다. 표준 편차를 이용하여 변동성을 계산합니다. \n\n"


        fig, axes = plt.subplots(nrows=3, ncols=1, figsize=(10, 30), sharex=True)
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

        axes[1].plot(stock_df.index, stock_df['bandwidth'], label='밴드폭', color="brown")
        axes[1].grid(True)
        axes[1].legend(loc='best')
        
        bw_status = "변동성이 추세를 이어갑니다."
        for i in range(len(stock_df['Close'])-1):
            if stock_df['bandwidth'].values[i-1] < stock_df['bandwidth'].values[i] and stock_df['bandwidth'].values[i] > stock_df['bandwidth'].values[i+1]:
                bw_status = "변동성이 하락 전환했습니다."
            elif stock_df['bandwidth'].values[i-1] > stock_df['bandwidth'].values[i] and stock_df['bandwidth'].values[i] < stock_df['bandwidth'].values[i+1]:
                bw_status = "변동성이 상승 전환했습니다."

        pb_status = "PB가 추세를 이어갑니다."
        for i in range(len(stock_df['Close'])-1):
            if stock_df['PB'].values[i-1] < stock_df['PB'].values[i] and stock_df['PB'].values[i] > stock_df['PB'].values[i+1]:
                pb_status = "PB가 하락 전환했습니다."
            elif stock_df['PB'].values[i-1] > stock_df['PB'].values[i] and stock_df['PB'].values[i] < stock_df['PB'].values[i+1]:
                pb_status = "PB가 상승 전환했습니다."

        axes[2].plot(stock_df.index, stock_df['MFI10'], label='MFI10', color="orange")
        axes[2].axhline(y=80, color="red", linestyle='dotted')
        axes[2].axhline(y=20, color="red", linestyle='dotted')
        axes[2].grid(True)
        axes[2].legend(loc='best')

        ##### analysis
        if stock_df[:int(len(stock_df)/2)]["bandwidth"].mean() > stock_df[int(len(stock_df)/2):]["bandwidth"].mean() :
            comment = comment + "볼린저 밴드의 Bandwidth 가 감소하고 있습니다. 변동성이 낮아지고 있습니다. "+ bw_status + "\n"
        else :
            comment = comment + "볼린저 밴드의 Bandwidth 가 증가하고 있습니다. 변동성이 증가하고 있습니다. "+ bw_status + "\n"

        if stock_df[-1:]["Close"].iloc[0] < stock_df[-1:]["upper"].iloc[0] and stock_df[-1:]["Close"].iloc[0] > stock_df[-1:]["lower"].iloc[0] :
            comment = comment + "볼린저 밴드의 내부에 있습니다. 박스권 입니다. 현대 박스권 내 위치는 {} % 입니다. \n".format(round(stock_df[-1:]["PB"].iloc[0], 2)*100)
            if stock_df[:int(len(stock_df)/2)]["PB"].mean() > stock_df[int(len(stock_df)/2):]["PB"].mean() :
                comment = comment + "PB 가 감소하고 있습니다. 박스권 내에서 하락추세 입니다. " + pb_status + "\n"
            else :
                comment = comment + "PB 가 증가하고 있습니다. 박스권 내에서 상승추세 입니다. " + pb_status + "\n"
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