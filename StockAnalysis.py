from flask import Flask, render_template, request, url_for, redirect
from polygon import RESTClient
from datetime import datetime, date, timedelta
import requests, time, json, random

app = Flask(__name__)

# Empty array for data storage
arr = []
changeArr = []
volumeArr = []
lengthVolume = 0
length = 0
today = 0
dataCreated = False

# This function takes in ticker to be added from html form to relay relevant data (appended to arr) to website
@app.route("/", methods=['GET', 'POST'])
def home():
	global today, dataCreated, lengthVolume, length
	if datetime.today().weekday() < 5:
		today = date.today()
	else:
		today = date.today() - timedelta(days = datetime.today().weekday() - 4)

	if request.method == 'POST':
		key = 'XoIHGXzAz89flV3zUjNGpOEf9zJ0iidW'
		ticker = request.form.get('tckr')
		req = requests.get("https://api.polygon.io/v2/aggs/ticker/" + ticker + "/range/1/day/" + str(today) + "/" + str(today) + "?adjusted=true&sort=asc&limit=120&apiKey=" + key)
		data = json.loads(req.content) #json.loads(s) takes a string, bytes, or byte array instance which contains the JSON document as a parameter(s).
		req = requests.get("https://api.polygon.io/v1/meta/symbols/" + ticker + "/company?apiKey=" + key)
		dataTwo = json.loads(req.content)
		data.update({'Name':dataTwo['name']})
		data.update({'logo':dataTwo['logo']})
		data.update({'Ticker ID': random.randint(100000,1000000)})
		data.update({'Button ID': random.randint(100000,1000000)})
		data.update({'Table Height': 50 + (len(arr) + 1) * 70}) # Updates table height dynamically after data is added for new stock
		req = requests.get("https://api.polygon.io/v2/aggs/ticker/" + ticker + "/prev?adjusted=true&apiKey=" + key)
		dataTwo = json.loads(req.content)
		data.update({'Stock Price':dataTwo['results'][0]['c']}) # data[i][0] = dictionary then add index (ex:['c'] or closing share price) to get specific key value
		data.update({'Price Change':round(((dataTwo['results'][0]['o'] - dataTwo['results'][0]['c']) / dataTwo['results'][0]['o']) * -100, 2)}) # Opening share price - closing share price / opening share price * -100
		req = requests.get("https://api.polygon.io/v2/reference/news?ticker=" + ticker + "&apiKey=" + key)
		dataTwo = json.loads(req.content)
		data.update({'News':dataTwo})
		arr.append(data)

	if dataCreated == False:
		key = '#'
		req = requests.get("https://api.polygon.io/v2/aggs/grouped/locale/us/market/stocks/" + str(today) + "?adjusted=true&apiKey=" + key)
		data = json.loads(req.content)
		length = 0
		# defines biggest losers and biggest winners across the entire stock market idea: do biggest gainers and losers by market cap and shares traded on the day

		for x in data['results']:
			if "." not in x['T']:
				change = [x['T'], round(((x['c'] - x['o']) / x['o']) * 100, 2)] # array with stock name then change in price
				changeArr.append(change)

		for x in data['results']:
			if "." not in x['T']:
				volume = [x['T'], x['v']] # array with stock name then volume
				volumeArr.append(volume)

		sort(changeArr)
		sort(volumeArr)
		length = len(changeArr) - 1
		lengthVolume = len(volumeArr) - 1
		dataCreated = True

	return render_template("index.html", arr=arr, changeArr=changeArr, volumeArr=volumeArr, length=length, lengthVolume=lengthVolume)

def sort(arr):
	i = 0 
	while i < len(arr):
		j = i + 1
		while j < len(arr):
			if arr[i][1] > arr[j][1]:
				x = arr[i]
				arr[i] = arr[j]
				arr[j] = x
			j = j + 1
		i = i + 1

	return 

# This function filters Stocks Overview based on user's desired shares traded limit to view the top gainers and losers of less traded stocks
@app.route("/filter/<string:sharesTraded>")
def filter(sharesTraded):

	return redirect("/")

# This function takes in string from url (ex: /delete/AAPL,TSLA,NVDA) then splits that into a list and deletes the matching array indices in data (arr)
@app.route("/delete/<string:tickers>")
def delete(tickers):
	global arr # globally declaring arr 
	tickersList = tickers.split(",")
	# Nested loop sorts through tickers submitted via tickersList and deletes them if they match previously stored data (arr)
	# Iterates backwards to avoid out of index errors when removing
	for i in range(len(arr) - 1, -1, -1):
		for j in range(len(tickersList)):
			if arr[i]['ticker'] == tickersList[j]:   
				del arr[i]     
				break # break to avoid out of index error for the rest of j's after i is removed

	# Updates table height parameter in the event that user removes a stock
	for x in arr:
		x['Table Height'] = 50 + len(arr) * 70

	return redirect("/")

@app.route("/markets")
def markets():
	return render_template("markets.html")

@app.route("/research")
def research():
	return render_template("research.html")

if __name__ == "__main__":
	app.run(debug=True)