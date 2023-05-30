
class RIM():
    def __init__(self, corp_nm, predict_roe, equity) -> None:
        self.corp_nm = corp_nm
        self.roe = predict_roe
        self.equity = equity

    def calculate_corp_val(self, target_return_rate=0.07, discount_roe=1.0) :
        if discount_roe == 1.0:
            value = self.equity + (self.equity * (self.roe - target_return_rate)) / target_return_rate
        else:
            excess_earning = self.equity * (self.roe - target_return_rate)
            mul = discount_roe / (1.0 + target_return_rate - discount_roe)
            value = self.equity + excess_earning * mul

        return value
    
    def target_price(self, calculate_corp_val, stock_quantity) :
        return round(calculate_corp_val / stock_quantity, 2) 