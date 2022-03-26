from flask import Flask
from flask import Flask, render_template, request, redirect, url_for
import numpy as np
import matplotlib.pyplot as plt
from scipy.stats import norm
from pprint import pprint
import pandas as pd
import datetime
import math
import itertools
import yfinance as yf
from math import log

#===============Flask===============#
app = Flask(__name__)

'''
@app.route("/")
def index():
    return df_html

'''
@app.route("/", methods=("POST", "GET"))
def chain():
    if request.method == 'POST':
   
	    tic = request.form["ticker"]
	    pri = request.form["price"]
	    dte = request.form["dte"]
	    vol = request.form["vol"]
	    num = request.form["strikes"]
	    values =f" {tic}, {pri}, 210 , {dte}, .01, .005, {vol}".replace(" ", "").split(",")
	    print(values)
	    n = num
	    tuple_objects = testing(values, n )
	    return render_template('chain.html', info_list=tuple_objects[1] , o_chain = tuple_objects[0])

    else:
         values = " AAPL, 166, 210 , 44, .01, .005, .55".replace(" ", "").split(",")
         n = 40
         tuple_objects = testing(values,n)
    return render_template('chain.html', info_list=tuple_objects[1] , o_chain = tuple_objects[0])




def testing(values, number_of_strikes ):


	# values = " AAPL, 166, 210 , 44, .01, .005, .55".replace(" ", "").split(",")
	#===============Input===============#
	# Input Data
	# values = input().replace(" ", "").split(",")
	ticker= values[0]
	values.pop(0)
	values_ints = [float(g) for g in values]
	S, K, T, r, q, sigma = values_ints


	# Clean and Normalize Data
	T = T/252        # Annualize the DTE (This at 365 was giving neg value....)
	for i, elem in enumerate(itertools.islice(values_ints, 3, 6)):
	    if elem >= 1:
	        values_ints[i+3] = elem/100
	        
	# Get Strike interval from y finance
	ref = yf.Ticker(ticker.lower())
	options = ref.option_chain()
	strike_interval = options.calls.strike[1] - options.calls.strike[0]



	# Number of strikes to show in the Chain
	# Rounds the Current Price S to strike intervals 
	# e.g. Showing 10 strikes for current price 166 at interval 5 for AAPL 
	# shows calls at strikes: 145 -> 195
	num_strikes = int(number_of_strikes)
	atm_strike = round(S / strike_interval) * strike_interval 
	high_strike = atm_strike + strike_interval* num_strikes/2
	low_strike = atm_strike - strike_interval* num_strikes/2
	chain_range = np.arange(low_strike, high_strike, strike_interval)


	# Even out the number of OTM and ITM strikes
	if atm_strike < S:  
	    chain_range = np.append(chain_range, [high_strike + strike_interval])
	    chain_range = np.delete(chain_range, 0)
	print("Inputs : ", S, K, T, r, q, sigma)

	


	#===============Logic===============#
	# Black scholes Eq
	# First term is risk adjusted probability of option being exercised
	# Occurs when S is equal or greater than K
	# Second term is inverse probability of investor not exercising
	# K is discounted by risk free ratr r for remainder of options maturity T


	def b_scholes_call(S, K, T, r, q, sigma):
	    
	    N = norm.cdf
	    call = S* N(d1(S,K,T,r,sigma)) - N(d2(d1(S,K,T,r,sigma), sigma, T))*K*np.exp(-r*T)
	    return call

	# Probabilty of option being exercised
	def d1(S, K, T, r, sigma):
	    return (np.log(S/K) + (r -q + sigma**2/2)*T) /(sigma*np.sqrt(T))


	# Probabilty of option not being exercised
	def d2(dee1, sigma, T ):
	    return dee1 - sigma*np.sqrt(T)

	# Calculate Delta, Change in option price with respect to Spot
	def delta_call(S, K, T, r, sigma):
	    N = norm.cdf
	    return N(d1(S, K, T, r, sigma))

	# Calculate Gamma,Change in Delta, Rate change of Delta
	# always positive fof a long position calls or puts
	def gamma_call(S,K, T, r , sigma):
	    N = norm.cdf
	    return N(d1(S, K, T, r, sigma))/(S*sigma*np.sqrt(T))

	# Sensitivity of option price with respect to volatility
	def vega_call(S, K , T, r, sigma):
	    N=norm.cdf
	    return S*np.sqrt(T)*N(d1(S, K, T, r, sigma))
	    


	#===============Chain===============#

	theo_price = []
	strike = []
	delta = []
	put_delta = []
	put_theo_price = []
	gamma = []
	vega = []

	# Get Option Chain details calling Black Scholes for each strike
	# Note this is iterating over strikes k , Note the strike that was given in input
	for k in chain_range:

	    # Call
	    call_price = b_scholes_call(S, k , T, r, q, sigma)
	    theo_price.append(call_price)
	    strike.append(int(k))
	    delta.append(delta_call(S, k, T, r, sigma))
	    gamma.append(gamma_call(S, k, T, r, sigma))
	    vega.append(gamma_call(S, k, T, r, sigma))
	    
	    # Put
	    put_delta.append((1- delta_call(S, k, T, r, sigma))*-1)
	    put_theo_price.append(call_price +( k / (1+ r)**T) - S)

	    


	#===============Testing=============#
	def ticker_curr_or_last(stock):
	  
	    t = yf.Ticker(stock.lower())
	    try:
	        # During market hours open
	        price = t.info['regularMarketPrice']
	        pricing = stock.upper() + " is Currently trading at ${}".format(price)

	    except:
	        # Get last close if you can't get live quote
	        t  = t.history(period='id')
	        price = t["Close"][0]
	        pricing = stock.upper() + " closed at  ${}".format(price)

	    return pricing




	# Specific Option Chain info 
	info_basic = f"Modeling {ticker} @ : ${S} , {sigma*100}% Implied Volatility with {int(T*252)} DTE\n"
	info_model = "European Options modeled with Black-Scholes-Merton , The greeks reflect a long option position.\n"
	info_ticker = ticker_curr_or_last(ticker) + "\n"
	info_list = [info_basic , info_model , info_ticker]

	print(info_model)
	print(info_ticker)
	print(info_basic)
	# print (f"Historical Volatility : XXX%")





	#===============Sytling===============#
	# Creation
	df = pd.DataFrame({"Call Price": theo_price,"Gamma":gamma,"Vega":vega,  "Delta":delta, "Strike":strike, "Delta ":put_delta,"Vega ":vega,"Gamma ":gamma, "Put Price": put_theo_price})
	df.insert(0,"IV", sigma*100 )
	df.insert(10,"IV ", sigma*100 )



	# Shading for Calls
	def call_shading(row):
	    if row['Strike'] < S:
	        return pd.Series('background-color: beige', row.index)
	    else: 
	        return pd.Series('background-color: azure', row.index)
	    

	# Applys multiple stylings to the df  
	def make_it_nice(styler, num_strike):
	    # Shade the calls
	    styler.apply(call_shading,axis=1)
	    
	    # Shade ITM puts
	    slicer  = [ "Delta ","Vega ", "Gamma ", "Put Price", "IV "]
	    styler.set_properties(**{"background-color": "beige"}, subset=slicer)
	    
	    # Shade OTM Puts
	    idx = pd.IndexSlice
	    sliced = idx[idx[0:(num_strike/2)-1],idx["Delta " :"IV "]]
	    styler.set_properties(**{"background-color": "azure"}, subset=sliced)
	    
	    

	    styler.set_properties(**{'font-weight': 'bold'}, subset=['Strike'])
	    # styler.set_properties(color="red", align="right")  
	    styler.set_properties(**{'background-color': 'lightslategrey','color':'white' }, subset=['Strike'])
	    
	    
	    return styler

	# Prepare html to display in flask
	fancy = df.style.pipe(make_it_nice, num_strikes)
	df_html = fancy.render()
	return df_html, info_list









if __name__ == '__main__':
    app.run(debug = False)


