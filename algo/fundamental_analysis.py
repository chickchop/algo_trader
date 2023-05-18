import platform
from datetime import datetime, timedelta
import pandas as pd
import matplotlib
import matplotlib.pyplot as plt
from matplotlib import font_manager, rc

from .data_reader import get_corp_book_data

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

def get_analysis_result(category, corp, analysis_type=1, start_date=defalut_option["start_date"]) :
    corp_nm, corp_code, stock_df, status = get_corp_book_data(category, corp)
    if analysis_type == 1 :
        return analysis_kpi(corp_nm, corp_code, stock_df, status)
    else :
        return analysis_factor_model(corp_nm, corp_code, stock_df, status)
    
def analysis_kpi(corp_nm, corp_code, stock_df, status) :
    if status == "Sucess" :        
        # fig, ax = plt.subplots()
        # fig = pd.plotting.table(ax=ax,data=stock_df)

        comment = "종목명 : {}({}) \n".format(stock_df["종목명"], stock_df["종목코드"])
        comment += "DPS : {}\n".format(stock_df["DPS"])
        comment += "배당수익률 : {}\n".format(stock_df["배당수익률"])
        comment += "배당금총액 : {}\n".format(stock_df["배당금총액"])
        comment += "EPS : {}\n".format(stock_df["EPS"])
        comment += "PER : {}\n".format(stock_df["PER"])
        comment += "BPS : {}\n".format(stock_df["BPS"])
        comment += "ROE : {}\n".format(stock_df["ROE"])
        comment += "ROA : {}\n".format(stock_df["ROA"])
        comment += "DE : {}\n".format(stock_df["DE"])

        return None, 200, status, comment
    else :
        comment = "잘못된 입력입니다."
        return None, 500, status, comment

def analysis_factor_model(corp_nm, corp_code, stock_df, status) :
    print(status)
