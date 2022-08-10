'''
Add all variables needed to configure the ETL script here and name this file config.py
'''
from datetime import datetime

# secret config - DO NOT PUSH TO REPO OR SHARE


# non secret config
verbose = True             # Controls whether print statements get executed
search_term = 'bitcoin'     # What term you're searching tweets for
max_results = 10             # how many results are returned per api call... we might want to bump this to the max of 100
max_pages = 10                # how many times should we repeat making the api call to get the next batch of results
aws_bucket_name = "cse6242-firemonkeys156-random-junk"   # what aws bucket we are saving the data in
pause_for_rate_limiting = 2.5  # how long to wait between api calls, in seconds
logging_on = True            # if true, then we will save a logfile with logging output from the script
log_file_name = "logfile.txt"    # name of the logfile to write on your local system, only runs if logging_on is also true

path="bitcoin_limited/"                   #Empty string if saving in the general bucket
end_time=datetime(2022,2,20)    #Pull tweets before a certain date. Keep this constant until we run out of tweets
start_time=datetime(2022,2,15)                 #datetime object. Pull tweets after a certain date. None if no restrictions
sort_order="recency"

calls_per_file=3
calls_per_day=2 #only used with etl_limited
