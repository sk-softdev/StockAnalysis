from flask import Blueprint, Flask, render_template, request, url_for, redirect, session, flash, g
from polygon import RESTClient
from datetime import datetime, date, timedelta
from StockAnalysis.db import get_db
import requests, time, json, random

bp = Blueprint("StockAnalysis", __name__)

# This function takes in ticker to be added from html form to relay relevant data (appended to arr) to website
# The g name stands for “global”, but that is referring to the data being global within a context. 
# The data on g is lost after the context ends, and it is not an appropriate place to store data between requests. 
# Use the session or a database to store data across requests.

@bp.route("/", methods=['GET', 'POST'])
def home():
	marketStatus = "closed"
	currentYear = str(date.today().year)
	holidays = [currentYear + "-01-17", currentYear + "-02-21", currentYear + "-04-15", currentYear + "-05-30", currentYear + "-06-20", currentYear + "-07-04", currentYear + "-09-05", currentYear + "-11-24", currentYear + "-12-26"]
	if 'dataCreated' not in session:
		session['dataCreated'] = False
		session['userDataCreated'] = False
		session['tableHeight'] = 50
		session['newsHeight'] = 50
		session['userFilter'] = ""
		session['noStocksAfterCreation'] = False
    
	dataCreated = session.get("dataCreated")
	userDataCreated = session.get("userDataCreated")
	tableHeight = session.get("tableHeight")
	newsHeight = session.get("newsHeight")
	userFilter = session.get("userFilter")
	noStocksAfterCreation = session.get("noStocksAfterCreation")

	if datetime.today().weekday() < 5:
		today = date.today()
	else:
		today = date.today() - timedelta(days = datetime.today().weekday() - 4)

	if str(today) in holidays:
		today = today - timedelta(days = 1)

	if request.method == 'POST':
		duplicate = False
		stored = False
		ticker = request.form.get('tckr')
		db = get_db()
		userStats = db.execute("SELECT * FROM userStats").fetchall()
		if g.user['stocks'] is not None:
			tickers = g.user['stocks']
			tickersList = tickers.split(",")
			for x in tickersList:
				if x == ticker:
					duplicate = True
					break

		if (duplicate == False):
			addStock(ticker, today, stored)
			tableHeight = session.get("tableHeight")
			newsHeight = session.get("newsHeight")
		else:
			flash("You're already tracking " + ticker + ".", "info")

	# initial data creation if stored data exists, shift + tab to go left
	if g.user is not None and userDataCreated == False or marketStatus == open:
		if g.user['stocks'] is not None:
			tickers = g.user['stocks']
			tickersList = tickers.split(",")
			db = get_db()
			db.execute("DELETE FROM userStats")
			db.commit()
			for ticker in tickersList:
				stored = True
				addStock(ticker, today, stored)
				tableHeight = session.get("tableHeight")
				newsHeight = session.get("newsHeight")
				time.sleep(10)
		session['userDataCreated'] = True

	if dataCreated == False or marketStatus == "open":
		dataCreate(today)
		dataCreated = True
		session['dataCreated'] = True

	db = get_db()
	marketWinners = db.execute("SELECT * FROM marketStats " + userFilter + " ORDER BY change DESC LIMIT 10").fetchall()
	marketLosers = db.execute("SELECT * FROM marketStats " + userFilter + " ORDER BY change LIMIT 10").fetchall()
	marketPopular = db.execute("SELECT * FROM marketStats " + userFilter + " ORDER BY volume DESC LIMIT 10").fetchall()
	userStats = db.execute("SELECT * FROM userStats").fetchall()
	return render_template("index.html", dataCreated=dataCreated, userDataCreated=userDataCreated, tableHeight=tableHeight, newsHeight=newsHeight, marketWinners=marketWinners, marketLosers=marketLosers, marketPopular=marketPopular, userStats=userStats, noStocksAfterCreation=noStocksAfterCreation)

def addStock(ticker, today, stored):
	session['noStocksAfterCreation'] = False
	key = 'XoIHGXzAz89flV3zUjNGpOEf9zJ0iidW'
	tableHeight = session.get("tableHeight")
	newsHeight = session.get("newsHeight")
	req = requests.get("https://api.polygon.io/v1/meta/symbols/" + ticker + "/company?apiKey=" + key)
	data = json.loads(req.content)
	name = data['name']
	logo = data['logo']
	tickerID = random.randint(100000,1000000)
	buttonID = random.randint(100000,1000000)
	session['tableHeight'] = tableHeight + 75
	session['newsHeight'] = newsHeight + 75
	req = requests.get("https://api.polygon.io/v2/aggs/ticker/" + ticker + "/prev?adjusted=true&apiKey=" + key)
	data = json.loads(req.content)
	stockPrice = data['results'][0]['c'] # data[i][0] = dictionary then add index (ex:['c'] or closing share price) to get specific key value
	priceChange = round(((data['results'][0]['o'] - data['results'][0]['c']) / data['results'][0]['o']) * -100, 2) # Opening share price - closing share price / opening share price * -100
	volume = data['results'][0]['v']
	req = requests.get("https://api.polygon.io/v2/reference/news?ticker=" + ticker + "&apiKey=" + key)
	data = json.loads(req.content)
	newsTitle = data['results'][1]['title']
	newsPublisher = data['results'][0]['publisher']['name']
	newsDate = data['results'][3]['published_utc']
	db = get_db()
	db.execute(
    	"INSERT INTO userStats (name, ticker, logo, tickerID, buttonID, stockPrice, priceChange, volume, newsTitle, newsPublisher, newsDate) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)",
    	(name, ticker, logo, tickerID, buttonID, stockPrice, priceChange, volume, newsTitle, newsPublisher, newsDate),
	)
	db.commit()

	if stored == False:
		user_id = session.get("user_id")   
		if (g.user['stocks'] is None): # initial 
			db.execute("UPDATE user SET stocks = ? WHERE id = ?", (ticker, g.user['id']))
		else: # update after initial creation
			db.execute("UPDATE user SET stocks = ? WHERE id = ?", (g.user['stocks'] + "," + ticker, g.user['id']))
		db.commit()

	return

def dataCreate(today):
	db = get_db()
	#db.execute("DELETE FROM marketStats")
	#db.commit()
	key = 'XoIHGXzAz89flV3zUjNGpOEf9zJ0iidW'
	req = requests.get("https://api.polygon.io/v2/aggs/grouped/locale/us/market/stocks/" + str(today) + "?adjusted=true&apiKey=" + key)
	data = json.loads(req.content)
	# defines biggest losers and biggest winners across the entire stock market idea: do biggest gainers and losers by market cap and shares traded on the day
	# 8 categories: All, less than 100 mil, less than 50 mil, less than 25 mil, less than 10 mil, less than 5 mil, less than 1 mil, less than 500k
	# Do analysis across a week of the volumes??
	for x in data['results']:
		if "." not in x['T']:
			db.execute(
                "INSERT INTO marketStats (ticker, volume, change) VALUES (?, ?, ?)",
                (x['T'], x['v'], round(((x['c'] - x['o']) / x['o']) * 100, 2)),
            )
			db.commit()			
	return

@bp.route("/view")
def view():
	db = get_db()

	rows = db.execute("SELECT * FROM user").fetchall()

	return render_template("view.html", rows=rows)

# This function filters Stocks Overview based on user's desired shares traded limit to view the top gainers and losers of less traded stocks
@bp.route("/filter/<int:sharesTraded>")
def filter(sharesTraded):
	if sharesTraded == 8:
		session['userFilter'] = ""
	elif sharesTraded == 7:
		session['userFilter'] = "WHERE volume between 50000000 and 100000000"
	elif sharesTraded == 6:
		session['userFilter'] = "WHERE volume between 25000000 and 50000000"
	elif sharesTraded == 5:
		session['userFilter'] = "WHERE volume between 10000000 and 25000000"
	elif sharesTraded == 4:
		session['userFilter'] = "WHERE volume between 5000000 and 10000000"
	elif sharesTraded == 3:
		session['userFilter'] = "WHERE volume between 1000000 and 5000000"
	elif sharesTraded == 2:
		session['userFilter'] = "WHERE volume between 500000 and 1000000"
	elif sharesTraded == 1:
		session['userFilter'] = "WHERE volume between 100000 and 500000"
	elif sharesTraded == 0:
		session['userFilter'] = "WHERE volume between 0 and 100000"

	return redirect("/")

# This function takes in string from url (ex: /delete/AAPL,TSLA,NVDA) then splits that into a list and deletes the matching array indices in data (dataArr)
@bp.route("/delete/<string:tickers>")
def delete(tickers):
	tableHeight = session.get("tableHeight")
	newsHeight = session.get("newsHeight")
	tickersList = tickers.split(",")

	# Nested loop sorts through tickers submitted via tickersList and deletes them if they match previously stored data (dataArr)
	# Iterates backwards to avoid out of index errors when removing

	db = get_db()
	
	for y in tickersList:
		session['tableHeight'] = tableHeight - 75  
		session['newsHeight'] = newsHeight - 75   
		db.execute("DELETE FROM userStats WHERE ticker = ?", (y,))
		db.commit()

	userTickers = g.user['stocks'] # stores all users stocks from database then splits them into list below
	userTickers = userTickers.split(",")

	for i in range(len(userTickers) - 1, -1, -1):
		for j in range(len(tickersList)):
			if userTickers[i] == tickersList[j]:
				del userTickers[i]   
				break # break to avoid out of index error for the rest of j's after i is removed	

	dataString = ""
	for x in userTickers:
		if x == userTickers[0]:
			dataString = x
		else:
			dataString = dataString + "," + x

	if dataString == "":
		session['noStocksAfterCreation'] = True

	db = get_db()
	db.execute("UPDATE user SET stocks = ? WHERE id = ?", (dataString, g.user['id']))
	db.commit()  

	return redirect("/")

@bp.route("/research", methods=['GET', 'POST'])
def research():
	if request.method == 'POST':
		ticker = request.form.get('tckr')
		req = requests.get("https://api.polygon.io/vX/reference/financials?ticker=" + ticker + "&apiKey=XoIHGXzAz89flV3zUjNGpOEf9zJ0iidW")
		data = json.loads(req.content)
		db = get_db()
		db.execute("DELETE FROM researchStats")
		db.commit()
		researchData = data['results'][0]['financials']['balance_sheet']
		queryArray = ['current_assets']
		for x in queryArray:
			x = researchData[x]
			db.execute(
			    "INSERT INTO researchStats (label, value) VALUES (?, ?)",
			    (x['label'], x['value']),
			)
			db.commit()
		researchStats = db.execute("SELECT * FROM researchStats").fetchall()
		return render_template("research.html", researchStats=researchStats)

	return render_template("research.html")