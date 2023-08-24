import time
import pyupbit
import datetime
import requests

access = "your-access"
secret = "your-secret"
myToken = "xoxb-your-token"

def post_message(token, channel, text):
    """슬랙 메시지 전송"""
    response = requests.post("https://slack.com/api/chat.postMessage",
        headers={"Authorization": "Bearer "+token},
        data={"channel": channel,"text": text}
    )
   
def get_start_time(ticker):
    """시작 시간 조회"""
    df = pyupbit.get_ohlcv(ticker, interval="day", count=1)
    start_time = df.index[0]
    return start_time

def get_balance(ticker):
    """잔고 조회"""
    balances = upbit.get_balances()
    for b in balances:
        if b['currency'] == ticker:
            if b['balance'] is not None:
                return float(b['balance'])
            else:
                return 0
    return 0    

def get_current_price(ticker):
    """현재가 조회"""
    return pyupbit.get_orderbook(ticker=ticker)["orderbook_units"][0]["ask_price"]

# 로그인
upbit = pyupbit.Upbit(access, secret)
print("autotrade start")
# 시작 메세지 슬랙 전송
post_message(myToken, "#crypto", "autotrade start")

def get_dmi_signal(ticker):
    """DMI 지표를 이용한 매매 신호 생성"""
    df = pyupbit.get_ohlcv(ticker, interval="day", count=15)  # DMI 계산을 위한 15일 데이터
    df["up_move"] = df["high"] - df["high"].shift(1)
    df["down_move"] = df["low"].shift(1) - df["low"]
    df["plus_dm"] = 0.0
    df["minus_dm"] = 0.0
    df.loc[df["up_move"] > df["down_move"], "plus_dm"] = df["up_move"]
    df.loc[df["down_move"] > df["up_move"], "minus_dm"] = df["down_move"]
    df["plus_di"] = 100 * df["plus_dm"].rolling(window=14).sum() / df["high"].rolling(window=14).sum()
    df["minus_di"] = 100 * df["minus_dm"].rolling(window=14).sum() / df["low"].rolling(window=14).sum()
    df["dx"] = 100 * abs(df["plus_di"] - df["minus_di"]) / (df["plus_di"] + df["minus_di"])
    df["adx"] = df["dx"].rolling(window=14).mean()
    
    # DMI 지표를 활용한 매매 신호 생성
    if df["plus_di"].iloc[-1] > df["minus_di"].iloc[-1] and df["adx"].iloc[-1] > 25:
        return "buy"
    elif df["plus_di"].iloc[-1] < df["minus_di"].iloc[-1] and df["adx"].iloc[-1] > 25:
        return "sell"
    else:
        return "hold"

while True:
    try:
        now = datetime.datetime.now()
        start_time = get_start_time("KRW-BTC")
        end_time = start_time + datetime.timedelta(days=1)

        if start_time < now < end_time - datetime.timedelta(seconds=10):
            dmi_signal = get_dmi_signal("KRW-BTC")
            current_price = get_current_price("KRW-BTC")
            krw = get_balance("KRW")
            
            if dmi_signal == "buy" and krw > 5000:
                buy_result = upbit.buy_market_order("KRW-BTC", krw * 0.9995)
                post_message(myToken, "#crypto", "BTC buy: " + str(buy_result))
                
        else:
            btc = get_balance("BTC")
            if dmi_signal == "sell" and btc > 0.00008:
                sell_result = upbit.sell_market_order("KRW-BTC", btc * 0.9995)
                post_message(myToken, "#crypto", "BTC sell: " + str(sell_result))
                
        time.sleep(1)
        
    except Exception as e:
        print(e)
        post_message(myToken, "#crypto", str(e))
        time.sleep(1)
