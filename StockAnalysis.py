from flask import Flask, render_template, request, url_for
from polygon import RESTClient
import requests
import time
import json
import random


app = Flask(__name__)

# Problem is: Data is undefined unless method posts so need to fill it with something to satisfy requirement
# TextArea tag defines a multi-line text input control. The textarea element is often used in a form to collect user inputs like comments or reviews.
'''Request, Purpose
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
loads() is used to convert the JSON String document into the Python dictionary.'''

# Empty array for data storage
arr = []

# This function takes in data from html form to relay ticker data to website
@app.route("/", methods=['GET', 'POST'])
def home():
	if request.method == "POST":
		key = '#'
		ticker = request.form.get('tckr')
		req = requests.get("https://api.polygon.io/v2/aggs/ticker/" + ticker + "/range/1/day/2021-12-30/2021-12-30?adjusted=true&sort=asc&limit=120&apiKey=" + key)
		data = json.loads(req.content) #json.loads(s) takes a string, bytes, or byte array instance which contains the JSON document as a parameter(s).
		for i in data:
			if i == "results":
				data.update({'Stock Price':data[i][0]['c']}) # data[i][0] = dictionary then add ['c'] to get specific key value
				data.update({'Price Change':round(((data[i][0]['o'] - data[i][0]['c']) / data[i][0]['o']) * -100, 2)})
				data.update({'Ticker ID': random.randint(100000,1000000)})
				data.update({'Button ID': random.randint(100000,1000000)})
				arr.append(data)
				break
				
		return render_template("index.html", arr=arr)
	else:
		return render_template("index.html")

# Function to remove tickers from data as user requests
@app.route("/delete", methods=['POST', 'GET'])
def delete():
	if request.method == 'POST':
		data = request.form.get('data')
		arr.remove(data)

@app.route("/markets")
def markets():
	return render_template("markets.html")

@app.route("/research")
def research():
	return render_template("research.html")

if __name__ == "__main__":
	app.run(debug=True)