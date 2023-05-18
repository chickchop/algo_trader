import FinanceDataReader as fdr
import datetime
import matplotlib.pyplot as plt


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