from flask import Flask, render_template, request, url_for, redirect
from polygon import RESTClient
import requests, time, json, random, copy

app = Flask(__name__)

'''
Request, Purpose
Get, The most common method. A GET Message is send, and the 
server returns data
Post, Used to send HTML form data to the server. The data received
by the Post method is not cached by the server.
Head, Same as GET method, but no response body.
Put, Replace all current representations of the target resource with
uploaded content.
Delete, Deletes all current representations of the target resource
given by the URL.
Here is the issue: Use flask/python specifically for the data handling. Only use javascript for client-side stuff.
loads() is used to convert the JSON String document into the Python dictionary.
'''

# Empty array for data storage
arr = []

# This function takes in ticker to be added from html form to relay relevant data to website
@app.route("/", methods=['GET', 'POST'])
def home():
	if request.method == 'POST':
		key = 'u8ubgf5HAZmgWl1xWOlpkbQ0asXYgAr3'
		ticker = request.form.get('tckr')
		req = requests.get("https://api.polygon.io/v2/aggs/ticker/" + ticker + "/range/1/day/2022-01-07/2022-01-07?adjusted=true&sort=asc&limit=120&apiKey=" + key)
		data = json.loads(req.content) #json.loads(s) takes a string, bytes, or byte array instance which contains the JSON document as a parameter(s).
		req = requests.get("https://api.polygon.io/v1/meta/symbols/" + ticker + "/company?apiKey=" + key)
		dataTwo = json.loads(req.content)
		data.update({'Name':dataTwo['name']})
		data.update({'logo':dataTwo['logo']})
		data.update({'Ticker ID': random.randint(100000,1000000)})
		data.update({'Button ID': random.randint(100000,1000000)})
		data.update({'Table Height': 50 + (len(arr) + 1) * 70}) # Updates table height dynamically after data is added for new stock

		for i in data:
			if i == "results":
				data.update({'Stock Price':data[i][0]['c']}) # data[i][0] = dictionary then add index (ex:['c'] or closing share price) to get specific key value
				data.update({'Price Change':round(((data[i][0]['o'] - data[i][0]['c']) / data[i][0]['o']) * -100, 2)}) # Opening share price - closing share price / opening share price * -100
				arr.append(data)
				break

	return render_template("index.html", arr=arr)

# This function takes in string from url (ex: /delete/AAPL,TSLA,NVDA) then splits that into a list and deletes the matching array indices in data (arr)
@app.route("/delete/<string:tickers>")
def delete(tickers):
	arrCopy = copy.copy(arr) # Copy of arr to reference as to avoid out of range issues when indices are deleted
	tickersList = tickers.split(",")
	# Nested loop sorts through tickers submitted via tickersList and deletes them if they match previously stored data (arr)
	for i in range(len(arrCopy)):
		for j in range(len(tickersList)):
			if arrCopy[i]['ticker'] == tickersList[j]:
				del(arr[i])

	return redirect("/")

@app.route("/markets")
def markets():
	return render_template("markets.html")

@app.route("/research")
def research():
	return render_template("research.html")

if __name__ == "__main__":
	app.run(debug=True)