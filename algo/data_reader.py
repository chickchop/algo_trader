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
        dv['thstrm'] = dv['thstrm'].replace('-','0')
        dv_dps   = dv[dv['se'] == '주당 현금배당금(원)']
        dv_eps   = dv[dv['se'].str.contains('주당순이익')]
        dv_yield = dv[dv['se'].str.contains('현금배당수익률')]
        dv_TD    = dv[dv['se'].str.contains('현금배당금총액')]

        DPS = int(dv_dps[['thstrm']].iloc[0,0].replace(',', '').strip()) # 주당 배당금
        Yield = float(dv_yield[['thstrm']].iloc[0,0].replace(',','').strip())
        TD = int(dv_TD[['thstrm']].iloc[0,0].replace(',', '').strip()) * 1000000 # 배당금총액. 백만원단위

        corp_book = dart.finstate_all(corp=corp_code, bsns_year=dart_year, fs_div="CFS", reprt_code=reprt_cd)
        corp_stock = dart.report(corp=corp_code, bsns_year=dart_year, reprt_code=reprt_cd, key_word="주식총수")
        equity = int(corp_book.loc[corp_book['sj_div'].isin(['BS']) & corp_book['account_nm'].str.contains('자본총계')]["thstrm_amount"].iloc[0].replace(",","")) # 당기자본(자본총계)
        liability = int(corp_book.loc[corp_book['sj_div'].isin(['BS']) & corp_book['account_nm'].str.contains('부채총계')]["thstrm_amount"].iloc[0].replace(",","")) # 당기부채(부채총계)
        assets = equity + liability # 자산총계
        profit = int(corp_book[corp_book['sj_div'].isin(['IS', 'CIS']) & corp_book['account_nm'].str.contains('당기순이익')]["thstrm_amount"].iloc[0].replace(",","")) # 당기순이익
        revenue = int(corp_book.loc[corp_book['sj_div'].isin(['IS']) & corp_book['account_nm'].str.contains('매출액')]["thstrm_amount"].iloc[0].replace(",","")) # 매출액
        cash_flow = int(corp_book.loc[corp_book['sj_div'].isin(['CF']) & corp_book['account_nm'].str.contains('영업활동 현금흐름')]["thstrm_amount"].iloc[0].replace(",","")) # 영업활동 현금흐름
        total_stock = int(corp_stock[corp_stock["se"] == "합계"]["distb_stock_co"].iloc[0].replace(",",""))

        EPS = round(profit/total_stock, 2)
        PER = round(stock_df["Close"][-1] / EPS, 2)
        BPS = round(equity / total_stock,2)
        PBR = round(stock_df["Close"][-1] / BPS, 2)
        SPS = round(revenue / total_stock,2)
        PSR = round(stock_df["Close"][-1] / SPS, 2)
        CPS = round(cash_flow / total_stock,2)
        PCR = round(stock_df["Close"][-1] / CPS, 2)
        ROE = round(PBR / PER, 2)
        ROA = round(profit / assets, 2)
        DE = round(liability / assets, 2)

        corp_book_df = {'종목코드':corp_code, '종목명':corp_nm, '보고서명칭' : reprt_nm, '사업연도' : str(dart_year),
            'DPS':DPS, '배당수익률':Yield, '배당금총액':TD, '기준주가':stock_df['Close'][-1],'EPS':EPS, 'PER':PER, 'BPS':BPS,  'PBR':PBR,
            'ROE':ROE, 'ROA':ROA, 'DE':DE, 'SPS':SPS, 'PSR':PSR, 'CPS':CPS, 'PCR':PCR}
        
    except Exception as e:
        print(e)
        return None, None, None, e

    return corp_nm, corp_code, corp_book_df, "Sucess"


def get_corp_last_book_data(category, text) :
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

        year = datetime.now().year -1
        bsns_year_list = [i for i in range(year-5,year)]

        corp_finance_data = []

        for i in bsns_year_list :
            corp_book = dart.finstate_all(corp=corp_code, bsns_year=i, fs_div="CFS", reprt_code="11011")
            corp_stock = dart.report(corp=corp_code, bsns_year=i, reprt_code="11011", key_word="주식총수")
            equity = int(corp_book.loc[corp_book['sj_div'].isin(['BS']) & corp_book['account_nm'].str.contains('자본총계')]["thstrm_amount"].iloc[0].replace(",","")) # 당기자본(자본총계)
            liability = int(corp_book.loc[corp_book['sj_div'].isin(['BS']) & corp_book['account_nm'].str.contains('부채총계')]["thstrm_amount"].iloc[0].replace(",","")) # 당기부채(부채총계)
            assets = equity + liability # 자산총계
            profit = int(corp_book[corp_book['sj_div'].isin(['IS', 'CIS']) & corp_book['account_nm'].str.contains('당기순이익')]["thstrm_amount"].iloc[0].replace(",","")) # 당기순이익
            revenue = int(corp_book.loc[corp_book['sj_div'].isin(['IS']) & corp_book['account_nm'].str.contains('매출액')]["thstrm_amount"].iloc[0].replace(",","")) # 매출액
            cash_flow = int(corp_book.loc[corp_book['sj_div'].isin(['CF']) & corp_book['account_nm'].str.contains('영업활동') & corp_book['account_nm'].str.contains('현금흐름')]["thstrm_amount"].iloc[0].replace(",","")) # 영업활동 현금흐름
            total_stock = int(corp_stock[corp_stock["se"] == "합계"]["distb_stock_co"].iloc[0].replace(",",""))
            stock_price = fdr.DataReader(symbol=corp_code, start=datetime(i,12,25), end=datetime(i,12,31))["Close"][-1]

            tmp = {
                "year" : i,
                "equity" : equity,
                "liability" : liability,
                "assets" : assets,
                "profit" : profit,
                "revenue" : revenue,
                "cash_flow" : cash_flow,
                "total_stock" : total_stock,
                "stock_price" : stock_price
            }
            corp_finance_data.append(tmp)

        corp_finance_data = pd.DataFrame(corp_finance_data)            
        corp_finance_data["EPS"] = round(corp_finance_data["profit"] / corp_finance_data["total_stock"], 2)
        corp_finance_data["PER"] = round(corp_finance_data["stock_price"] / corp_finance_data["EPS"], 2)
        corp_finance_data["BPS"] = round(corp_finance_data["equity"] / corp_finance_data["total_stock"], 2)
        corp_finance_data["PBR"] = round(corp_finance_data["stock_price"] / corp_finance_data["BPS"], 2)
        corp_finance_data["SPS"] = round(corp_finance_data["revenue"] / corp_finance_data["total_stock"], 2)
        corp_finance_data["PSR"] = round(corp_finance_data["stock_price"] / corp_finance_data["SPS"], 2)
        corp_finance_data["CPS"] = round(corp_finance_data["cash_flow"] / corp_finance_data["total_stock"], 2)
        corp_finance_data["PCR"] = round(corp_finance_data["stock_price"] / corp_finance_data["CPS"], 2)
        corp_finance_data["ROE"] = round(corp_finance_data["PBR"] / corp_finance_data["PER"], 2)
        corp_finance_data["ROA"] = round(corp_finance_data["profit"] / corp_finance_data["assets"], 2)
        corp_finance_data["DE"] = round(corp_finance_data["liability"] / corp_finance_data["assets"], 2)

        corp_finance_data["corp_nm"] = corp_nm
        corp_finance_data["corp_code"] = corp_code
        
        start_date = datetime.today() - timedelta(days=7)
        stock_df = fdr.DataReader(symbol=corp_code, start=start_date)
        corp_finance_data["current_price"] = stock_df["Close"][-1]

    except Exception as e:
        print(e)
        return None, None, None, e

    return corp_nm, corp_code, corp_finance_data, "Sucess"


# get_corp_last_book_data("종목명", "셀트리온")