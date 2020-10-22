#!/usr/bin/env python
# coding: utf-8

# In[ ]:


import pandas as pd
import numpy as np

import hashlib
import hmac
import json
import requests
import datetime
import math

from satang_pro import SatangPro

import websocket
import http.client

def getbotrate():  
    # get daily rate from thai central bank API
    conn = http.client.HTTPSConnection("apigw1.bot.or.th")
    headers = {
     'x-ibm-client-id': "b8ebe4b4-76ae-43f4-b661-d9c3a09aabfb",'accept': "application/json"
     }
    conn.request("GET", "/bot/public/Stat-ReferenceRate/v2/DAILY_REF_RATE/?start_period=2020-09-01&end_period=2020-09-01", headers=headers)
    res = conn.getresponse()
    data = res.read()
    #json or dict
    j = pd.io.json.loads(data.decode("utf-8"))
    updated_date=j["result"]["data"]["data_header"]["last_updated"]
    conn.request("GET", "/bot/public/Stat-ReferenceRate/v2/DAILY_REF_RATE/?start_period="+updated_date+"&end_period="+updated_date, headers=headers)
    res = conn.getresponse()
    data = res.read()
    j2 = pd.io.json.loads(data.decode("utf-8"))
    rate=float(j2["result"]["data"]["data_detail"][0]["rate"])
    
    return rate

def bk_slp():
    
    # bitkub
    API_HOST = 'https://api.bitkub.com'
    API_KEY = '0dcfc8f1305a0a14f3ec9342ecb15ae9'
    API_SECRET = b'046299c776c54c81158452d5241e63ee'
    def json_encode(data):
        return json.dumps(data, separators=(',', ':'), sort_keys=True)
    # check server time
    response = requests.get(API_HOST + '/api/servertime')
    ts = int(response.text)
    data = {
        'sym': 'THB_BTC', # The symbol
        'lmt': 600
    }
    response = requests.get(API_HOST + '/api/market/books',data)
    a = response.json()
    #     bit-ask datafreame
    ask=a['result']['asks']
    bid=a['result']['bids']
    df_bid = pd.DataFrame(columns=["order id","timestamp","total","price","amount"])
    df_ask = pd.DataFrame(columns=["order id","timestamp","total","price","amount"])


    for i in range(len(bid)):
        df_bid.loc[i]=bid[i]
        df_ask.loc[i]=ask[i]

    df_bid=df_bid[['price','amount','total']]
    df_ask=df_ask[['price','amount','total']]
    # minimum ask sell rate 
    df_ask=df_ask.sort_values(by='price', ascending=True)
    # maximum bid buy rate 
    df_bid=df_bid.sort_values(by='price', ascending=False)
    #    bid slippage change
    best_ask=df_ask.iloc[0]['price']
    best_bid=df_bid.iloc[0]['price']
    
    a_s1_tp=0
    a_s1_ta=0
    a_s3_tp=0
    a_s3_ta=0
    b_s1_tp=0
    b_s1_ta=0
    b_s3_tp=0


    # bid slippage change
    bid_slp=[]
    b_pi=best_bid
    for i in df_bid['price']:
        bid_slippage=(math.fabs(i-b_pi)/b_pi)*100
        bid_slp.append(bid_slippage)

    df_bid['bid_slp']=bid_slp
    if(df_bid['bid_slp'].max()<1.0):
        b_s1_tp=-1
        b_s1_ta=-1
#         print("max bid slippage less than 1.0%")
    if(df_bid['bid_slp'].max()>=1.0):
        slp_1=df_bid[df_bid['bid_slp']<1.0]
        cur_price_1=df_bid['total'][df_bid['bid_slp']>=1.0].iloc[0]
        cur_amount_1=df_bid['amount'][df_bid['bid_slp']>=1.0].iloc[0]
#         print("______________________________________________________________")
#         print("****เราต้องกว้านขาย BTC เพื่อให้ bid slippage เปลี่ยน 1 % จำนวน****")
#         print("Total price(THB) for changing 1% bid slippage : "+str(slp_1['total'].sum()+cur_price_1))
#         print("Total amount(BTC) for changing 1% bid slippage : "+str(slp_1['amount'].sum()+cur_amount_1))
#         print("")
    if(df_bid['bid_slp'].max()<3.0):
        b_s3_tp=-1
        b_s3_ta=-1
#         print("max bid slippage less than 3.0%")
    if(df_bid['bid_slp'].max()>=3.0): 
        slp_3=df_bid[df_bid['bid_slp']<3.0]
        cur_price_3=df_bid['total'][df_bid['bid_slp']>=3.0].iloc[0]
        cur_amount_3=df_bid['amount'][df_bid['bid_slp']>=3.0].iloc[0]
#         print("****เราต้องกว้านขาย BTC เพื่อให้ bid slippage เปลี่ยน 3 % จำนวน****")
#         print("Total price(THB) for changing 3% bid slippage : "+str(slp_3['total'].sum()+cur_price_3))
#         print("Total amount(BTC) for changing 3% bid slippage : "+str(slp_3['amount'].sum()+cur_amount_3))
#         print("______________________________________________________________")

    # ask slippage change  
    ask_slp=[]
    a_pi=best_ask
    for i in df_ask['price']:
        ask_slippage=(math.fabs(i-a_pi)/a_pi)*100
        ask_slp.append(ask_slippage)
    df_ask['ask_slp']=ask_slp
    if(df_ask['ask_slp'].max()<1.0):
        a_s1_tp=-1
        a_s1_ta=-1
#         print("max ask slippage less than 1.0%")

    if(df_ask['ask_slp'].max()>=1.0):
        a_slp_1=df_ask[df_ask['ask_slp']<1.0]
        a_cur_price_1=df_ask['total'][df_ask['ask_slp']>=1.0].iloc[0]
        a_cur_amount_1=df_ask['amount'][df_ask['ask_slp']>=1.0].iloc[0]
#         print("______________________________________________________________")
#         print("****เราต้องกว้านซื้อ BTC เพื่อให้ ask slippage เปลี่ยน 1 % จำนวน****")
#         print("Total price(THB) for changing 1% ask slippage : "+str(a_slp_1['total'].sum()+a_cur_price_1))
#         print("Total amount(BTC) for changing 1% ask slippage : "+str(a_slp_1['amount'].sum()+a_cur_amount_1))
#         print("")
    if(df_ask['ask_slp'].max()<3.0):
        a_s3_tp=-1
        a_s3_ta=-1
#         print("max ask slippage less than 3.0%")

    if(df_ask['ask_slp'].max()>=3.0):
        a_slp_3=df_ask[df_ask['ask_slp']<3.0]
        a_cur_price_3=df_ask['total'][df_ask['ask_slp']>=3.0].iloc[0]
        a_cur_amount_3=df_ask['amount'][df_ask['ask_slp']>=3.0].iloc[0]

#         print("****เราต้องกว้านซื้อ BTC เพื่อให้ ask slippage เปลี่ยน 3 % จำนวน****")
#         print("Total price(THB) for changing 3% ask slippage : "+str(a_slp_3['total'].sum()+a_cur_price_3))
#         print("Total amount(BTC) for changing 3% ask slippage : "+str(a_slp_3['amount'].sum()+a_cur_amount_3))
#         print("______________________________________________________________")
    
    if(a_s1_tp!=-1 ):
        a_s1_tp=a_slp_1['total'].sum()+a_cur_price_1
        a_s1_ta=a_slp_1['amount'].sum()+a_cur_amount_1
    if(a_s3_tp!=-1 ):
        a_s3_tp=a_slp_3['total'].sum()+a_cur_price_3
        a_s3_ta=a_slp_3['amount'].sum()+a_cur_amount_3
    if(b_s1_tp!=-1 ):
        b_s1_tp=slp_1['total'].sum()+cur_price_1
        b_s1_ta=slp_1['amount'].sum()+cur_amount_1
    if(b_s3_tp!=-1 ):
        b_s3_tp=slp_3['total'].sum()+cur_price_3
        b_s3_ta=slp_3['amount'].sum()+cur_amount_3
    
    return a_s1_tp,a_s1_ta,a_s3_tp,a_s3_ta,b_s1_tp,b_s1_ta,b_s3_tp,b_s3_ta
def hb_slp():
    API_HOST = 'https://www.huobi.co.th/api'
    API_KEY = 'c7c22f11-feb097ef-a6aa3e21-ur2fg6h2gf'
    API_SECRET = b'298d9c50-bc6f69c5-2942dd26-d94df'
    def json_encode(data):
        return json.dumps(data, separators=(',', ':'), sort_keys=True)
    # check server time
    response = requests.get(API_HOST + '/v1/common/timestamp')
    ts = response.json()
    data = {
        'symbol': 'btcthb', 
        'type':'step0'
    }
    response = requests.get(API_HOST + '/market/depth',data)
    t=int(ts['data'])/1000
    time=datetime.datetime.fromtimestamp(t)
    a = response.json()
    bid=a['tick']['bids']
    ask= a['tick']['asks']
    # BID-ASK DATAFRAME
    df_bid = pd.DataFrame(columns=["price","amount"])
    df_ask = pd.DataFrame(columns=["price","amount"])
    for i in range(len(bid)):
        df_bid.loc[i]=bid[i]
    for i in range(len(ask)):
        df_ask.loc[i]=ask[i]
    df_ask=df_ask.sort_values(by='price', ascending=True)
    df_bid=df_bid.sort_values(by='price', ascending=False)

    df_bid['total'] = df_bid.apply(lambda row: row.price * row.amount, axis=1)
    df_ask['total'] = df_ask.apply(lambda row: row.price * row.amount, axis=1)

    max_bid=float(df_bid.iloc[0]['price'])
    min_ask=float(df_ask.iloc[0]['price'])
    spread=((min_ask-max_bid)/min_ask)*100
    #slippage
    best_ask=min_ask
    best_bid=max_bid
    
    a_s1_tp=0
    a_s1_ta=0
    a_s3_tp=0
    a_s3_ta=0
    b_s1_tp=0
    b_s1_ta=0
    b_s3_tp=0


    # bid slippage change
    bid_slp=[]
    b_pi=best_bid
    for i in df_bid['price']:
        bid_slippage=(math.fabs(i-b_pi)/b_pi)*100
        bid_slp.append(bid_slippage)

    df_bid['bid_slp']=bid_slp
    if(df_bid['bid_slp'].max()<1.0):
        b_s1_tp=-1
        b_s1_ta=-1
#         print("max bid slippage less than 1.0%")
    if(df_bid['bid_slp'].max()>=1.0):
        slp_1=df_bid[df_bid['bid_slp']<1.0]
        cur_price_1=df_bid['total'][df_bid['bid_slp']>=1.0].iloc[0]
        cur_amount_1=df_bid['amount'][df_bid['bid_slp']>=1.0].iloc[0]
#         print("______________________________________________________________")
#         print("****เราต้องกว้านขาย BTC เพื่อให้ bid slippage เปลี่ยน 1 % จำนวน****")
#         print("Total price(THB) for changing 1% bid slippage : "+str(slp_1['total'].sum()+cur_price_1))
#         print("Total amount(BTC) for changing 1% bid slippage : "+str(slp_1['amount'].sum()+cur_amount_1))
#         print("")
    if(df_bid['bid_slp'].max()<3.0):
        b_s3_tp=-1
        b_s3_ta=-1
#         print("max bid slippage less than 3.0%")
    if(df_bid['bid_slp'].max()>=3.0):
        slp_3=df_bid[df_bid['bid_slp']<3.0]
        cur_price_3=df_bid['total'][df_bid['bid_slp']>=3.0].iloc[0]
        cur_amount_3=df_bid['amount'][df_bid['bid_slp']>=3.0].iloc[0]
#         print("****เราต้องกว้านขาย BTC เพื่อให้ bid slippage เปลี่ยน 3 % จำนวน****")
#         print("Total price(THB) for changing 3% bid slippage : "+str(slp_3['total'].sum()+cur_price_3))
#         print("Total amount(BTC) for changing 3% bid slippage : "+str(slp_3['amount'].sum()+cur_amount_3))
#         print("______________________________________________________________")

    # ask slippage change  
    ask_slp=[]
    a_pi=best_ask
    for i in df_ask['price']:
        ask_slippage=(math.fabs(i-a_pi)/a_pi)*100
        ask_slp.append(ask_slippage)

    df_ask['ask_slp']=ask_slp
    if(df_ask['ask_slp'].max()<1.0):
        a_s1_tp=-1
        a_s1_ta=-1
#         print("max ask slippage less than 1.0%")

    if(df_ask['ask_slp'].max()>=1.0):
        a_slp_1=df_ask[df_ask['ask_slp']<1.0]
        a_cur_price_1=df_ask['total'][df_ask['ask_slp']>=1.0].iloc[0]
        a_cur_amount_1=df_ask['total'][df_ask['ask_slp']>=1.0].iloc[0]
#         print("______________________________________________________________")
#         print("****เราต้องกว้านซื้อ BTC เพื่อให้ ask slippage เปลี่ยน 1 % จำนวน****")
#         print("Total price(THB) for changing 1% ask slippage : "+str(a_slp_1['total'].sum()+a_cur_price_1))
#         print("Total amount(BTC) for changing 1% ask slippage : "+str(a_slp_1['amount'].sum()+a_cur_amount_1))
#         print("")
    if(df_ask['ask_slp'].max()<3.0):
        a_s3_tp=-1
        a_s3_ta=-1
#         print("max ask slippage less than 3.0%")

    if(df_ask['ask_slp'].max()>=3.0):
        a_slp_3=df_ask[df_ask['ask_slp']<3.0]
        a_cur_price_3=df_ask['total'][df_ask['ask_slp']>=3.0].iloc[0]
        a_cur_amount_3=df_ask['total'][df_ask['ask_slp']>=3.0].iloc[0]
#         print("****เราต้องกว้านซื้อ BTC เพื่อให้ ask slippage เปลี่ยน 3 % จำนวน****")
#         print("Total price(THB) for changing 3% ask slippage : "+str(a_slp_3['total'].sum()+a_cur_price_3))
#         print("Total amount(BTC) for changing 3% ask slippage : "+str(a_slp_3['amount'].sum()+a_cur_amount_3))
#         print("______________________________________________________________")


    if(a_s1_tp!=-1 ):
        a_s1_tp=a_slp_1['total'].sum()+a_cur_price_1
        a_s1_ta=a_slp_1['amount'].sum()+a_cur_amount_1
    if(a_s3_tp!=-1 ):
        a_s3_tp=a_slp_3['total'].sum()+a_cur_price_3
        a_s3_ta=a_slp_3['amount'].sum()+a_cur_amount_3
    if(b_s1_tp!=-1 ):
        b_s1_tp=slp_1['total'].sum()+cur_price_1
        b_s1_ta=slp_1['amount'].sum()+cur_amount_1
    if(b_s3_tp!=-1 ):
        b_s3_tp=slp_3['total'].sum()+cur_price_3
        b_s3_ta=slp_3['amount'].sum()+cur_amount_3
    
    return time,a_s1_tp,a_s1_ta,a_s3_tp,a_s3_ta,b_s1_tp,b_s1_ta,b_s3_tp,b_s3_ta

def sp_slp():
    
    API_KEY = "live-2a6c1bd5eb0b4321aaaf26721e997e9f"
    SECRET_KEY = "fc8fa6ef2a9e4949bdf72d38208803657659ff67f2a74486a04a64b0bf1f2e6f"
    sp = SatangPro(api_key=API_KEY, secret_key=SECRET_KEY)
    sp.orders(pair='btc_thb')
    bid=sp.orders(pair='btc_thb')['bid']
    ask =sp.orders(pair='btc_thb')['ask']
    sp.orders(pair='btc_thb')['ask']
    # BIT-ASK DATAFRAME
    df_bid = pd.DataFrame(columns=["price","amount"])
    df_ask = pd.DataFrame(columns=["price","amount"])
    for i in range(len(bid)):
        df_bid.loc[i]=list(bid[i].values())
        df_ask.loc[i]=list(ask[i].values())
    df_bid['price']=df_bid['price'].apply(lambda x: float(x))
    df_bid['amount']=df_bid['amount'].apply(lambda x: float(x))
    df_ask['price']=df_ask['price'].apply(lambda x: float(x))
    df_ask['amount']=df_ask['amount'].apply(lambda x: float(x))

    df_ask=df_ask.sort_values(by='price', ascending=True)
    df_bid=df_bid.sort_values(by='price', ascending=False)

    df_bid['total'] = df_bid.apply(lambda row: row.price * row.amount, axis=1)
    df_ask['total'] = df_ask.apply(lambda row: row.price * row.amount, axis=1)

    max_bid=float(df_bid.iloc[0]['price'])
    min_ask=float(df_ask.iloc[0]['price'])

    best_ask=min_ask
    best_bid=max_bid
    
    a_s1_tp=0
    a_s1_ta=0
    a_s3_tp=0
    a_s3_ta=0
    b_s1_tp=0
    b_s1_ta=0
    b_s3_tp=0

    # bid slippage change
    bid_slp=[]
    b_pi=best_bid
    for i in df_bid['price']:
        bid_slippage=(math.fabs(i-b_pi)/b_pi)*100
        bid_slp.append(bid_slippage)

    df_bid['bid_slp']=bid_slp
    if(df_bid['bid_slp'].max()<1.0):
        b_s1_tp=-1
        b_s1_ta=-1
#         print("max bid slippage less than 1.0%")
    if(df_bid['bid_slp'].max()>=1.0):
        slp_1=df_bid[df_bid['bid_slp']<1.0]
        cur_price_1=df_bid['total'][df_bid['bid_slp']>=1.0].iloc[0]
        cur_amount_1=df_bid['amount'][df_bid['bid_slp']>=1.0].iloc[0]
#         print("______________________________________________________________")
#         print("****เราต้องกว้านขาย BTC เพื่อให้ bid slippage เปลี่ยน 1 % จำนวน****")
#         print("Total price(THB) for changing 1% bid slippage : "+str(slp_1['total'].sum()+cur_price_1))
#         print("Total amount(BTC) for changing 1% bid slippage : "+str(slp_1['amount'].sum()+cur_amount_1))
#         print("")
    if(df_bid['bid_slp'].max()<3.0):
        b_s3_tp=-1
        b_s3_ta=-1
#         print("max bid slippage less than 3.0%")
    if(df_bid['bid_slp'].max()>=3.0):  
        slp_3=df_bid[df_bid['bid_slp']<3.0]
        cur_price_3=df_bid['total'][df_bid['bid_slp']>=3.0].iloc[0]
        cur_amount_3=df_bid['amount'][df_bid['bid_slp']>=3.0].iloc[0]

#         print("****เราต้องกว้านขาย BTC เพื่อให้ bid slippage เปลี่ยน 3 % จำนวน****")
#         print("Total price(THB) for changing 3% bid slippage : "+str(slp_3['total'].sum()+cur_price_3))
#         print("Total amount(BTC) for changing 3% bid slippage : "+str(slp_3['amount'].sum()+cur_amount_3))
#         print("______________________________________________________________")

    # ask slippage change  
    ask_slp=[]
    a_pi=best_ask
    for i in df_ask['price']:
        ask_slippage=(math.fabs(i-a_pi)/a_pi)*100
        ask_slp.append(ask_slippage)



    df_ask['ask_slp']=ask_slp
    if(df_ask['ask_slp'].max()<1.0):
        a_s1_tp=-1
        a_s1_ta=-1
#         print("max ask slippage less than 1.0%")

    if(df_ask['ask_slp'].max()>=1.0):
        a_slp_1=df_ask[df_ask['ask_slp']<1.0]
        a_cur_price_1=df_ask['total'][df_ask['ask_slp']>=1.0].iloc[0]
        a_cur_amount_1=df_ask['total'][df_ask['ask_slp']>=1.0].iloc[0]

#         print("______________________________________________________________")
#         print("****เราต้องกว้านซื้อ BTC เพื่อให้ ask slippage เปลี่ยน 1 % จำนวน****")
#         print("Total price(THB) for changing 1% ask slippage : "+str(a_slp_1['total'].sum()+a_cur_price_1))
#         print("Total amount(BTC) for changing 1% ask slippage : "+str(a_slp_1['amount'].sum()+a_cur_amount_1))
#         print("")

    if(df_ask['ask_slp'].max()<3.0):
        a_s3_tp=-1
        a_s3_ta=-1
#         print("max ask slippage less than 3.0%")

    if(df_ask['ask_slp'].max()>=3.0):

        a_slp_3=df_ask[df_ask['ask_slp']<3.0]
        a_cur_price_3=df_ask['total'][df_ask['ask_slp']>=3.0].iloc[0]
        a_cur_amount_3=df_ask['total'][df_ask['ask_slp']>=3.0].iloc[0]

#         print("****เราต้องกว้านซื้อ BTC เพื่อให้ ask slippage เปลี่ยน 3 % จำนวน****")
#         print("Total price(THB) for changing 3% ask slippage : "+str(a_slp_3['total'].sum()+a_cur_price_3))
#         print("Total amount(BTC) for changing 3% ask slippage : "+str(a_slp_3['amount'].sum()+a_cur_amount_3))
#         print("______________________________________________________________")
        


    if(a_s1_tp!=-1 ):
        a_s1_tp=a_slp_1['total'].sum()+a_cur_price_1
        a_s1_ta=a_slp_1['amount'].sum()+a_cur_amount_1
    if(a_s3_tp!=-1 ):
        a_s3_tp=a_slp_3['total'].sum()+a_cur_price_3
        a_s3_ta=a_slp_3['amount'].sum()+a_cur_amount_3
    if(b_s1_tp!=-1 ):
        b_s1_tp=slp_1['total'].sum()+cur_price_1
        b_s1_ta=slp_1['amount'].sum()+cur_amount_1
    if(b_s3_tp!=-1 ):
        b_s3_tp=slp_3['total'].sum()+cur_price_3
        b_s3_ta=slp_3['amount'].sum()+cur_amount_3
    return a_s1_tp,a_s1_ta,a_s3_tp,a_s3_ta,b_s1_tp,b_s1_ta,b_s3_tp,b_s3_ta


def bz_slp():
    
    # API CONNECTION
    ws = websocket.WebSocket()
    ws.connect("wss://apexapi.bitazza.com/WSGateway/")
    frame ={
        "m":0,
        "i":0,
        "n":"OrderBook",
        "o": ""
    }
    payload ={
        "market_pair": "BTCTHB", #THBBTC error
        "level": 2, #// level 1 or level 2 data
        "depth": 100,
    }
    frame["o"]=json.dumps(payload) 
    ws.send(json.dumps(frame))
    result =  ws.recv()
    ws.close()
    json.loads(result)
    a = json.loads(json.loads(result)["o"])
    t=int(a['timestamp'])/1000
    time=datetime.datetime.fromtimestamp(t)
    bid=a['bids']
    ask= a['asks']
    # BID-ASK DATAFRAME
    df_bid = pd.DataFrame(columns=["amount","price"])
    df_ask = pd.DataFrame(columns=["amount","price"])
    for i in range(len(bid)):
        df_bid.loc[i]=bid[i]
    for i in range(len(ask)):
        df_ask.loc[i]=ask[i]
    df_ask=df_ask.sort_values(by='price', ascending=True)
    df_bid=df_bid.sort_values(by='price', ascending=False)

    df_bid['total'] = df_bid.apply(lambda row: row.price * row.amount, axis=1)
    df_ask['total'] = df_ask.apply(lambda row: row.price * row.amount, axis=1)

    max_bid=float(df_bid.iloc[0]['price'])
    min_ask=float(df_ask.iloc[0]['price'])
    spread=((min_ask-max_bid)/min_ask)*100
    # SLIPPAGE
    best_ask=min_ask
    best_bid=max_bid

    a_s1_tp=0
    a_s1_ta=0
    a_s3_tp=0
    a_s3_ta=0
    b_s1_tp=0
    b_s1_ta=0
    b_s3_tp=0

    # bid slippage change
    bid_slp=[]
    b_pi=best_bid
    for i in df_bid['price']:
        bid_slippage=(math.fabs(i-b_pi)/b_pi)*100
        bid_slp.append(bid_slippage)

    df_bid['bid_slp']=bid_slp
    if(df_bid['bid_slp'].max()<1.0):
        b_s1_tp=-1
        b_s1_ta=-1
#         print("max bid slippage less than 1.0%")
    if(df_bid['bid_slp'].max()>=1.0):
        slp_1=df_bid[df_bid['bid_slp']<1.0]
        cur_price_1=df_bid['total'][df_bid['bid_slp']>=1.0].iloc[0]
        cur_amount_1=df_bid['amount'][df_bid['bid_slp']>=1.0].iloc[0]
#         print("______________________________________________________________")
#         print("****เราต้องกว้านขาย BTC เพื่อให้ bid slippage เปลี่ยน 1 % จำนวน****")
#         print("Total price(THB) for changing 1% bid slippage : "+str(slp_1['total'].sum()+cur_price_1))
#         print("Total amount(BTC) for changing 1% bid slippage : "+str(slp_1['amount'].sum()+cur_amount_1))
#         print("")
    if(df_bid['bid_slp'].max()<3.0):
        b_s3_tp=-1
        b_s3_ta=-1
#         print("max bid slippage less than 3.0%")
    if(df_bid['bid_slp'].max()>=3.0):  
        slp_3=df_bid[df_bid['bid_slp']<3.0]
        cur_price_3=df_bid['total'][df_bid['bid_slp']>=3.0].iloc[0]
        cur_amount_3=df_bid['amount'][df_bid['bid_slp']>=3.0].iloc[0]

#         print("****เราต้องกว้านขาย BTC เพื่อให้ bid slippage เปลี่ยน 3 % จำนวน****")
#         print("Total price(THB) for changing 3% bid slippage : "+str(slp_3['total'].sum()+cur_price_3))
#         print("Total amount(BTC) for changing 3% bid slippage : "+str(slp_3['amount'].sum()+cur_amount_3))
#         print("______________________________________________________________")

    # ask slippage change  
    ask_slp=[]
    a_pi=best_ask
    for i in df_ask['price']:
        ask_slippage=(math.fabs(i-a_pi)/a_pi)*100
        ask_slp.append(ask_slippage)



    df_ask['ask_slp']=ask_slp
    if(df_ask['ask_slp'].max()<1.0):
        a_s1_tp=-1
        a_s1_ta=-1
#         print("max ask slippage less than 1.0%")

    if(df_ask['ask_slp'].max()>=1.0):
        a_slp_1=df_ask[df_ask['ask_slp']<1.0]
        a_cur_price_1=df_ask['total'][df_ask['ask_slp']>=1.0].iloc[0]
        a_cur_amount_1=df_ask['total'][df_ask['ask_slp']>=1.0].iloc[0]

#         print("______________________________________________________________")
#         print("****เราต้องกว้านซื้อ BTC เพื่อให้ ask slippage เปลี่ยน 1 % จำนวน****")
#         print("Total price(THB) for changing 1% ask slippage : "+str(a_slp_1['total'].sum()+a_cur_price_1))
#         print("Total amount(BTC) for changing 1% ask slippage : "+str(a_slp_1['amount'].sum()+a_cur_amount_1))
#         print("")

    if(df_ask['ask_slp'].max()<3.0):
        a_s3_tp=-1
        a_s3_ta=-1
#         print("max ask slippage less than 3.0%")

    if(df_ask['ask_slp'].max()>=3.0):

        a_slp_3=df_ask[df_ask['ask_slp']<3.0]
        a_cur_price_3=df_ask['total'][df_ask['ask_slp']>=3.0].iloc[0]
        a_cur_amount_3=df_ask['total'][df_ask['ask_slp']>=3.0].iloc[0]

#         print("****เราต้องกว้านซื้อ BTC เพื่อให้ ask slippage เปลี่ยน 3 % จำนวน****")
#         print("Total price(THB) for changing 3% ask slippage : "+str(a_slp_3['total'].sum()+a_cur_price_3))
#         print("Total amount(BTC) for changing 3% ask slippage : "+str(a_slp_3['amount'].sum()+a_cur_amount_3))
#         print("______________________________________________________________")



    if(a_s1_tp!=-1 ):
        a_s1_tp=a_slp_1['total'].sum()+a_cur_price_1
        a_s1_ta=a_slp_1['amount'].sum()+a_cur_amount_1
    if(a_s3_tp!=-1 ):
        a_s3_tp=a_slp_3['total'].sum()+a_cur_price_3
        a_s3_ta=a_slp_3['amount'].sum()+a_cur_amount_3
    if(b_s1_tp!=-1 ):
        b_s1_tp=slp_1['total'].sum()+cur_price_1
        b_s1_ta=slp_1['amount'].sum()+cur_amount_1
    if(b_s3_tp!=-1 ):
        b_s3_tp=slp_3['total'].sum()+cur_price_3
        b_s3_ta=slp_3['amount'].sum()+cur_amount_3
        
    return a_s1_tp,a_s1_ta,a_s3_tp,a_s3_ta,b_s1_tp,b_s1_ta,b_s3_tp,b_s3_ta

bk_thb_a1,bk_btc_a1,bk_thb_a3,bk_btc_a3,bk_thb_b1,bk_btc_b1,bk_thb_b3,bk_btc_b3=bk_slp()
sp_thb_a1,sp_btc_a1,sp_thb_a3,sp_btc_a3,sp_thb_b1,sp_btc_b1,sp_thb_b3,sp_btc_b3=sp_slp()
date,hb_thb_a1,hb_btc_a1,hb_thb_a3,hb_btc_a3,hb_thb_b1,hb_btc_b1,hb_thb_b3,hb_btc_b3=hb_slp()
bz_thb_a1,bz_btc_a1,bz_thb_a3,bz_btc_a3,bz_thb_b1,bz_btc_b1,bz_thb_b3,bz_btc_b3=bz_slp()
rate=getbotrate()
bk_usd_a1=bk_thb_a1/rate
bk_usd_a3=bk_thb_a3/rate
bk_usd_b1=bk_thb_b1/rate
bk_usd_b3=bk_thb_b3/rate
sp_usd_a1=sp_thb_a1/rate
sp_usd_a3=sp_thb_a3/rate
sp_usd_b1=sp_thb_b1/rate
sp_usd_b3=sp_thb_b3/rate
hb_usd_a1=hb_thb_a1/rate
hb_usd_a3=hb_thb_a3/rate
hb_usd_b1=hb_thb_b1/rate
hb_usd_b3=hb_thb_b3/rate
bz_usd_a1=bz_thb_a1/rate
bz_usd_a3=bz_thb_a3/rate
bz_usd_b1=bz_thb_b1/rate
bz_usd_b3=bz_thb_b3/rate


slp3_rows=[date,bk_btc_a1,bk_usd_a1,bk_thb_a1,sp_btc_a1,sp_usd_a1,sp_thb_a1,hb_btc_a1,hb_usd_a1,hb_thb_a1,bz_btc_a1,bz_usd_a1,bz_thb_a1,
           bk_btc_a3,bk_usd_a3,bk_thb_a3,sp_btc_a3,sp_usd_a3,sp_thb_a3,hb_btc_a3,hb_usd_a3,hb_thb_a3,bz_btc_a3,bz_usd_a3,bz_thb_a3,
           bk_btc_b1,bk_usd_b1,bk_thb_b1,sp_btc_b1,sp_usd_b1,sp_thb_b1,hb_btc_b1,hb_usd_b1,hb_thb_b1,bz_btc_b1,bz_usd_b1,bz_thb_b1,
           bk_btc_b3,bk_usd_b3,bk_thb_b3,sp_btc_b3,sp_usd_b3,sp_thb_b3,hb_btc_b3,hb_usd_b3,hb_thb_b3,bz_btc_b3,bz_usd_b3,bz_thb_b3]

slp3_rows_nosp=[date,bk_btc_a1,bk_usd_a1,bk_thb_a1,hb_btc_a1,hb_usd_a1,hb_thb_a1,bz_btc_a1,bz_usd_a1,bz_thb_a1,
           bk_btc_a3,bk_usd_a3,bk_thb_a3,hb_btc_a3,hb_usd_a3,hb_thb_a3,bz_btc_a3,bz_usd_a3,bz_thb_a3,
           bk_btc_b1,bk_usd_b1,bk_thb_b1,hb_btc_b1,hb_usd_b1,hb_thb_b1,bz_btc_b1,bz_usd_b1,bz_thb_b1,
           bk_btc_b3,bk_usd_b3,bk_thb_b3,hb_btc_b3,hb_usd_b3,hb_thb_b3,bz_btc_b3,bz_usd_b3,bz_thb_b3]
#_________________________________________________________________________________________
# https://jakevdp.github.io/PythonDataScienceHandbook/03.05-hierarchical-indexing.html
columns = pd.MultiIndex.from_product([['ask slippage', 'bid slippage'], ['1%', '3%'],['bk','sp','hb','bz'],['BTC','USD','THB']])
df = pd.DataFrame(columns=columns)
df['date']=None
df=df[['date','ask slippage','bid slippage']]
# df.to_csv("//Users//thunchanok//Desktop//slp3.csv",index=False)
df.to_csv("spread-slippage/slp3.csv",index=False)

# nosp
columns = pd.MultiIndex.from_product([['ask slippage', 'bid slippage'], ['1%', '3%'],['bk','hb','bz'],['BTC','USD','THB']])
df_ = pd.DataFrame(columns=columns)
df_['date']=None
df_=df_[['date','ask slippage','bid slippage']]
# df.to_csv("//Users//thunchanok//Desktop//slp3.csv",index=False)
df_.to_csv("spread-slippage/slp3_nosp.csv",index=False)
#_________________________________________________________________________________________
# +++++++++++++++++
# df=pd.read_csv("//Users//thunchanok//Desktop//slp3.csv", header=[0,1,2,3])
df=pd.read_csv("spread-slippage/slp3.csv", header=[0,1,2,3])
df.loc[len(df)]=slp3_rows
df.to_csv("spread-slippage/slp3.csv",index=False)

df_=pd.read_csv("spread-slippage/slp3_nosp.csv", header=[0,1,2,3])
df_.loc[len(df)]=slp3_rows
df_.to_csv("spread-slippage/slp3_nosp.csv",index=False)
# df.to_csv("//Users//thunchanok//Desktop//slp3.csv",index=False)

