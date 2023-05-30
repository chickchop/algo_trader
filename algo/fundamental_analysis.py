import platform
from datetime import datetime, timedelta
import pandas as pd
import matplotlib
import matplotlib.pyplot as plt
from matplotlib import font_manager, rc

from .data_reader import get_corp_book_data, get_corp_last_book_data
from .valuation_models import RIM

if platform.system() == 'Windows':
    font_name = font_manager.FontProperties(fname="c:/Windows/Fonts/malgun.ttf").get_name()
    rc('font', family=font_name)
elif platform.system() == 'Mac' :    
# Mac 인 경우
    rc('font', family='AppleGothic')
else :
    rc('font', family='NanumGothic')

matplotlib.rcParams['axes.unicode_minus'] = False
defalut_option = {
    "start_date" : datetime.today() - timedelta(days=80)
}

def get_analysis_result(category, corp, analysis_type=1, start_date=defalut_option["start_date"]) :
    if analysis_type == 1 :
        corp_nm, corp_code, stock_df, status = get_corp_book_data(category, corp)
        return analysis_kpi(corp_nm, corp_code, stock_df, status)
    else :
        corp_nm, corp_code, corp_finance_data, status = get_corp_last_book_data(category, corp)
        return analysis_RIM(corp_nm, corp_code, corp_finance_data, status)
    
def analysis_kpi(corp_nm, corp_code, stock_df, status) :
    if status == "Sucess" :        
        # fig, ax = plt.subplots()
        # fig = pd.plotting.table(ax=ax,data=stock_df)

        comment = "재무제표를 기반으로 기업의 가치를 평가하기 위한 투자 지표들입니다.\n"
        comment += "투자지표는 절대적인 값이 아닌 상대적인 값입니다. 산업군 평균이나 경쟁 기업들과 비교해서 지표를 봐야합니다. \n"
        comment += "종목명 : {}({}) \n".format(stock_df["종목명"], stock_df["종목코드"])
        comment += "기준주가 : {} \n".format(stock_df["기준주가"])
        comment += "사용 사업보고서 : {}({}) \n".format(stock_df["보고서명칭"], stock_df["사업연도"])
        comment += "DPS(안전마진) : {}\n".format(stock_df["DPS"])
        comment += "배당수익률(안전마진) : {}%\n".format(stock_df["배당수익률"])
        comment += "배당금총액(안전마진) : {}\n".format(stock_df["배당금총액"])
        comment += "ROE(수익성지표) : {}%\n".format(stock_df["ROE"] *  100)
        comment += "ROA(수익성지표) : {}%\n".format(stock_df["ROA"] *  100)
        comment += "SPS(수익성지표) : {}\n".format(stock_df["SPS"])
        comment += "PSR(수익성지표) : {}\n".format(stock_df["PSR"])
        comment += "CPS(수익성지표) : {}\n".format(stock_df["CPS"])
        comment += "PCR(수익성지표) : {}\n".format(stock_df["PCR"])
        comment += "DE(재무위험지표) : {}%\n".format(stock_df["DE"] *  100)
        comment += "EPS(주식가치지표) : {}\n".format(stock_df["EPS"])
        comment += "PER(주식가치지표) : {}\n".format(stock_df["PER"])
        comment += "BPS(주식가치지표) : {}\n".format(stock_df["BPS"])
        comment += "PBR(주식가치지표) : {}\n".format(stock_df["PBR"])

        return None, 200, status, comment
    else :
        comment = "잘못된 입력입니다."
        return None, 500, status, comment

def analysis_RIM(corp_nm, corp_code, corp_finance_data, status) :
    if status == "Sucess" :
        ROE = corp_finance_data["ROE"].mean()
        equity = corp_finance_data["equity"][-1:].iloc[0]
        total_stock = corp_finance_data["total_stock"][-1:].iloc[0]
        current_price = corp_finance_data["current_price"][-1:].iloc[0]
        
        model = RIM(corp_nm, ROE, equity)
        value = model.calculate_corp_val()

        import requests
        from bs4 import BeautifulSoup

        url = "https://www.kisrating.co.kr/ratingsStatistics/statics_spread.do#"

        r = requests.get(url)
        page = BeautifulSoup(r.text, 'lxml')
        tbl_section = page.select_one('div.table_ty1')

        tbl_html = str(tbl_section)
        df = pd.read_html(tbl_html)[0]
        df.set_index("구분", inplace=True)

        intrest_rate = df.loc['BBB-', '5년']
        intrest_rate = intrest_rate * 0.01
        discounted_value = model.calculate_corp_val(target_return_rate=intrest_rate, discount_roe=0.9)
        price = model.target_price(value, total_stock)
        discounted_price = model.target_price(discounted_value, total_stock)


        comment = "잔여이익을 기반으로 한 절대가치를 산정한 RIM 모델입니다. \n"
        comment += "목표 수익률을 {}% 선정했습니다.  \n".format(intrest_rate*100)
        comment += "예측된 ROE 는 {}%로 선정했습니다.  \n".format(round(ROE * 100, 2))
        comment += "현재 주가는 {} 입니다.  \n".format(current_price)
        comment += "적정 주가는 {} 입니다.  \n".format(price)
        comment += "실적 저하일 경우를 대비한 적정 주가는 {} 입니다.  \n".format(discounted_price)
        
    
        return None, 200, status, comment
    else :
        comment = "잘못된 입력입니다."
        return None, 500, status, comment