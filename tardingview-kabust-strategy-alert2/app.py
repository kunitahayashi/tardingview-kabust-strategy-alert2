import json, config
from flask import Flask, request, jsonify, render_template
import constants
# from binance.client import Client
# from binance.enums import *

app = Flask(__name__)

# client = Client(config.API_KEY, config.API_SECRET, tld='us')

import urllib.request
import json
import pprint

def generate_token():
    obj = {'APIPassword': 'xxxxxx'}
    json_data = json.dumps(obj).encode('utf8')
    url = 'http://localhost:18080/kabusapi/token'
    req = urllib.request.Request(url, json_data, method='POST')
    req.add_header('Content-Type', 'application/json')
    try:
        with urllib.request.urlopen(req) as res:
            content = json.loads(res.read())    
            token_value = content.get('Token')
    except urllib.error.HTTPError as e:
        print(e)
    return token_value

def get_symbol(token):

    url = 'http://localhost:18080/kabusapi/symbolname/future'
    params = { 'FutureCode': 'NK225mini', 'DerivMonth': 0 }
    req_symbol = urllib.request.Request('{}?{}'.format(url, urllib.parse.urlencode(params)), method='GET') 
    req_symbol.add_header('X-API-KEY', token)
    req_symbol.add_header('Content-Type', 'application/json')

    try:
        with urllib.request.urlopen(req_symbol) as res_symbol:
            content_symbol = json.loads(res_symbol.read())
    except urllib.error.HTTPError as e_symbol:
        print(e_symbol)
        content_symbol = json.loads(e_symbol.read())
    return content_symbol



#多分content_symbol["Symbol"] でSymbolゲット



def new_order(size,side,token_value,content_symbol):


    obj = { 'Password':"取引パスワード代入",
            'Symbol': content_symbol["Symbol"] ,
            'Exchange': 23,
            'TradeType': 1,# 新規１返済２
            'TimeInForce': 2,
            'Side': side,#買い２売り１
            'Qty': size,#枚数初期値は１枚に設定
            'FrontOrderType': 120,#成行
            'Price': 0,# 成行
            'ExpireDay': 0,# 本日以内0
            # 'ClosePositions': [
            #                 {'HoldID':'E20200924*****','Qty':2},
            #                 {'HoldID':'E20200924*****','Qty':1}
            #                 ],
            # 'FrontOrderType': 20,
            # 'Price': 22000,
            # 'ExpireDay': 0,
            'ReverseLimitOrder': {
                                'TriggerPrice': 0,
                                'UnderOver': 2, #1.以下 2.以上
                                'AfterHitOrderType': 1, #1.成行 2.指値
                                'AfterHitPrice': 0
                                } # 逆指値を設定した場合のみ必要
        }
    #https://kabucom.github.io/kabusapi/reference/index.html#operation/sendoderFuturePostを参照



    json_data = json.dumps(obj).encode('utf-8')

    url = 'http://localhost:18080/kabusapi/sendorder/future'
    req = urllib.request.Request(url, json_data, method='POST')
    req.add_header('Content-Type', 'application/json')
    req.add_header('X-API-KEY',token_value)

    try:
        with urllib.request.urlopen(req) as res:
            print(res.status, res.reason)
            for header in res.getheaders():
                print(header)
            print()
            content = json.loads(res.read())
            pprint.pprint(content)
            print(f"sending order {side}")
    except urllib.error.HTTPError as e:
        print(e)
        content = json.loads(e.read())
        pprint.pprint(content)
    except Exception as e:
        print(e)
    return content




def close_trade(size,side,token_value,content_symbol):


    # 新しいポジションサイズが0の時、決済を意味するから
    obj = { 'Password':"取引パスワード代入",
            'Symbol': content_symbol["Symbol"] ,
            'Exchange': 23,
            'TradeType': 2,# 新規１返済２
            'TimeInForce': 2,
            'Side': side,#買い２売り１
            'Qty': size,#枚数初期値は１枚に設定
            'ClosePositionOrder': 3,#exit時に両方指定するとエラー # 0	日（古）損（高） 1:	日（古）損（低）2:	日（新）損（高）3:	日（新）損（低） 4:	損（高）日（古）5:	損（高）日（新）6:	損（低）日（古）7:	損（低）日（新）
            'FrontOrderType': 120,#成行
            'Price': 0,# 成行
            'ExpireDay': 0,# 本日以内0
            'ReverseLimitOrder': {
                                'TriggerPrice': 0,
                                'UnderOver': 2, #1.以下 2.以上
                                'AfterHitOrderType': 1, #1.成行 2.指値
                                'AfterHitPrice': 0
                                } # 逆指値を設定した場合のみ必要
            }
    json_data = json.dumps(obj).encode('utf-8')

    url = 'http://localhost:18080/kabusapi/sendorder/future'
    req = urllib.request.Request(url, json_data, method='POST')
    req.add_header('Content-Type', 'application/json')
    req.add_header('X-API-KEY', token_value)

    try:
        with urllib.request.urlopen(req) as res:
            print(res.status, res.reason)
            for header in res.getheaders():
                print(header)
            print()
            content = json.loads(res.read())
            pprint.pprint(content)
    except urllib.error.HTTPError as e:
        print(e)
        content = json.loads(e.read())
        pprint.pprint(content)
    except Exception as e:
        print(e)
    return content



@app.route('/')
def welcome():
    return render_template('index.html')

@app.route('/webhook', methods=['POST'])
def webhook():
    #print(request.data)
    data = json.loads(request.data)

# strategy.position_sizeが0以外の時、新規購入

    if data['新しいポジションサイズ'] != 0:
    
        if data['passphrase'] != config.WEBHOOK_PASSPHRASE:
            return {
                "code": "error",
                "message": "Nice try, invalid passphrase"
            }


        size =1
        side_buyorsell = data['strategy']['order_action'].upper()

        if side_buyorsell == constants.BUY:
            side = 1
        elif side_buyorsell == constants.SELL:
            side = 2

        token_value = generate_token()
        content_symbol = get_symbol(token_value)
        order_response = new_order(size,side,token_value,content_symbol)

        if order_response:
            return {
                "code": "success",
                "message": "order executed"
            }
        else:
            print("order failed")

            return {
                "code": "error",
                "message": "order failed"
            }

    else:
    # strategy.position_sizeが0の時、決済


        if data['passphrase'] != config.WEBHOOK_PASSPHRASE:
            return {
                "code": "error",
                "message": "Nice try, invalid passphrase"
            }


        size =1
        side_buyorsell = data['strategy']['order_action'].upper()

        if side_buyorsell == constants.BUY:
            side = 1
        elif side_buyorsell == constants.SELL:
            side = 2

        token_value = generate_token()
        content_symbol = get_symbol(token_value)
        order_response = close_trade(size,side,token_value,content_symbol)

        if order_response:
            return {
                "code": "success",
                "message": "order executed"
            }
        else:
            print("order failed")

            return {
                "code": "error",
                "message": "order failed"
            }



