import ccxt
import telegram
import os
import json
import time
import datetime
import pytz

# 텔레그램 봇 v13.15 버전에 최적화 // pip install python-telegram-bot==13.15
bot = telegram.Bot(token='YOUR_TOKEN') # 봇 토큰값 입력

# 바이낸스 거래소 설정
exchange = ccxt.binance({
    'apiKey': 'YOUR_API_KEY',  # 바이낸스 API Key 입력
    'secret': 'YOUR_SECRET',  # 바이낸스 Secret Key 입력
    'enableRateLimit': True,
    'options': {
        'defaultType': 'future'
    }
})

# (포지션 진입수량 계산 : 비트코인 전용 계산법)
# 비트코인 레버리지 x125배 기준이며, 레버리지가 낮으면 분할값도 낮춰야함.
# 대략, 지갑금액의 1/10 비중으로 진입수량을 소량으로 맞춘다고 생각하시면 되겠습니다.
# 한화 100만원을 1USD환산 1317원기준 = ( 759 usd )
# 759usdt / 25000분할 = ( 0.030 btc진입수량 )
cal_usdt = 25000 # 포지션 진입수량 계산 기준을 정의

# 경고 !!!!!! 아래 부터는 절대 코드 건들면 안됩니다 !!!!!!
# 경고 !!!!!! 아래 부터는 절대 코드 건들면 안됩니다 !!!!!!
# 경고 !!!!!! 아래 부터는 절대 코드 건들면 안됩니다 !!!!!!
# 경고 !!!!!! 아래 부터는 절대 코드 건들면 안됩니다 !!!!!!
# 경고 !!!!!! 아래 부터는 절대 코드 건들면 안됩니다 !!!!!!

sig_s = 'Short'
sig_l = 'Long'

last_sig = ''

symbol = 'BTC/USDT'
target_coin = 'BTCUSDT'

MUL_SCO = 0

L_MIN = 1.001
S_MIN = 0.999

MUL_L = 0.95
MUL_S = 1.05

amount = 0

log_file_name = 'bot_msg.json'
if not os.path.exists(log_file_name):
    with open(os.path.join(log_file_name), 'w', encoding='utf-8') as file_name:
        data = {
            'amtt':amount,
            'mulsco':MUL_SCO,
            'lastsig':last_sig
        }
        json.dump(data,file_name)

if os.path.exists(log_file_name):
    with open(os.path.join(log_file_name), "r", encoding='utf-8') as file_name:
        data = json.load(file_name)
        amount = data['amtt']
        MUL_SCO = data['mulsco']
        last_sig = data['lastsig']

while True:
    try:
        tel_sig = 0

        now = datetime.datetime.now(tz=pytz.timezone('Asia/Seoul'))

        # 핵심코드 // ㅡㅡㅡㅡㅡ 꿀비트AI봇과 실시간 동기화 진행 ㅡㅡㅡㅡㅡ
        # 텔레그램봇이 최근 시그널을 확인하고 가져옴
        # 최근 시그널의 시간대를 msg_time 변수에 저장
        # 현재 시간과 최근 시그널 시간 차이를 diff 변수에 저장
        # 최종 시그널이 5분 이내인지 확인
        updates = bot.get_updates()
        if updates:
            message = updates[-1].message
            msg_time = message.date
            diff = now - msg_time
            if diff < datetime.timedelta(minutes=5):
                tel_msg = message.text
                if sig_s in tel_msg:
                    tel_sig = 1
                elif sig_l in tel_msg:
                    tel_sig = 2
                else:
                    tel_sig = 3
                    signal_msg = "꿀비트Ai봇 시그널을 확인중입니다..\n"
            else:
                tel_sig = 3
                signal_msg = "꿀비트Ai봇 시그널을 확인중입니다..\n"
        
        else:
            signal_msg = "꿀비트Ai봇 시그널을 확인중입니다..\n"
        # 핵심코드 // ㅡㅡㅡㅡㅡ 꿀비트AI봇과 실시간 동기화 진행 ㅡㅡㅡㅡㅡ



        ticker = exchange.fetch_ticker(symbol)
        cur_price = ticker['last']

        balance = exchange.fetch_balance()
        usdt = balance['total']['USDT']

        def cal_amt():
            amount = round(usdt / cal_usdt,3)
            return amount
        
        for posi in balance['info']['positions']:
            if posi['symbol'] == target_coin:
                amt = float(posi['positionAmt'])
                entryp = float(posi['entryPrice'])
                unrealpf = float(posi['unrealizedProfit'])

        if MUL_SCO != 0 and amt != 0:
            mul_amt = amt * 0.7



        # 포지션 마감
        if amt < 0 and tel_sig == 2 and (cur_price < ((entryp + 0.01) * S_MIN)):
            exchange.create_market_buy_order(symbol=symbol, amount=abs(amt))
            amount = cal_amt()
            MUL_SCO = 0
            signal_msg = f"숏마감 - 가격: {cur_price}\n"
        elif amt > 0 and tel_sig == 1 and (cur_price > ((entryp + 0.01) * L_MIN)):
            exchange.create_market_sell_order(symbol=symbol, amount=abs(amt))
            amount = cal_amt()
            MUL_SCO = 0
            signal_msg = f"롱마감 - 가격: {cur_price}\n"

        # 물타기 수량 자동 청산
        if MUL_SCO == 1:
            if amt < 0 and (cur_price < ((entryp + 0.01) * S_MIN)):
                exchange.create_market_buy_order(symbol=symbol, amount=abs(mul_amt))
                MUL_SCO = 0
                signal_msg = f"추매마감 - 가격: {cur_price}"
            
            elif amt > 0 and (cur_price > ((entryp + 0.01) * L_MIN)):
                exchange.create_market_sell_order(symbol=symbol, amount=abs(mul_amt))
                MUL_SCO = 0
                signal_msg = f"추매마감 - 가격: {cur_price}"

        #포지션 진입 (자동 물타기)
        if (amt == 0 and tel_sig == 2) or (amt > 0 and tel_sig == 2 and MUL_SCO == 0 and cur_price < (entryp * MUL_L)):
            exchange.create_market_buy_order(symbol=symbol, amount=cal_amt())
            signal_msg = "\033[96m"f" _\n| |    ___  _ __   __ _\n| |   / _ \| '_ \ / _` |\n| |__| (_) | | | | (_| |\n|_____\___/|_| |_|\__, |\n                  |___/\n\n■■■■■■■■■■■■■■■■■■■■■■■■■\n 롱 ( Long ) 신호포착 !!\n*진입시간 : {now.hour}:{now.minute}:{now.second}\n■■■■■■■■■■■■■■■■■■■■■■■■■\n""\033[0m"
            last_sig = f"롱진입 {round(cur_price)} / {now.month}월{now.day}일 {now.hour}시{now.minute}분"
            amount = amount
            amount += cal_amt() / 2
            if amt > 0 and (entryp * MUL_L) > cur_price:
                MUL_SCO += 1
        elif (amt == 0 and tel_sig == 1) or (amt < 0 and tel_sig == 1 and MUL_SCO == 0 and cur_price > (entryp * MUL_S)):
            exchange.create_market_sell_order(symbol=symbol, amount=cal_amt())
            signal_msg = "\033[91m"f" ____  _                _\n/ ___|| |__   ___  _ __| |_\n\___ \| '_ \ / _ \| '__| __|\n ___) | | | | (_) | |  | |_\n|____/|_| |_|\___/|_|   \__|\n\n■■■■■■■■■■■■■■■■■■■■■■■■■\n 숏 ( Short ) 신호포착 !!\n*진입시간 : {now.hour}:{now.minute}:{now.second}\n■■■■■■■■■■■■■■■■■■■■■■■■■\n""\033[0m"
            last_sig = f"숏진입 {round(cur_price)} / {now.month}월{now.day}일 {now.hour}시{now.minute}분"
            amount = amount
            amount += cal_amt() / 2
            if amt < 0 and (entryp * MUL_S) < cur_price:
                MUL_SCO += 1



        print("\n\n\n\n■ 꿀비트AI봇 연동 실시간 자동매매")
        print(f"■ 현재시간 : {now.hour}시 {now.minute}분 {now.second}초")
        print(f"{last_sig}")
        print("ㅡㅡㅡㅡㅡㅡㅡㅡㅡㅡㅡㅡㅡㅡㅡㅡㅡ\n")
        print(f"{signal_msg}")
        print("ㅡㅡㅡㅡㅡㅡㅡㅡㅡㅡㅡㅡㅡㅡㅡㅡㅡ\n")
        print(f"*지갑  잔액: {round(usdt,3)}\n*진입  수량: {amt}\n*실시간수익: {round(unrealpf,3)}\n\n진입가능수량: {amount} 자동계산\n물타기 롱.숏 비율 [ {round(MUL_L,3)} | {round(MUL_S,3)} ]\n\nㅡㅡㅡㅡㅡㅡㅡㅡㅡㅡㅡㅡㅡㅡㅡㅡㅡ\n")



        with open(os.path.join(log_file_name), 'w', encoding='utf-8') as file_name:
            data = {
                'amtt':amount,
                'mulsco':MUL_SCO,
                'lastsig':last_sig
            }
            json.dump(data,file_name)



        time.sleep(10)
    except Exception as e:
        print('에러 발생', e)
        time.sleep(10)
