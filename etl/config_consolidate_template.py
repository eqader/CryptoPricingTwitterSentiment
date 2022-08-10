'''
Add all variables needed to configure the ETL script here and name this file config_consolidated.py
'''
from datetime import datetime

# secret config - DO NOT PUSH TO REPO OR SHARE
aws_access_key_id = "<your aws access key>"
aws_secret_access_key = "<your aws secret key>"

# non secret config
verbose = False               # Controls whether print statements get executed
source_aws_bucket_name = "cse6242-firemonkeys156-random-junk"   # what aws bucket we are saving the data in
source_path = "test1sv-ether/" #be sure to add / at the end of this string
target_aws_bucket_name = "cse6242-firemonkeys156-random-junk" 
target_path = "test1sv-ether-consolidated/" #be sure to add / at the end of this string

# Currently logging isn't enabled so these don't do anything
logging_on = True            # if true, then we will save a logfile with logging output from the script
log_file_name = "logfile.txt"    # name of the logfile to write on your local system, only runs if logging_on is also true

tweets_per_outfile = 10
