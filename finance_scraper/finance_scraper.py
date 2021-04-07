''' Other potential data sources:
https://www.alphavantage.co/
https://www.alphavantage.co/documentation/
https://iextrading.com/
'''

import pandas as pd
import datetime as dt

# Use BeautifulSoup for webscraping
from bs4 import BeautifulSoup
import requests
import bs4

# Build a list of valid keys the user puts in
keys = []

ticker_str = input("Please input the ticker name of the stock you would like the information of (enter '0' to end): ")
# Continue looping until the user types a `0`
while (not(ticker_str.isnumeric() and int(ticker_str) is 0)):

    # Check to see if the user-inputted ticker is valid
    ticker = requests.get('https://finance.yahoo.com/quote/{}?p={}'.format(ticker_str, ticker_str))

    # If it isn't, print an error message. Else, add it to `keys`
    if (ticker.find('No results for') is not -1):
        print('{} is not a valid ticker. Please try again.'.format(ticker_str))
    else:
        keys.append(ticker_str)
    ticker_str = input("Please input the ticker name of the stock you would like the information of (enter '0' to end): ")

# Open Yahoo's finance website with the first ticker (only using this to get the labels) and get the HTML
ticker = requests.get('https://finance.yahoo.com/quote/{}?p={}'.format(keys[0], keys[0]))
soup = bs4.BeautifulSoup(ticker.text, 'html.parser')
soup.prettify()

# Find the 16 summary labels on the page
columns = soup.find(id='quote-summary')
labels = [item for item in columns.find_all('td') if item not in columns.find_all('td', attrs={'class':"Ta(end) Fw(600) Lh(14px)"})]
labels = [x.text for x in labels]

# Create a dataframe with these labels
result = pd.DataFrame({'labels': labels})

# Create a ton of new rows that can have numerical values based on the data given
addedRows = pd.DataFrame(['Bid-Price'], index=result.columns).transpose()
addedRows = addedRows.append({'labels': 'Bid-Volume'}, ignore_index=True)
addedRows = addedRows.append({'labels': 'Ask-Price'}, ignore_index=True)
addedRows = addedRows.append({'labels': 'Ask-Volume'}, ignore_index=True)
addedRows = addedRows.append({'labels': 'Day\'s Range Low'}, ignore_index=True)
addedRows = addedRows.append({'labels': 'Day\'s Range High'}, ignore_index=True)
addedRows = addedRows.append({'labels': '52 Week Range Low'}, ignore_index=True)
addedRows = addedRows.append({'labels': '52 Week Range High'}, ignore_index=True)
addedRows = addedRows.append({'labels': 'Earnings Date Old'}, ignore_index=True)
addedRows = addedRows.append({'labels': 'Earnings Date New'}, ignore_index=True)
addedRows = addedRows.append({'labels': 'Forward Divided'}, ignore_index=True)
addedRows = addedRows.append({'labels': 'Forward Yield'}, ignore_index=True)
frames = [result, addedRows]
df = pd.concat(frames, ignore_index=True)

# Iterate through all user-entered tickers and add the corresponding values to the dataframe
for item in keys:

    # Open Yahoo's finance website at the ticker's page
    ticker = requests.get('https://finance.yahoo.com/quote/{}?p={}'.format(item, item))
    soup = bs4.BeautifulSoup(ticker.text, 'html.parser')
    soup.prettify()

    # Find the corresponding values
    columns = soup.find(id='quote-summary')
    values = columns.find_all('td', attrs={'class':"Ta(end) Fw(600) Lh(14px)"})
    values = [x.text for x in values]

    # Clean up the values by getting the string, parsing it, and adding it to values
    # Do this for bid (split into bid-price and bid-volume), ask (ask-price and ask-volume), day range (low and high),
    # 52 week range (low and high), earnings date (old and new), and forward dividend and yield (split it up).
    # This way, the values array matches the labels that we added
    bid_arr = values[2].split('x')
    values.append(float(bid_arr[0]))
    values.append(int(bid_arr[1]))

    ask_arr = values[3].split('x')
    values.append(float(ask_arr[0]))
    values.append(int(ask_arr[1]))

    day_range = values[4].split('-')
    values.append(float(day_range[0]))
    values.append(float(day_range[1]))

    year_range = values[5].split('-')
    values.append(float(year_range[0]))
    values.append(float(year_range[1]))

    earnings_date = values[12].split(' - ')
    values.append(dt.datetime.strptime(earnings_date[0], '%b %d, %Y'))
    values.append(dt.datetime.strptime(earnings_date[1], '%b %d, %Y'))

    forward_div = values[13].split(' ')
    values.append(float(forward_div[0]))
    for_div = forward_div[1]
    values.append(float(for_div[1:for_div.find('%')]))

    values[14] = dt.datetime.strptime(values[14], '%Y-%m-%d')

    # Change the market cap to the numerical value (currently has M, B, or T
    # representing millions, billions, and trillions, respectively)
    market_cap = values[8]
    if (market_cap.endswith('M')):
        values[8] = float(market_cap[:-1])*10**6
    if (market_cap.endswith('B')):
        values[8] = float(market_cap[:-1])*10**9
    if (market_cap.endswith('T')):
        values[8] = float(market_cap[:-1])*10**12

    # Add these values to the dataframe
    value_title = 'values-{}'.format(item.upper())
    df[value_title] = values

    # Convert to numeric values when possible (should be done for a lot of them because casting was done when parsing)
    # Affects the following labels: Previous Close, Open, Volume, Avg. Volume, Beta, PE Ratio, EPS, 1y Target Est
    df[value_title] = pd.to_numeric(df[value_title], errors='ignore')

# Remove the rows that had non-numeric values and reset the row indexing
df = df.drop([2, 3, 4, 5, 12, 13]).reset_index(drop=True)

# Now we have our df DataFrame!
print(df)
