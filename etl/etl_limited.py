'''
Sample ETL script to load data from twitter into s3
'''

import tweepy
import config #this is the filename where we store our secret keys and other config
import boto3 # for s3 access
from pprint import pprint #pretty printer
import json #use to format as json
import time #use to pause script
import logging #use to write a log file
from datetime import datetime,timedelta #use to get system time for logging / tracking
import traceback #for error logging

# had trouble getting the bearer_token.txt file to open
# bearer_token=open("bearer_token.txt").read()

# LOAD CONFIG
bearer_token = config.twitter_key
verbose = config.verbose # controls print output. Toggle on/ off for debugging
search_term = config.search_term
max_results_per_page = config.max_results
max_pages = config.max_pages
aws_access_key_id = config.aws_access_key_id
aws_secret_access_key = config.aws_secret_access_key
aws_bucket_name = config.aws_bucket_name
pause_for_rate_limiting = config.pause_for_rate_limiting
logging_on = config.logging_on
log_file_name = config.log_file_name
aws_bucket_path=config.path
tweepy_start_time=config.start_time
tweepy_end_time=config.end_time
tweepy_sort_order=config.sort_order
calls_per_file=config.calls_per_file
calls_per_day=config.calls_per_day

script_start_time = datetime.now()


# Set up logging to write to logfile.
# I want to at least make a record of the next_token in case it crashes.
# That way we can pick up where we left off.
# We could also spit out other things if we wanted to track stuff
# see: https://docs.python.org/3/library/logging.html#logging.basicConfig
if logging_on:
    logging.basicConfig(filename=log_file_name,
                                filemode='a',
                                format='%(asctime)s,%(msecs)d %(name)s %(levelname)s %(message)s',
                                datefmt='%H:%M:%S',
                                level=logging.WARNING)

# SET UP CONNECTIONS TO SERVICES
# Twitter
client=tweepy.Client(bearer_token)
tweet_fields=["id","author_id","conversation_id","lang",
              "created_at","context_annotations","text"]

# s3 / AWS
s3 = boto3.resource('s3',
                    aws_access_key_id=aws_access_key_id,
                    aws_secret_access_key=aws_secret_access_key)

# define function to write out data
def writeout(bucket_name, filename, data):
    print(f"writing to {bucket_name}{filename}")
    if verbose:
        pprint(data)
    s3_outfile = s3.Object(bucket_name, filename)
    s3_outfile.put(Body=json.dumps(data))
    return

def initialize_next_file(files_written):
    calls_pulled_per_file = 0
    tweets_pulled_per_file=0
    outtext =  [ dict() ] * calls_per_file*max_results_per_page
    outfilename = aws_bucket_path + "tweet_chunk_" + str(files_written).zfill(5)
    return (calls_pulled_per_file,tweets_pulled_per_file, outtext, outfilename)

try:
    with open("restart_limited_"+aws_bucket_path[0:-1]+".txt","r") as file:
        restart_datain=json.loads(file.read())
    tweepy_next_token_start=restart_datain['next_token']
    files_written=restart_datain['files_written']
    tweets_pulled=restart_datain['tweets_pulled']
    current_date=datetime.strptime(restart_datain['current_date'],"%m/%d/%y")
    calls_current_date=restart_datain['calls_current_date']
    
except FileNotFoundError:
    tweepy_next_token_start=None
    files_written=0
    tweets_pulled=0
    current_date=tweepy_end_time
    calls_current_date=0

# keep looping over api call until either the next page token 
# isn't returned, or the max page limit is reached
next_token = tweepy_next_token_start #Usually None
i = 1
calls_pulled_per_file, tweets_pulled_per_file, outtext, outfilename = initialize_next_file(files_written)
last_date=tweepy_end_time.strftime("%m/%d/%y")



# START LOOP TO PULL ALL TWEETS
while i <= max_pages and current_date>tweepy_start_time:

    # Non optional print statement. Nice to get some sort of status update if
    # it will be running for a long time
    if i % 10 == 0:
        print(f"Loading page {i} of results for {search_term}. "
            f"Script has been running for {datetime.now() - script_start_time} (H:MM:SS.XXX). "
            f"{tweets_pulled} tweets have been extracted and saved. "
            f"Most recent tweet is from {last_date}")
        print(f"Next writing data to file {outfilename}")
        print(f"*** {files_written} files have been written")
    if verbose: print(f"\n\nPULLING RESULTS FOR PAGE {i} of {max_pages}\n")

    # MAKE VERY TWEEPY API CALLS... (birdy say tweep tweep)
    # useful docs: https://docs.tweepy.org/en/stable/client.html#tweepy.Client
    query=search_term+" lang:en -is:retweet" #filters out non-english tweets and retweets
    retry = True
    while retry:
        try:
            response=client.search_all_tweets(query,
                                    max_results=max_results_per_page,
                                    tweet_fields=tweet_fields,
                                    next_token=next_token,start_time=current_date-timedelta(1),end_time=current_date,
                                    sort_order=tweepy_sort_order)
            retry=False
        except Exception as e:
            print("\n**** WARNING: Tweepy got sick and could not tweep this tweep...")
            print(query, tweet_fields, next_token)
            print(e)
            traceback.print_exc()
            time.sleep(20)


    response_meta = response.meta
    if verbose: pprint(response_meta)

    # If this is going to run over millions of tweets, we might want to start adding some
    # retry logic when one of these calls inevitably fails. For example, maybe there's a blip
    # in the internet connectivity. Or maybe we exceed the twitter rate limit and the response
    # just says "NO"... we would want to figure out what that "NO" looks like, maybe by exceeding
    # the rate limit.  


    # REVIEW AND SAVE RESULTS
    if verbose: pprint(response)
    if response_meta['result_count']==0:
        next_token=None
        
    else:
        for tweet in response.data:
            if verbose:
                print("\n--------------------------------------------------\n")
                print(type(tweet))
    
            outtext_tweet = dict()
            outtext_tweet["search_term"] = search_term # Add search term to output so we can categorize the data better
            for field in tweet_fields:
                if verbose: print(field, ": ", tweet[field])
    
                # I'm taking the data out of the tweepy data structure and 
                # making it into a dictionary, so I can easially convert this
                # into json.  If needed, we can change the output data format here
                outtext_tweet[field] = str(tweet[field])
    
            # Save each tweet as separate file where tweet_id is added to the file name.
            if verbose:
                print()
                pprint(outtext_tweet)
            outtext[tweets_pulled_per_file]=outtext_tweet
            tweets_pulled_per_file+=1
        
        
        
        # Get next token so we can pull the next batch of results
        # Check if next token in response
        # I'm not sure what the terminating condition is when it gets to 
        # the last possible page of results... I'm guessing there's
        # just no next_token, but we will have to see what happens.
        if 'next_token' in response_meta:
            next_token=response_meta['next_token']
            if logging_on: logging.info(f": {next_token}")
            if verbose: print(f"Next Token is: {next_token}")
        else:
            #end loop if no more pages
            next_token=None
            print("No next token")
    calls_pulled_per_file+=1
    calls_current_date+=1
    if calls_current_date>=calls_per_day or next_token==None:
        current_date=current_date-timedelta(1)
        calls_current_date=0
        next_token=None
    if calls_pulled_per_file >= calls_per_file:

        writeout(aws_bucket_name, outfilename, outtext[0:tweets_pulled_per_file])

        files_written += 1
        tweets_pulled+=tweets_pulled_per_file
        calls_pulled_per_file, tweets_pulled_per_file, outtext, outfilename = initialize_next_file(files_written)
                 
        
        last_date=tweet['created_at'].strftime("%m/%d/%y")
        
        with open("restart_limited_"+aws_bucket_path[0:-1]+".txt","w") as file:
            restart_dataout={'next_token':next_token,'files_written':files_written,
                             'tweets_pulled':tweets_pulled,'current_date':current_date.strftime('%m/%d/%y'),
                             'calls_current_date':calls_current_date}
            file.write(json.dumps(restart_dataout))
            
            

    # next iteration
    i += 1
    
    
    time.sleep(pause_for_rate_limiting)

if calls_pulled_per_file > 0: #in case tweets pefectly divides into files written
    writeout(aws_bucket_name, outfilename, outtext[0:tweets_pulled_per_file])
    files_written+=1
    
    last_date=tweet['created_at'].strftime("%m/%d/%y")
    
    with open("restart_limited_"+aws_bucket_path[0:-1]+".txt","w") as file:
        restart_dataout={'next_token':next_token,'files_written':files_written,
                         'tweets_pulled':tweets_pulled,'current_date':current_date.strftime('%m/%d/%y'),
                         'calls_current_date':calls_current_date}
        file.write(json.dumps(restart_dataout))
# END OF SCRIPT / PRINT SUMMARY
script_end_time = datetime.now()
print("\n***PROCESS COMPLETE")
print(f"Current system time is: {script_end_time}")
print(f"Script ran for {script_end_time - script_start_time} (H:MM:SS.XXX)")
print(f"{tweets_pulled} tweets were extracted and saved")
print(f"{i-1} pages were visited")
print(f"Most recent tweet is from {last_date}")
print(f"Next writing data to file {outfilename}")
print(f"*** {files_written} files have been written")
