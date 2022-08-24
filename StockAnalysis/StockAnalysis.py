from flask import Blueprint, Flask, render_template, request, url_for, redirect, session, flash, g
from polygon import RESTClient
from datetime import datetime, date, timedelta
from StockAnalysis.db import get_db
import requests, time, json, random, sys

bp = Blueprint("StockAnalysis", __name__)

# StockAnalysis, otherwise known as Stockie, is a stock analysis webapp that allows user to track stocks as well as research them.

@bp.route("/", methods=['GET', 'POST'])
def home():
    # initial data set-up for session
    if 'dataCreated' not in session:
        session['dataCreated'] = False
        session['userDataCreated'] = False
        session['tableHeight'] = 50
        session['newsHeight'] = 50
        session['userFilter'] = ""
        session['noStocksAfterCreation'] = True

    # determines the day and adjusts to be a weekday
    # polygon api doesn't allow data of the current day to be accessed for free (assuming it's a business day), so the day must be set back by one
    if datetime.today().weekday() - 1 < 0:
        today = date.today() - timedelta(days = 3)
    elif datetime.today().weekday() - 1 < 5:
        today = date.today() - timedelta(days = 1)
    else:
        today = date.today() - timedelta(days = datetime.today().weekday() - 4)

    currentYear = str(date.today().year)
    holidays = [currentYear + "-01-17", currentYear + "-02-21", currentYear + "-04-15", currentYear + "-05-30", currentYear + "-06-20", currentYear + "-07-04", currentYear + "-09-05", currentYear + "-11-24", currentYear + "-12-26"]
    
    # ensures the day isn't a holiday as the market wouldn't of been open
    if str(today) in holidays:
        today = today - timedelta(days = 1)

    if request.method == 'POST':
        session['noStocksAfterCreation'] = False
        duplicate = False
        stored = False
        ticker = request.form.get('tckr')
        db = get_db()
        if g.user['stocks'] is not None:
            tickers = g.user['stocks']
            tickersList = tickers.split(",")
            for x in tickersList:
                if x == ticker:
                    duplicate = True
                    break

        # checks to see if input is a duplicate stock. if not, then the stock is added
        if (duplicate == False):
            try:
                addStock(ticker, today, stored)
            except:
                flash("Oops!" + str(sys.exc_info()[0]) + "occurred.")
                flash("Please wait 5 minutes then refresh. The API calls are limited.")
        else:
            flash("You're already tracking " + ticker + ".", "info")

    # adds data previously stored in the user database
    if g.user != None and session['userDataCreated'] == False:
        if g.user['stocks'] != None and today != g.user['lastLogin']:
            session['noStocksAfterCreation'] = False
            session['userDataCreated'] = True

            tickers = g.user['stocks']
            tickersList = tickers.split(",")

            db = get_db()

            # clears out previous data to update
            db.execute("DELETE FROM userStats WHERE username = ?", (g.user['username'],))
            db.commit()

            stored = True

            # add all stocks retrieved from database
            for ticker in tickersList:
                try:
                    addStock(ticker, today, stored)
                except:
                    session['userDataCreated'] = False
                    session['noStocksAfterCreation'] = True
                    flash("Oops!" + str(sys.exc_info()[0]) + "occurred.")
                    flash("Please wait 5 minutes then refresh. The API calls are limited.")
                    break
        else:
            session['userDataCreated'] = True
            if g.user['stocks'] != None:
                session['noStocksAfterCreation'] = False
                session['tableHeight'] = g.user['stocks'].split(",").length * 75
                session['newsHeight'] = g.user['stocks'].split(",").length * 75

        # logs login date to avoid excessive data updates
        db = get_db()
        db.execute("UPDATE user SET lastLogin = ? WHERE id = ?", (today, g.user['id']))
        db.commit()

    # initial market data creation
    if session['dataCreated'] == False:
        try:
            db = get_db()
            # checks if market data has already been created
            dateUpdated = db.execute("SELECT dateUpdated FROM marketStats").fetchone()           
            if dateUpdated != today:
                dataCreate(today)

            session['dataCreated'] = True
        except:
            flash("Oops!" + str(sys.exc_info()[0]) + "occurred.")
            flash("Please wait 5 minutes then refresh. The API calls are limited.")

    # stores market data
    db = get_db()
    marketWinners = db.execute("SELECT * FROM marketStats " + session.get("userFilter") + " ORDER BY change DESC LIMIT 10").fetchall()
    marketLosers = db.execute("SELECT * FROM marketStats " + session.get("userFilter") + " ORDER BY change LIMIT 10").fetchall()
    marketPopular = db.execute("SELECT * FROM marketStats " + session.get("userFilter") + " ORDER BY volume DESC LIMIT 10").fetchall()

    # retrieves user data, if a user is logged in 
    if g.user != None:
        userStats = db.execute("SELECT * FROM userStats WHERE username = ?", (g.user['username'],)).fetchall()
    else:
        userStats = None

    return render_template("index.html", dataCreated=session.get("dataCreated"), userDataCreated=session.get("userDataCreated"), tableHeight=session.get("tableHeight"), newsHeight=session.get("newsHeight"), marketWinners=marketWinners, marketLosers=marketLosers, marketPopular=marketPopular, userStats=userStats, noStocksAfterCreation=session.get("noStocksAfterCreation"), today=today)

def setStockData(ticker):
    key = 'placeholder'
    req = requests.get("https://api.polygon.io/v1/meta/symbols/" + ticker + "/company?apiKey=" + key)
    data = json.loads(req.content)
    name = data['name']
    logo = data['logo']
    tickerID = random.randint(100000,1000000)
    buttonID = random.randint(100000,1000000)
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
    
    # cuts news date to just include the date
    for x in newsDate:
        if x == "T":
            newsDate = newsDate[:newsDate.index(x)]
            break

    newsURL = data['results'][4]['article_url']

    stockData = [name, ticker, logo, tickerID, buttonID, stockPrice, priceChange, volume, newsTitle, newsPublisher, newsDate, newsURL]

    return stockData

def addStock(ticker, today, stored):
    session['noStocksAfterCreation'] = False
    session['tableHeight'] = session.get("tableHeight") + 75
    session['newsHeight'] = session.get("newsHeight") + 75
    
    stockData = setStockData(ticker)

    db = get_db()
    db.execute(
        "INSERT INTO userStats (username, name, ticker, logo, tickerID, buttonID, stockPrice, priceChange, volume, newsTitle, newsPublisher, newsDate, newsURL) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)",
        (g.user['username'], stockData[0], stockData[1], stockData[2], stockData[3], stockData[4], stockData[5], stockData[6], stockData[7], stockData[8], stockData[9], stockData[10], stockData[11]),
    )

    # updates user's stocks in db, if not retrieving previously stored stocks
    if stored == False:
        db = get_db()
        if (g.user['stocks'] == None): # initial
            db.execute("UPDATE user SET stocks = ? WHERE id = ?", (ticker, g.user['id']))
        else: # update after initial creation
            db.execute("UPDATE user SET stocks = ? WHERE id = ?", (g.user['stocks'] + "," + ticker, g.user['id']))
    
    db.commit()

    return

def dataCreate(today):
    db = get_db()
    db.execute("DELETE FROM marketStats")
    db.execute("INSERT INTO marketStats (dateUpdated, change) VALUES (?, ?)", (today, 0))
    key = 'placeholder'
    req = requests.get("https://api.polygon.io/v2/aggs/grouped/locale/us/market/stocks/" + str(today) + "?adjusted=true&apiKey=" + key)
    data = json.loads(req.content)
    for x in data['results']:
        if len(x['T']) < 5: # excludes warrants/issues etc
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

# This function takes in string from url (ex: /delete/AAPL,TSLA,NVDA) then splits that into a list and deletes the matching array indices
@bp.route("/delete/<string:tickers>")
def delete(tickers):

    db = get_db()
    tickersList = tickers.split(",")

    # Nested loop sorts through tickers submitted via tickersList and deletes them from user data.
    # Iterates backwards to avoid out of index errors when removing.

    for y in tickersList:
        session['tableHeight'] = session['tableHeight'] - 75
        session['newsHeight'] = session['newsHeight'] - 75
        db.execute("DELETE FROM userStats WHERE ticker = ?", (y,))
        db.commit()

    userTickers = g.user['stocks']
    userTickers = userTickers.split(",")

    # removes deleted stock from user's stocks
    for i in range(len(userTickers) - 1, -1, -1):
        for j in range(len(tickersList)):
            if userTickers[i] == tickersList[j]:
                del userTickers[i]
                break
    
    # recreates user's stocks after stock has been removed
    stocksString = ""
    for x in userTickers:
        if x == userTickers[0]:
            stocksString = x
        else:
            stocksString = stocksString + "," + x

    if stocksString == "":
        session['noStocksAfterCreation'] = True
        stocksString = None

    db = get_db()
    db.execute("UPDATE user SET stocks = ? WHERE id = ?", (stocksString, g.user['id']))
    db.commit()

    return redirect("/")

# Iterates through financials of desired company to research and stores them 
@bp.route("/research", methods=['GET', 'POST'])
def research():
    if request.method == 'POST':
        ticker = request.form.get('tckr')
        researchArr = []
        try:
            req = requests.get("https://api.polygon.io/vX/reference/financials?ticker=" + ticker + "&apiKey=placeholder")
            data = json.loads(req.content)
            researchData = [[data['results'][0]['financials']['comprehensive_income'], "Comprehensive Income"], [data['results'][0]['financials']['income_statement'], "Income Statement"], [data['results'][0]['financials']['balance_sheet'], "Balance Sheet"], [data['results'][0]['financials']['cash_flow_statement'], "Cash Flow Statement"]]

            for x in researchData:
                # stores section title stored in second index. ex: "Comprehensive Income"
                section = x[1]
                
                # iterates through data stored in first index
                for y in x[0]:
                    researchArr.append([x[0][y]['label'], x[0][y]['value'], section])
                    section = ""
        except:
            flash("Oops!" + str(sys.exc_info()[0]) + "occurred.")
            flash("Please wait 5 minutes then refresh. The API calls are limited.")
        
        return render_template("research.html", researchArr=researchArr, ticker=ticker)

    return render_template("research.html")