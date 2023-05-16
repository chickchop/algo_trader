import FinanceDataReader as fdr
import datetime
import matplotlib.pyplot as plt


def get_corp_data(category, text, start_date) :
    df_krx = fdr.StockListing('KRX')
    print(text)
    try :
        if category == "종목명" :
            corp_nm = text
            corp_code = df_krx[df_krx["Name"] == text]["Code"].iloc[0]
            print(corp_code)
        else :
            corp_code = text
            corp_nm = df_krx[df_krx["Code"] == text]["Name"].iloc[0]
            print(corp_nm)

        stock_df = fdr.DataReader(symbol=corp_code, start= start_date) 
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
        stock_df = stock_df[19:]
        
    except Exception as e:
        print(e)
        return None, None, None, e

    return corp_nm, corp_code, stock_df, "Sucess"