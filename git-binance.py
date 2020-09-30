#!/usr/bin/env python
# coding: utf-8

# In[4]:


# https://python-binance.readthedocs.io/en/latest/
from binance.client import Client
import datetime
import pandas as pd
import math
import numpy as np

client = Client('dyZMalaTBM0vNWwLKeDfjp6r7CxswhmqHGb29LIA15lvR1klcmUp0qmTxQueKMGD', 'AnYFvyhK1dTntOiiq2wrCXbEJms11bLFYWvjFcHfJMLXqSvGleiO3NsRzalsLQFL')

# get market depth
depth = client.get_order_book(symbol='ETHBTC')

t=(client.get_exchange_info())['serverTime']
time=datetime.datetime.fromtimestamp(t/1000)

depth
bid=depth['bids']
ask=depth['asks']

# BID-ASK DATAFRAME
df_bid = pd.DataFrame(columns=["price","amount"])
df_ask = pd.DataFrame(columns=["price","amount"])
for i in range(len(bid)):
    df_bid.loc[i]=bid[i]
for i in range(len(ask)):
    df_ask.loc[i]=ask[i]
df_ask=df_ask.sort_values(by='price', ascending=True)
df_bid=df_bid.sort_values(by='price', ascending=False)

# spread
max_bid=float(df_bid.iloc[0]['price'])
min_ask=float(df_ask.iloc[0]['price'])
spread=((min_ask-max_bid)/min_ask)*100


# SLIPPAGE
avg_buy_price=0
best_ask=min_ask
best_bid=max_bid
midPrice=(best_ask+best_bid)/2
sum_buy_price=0
btc_sell_list=[0.1,0.3,0.5,1,5]
shrimpy_slippage_list=[]
kaiko_slippage_list=[]
bybit_slippage_list=[]
bn_slippage_list=[]


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
        bn_slippage_list.append([-1,-1,-1])
        while(len(bn_slippage_list)!= len(btc_sell_list)) :
            bn_slippage_list.append([-1,-1,-1])

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

    bn_slippage_list.append([shrimpy_slippage,kaiko_slippage,bybit_slippage])

bn_slp_rows=(np.array(bn_slippage_list).T).tolist()
bn_slippage_spread_rows=[time,spread,bn_slp_rows[0],bn_slp_rows[1],bn_slp_rows[2]]


# comment this when exist csv file##############################################################
# bn_slippage_spread = pd.DataFrame(columns=["date","bn-spread","bn-slp-shrimpy","bn-slp-kaiko","bn-slp-bybit"])
# bn_slippage_spread.to_csv("spread-slippage/bn_slippage_spread.csv", index=False)
#################################################################################################


df=pd.read_csv("spread-slippage/bn_slippage_spread.csv")

df.loc[len(df)]=bn_slippage_spread_rows
df.to_csv("spread-slippage/bn_slippage_spread.csv", index=False)



