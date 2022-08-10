# https://www.coingecko.com/en/api/documentation

from requests import Request, Session
from requests.exceptions import ConnectionError, Timeout, TooManyRedirects
from datetime import datetime
import json
import csv


class cryptoPrice:

    def coins(limit=None):
        url = 'https://api.coingecko.com/api/v3/coins/markets'
        parameters={'vs_currency':'USD'}
        headers = {
        'Accepts': 'application/json'
        }

        session = Session()
        session.headers.update(headers)

        try:
            response = session.get(url,params=parameters)
            data = json.loads(response.text)
            return data[0:limit]
        except (ConnectionError, Timeout, TooManyRedirects) as e:
            return e
    
    def historical(crypto, start, end):
        
        """
        Data granularity is automatic (cannot be adjusted)
        1 day from query time = 5 minute interval data
        1 - 90 days from query time = hourly data
        above 90 days from query time = daily data (00:00 UTC)
        """

        url = 'https://api.coingecko.com/api/v3/coins/' + crypto + '/market_chart/range'
        parameters = {
            'vs_currency':'USD',
            'from': start, #unix timestamp
            'to': end #unix timestamp
        }
        headers = {
        'Accepts': 'application/json'
        }

        session = Session()
        session.headers.update(headers)

        try:
            response = session.get(url, params=parameters)
            data = json.loads(response.text)
            return data
        except (ConnectionError, Timeout, TooManyRedirects) as e:
            return e

    def latest(crypto):
        url = 'https://api.coingecko.com/api/v3/simple/price'
        parameters = {
            'ids': crypto,
            'vs_currencies':'USD',
        }
        headers = {
            'Accepts': 'application/json'
        }

        session = Session()
        session.headers.update(headers)

        try:
            response = session.get(url, params=parameters)
            data = json.loads(response.text)
            return data
        except (ConnectionError, Timeout, TooManyRedirects) as e:
            return e

    def top_historical(start, end, amount):

        # Writing as csv files
        
        top_historical = cryptoPrice.coins()
        for x in range(amount):
            crypto_historical = cryptoPrice.historical(top_historical[x]['id'], start, end)
            with open('top_historical_data/'+top_historical[x]['id']+'.csv', 'w', encoding='UTF8', newline='') as f:
                writer = csv.writer(f)
                rows = []
                for current_row in range(len(crypto_historical['prices'])):
                    converted_string = str(crypto_historical['prices'][current_row][0])
                    top_ten_unix_digits = converted_string[0:10]
                    converted_date = datetime.utcfromtimestamp(int(top_ten_unix_digits)).strftime('%Y-%m-%d')
                    precision_price = format(float(crypto_historical['prices'][current_row][1]),".2f")
                    precision_market_cap = format(float(crypto_historical['market_caps'][current_row][1]),".2f")
                    precision_volume = format(float(crypto_historical['total_volumes'][current_row][1]),".2f")
                    rows.append([str(converted_date), str(precision_price), str(precision_market_cap), str(precision_volume)])
                writer.writerow(['Day', 'Price', 'Market Cap', 'Volume'])
                writer.writerows(rows)
        return

        # Writing as text files
        """
        top_historical = cryptoPrice.coins()
        for x in range(amount):
            crypto_historical = cryptoPrice.historical(top_historical[x]['id'], start, end)
            with open('top_historical_data/'+top_historical[x]['id']+'.txt', 'w') as f:
                for daily_price in crypto_historical['prices']:
                    converted_string = str(daily_price[0])
                    top_ten = converted_string[0:10]
                    converted_date = datetime.utcfromtimestamp(int(top_ten)).strftime('%Y-%m-%d')
                    precision_price = format(float(daily_price[1]),".2f")
                    f.write(f"{str(converted_date)}: {str(precision_price)}\n")
        return
        """

        # Opening and reading data from csv
        """
        with open("searches.csv", "r") as f:
            reader = csv.reader(f, delimiter="\t")
            for i, line in enumerate(reader):
                line = line[0].split(",")
                print(line[0])
                #print('line[{}] = {}'.format(i, line))
        print(datetime.utcfromtimestamp(1649539147).strftime('%Y-%m-%d %H:%M:%S'))
        """

#print(cryptoPrice.historical('bitcoin', '1630454367', '1646179167'))
cryptoPrice.top_historical('1630454367', '1646179167', 50)