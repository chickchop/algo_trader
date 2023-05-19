import FinanceDataReader as fdr
from datetime import datetime, timedelta
import matplotlib.pyplot as plt
import OpenDartReader
import pandas as pd


def get_corp_data(category, text, start_date) :
    df_krx = fdr.StockListing('KRX')
    print("get : " + text)
    try :
        if category == "종목명" :
            corp_nm = text
            corp_code = df_krx[df_krx["Name"] == text]["Code"].iloc[0]
            print(corp_code)
        else :
            corp_code = text
            corp_nm = df_krx[df_krx["Code"] == text]["Name"].iloc[0]
            print(corp_nm)

        stock_df = fdr.DataReader(symbol=corp_code) 
        stock_df['ma20'] = stock_df['Close'].rolling(window=20).mean() # 20일 이동평균
        stock_df['stddev'] = stock_df['Close'].rolling(window=20).std() # 20일 이동표준편차
        stock_df['upper'] = stock_df['ma20'] + 2*stock_df['stddev'] # 상단밴드
        stock_df['lower'] = stock_df['ma20'] - 2*stock_df['stddev'] # 하단밴드
        stock_df['PB'] = (stock_df["Close"] - stock_df['lower']) / (stock_df["upper"] - stock_df['lower'])
        stock_df['bandwidth'] = (stock_df["upper"] - stock_df['lower']) / (stock_df["ma20"])

        stock_df['ma5'] = stock_df['Close'].rolling(window=5).mean() # 60일 이동평균
        stock_df['ma60'] = stock_df['Close'].rolling(window=60).mean() # 60일 이동평균
        stock_df['ma120'] = stock_df['Close'].rolling(window=120).mean() # 120일 이동평균
        
        stock_df = stock_df[stock_df.index > start_date]
        
    except Exception as e:
        print(e)
        return None, None, None, e

    return corp_nm, corp_code, stock_df, "Sucess"


def get_corp_book_data(category, text) :
    df_krx = fdr.StockListing('KRX')
    print("get : " + text)
    try :
        if category == "종목명" :
            corp_nm = text
            corp_code = df_krx[df_krx["Name"] == text]["Code"].iloc[0]
            print(corp_code)
        else :
            corp_code = text
            corp_nm = df_krx[df_krx["Code"] == text]["Name"].iloc[0]
            print(corp_nm)

        
        api_key = "c3d9a5fef22af5e566ddf1bf10e8c27ca46d0b15"
        dart = OpenDartReader(api_key)
        if datetime.today().month >= 4 :
            reprt_nm = "사업보고서"
            reprt_cd = "11011"
            dart_year = datetime.today().year -1
            end_date = datetime(dart_year, 12, 31)
        elif datetime.today().month >= 6 :
            reprt_nm = "1/4분기 보고서"
            reprt_cd = "11013"
            dart_year = datetime.today().year
            end_date = datetime(dart_year, 3, 31)
        elif datetime.today().month >= 9 :
            reprt_nm = "반기 보고서"
            reprt_cd = "11012"
            dart_year = datetime.today().year
            end_date = datetime(dart_year, 6, 30)
        elif datetime.today().month >= 12 :
            reprt_nm = "3/4분기 보고서"
            reprt_cd = "11014"
            dart_year = datetime.today().year
            end_date = datetime(dart_year, 9, 30)
        else :
            reprt_nm = "3/4분기 보고서"
            reprt_cd = "11014"
            dart_year = datetime.today().year - 1
            end_date = datetime(dart_year, 9, 30)

        
        start_date = datetime(dart_year, 1, 1)
        stock_df = fdr.DataReader(symbol=corp_code, start=start_date, end=end_date) 
        
        dv = dart.report(corp=corp_code, bsns_year=dart_year, reprt_code=reprt_cd, key_word="배당")
        dv_dps   = dv[dv['se'] == '주당 현금배당금(원)']
        dv_eps   = dv[dv['se'].str.contains('주당순이익')]
        dv_yield = dv[dv['se'].str.contains('현금배당수익률')]
        dv_TD    = dv[dv['se'].str.contains('현금배당금총액')]

        DPS = int(dv_dps[['thstrm']].iloc[0,0].replace(',', '').strip()) # 주당 배당금
        Yield = float(dv_yield[['thstrm']].iloc[0,0].replace(',','').strip())
        TD = int(dv_TD[['thstrm']].iloc[0,0].replace(',', '').strip()) * 1000000 # 배당금총액. 백만원단위

        corp_book = dart.finstate_all(corp=corp_code, bsns_year=dart_year, fs_div="CFS", reprt_code=reprt_cd)
        equity = int(corp_book.loc[corp_book['sj_div'].isin(['BS']) & corp_book['account_id'].isin(['ifrs-full_Equity']), 'thstrm_amount'].replace(",", "")) # 당기자본(자본총계)
        liability = int(corp_book.loc[corp_book['sj_div'].isin(['BS']) & corp_book['account_id'].isin(['ifrs-full_Liabilities']), 'thstrm_amount'].replace(",", "")) # 당기부채(부채총계)
        assets = equity + liability # 자산총계
        profit = int(corp_book[corp_book['sj_div'].isin(['IS', 'CIS']) & corp_book['account_nm'].str.contains('당기순이익')]["thstrm_amount"].iloc[0].replace(",","")) # 당기순이익

        tmp = dart.report(corp=corp_code, bsns_year=dart_year, reprt_code=reprt_cd, key_word="주식총수")
        total_stock = int(tmp[tmp["se"] == "합계"]["distb_stock_co"].iloc[0].replace(",",""))

        EPS = round(profit/total_stock, 2)
        PER = round(stock_df["Close"][-1] / EPS, 2)
        BPS = round(equity / total_stock,2)
        PBR = round(stock_df["Close"][-1] / BPS, 2)
        ROE = round(PBR / PER, 2)
        ROA = round(profit / assets, 2)
        DE = round(liability / assets, 2)

        corp_book_df = {'종목코드':corp_code, '종목명':corp_nm, '보고서명칭' : reprt_nm, '사업연도' : str(dart_year),
            'DPS':DPS, '배당수익률':Yield, '배당금총액':TD, 'EPS':EPS, 'PER':PER, 'BPS':BPS,  'PBR':PBR,
            'ROE':ROE, 'ROA':ROA, 'DE':DE}
        
    except Exception as e:
        print(e)
        return None, None, None, e

    return corp_nm, corp_code, corp_book_df, "Sucess"


get_corp_book_data("종목명", "데브시스터즈")