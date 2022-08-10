#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Wed Mar 23 15:28:47 2022

@author: philiptrettenero
"""
import re
import numpy as np
import random
import pandas as pd
#import pandasql as ps
import os
import nltk
import math
#https://stackoverflow.com/questions/41610543/corpora-stopwords-not-found-when-import-nltk-library
#nltk.download("stopwords")
import gensim
from gensim.models import Word2Vec
import time
from Help import (Tokenizer,
                       w2v_trainer,
                       calculate_overall_similarity_score,
                       overall_semantic_sentiment_analysis,
                       list_similarity,
                       calculate_topn_similarity_score,
                       topn_semantic_sentiment_analysis,
                       scale)

t0 = time.time()
#list to hold dates, tweets and coins for dataframe creation
dates = []
tweets = []
coin = []

#returns the names of the files in the directory data as a list
directory = os.listdir("Tweets/")
for folder in directory:
    list_of_files = os.listdir("Tweets/"+folder)
    for file in list_of_files:
        coin_name = []
        with open("Tweets/"+folder+"/"+file, "r") as fd:
            raw_input = fd.readline()
            term = "\d\d\d\d-\d\d-\d\d \d\d:\d\d:\d\d\+\d\d:\d\d"
            long_dates = re.findall(term, raw_input)
            term = '"text":.*?}'
            long_tweets = re.findall(term, raw_input)
        for i in range(len(long_dates)):
            long_dates[i] = long_dates[i].split(" ")
            long_tweets[i] = long_tweets[i].replace('"text":', "")
            long_tweets[i] = long_tweets[i].replace('\\n', "")
            long_tweets[i] = long_tweets[i].replace('}', "")
            long_tweets[i] = long_tweets[i].replace('"', "")
            long_tweets[i] = long_tweets[i].replace('\\u2019', "'")
            coin_name.append(folder)
        dates.extend([row[0] for row in long_dates])
        tweets.extend(long_tweets)
        coin.extend(coin_name)
    print(folder, "data loaded.")

#combine all data into dataframe
df = pd.DataFrame(data = tweets,index = None, columns = ["plain_text"])
df['date'] =  dates
df['coin'] =  coin
print("Dataframe has successfully been created.")
print()

#tokenize text for analysis
tokenizer = Tokenizer(clean= True, lower= True, de_noise= True, remove_stop_words= True, keep_negation=True)
df['tokenized_text'] = df['plain_text'].apply(tokenizer.tokenize)
print("Text has been tokenized and added to dataframe.")
print()

# remove Tweets with less than 5 tokenized words
def calc_new_col(row):
    return len(row['tokenized_text'])

df["token_len"] = df.apply(calc_new_col, axis=1)
df = df[df['token_len'] > 5]

#train vocabulary
keyed_vectors, keyed_vocab = w2v_trainer(df['tokenized_text'], vector_size = 300)
print("Vocabulary created.")
print()

# define word lists for each sentiment
positive_concepts = ['excellent', 'awesome', 'cool','up','amazing', 'strong', 'good', 'great', 'moon', 'bull',
                     'gain', 'high', 'rich', 'retire', 'decentralized', 'equitable', 'transparent', 'easy',
                     'love', 'tothemoon', 'u1f600', 'u1f911', 'u1f929', 'rocket', 'buy']
pos_concepts = [concept for concept in positive_concepts if concept in keyed_vocab]

negative_concepts = ['terrible','awful','horrible','fuck','bad', 'disappointing', 'weak', 'poor', 'senseless',
                     'confusing', 'bear', 'drop', 'crash', 'down', 'fall', 'lost', 'broke', 'volatile', 'risky',
                     'complicated', 'hate','shit', 'u1f62d', 'u1f625', 'u2639', 'u1f605', 'u2639', 'u1f61e', 'u1f631', 'ponzi']
neg_concepts = [concept for concept in negative_concepts if concept in keyed_vocab]

spam_concepts = ['reward','referral','claim', 'giveaway', 'join', 'community', 'tribe', 'follow']
s_concepts = [concept for concept in spam_concepts if concept in keyed_vocab]


# calculate sentiment scores with TopSSA model
topn_df_scores = topn_semantic_sentiment_analysis (keyed_vectors = keyed_vectors, positive_target_tokens = pos_concepts,
                                                   negative_target_tokens = neg_concepts, spam_target_tokens = s_concepts,
                                                   doc_tokens = df['tokenized_text'], topn=10)

#add sentiment outputs to dataframe.
df['spam_score'] = topn_df_scores[3]
df['sentiment_score'] = topn_df_scores[2]
print("Sentiment analysis completed.")
print()
#get rid of tokenized text to simplify dataframe
df.drop(['tokenized_text'], axis = 1, inplace = True)
df.drop(['token_len'], axis = 1, inplace = True)

#remove spam Tweets - removes spam Tweets with a spam score greater threshold
pre_spam_length = df.shape[0]
spam_df = df[df['spam_score'] > 0.15]
spam_accuracy = spam_df.sample(n=500)
spam_accuracy.to_csv("spam_accuracy.csv", encoding='utf-8', index=False)
print("Spam DF successfully written to file.")

#remove spam Tweets and sample Tweets for evaluation
df = df[df['spam_score'] <= 0.15]
post_spam_length = df.shape[0]
print(pre_spam_length - post_spam_length, "spam Tweets were removed.")
print("That's approximately ", round((1- post_spam_length/pre_spam_length)*100, 3), "percent.")
print()
sentiment_accuracy = df.sample(n=5000)
sentiment_accuracy.to_csv("sentiment_accuracy.csv", encoding='utf-8', index=False)
print("Sentiment DF successfully written to file.")

#functions to calculate sentiment quantiles
def percentile_low(x):
    return x.quantile(.33)
def percentile_high(x):
    return x.quantile(.66)

# average Tweets by date and coin
final = df.groupby(['coin', 'date'], as_index = False).agg({'sentiment_score': 'mean'})
final_range = df.groupby(['coin', 'date'], as_index = False).agg({'sentiment_score': [percentile_low, percentile_high]})
print("Final dataframe created.")
print("Identifying middle 1/3 sample Tweets.")
length = len(final)
phrase1 = []
phrase2 = []
phrase3 = []
phrase4 = []
phrase5 = []
for index, row in final_range.iterrows():
    try:
        selection = df.loc[(df['coin'] == row['coin'].iloc[0]) & (df['date'] == row['date'].iloc[0]) & (df['sentiment_score'] >= row['sentiment_score']['percentile_low']) & (df['sentiment_score'] <= row['sentiment_score']['percentile_high']) ].iloc[:5]
        #print(selection)
        val1 = selection['plain_text'].iloc[0]
        val2 = selection['plain_text'].iloc[1]
        val3 = selection['plain_text'].iloc[2]
        val4 = selection['plain_text'].iloc[3]
        val5 = selection['plain_text'].iloc[4]
    except:
        val1 = "Insufficient Tweet data."
        val2 = "Insufficient Tweet data."
        val3 = "Insufficient Tweet data."
        val4 = "Insufficient Tweet data."
        val5 = "Insufficient Tweet data."
    phrase1.append(val1)
    phrase2.append(val2)
    phrase3.append(val3)
    phrase4.append(val4)
    phrase5.append(val5)
# append value to a list to be added to final later
    if len(phrase1) % 5 == 0:
        print(round(len(phrase1)/length *100), "percent complete")

#scale final sentiment scores to -1 to 1 range, add to dataframe
srcRange = [min(final['sentiment_score']), max(final['sentiment_score'])]
dstRange = [-1,1]
final['sentiment'] = scale(final['sentiment_score'], srcRange, dstRange)
print("Scaling completed.")
print()

# add example Tweets and format columns for the front end
final['sample_tweet1'] = phrase1
final['sample_tweet2'] = phrase2
final['sample_tweet3'] = phrase3
final['sample_tweet4'] = phrase4
final['sample_tweet5'] = phrase5
final.drop('sentiment_score', axis = 1, inplace = True)
cols = ['date', 'sentiment','sample_tweet1','sample_tweet2','sample_tweet3','sample_tweet4','sample_tweet5', 'coin']
final = final[cols]

# file output to csv
for folder in directory:
    out = final[final['coin'] == folder]
    out.to_csv(folder+"final.csv", encoding='utf-8', index=False)
print("Output written to files.")

t1 = time.time()
print(t1-t0)
