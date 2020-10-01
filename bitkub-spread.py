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
            bk_slippage_list.append([-1,-1,-1])
            while(len(bk_slippage_list)!= len(btc_sell_list)) :
                bk_slippage_list.append([-1,-1,-1])
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
btc_sell_list=[0.1,0.3,0.5,1,5]
bk_time,bk_slippage,bk_spread=bitkub(btc_sell_list)


bk_slp_rows=(np.array(bk_slippage).T).tolist()


slippage_spread_rows=[bk_time,bk_slippage,bk_slp_rows[0],bk_slp_rows[1],bk_slp_rows[2]]



# df_slippage_spread = pd.DataFrame(columns=["date","bk-spread","bk-slp-shrimpy","bk-slp-kaiko","bk-slp-bybit"])
# df_slippage_spread.to_csv("spread-slippage/bk_slippage_spread.csv", index=False)


df=pd.read_csv("spread-slippage/bk_slippage_spread.csv")
df.loc[len(df)]=slippage_spread_rows
df.to_csv("spread-slippage/bk_slippage_spread.csv", index=False)


# In[ ]:




