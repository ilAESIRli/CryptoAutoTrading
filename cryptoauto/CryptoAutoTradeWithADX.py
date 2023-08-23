import time
import pyupbit
import datetime
import schedule
import requests
import numpy as np

access = ""  # access code (from Upbit)
secret = ""  # secret code (from Upbit)
myToken = "xoxb-2654581905953-2647491313682-jMhV6MAHrr8h79W0aSeLkkC9"

def post_message(token, channel, text):
    """슬랙 메시지 전송"""
    response = requests.post("https://slack.com/api/chat.postMessage",
        headers={"Authorization": "Bearer " + token},
        data={"channel": channel, "text": text}
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
post_message(myToken,"#crypto", "autotrade start")

def calculate_adx(ticker, interval, period):
    df = pyupbit.get_ohlcv(ticker, interval=interval)
    df['true_range'] = np.maximum(df['high'] - df['low'], np.maximum(abs(df['high'] - df['close'].shift(1)), abs(df['low'] - df['close'].shift(1))))
    df['up_move'] = df['high'] - df['high'].shift(1)
    df['down_move'] = df['low'].shift(1) - df['low']
    df['plus_dm'] = np.where((df['up_move'] > df['down_move']) & (df['up_move'] > 0), df['up_move'], 0)
    df['minus_dm'] = np.where((df['down_move'] > df['up_move']) & (df['down_move'] > 0), df['down_move'], 0)
    df['tr_sum'] = df['true_range'].rolling(window=period).sum()  # true_range 합계
    df['plus_di'] = (df['plus_dm'].rolling(window=period).sum() / df['tr_sum']) * 100
    df['minus_di'] = (df['minus_dm'].rolling(window=period).sum() / df['tr_sum']) * 100
    df['adx'] = (abs(df['plus_di'] - df['minus_di']) / (df['plus_di'] + df['minus_di'])) * 100
    return df

def check_adx_cross(df):
    """ADX와 +DI, -DI의 교차 확인"""
    buy_signal = df['plus_di'] > df['minus_di']  # +DI가 -DI보다 위에 있는지 확인
    sell_signal = df['plus_di'] < df['minus_di']  # -DI가 +DI보다 위에 있는지 확인
    return buy_signal, sell_signal

while True:
    try:
        now = datetime.datetime.now()
        start_time = get_start_time("KRW-BTC")
        end_time = start_time + datetime.timedelta(days=1)

        if start_time < now < end_time - datetime.timedelta(seconds=10):
            df = calculate_adx("KRW-BTC", 5, 14)
            latest_plus_di = df['plus_di'].iloc[-1]
            latest_minus_di = df['minus_di'].iloc[-1]
                
            if latest_plus_di > latest_minus_di:
                krw = get_balance("KRW")
                if krw > 5000:
                    current_price = get_current_price("KRW-BTC")
                    upbit.buy_market_order("KRW-BTC", krw * 0.9995)
                    post_message(myToken, "#crypto", "BTC buy : " + str(current_price))
            
        else:
            btc = get_balance("BTC")
            if btc > 0.00008:
                sell_result = upbit.sell_market_order("KRW-BTC", btc * 0.9995)
                post_message(myToken, "#crypto", "BTC sell : " + str(sell_result))
        time.sleep(1)
    except Exception as e:
        print(e)
        post_message(myToken, "#crypto", str(e))
        time.sleep(1)