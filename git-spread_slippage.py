#!/usr/bin/env python
# coding: utf-8

# In[1]:


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


def bitkub(btc_sell_list):
    # sample_place_bid   
#     API CONNECTION
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
        'lmt': 10
    }
    response = requests.get(API_HOST + '/api/market/books',data)
    a = response.json()
#     bit-ask datafreame
    ask=a['result']['asks']
    bid=a['result']['bids']
    df_bid = pd.DataFrame(columns=["order id","timestamp","volume","rate","amount"])
    df_ask = pd.DataFrame(columns=["order id","timestamp","volume","rate","amount"])
    for i in range(len(bid)):
        df_bid.loc[i]=bid[i]
        df_ask.loc[i]=ask[i]
    # minimum ask sell rate 
    df_ask=df_ask.sort_values(by='rate', ascending=True)
    df_ask['time'] = df_ask['timestamp'].apply(lambda x: datetime.datetime.fromtimestamp(x))
    # maximum bid buy rate 
    df_bid=df_bid.sort_values(by='rate', ascending=False)
    df_bid['time'] = df_bid['timestamp'].apply(lambda x: datetime.datetime.fromtimestamp(x))

#     space
    # https://blog.shrimpy.io/blog/cryptocurrency-trading-101-exchange-market-spread?rq=spread
    # AL(lowest ask price) - BH(highest buy price) = Spread
    # Percent Spread = (Spread / lowest ask price) x 100
    max_bid=df_bid.iloc[0]['rate']
    min_ask=df_ask.iloc[0]['rate']
    spread=((min_ask-max_bid)/min_ask)*100

#     slippage
    # kaiko
    avg_buy_price=0
    best_ask=min_ask
    best_bid=max_bid
    midPrice=(best_ask+best_bid)/2
    sum_buy_price=0
    shrimpy_slippage_list=[]
    kaiko_slippage_list=[]
    bybit_slippage_list=[]
    bk_slippage_list=[]
    for btc_sell_amount in btc_sell_list:
        sum_amount=0
        pi=float(df_ask.iloc[0]['rate'])
        sum_buy_price=0 
        for i in range (len(ask)):
            if btc_sell_amount > sum_amount:
                sum_amount=float(df_ask.iloc[i]['amount'])+sum_amount
                sum_buy_price= sum_buy_price+float(df_ask.iloc[i]['rate'])
                if sum_amount>=btc_sell_amount:
                    pf=float(df_ask.iloc[i]['rate'])
                    index=i+1
                    break
        if sum_amount<btc_sell_amount and i==len(ask)-1 :
            bk_slippage_list.append([-1,-1,-1])
            while(len(bk_slippage_list)!= len(btc_sell_list)) :
                bk_slippage_list.append([-1,-1,-1])
            break
        b_sum_amount=0
        sum_ask_price= 0
        b_pi=float(df_bid.iloc[0]['rate'])
        for i in range (len(bid)):
            if btc_sell_amount > b_sum_amount:
                b_sum_amount=float(df_bid.iloc[i]['amount'])+b_sum_amount
                sum_ask_price= sum_ask_price+float(df_bid.iloc[i]['rate'])
                if b_sum_amount>=btc_sell_amount:
                    b_pf=float(df_bid.iloc[i]['rate'])
                    b_index=i+1
                    break
        if b_sum_amount<btc_sell_amount and i==len(ask)-1:
            break
        avg_buy_price=sum_buy_price/(index)
        bybit_slippage=math.fabs(b_pf-pf)/midPrice
        shrimpy_slippage=(math.fabs(pf-pi)/pi)
        kaiko_slippage=(math.fabs(avg_buy_price-midPrice)/midPrice)

        shrimpy_slippage_list.append(shrimpy_slippage)
        kaiko_slippage_list.append(kaiko_slippage)
        bybit_slippage_list.append(bybit_slippage)

        
#         slippage_list.append(shrimpy_slippage_list)
#         slippage_list.append(kaiko_slippage_list)
#         slippage_list.append(bybit_slippage_list)
        bk_slippage_list.append([shrimpy_slippage,kaiko_slippage,bybit_slippage])
    return [df_ask.iloc[0]['time'],bk_slippage_list,spread]


def huobi_thailand(btc_sell_list):
# API
    API_HOST = 'https://www.huobi.co.th/api'
    API_KEY = 'c7c22f11-feb097ef-a6aa3e21-ur2fg6h2gf'
    API_SECRET = b'298d9c50-bc6f69c5-2942dd26-d94df'

    def json_encode(data):
        return json.dumps(data, separators=(',', ':'), sort_keys=True)
    # check server time
    response = requests.get(API_HOST + '/v1/common/timestamp')
    ts = response.json()
    data = {
        'symbol': 'btcthb', # The symbol
        'type': 'step0' #https://www.reddit.com/r/huobi/comments/9xa5xg/what_is_the_purpose_of_step0_step1_step2_step3/
    }
    # Depth Type: step0, step1, step2, step3, step4, step5（merged depth 0-5）- step0 means doesn’t merge
    # When the user selects “Merged Depth”, the market pending orders within the certain quotation accuracy will be combined and displayed. The merged depth only changes the display mode and does not change the actual order price
    # 24 hours trade summary and best bid/ask for a symbol
    # response = requests.get(API_HOST + '/market/depth',data)
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
#spread
    # https://blog.shrimpy.io/blog/cryptocurrency-trading-101-exchange-market-spread?rq=spread
    # AL(lowest ask price) - BH(highest buy price) = Spread
    # Percent Spread = (Spread / lowest ask price) x 100
    max_bid=float(df_bid.iloc[0]['price'])
    min_ask=float(df_ask.iloc[0]['price'])
    spread=((min_ask-max_bid)/min_ask)*100
#slippage
    # kaiko
    avg_buy_price=0
    best_ask=min_ask
    best_bid=max_bid
    midPrice=(best_ask+best_bid)/2
    sum_buy_price=0
    shrimpy_slippage_list=[]
    kaiko_slippage_list=[]
    bybit_slippage_list=[]
    hb_slippage_list=[]
    for btc_sell_amount in btc_sell_list:
        sum_amount=0
        pi=float(df_ask.iloc[0]['price'])
        sum_buy_price=0 
        for i in range (len(ask)):
            if btc_sell_amount > sum_amount:
                sum_amount=float(df_ask.iloc[i]['amount'])+sum_amount
                sum_buy_price= sum_buy_price+float(df_ask.iloc[i]['price'])
                if sum_amount>=btc_sell_amount:
                    pf=float(df_ask.iloc[i]['price'])
                    index=i+1
                    break
        if sum_amount<btc_sell_amount and i==len(ask)-1:
                hb_slippage_list.append([-1,-1,-1])
                while(len(hb_slippage_list)!= len(btc_sell_list)) :
                    hb_slippage_list.append([-1,-1,-1])
                break
        b_sum_amount=0
        sum_ask_price= 0
        b_pi=float(df_bid.iloc[0]['price'])
        for i in range (len(bid)):
            if btc_sell_amount > b_sum_amount:
                b_sum_amount=float(df_bid.iloc[i]['amount'])+b_sum_amount
                sum_ask_price= sum_ask_price+float(df_bid.iloc[i]['price'])
                if b_sum_amount>=btc_sell_amount:
                    b_pf=float(df_bid.iloc[i]['price'])
                    b_index=i+1
                    break
        if b_sum_amount<btc_sell_amount and i==len(ask)-1:
                break
        avg_buy_price=sum_buy_price/(index)
        bybit_slippage=math.fabs(b_pf-pf)/midPrice
        shrimpy_slippage=(math.fabs(pf-pi)/pi)
        kaiko_slippage=(math.fabs(avg_buy_price-midPrice)/midPrice)

        shrimpy_slippage_list.append(shrimpy_slippage)
        kaiko_slippage_list.append(kaiko_slippage)
        bybit_slippage_list.append(bybit_slippage)
        
        hb_slippage_list.append([shrimpy_slippage,kaiko_slippage,bybit_slippage])
#         hb_slippage_list.append(shrimpy_slippage_list)
#         hb_slippage_list.append(kaiko_slippage_list)
#         hb_slippage_list.append(bybit_slippage_list)
        

    return [time,hb_slippage_list,spread]


def satang(btc_sell_list):
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
    df_ask=df_ask.sort_values(by='price', ascending=True)
    df_bid=df_bid.sort_values(by='price', ascending=False)
#spread
    # https://blog.shrimpy.io/blog/cryptocurrency-trading-101-exchange-market-spread?rq=spread
    # AL(lowest ask price) - BH(highest buy price) = Spread
    # Percent Spread = (Spread / lowest ask price) x 100
    max_bid=float(df_bid.iloc[0]['price'])
    min_ask=float(df_ask.iloc[0]['price'])
    spread=((min_ask-max_bid)/min_ask)*100
#slippage
    # kaiko
    avg_buy_price=0
    best_ask=min_ask
    best_bid=max_bid
    midPrice=(best_ask+best_bid)/2
    sum_buy_price=0
    shrimpy_slippage_list=[]
    kaiko_slippage_list=[]
    bybit_slippage_list=[]
    sp_slippage_list=[]
    for btc_sell_amount in btc_sell_list:
        sum_amount=0
        pi=float(df_ask.iloc[0]['price'])
        sum_buy_price=0 
        for i in range (len(ask)):
            if btc_sell_amount > sum_amount:
                sum_amount=float(df_ask.iloc[i]['amount'])+sum_amount
                sum_buy_price= sum_buy_price+float(df_ask.iloc[i]['price'])
                if sum_amount>=btc_sell_amount:
                    pf=float(df_ask.iloc[i]['price'])
                    index=i+1
                    break
        if sum_amount<btc_sell_amount and i==len(ask)-1:
                sp_slippage_list.append([-1,-1,-1])
                while(len(sp_slippage_list)!= len(btc_sell_list)) :
                    sp_slippage_list.append([-1,-1,-1])
                break
        b_sum_amount=0
        sum_ask_price= 0
        b_pi=float(df_bid.iloc[0]['price'])
        for i in range (len(bid)):
            if btc_sell_amount > b_sum_amount:
                b_sum_amount=float(df_bid.iloc[i]['amount'])+b_sum_amount
                sum_ask_price= sum_ask_price+float(df_bid.iloc[i]['price'])
                if b_sum_amount>=btc_sell_amount:
                    b_pf=float(df_bid.iloc[i]['price'])
                    b_index=i+1
                    break
        if b_sum_amount<btc_sell_amount and i==len(ask)-1:
                    break
        avg_buy_price=sum_buy_price/(index)
        bybit_slippage=math.fabs(b_pf-pf)/midPrice
        shrimpy_slippage=(math.fabs(pf-pi)/pi)
        kaiko_slippage=(math.fabs(avg_buy_price-midPrice)/midPrice)
        
        shrimpy_slippage_list.append(shrimpy_slippage)
        kaiko_slippage_list.append(kaiko_slippage)
        bybit_slippage_list.append(bybit_slippage)
        
        sp_slippage_list.append([shrimpy_slippage,kaiko_slippage,bybit_slippage])
#         sp_slippage_list.append(shrimpy_slippage_list)
#         sp_slippage_list.append(kaiko_slippage_list)
#         sp_slippage_list.append(bybit_slippage_list)
    return [sp_slippage_list,spread]


def bitazza(btc_sell_list):
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
        "depth": 10,
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
# spread
    # https://blog.shrimpy.io/blog/cryptocurrency-trading-101-exchange-market-spread?rq=spread
    # AL(lowest ask price) - BH(highest buy price) = Spread
    # Percent Spread = (Spread / lowest ask price) x 100
    max_bid=float(df_bid.iloc[0]['price'])
    min_ask=float(df_ask.iloc[0]['price'])
    spread=((min_ask-max_bid)/min_ask)*100
# SLIPPAGE
    # kaiko
    avg_buy_price=0
    best_ask=min_ask
    best_bid=max_bid
    midPrice=(best_ask+best_bid)/2
    sum_buy_price=0
    shrimpy_slippage_list=[]
    kaiko_slippage_list=[]
    bybit_slippage_list=[]
    bz_slippage_list=[]
    for btc_sell_amount in btc_sell_list:
        sum_amount=0
        pi=float(df_ask.iloc[0]['price'])
        sum_buy_price=0 
        for i in range (len(ask)):
            if btc_sell_amount > sum_amount:
                sum_amount=float(df_ask.iloc[i]['amount'])+sum_amount
                sum_buy_price= sum_buy_price+float(df_ask.iloc[i]['price'])
                if sum_amount>=btc_sell_amount:
                    pf=float(df_ask.iloc[i]['price'])
                    index=i+1
                    break
        if sum_amount<btc_sell_amount and i==len(ask)-1:
            bz_slippage_list.append([-1,-1,-1])
            while(len(bz_slippage_list)!= len(btc_sell_list)) :
                bz_slippage_list.append([-1,-1,-1])
                
            break
        b_sum_amount=0
        sum_ask_price= 0
        b_pi=float(df_bid.iloc[0]['price'])
        for i in range (len(bid)):
            if btc_sell_amount > b_sum_amount:
                b_sum_amount=float(df_bid.iloc[i]['amount'])+b_sum_amount
                sum_ask_price= sum_ask_price+float(df_bid.iloc[i]['price'])
                if b_sum_amount>=btc_sell_amount:
                    b_pf=float(df_bid.iloc[i]['price'])
                    b_index=i+1
                    break

        if b_sum_amount<btc_sell_amount and i==len(ask)-1:
                    break
        avg_buy_price=sum_buy_price/(index)
        
        bybit_slippage=math.fabs(b_pf-pf)/midPrice
        shrimpy_slippage=(math.fabs(pf-pi)/pi)
        kaiko_slippage=(math.fabs(avg_buy_price-midPrice)/midPrice)

        shrimpy_slippage_list.append(shrimpy_slippage)
        kaiko_slippage_list.append(kaiko_slippage)
        bybit_slippage_list.append(bybit_slippage)
        
        bz_slippage_list.append([shrimpy_slippage,kaiko_slippage,bybit_slippage])
#         bz_slippage_list.append(shrimpy_slippage_list)
#         bz_slippage_list.append(kaiko_slippage_list)
#         bz_slippage_list.append(bybit_slippage_list)
    return [time,bz_slippage_list,spread]

# MAIN-----------------------------------

btc_sell_list=[0.1,0.3,0.5,1,5]
bk_time,bk_slippage,bk_spread=bitkub(btc_sell_list)
hb_time,hb_slippage,hb_spread=huobi_thailand(btc_sell_list)
sp_slippage,sp_spread=satang(btc_sell_list)
bz_time,bz_slippage,bz_spread=bitazza(btc_sell_list)

bk_slp_rows=(np.array(bk_slippage).T).tolist()
hb_slp_rows=(np.array(hb_slippage).T).tolist()
sp_slp_rows=(np.array(sp_slippage).T).tolist()
bz_slp_rows=(np.array(bz_slippage).T).tolist()

slippage_spread_rows=[hb_time,bk_slippage,bk_slp_rows[0],bk_slp_rows[1],bk_slp_rows[2],
                      sp_slippage,sp_slp_rows[0],sp_slp_rows[1],sp_slp_rows[2],
                      hb_slippage,hb_slp_rows[0],hb_slp_rows[1],hb_slp_rows[2],
                      bz_slippage,bz_slp_rows[0],bz_slp_rows[1],bz_slp_rows[2]]

df_slippage_spread = pd.DataFrame(columns=["date","bk-spread","bk-slp-shrimpy","bk-slp-kaiko","bk-slp-bybit",
                                           "sp-spread","sp-slp-shrimpy","sp-slp-kaiko","sp-slp-bybit",
                                           "hb-spread","hb-slp-shrimpy","hb-slp-kaiko","hb-slp-bybit",
                                           "bz-spread","bz-slp-shrimpy","bz-slp-kaiko","bz-slp-bybit"])
df_slippage_spread.to_csv("df_slippage_spread.csv", index=False)
df=pd.read_csv("df_slippage_spread.csv")
df=pd.read_csv("df_slippage_spread.csv")
df.loc[len(df)]=slippage_spread_rows
df.to_csv("df_slippage_spread.csv", index=False)
df


# In[ ]:




