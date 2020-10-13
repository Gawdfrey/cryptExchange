from flask import Flask, render_template, request
from flask_table import Table, Col, create_table
import datetime
import requests
import json
from pycoingecko import CoinGeckoAPI
from time import time, sleep

coinGecko = CoinGeckoAPI()

#Dict to help convert abbreviated froms to full forms
nameToId = dict(BTC = "bitcoin", ETH="ethereum", LTC="litecoin", XRP="ripple",
           DAI="dai", MKR="maker", ZEC="zcash", ZRX="0x", BCH="bitcoin-cash",
           BAT="basic-attention-token", OMG="omisego")

app = Flask(__name__)

token = "token goes here"

url = "https://fintech-webinar-2020-api.vercel.app/api/accounts"

#Storing the wallets so i can access them later without requesting individually
wallets = requests.get(url, headers={'Authorization': f"Bearer {token}"}).json()

#Where the rows are going to be stored, in the correct order
rowsInTable = []

#Initializing the table
initTable = create_table('cryptoExchange')

#Filling the table with columns and correct names
for colName in wallets[0]:
    if colName == "balance":
        initTable \
        .add_column("amount", Col("Amount")) \
        .add_column("currency", Col("Currency")) \
        .add_column("usd", Col("In USD")) \
        .add_column("market_cap", Col("Market cap USD"))
    else:
        colName = str(colName)
        displayName = colName.replace('_', ' ').capitalize()
        initTable.add_column(colName, Col(displayName))

#Gets the value of the crypto in usd and the market cap in usd
def getVal(name):
    name = nameToId[name]
    return coinGecko.get_price(ids=name, vs_currencies="usd", include_market_cap="true")[name]

for i in wallets:
    values = getVal(i["balance"]["currency"])
    newDict = dict(id=i["id"],
        name=i["name"],
        amount=i["balance"]["amount"],
        currency=i["balance"]["currency"],
        usd=float(values["usd"]) * float(i["balance"]["amount"]),
        market_cap=values["usd_market_cap"],
        created_at=datetime.datetime.strptime(i["created_at"], '%Y-%m-%dT%H:%M:%SZ'),
        updated_at=datetime.datetime.strptime(i["updated_at"], '%Y-%m-%dT%H:%M:%SZ'),
        resource_path=i["resource_path"],
        allow_deposits=i["allow_deposits"],
        allow_withdrawals=i["allow_withdrawals"],
        active=i["active"])
    rowsInTable.append(newDict)

def getTotalVal(date):
    sum = 0
    #Date is converted to correct format
    historicDate = datetime.datetime.strptime(date, "%Y-%m-%d").strftime("%d-%m-%Y")
    for i in wallets:
        try:
            name = nameToId[i["balance"]["currency"]]
            sum += int(float(coinGecko.get_coin_history_by_id(name, historicDate)["market_data"]["current_price"]["usd"]) * float(i["balance"]["amount"]))
        except KeyError as e:
            print('I got a KeyError - reason "%s"' % str(e))
    return sum

#List is reversed so that the biggest number appears on the top of the table
def sortByUsd():
    return sorted(rowsInTable, key = lambda i: i['usd'], reverse=True)

def sortByMarketCap():
    return sorted(rowsInTable, key = lambda i: i['market_cap'], reverse=True)

## ROUTES ######################################################################

@app.route('/')
def home():
    return render_template('home.html', table=initTable(rowsInTable))

@app.route('/sorted-by-usd')
def usd():
    return render_template('home.html', table=initTable(sortByUsd()))

@app.route('/sorted-by-market-cap')
def market_cap():
    return render_template('home.html', table=initTable(sortByMarketCap()))

@app.route('/total', methods=['GET', 'POST'])
def total():
    val = ''
    date = 0
    #Gets yesterdays date to set as max date for datepicker
    todaysDate = datetime.date.today() - datetime.timedelta(days=1)
    if request.method == 'POST':
        val = getTotalVal(request.form['date'])
        date = request.form['date']
    return render_template('total.html', val=val, todaysDate=todaysDate, date=date)

if __name__ == "__main__":
    createTable()
    fillRows()
    app.run()
