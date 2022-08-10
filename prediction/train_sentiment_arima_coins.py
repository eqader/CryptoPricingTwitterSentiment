# Tuning and Model evaluation help from here
# https://machinelearningmastery.com/grid-search-arima-hyperparameters-with-python/

import os
import pandas as pd
# Need s3fs as well
import dotenv
from statsmodels.tsa.statespace.sarimax import SARIMAX
from sklearn.metrics import mean_squared_error
from math import sqrt
import warnings
from datetime import datetime
import matplotlib.pyplot as plt
import seaborn as sns

warnings.filterwarnings("ignore")
dotenv.load_dotenv('.env', override=True)

# IMPORTANT! - price and sentiment coin list must align indexes with the same coin!!!!
PRICE_COINS = ['avalanche-2', 
'binancecoin', 
'bitcoin', 
'cardano',  
'dogecoin',
'ethereum', 
'polkadot', 
'ripple', 
'solana',  
'terra-luna'] 

SENTIMENT_COINS = ['Avalanchefinal',
'BNBfinal',
'Bitcoinfinal',
'Cardanofinal',
'Dogefinal',
'Ethereumfinal',
'PolkaDotfinal',
'XRPfinal',
'Solanafinal',
'Terrafinal'] 

def load_price_data():

    AWS_S3_BUCKET = os.getenv("AWS_S3_BUCKET_PRICE")
    AWS_ACCESS_KEY_ID = os.getenv("AWS_ACCESS_KEY_ID")
    AWS_SECRET_ACCESS_KEY = os.getenv("AWS_SECRET_ACCESS_KEY")

    price_data = []

    for coin in PRICE_COINS:

        price_df = pd.read_csv(
            f"s3://{AWS_S3_BUCKET}/{coin}.csv",
            storage_options={
                "key": AWS_ACCESS_KEY_ID,
                "secret": AWS_SECRET_ACCESS_KEY
            },
        )

        price_df.index = pd.to_datetime(price_df['Day'], format='%Y-%m-%d')
        price_df.drop(columns=['Day'], inplace=True)
        price_df.drop(price_df.tail(1).index,inplace=True) 

        price_data.append(price_df)

    return price_data


def load_sentiment_data():

    AWS_S3_BUCKET = os.getenv("AWS_S3_BUCKET_SENTIMENT")
    AWS_ACCESS_KEY_ID = os.getenv("AWS_ACCESS_KEY_ID")
    AWS_SECRET_ACCESS_KEY = os.getenv("AWS_SECRET_ACCESS_KEY")

    sentiment_data = []

    for coin in SENTIMENT_COINS:
        if coin == '':
            sentiment_data.append(None)
            continue

        sentiment_df = pd.read_csv(
            f"s3://{AWS_S3_BUCKET}/{coin}.csv",
            storage_options={
                "key": AWS_ACCESS_KEY_ID,
                "secret": AWS_SECRET_ACCESS_KEY
            },
        )

        sentiment_df.index = pd.to_datetime(sentiment_df['date'], format='%Y-%m-%d')
        sentiment_df.drop(columns=['date'], inplace=True)
        # print(f'Coin: {coin}, last date:{sentiment_df.last_valid_index()}')
        sentiment_data.append(sentiment_df)

    return sentiment_data


def combine_data(price_data, sentiment_data):

    for coin_idx in range(len(price_data)):
        coin_price_df = price_data[coin_idx]
        coin_sentiment_df = sentiment_data[coin_idx]

        if coin_sentiment_df is not None:
            coin_price_df['Sentiment'] = coin_sentiment_df['sentiment']
        else:
            coin_price_df['Sentiment'] = 0.5

        coin_price_df.fillna(0, inplace=True)

    return price_data

# evaluate an ARIMA model for a given order (p,d,q)
def evaluate_arima_model(X, arima_order):
	# prepare training dataset
    train_size = int(len(X) * 0.66)

    train, test = X[0:train_size]['Price'], X[train_size:]['Price']
    sent_train, sent_test = X[0:train_size]['Sentiment'], X[train_size:]['Sentiment']
    history = [x for x in train]
    sent_history = [x for x in sent_train]

    sent_forcast = [x for x in sent_test]

    # make predictions
    predictions = list()
    for t in range(len(test)):
        model = SARIMAX(history, sent_history, order=arima_order)
        model_fit = model.fit(disp=0)
        yhat = model_fit.forecast(exog=sent_forcast[0])[0]
        predictions.append(yhat)
        history.append(test[t])

        sent_history.append(sent_forcast.pop(0))
    # calculate out of sample error
    rmse = sqrt(mean_squared_error(test, predictions))
    return rmse


def train_model(dataset, arima_order):
    model = SARIMAX(dataset['Price'], dataset['Sentiment'], order=arima_order)
    model_fit = model.fit(disp=0)

    return model_fit


def tune_models(price_data, p_values, d_values, q_values):
    cur_date = datetime.now().strftime("%Y_%m_%d-%I_%M_%S_%p")
    tune_results_df = pd.DataFrame(columns=['coin', 'best_params', 'best_score'])
    models = []


    for coin_idx in range(len(PRICE_COINS)):
        coin_name = PRICE_COINS[coin_idx]
        dataset = price_data[coin_idx][['Price','Sentiment']]
        best_score, best_cfg, best_model = float("inf"), None, None
        for p in p_values:
            for d in d_values:
                for q in q_values:
                    order = (p,d,q)
                    try:
                        rmse = evaluate_arima_model(dataset, order)
                        if rmse < best_score:
                            best_score, best_cfg = rmse, order
                            best_model = train_model(dataset, best_cfg)
                        print('ARIMA%s RMSE=%.3f' % (order,rmse))
                    except Exception as e:
                        print(f'Error in training: {e}')
                        continue
        print('Coin: %s Best ARIMA%s RMSE=%.3f' % (coin_name, best_cfg, best_score))
        models.append(best_model)
        tune_results_df = tune_results_df.append({  'coin' : coin_name, 
                                                    'best_params' : f'{best_cfg}', 
                                                    'best_score' : best_score}, ignore_index = True)
                                                    
        best_model.save(f'models/sentiment/{coin_name}.pkl')
        tune_results_df.to_csv(f'tuning/sentiment/tune_results_{cur_date}.csv')



def main():
    p_values = [0, 1, 2, 4, 5, 6]
    d_values = [0, 1, 2, 3, 4]
    q_values = [0, 1, 2]

    price_data = load_price_data()
    sentiment_data = load_sentiment_data()

    coin_data = combine_data(price_data, sentiment_data)

    tune_models(coin_data, p_values, d_values, q_values)


if __name__ == '__main__':
    main()