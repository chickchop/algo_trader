import FinanceDataReader as fdr
import datetime
import matplotlib.pyplot as plt


def get_corp_data(category, text, start_date) :
    df_krx = fdr.StockListing('KRX')
    try :
        if category == "종목명" :
            corp_nm = text
            corp_code = df_krx[df_krx["Name"] == text]["Code"][0]
        else :
            corp_code = text
            corp_nm = df_krx[df_krx["Code"] == text]["Name"][0]

        stock_df = fdr.DataReader(symbol=corp_code, start=start_date) 
    except Exception as e:
        return None, None, None, e

    return corp_nm, corp_code, stock_df, "Sucess"