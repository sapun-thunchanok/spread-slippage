#!/usr/bin/env python
# coding: utf-8

# In[33]:


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
        'lmt': 100
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
    
    best_ask=min_ask
    best_bid=max_bid
    sum_buy_price=0
    ask_slippage_list=[]
    bid_slippage_list=[]
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
            ask_slippage_list.append(-1)
            while(len(ask_slippage_list)!= len(btc_sell_list)) :
                ask_slippage_list.append(-1)
            break
        
        ask_slippage=(math.fabs(pf-pi)/pi)*100
        ask_slippage_list.append(ask_slippage)
       
    for btc_sell_amount in btc_sell_list:
        sum_amount=0
        b_pi=float(df_bid.iloc[0]['rate'])
        sum_sell_price=0 
        for i in range (len(bid)):
            if btc_sell_amount > sum_amount:
                sum_amount=float(df_bid.iloc[i]['amount'])+sum_amount
                sum_sell_price= sum_sell_price+float(df_bid.iloc[i]['rate'])
                if sum_amount>=btc_sell_amount:
                    b_pf=float(df_bid.iloc[i]['rate'])
                    index=i+1
                    break
        if sum_amount<btc_sell_amount and i==len(bid)-1 :
            bid_slippage_list.append(-1)
            while(len(bid_slippage_list)!= len(btc_sell_list)) :
                bid_slippage_list.append(-1)
            break
        
        bid_slippage=(math.fabs(b_pf-b_pi)/b_pi)*100
        bid_slippage_list.append(bid_slippage)
    return [df_ask.iloc[0]['time'],ask_slippage_list,bid_slippage_list,spread]
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
    best_ask=min_ask
    best_bid=max_bid
    ask_slippage_list=[]
    bid_slippage_list=[]
#     ask slippage
    for btc_sell_amount in btc_sell_list:
        sum_amount=0
        a_pi=float(df_ask.iloc[0]['price'])
        sum_buy_price=0 
        for i in range (len(ask)):
            if btc_sell_amount > sum_amount:
                sum_amount=float(df_ask.iloc[i]['amount'])+sum_amount
                sum_buy_price= sum_buy_price+float(df_ask.iloc[i]['price'])
                if sum_amount>=btc_sell_amount:
                    a_pf=float(df_ask.iloc[i]['price'])
                    index=i+1
                    break
        if sum_amount<btc_sell_amount and i==len(ask)-1:
                ask_slippage_list.append(-1)
                while(len(ask_slippage_list)!= len(btc_sell_list)) :
                    ask_slippage_list.append(-1)
                break
        
        ask_slippage=(math.fabs(a_pf-a_pi)/a_pi)*100
        ask_slippage_list.append(ask_slippage)
#     bid slippage
    for btc_sell_amount in btc_sell_list:
        sum_amount=0
        b_pi=float(df_bid.iloc[0]['price'])
        sum_sell_price=0 
        for i in range (len(bid)):
            if btc_sell_amount > sum_amount:
                sum_amount=float(df_bid.iloc[i]['amount'])+sum_amount
                sum_sell_price= sum_sell_price+float(df_bid.iloc[i]['price'])
                if sum_amount>=btc_sell_amount:
                    b_pf=float(df_bid.iloc[i]['price'])
                    index=i+1
                    break
        if sum_amount<btc_sell_amount and i==len(bid)-1:
                bid_slippage_list.append(-1)
                while(len(bid_slippage_list)!= len(btc_sell_list)) :
                    bid_slippage_list.append(-1)
                break
        
        bid_slippage=(math.fabs(b_pf-b_pi)/b_pi)*100
        bid_slippage_list.append(bid_slippage)

    return [time,ask_slippage_list,bid_slippage_list,spread]

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
    best_ask=min_ask
    best_bid=max_bid
    ask_slippage_list=[]
    bid_slippage_list=[]
#     ask slippage
    for btc_sell_amount in btc_sell_list:
        sum_amount=0
        a_pi=float(df_ask.iloc[0]['price'])
        sum_buy_price=0 
        for i in range (len(ask)):
            if btc_sell_amount > sum_amount:
                sum_amount=float(df_ask.iloc[i]['amount'])+sum_amount
                sum_buy_price= sum_buy_price+float(df_ask.iloc[i]['price'])
                if sum_amount>=btc_sell_amount:
                    a_pf=float(df_ask.iloc[i]['price'])
                    index=i+1
                    break
        if sum_amount<btc_sell_amount and i==len(ask)-1:
                ask_slippage_list.append(-1)
                while(len(ask_slippage_list)!= len(btc_sell_list)) :
                    ask_slippage_list.append(-1)
                break
        
    
        ask_slippage=(math.fabs(a_pf-a_pi)/a_pi)*100
        ask_slippage_list.append(ask_slippage)
#     bid slippage
    for btc_sell_amount in btc_sell_list:
        sum_amount=0
        b_pi=float(df_bid.iloc[0]['price'])
        sum_sell_price=0 
        for i in range (len(bid)):
            if btc_sell_amount > sum_amount:
                sum_amount=float(df_bid.iloc[i]['amount'])+sum_amount
                sum_sell_price= sum_sell_price+float(df_bid.iloc[i]['price'])
                if sum_amount>=btc_sell_amount:
                    b_pf=float(df_bid.iloc[i]['price'])
                    index=i+1
                    break
        if sum_amount<btc_sell_amount and i==len(bid)-1:
                bid_slippage_list.append(-1)
                while(len(bid_slippage_list)!= len(btc_sell_list)) :
                    bid_slippage_list.append(-1)
                break
        
    
        bid_slippage=(math.fabs(b_pf-b_pi)/b_pi)*100
        bid_slippage_list.append(bid_slippage)

    return [ask_slippage_list,bid_slippage_list,spread]
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
# spread
    # https://blog.shrimpy.io/blog/cryptocurrency-trading-101-exchange-market-spread?rq=spread
    # AL(lowest ask price) - BH(highest buy price) = Spread
    # Percent Spread = (Spread / lowest ask price) x 100
    max_bid=float(df_bid.iloc[0]['price'])
    min_ask=float(df_ask.iloc[0]['price'])
    spread=((min_ask-max_bid)/min_ask)*100
# SLIPPAGE
    best_ask=min_ask
    best_bid=max_bid
    ask_slippage_list=[]
    bid_slippage_list=[]
#     ask slippage
    for btc_sell_amount in btc_sell_list:
        sum_amount=0
        a_pi=float(df_ask.iloc[0]['price'])
        sum_buy_price=0 
        for i in range (len(ask)):
            if btc_sell_amount > sum_amount:
                sum_amount=float(df_ask.iloc[i]['amount'])+sum_amount
                sum_buy_price= sum_buy_price+float(df_ask.iloc[i]['price'])
                if sum_amount>=btc_sell_amount:
                    a_pf=float(df_ask.iloc[i]['price'])
                    index=i+1
                    break
        if sum_amount<btc_sell_amount and i==len(ask)-1:
            ask_slippage_list.append(-1)
            while(len(ask_slippage_list)!= len(btc_sell_list)) :
                ask_slippage_list.append(-1)
                
            break
        ask_slippage=(math.fabs(a_pf-a_pi)/a_pi)
        ask_slippage_list.append(ask_slippage)
#     bid slippage
    for btc_sell_amount in btc_sell_list:
        sum_amount=0
        b_pi=float(df_bid.iloc[0]['price'])
        sum_sell_price=0 
        for i in range (len(bid)):
            if btc_sell_amount > sum_amount:
                sum_amount=float(df_bid.iloc[i]['amount'])+sum_amount
                sum_sell_price= sum_sell_price+float(df_bid.iloc[i]['price'])
                if sum_amount>=btc_sell_amount:
                    b_pf=float(df_bid.iloc[i]['price'])
                    index=i+1
                    break
        if sum_amount<btc_sell_amount and i==len(bid)-1:
            bid_slippage_list.append(-1)
            while(len(bid_slippage_list)!= len(btc_sell_list)) :
                bid_slippage_list.append(-1)
                
            break
        bid_slippage=(math.fabs(b_pf-b_pi)/b_pi)
        bid_slippage_list.append(bid_slippage)
    return [time,ask_slippage_list,bid_slippage_list,spread]

# MAIN-----------------------------------
btc_sell_list=[0.1,0.3,0.5,1,5]
bk_time,bk_ask_slippage,bk_bid_slippage,bk_spread=bitkub(btc_sell_list)
hb_time,hb_ask_slippage,hb_bid_slippage,hb_spread=huobi_thailand(btc_sell_list)
sp_ask_slippage,sp_bid_slippage,sp_spread=satang(btc_sell_list)
bz_time,bz_ask_slippage,bz_bid_slippage,bz_spread=bitazza(btc_sell_list)


slippage_spread_rows=[hb_time,bk_spread,bk_ask_slippage,bk_bid_slippage,
                      hb_spread,hb_ask_slippage,hb_bid_slippage,
                      sp_spread,sp_ask_slippage,sp_bid_slippage,
                      bz_spread,bz_ask_slippage,bz_bid_slippage]
# df_slippage_spread = pd.DataFrame(columns=["date","bk-spread","bk_ask_slippage","bk_bid_slippage",
#                                            "sp-spread","sp_ask_slippage","sp_bid_slippage",
#                                            "hb-spread","hb_ask_slippage","hb_bid_slippage",
#                                            "bz-spread","bz_ask_slippage","bz_bid_slippage"])
# # df_slippage_spread.to_csv("spread-slippage/df_slippage_spread.csv", index=False)
# # df_slippage_spread.to_csv("//Users//thunchanok//Downloads//df_slippage-eq1.csv", index=False)
# df_slippage_spread.to_csv("spread-slippage/df_slippage-eq1.csv", index=False)

# df=pd.read_csv("//Users//thunchanok//Downloads//df_slippage-eq1.csv")
df=pd.read_csv("spread-slippage/df_slippage-eq1.csv")
df.loc[len(df)]=slippage_spread_rows
# df.to_csv("//Users//thunchanok//Downloads//df_slippage-eq1.csv", index=False)
df.to_csv("spread-slippage/df_slippage-eq1.csv", index=False)
# df


# In[37]:


# print(df['bk_ask_slippage'].loc[0])
# print(df['bk_bid_slippage'].loc[0])
# print(df['sp_ask_slippage'].loc[0])
# print(df['sp_bid_slippage'].loc[0])
# print(df['hb_ask_slippage'].loc[0])
# print(df['hb_bid_slippage'].loc[0])
# print(df['bz_ask_slippage'].loc[0])
# print(df['bz_bid_slippage'].loc[0])


# In[ ]:




