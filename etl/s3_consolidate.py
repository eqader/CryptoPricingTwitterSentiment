'''
This script will help solve a problem by consolidating our small files in s3 into larger files

'''

import config_consolidate as c #this is the filename where we store our secret keys and other config
import boto3 # for s3 access
from botocore.exceptions import ClientError
from pprint import pprint #pretty printer
import json #use to format as json
import time #use to pause script
import logging #use to write a log file
from datetime import datetime #use to get system time for logging / tracking

script_start_time = datetime.now()

# import config
verbose = c.verbose
if verbose: print("Initializing Script")
aws_access_key_id = c.aws_access_key_id
aws_secret_access_key = c.aws_secret_access_key

source_aws_bucket_name = c.source_aws_bucket_name
target_aws_bucket_name = c.target_aws_bucket_name

tweets_per_outfile = c.tweets_per_outfile

source_path = c.source_path
target_path = c.target_path


# Connect to s3
if verbose: print("Connecting to s3...")
s3 = boto3.resource('s3',
                    aws_access_key_id=aws_access_key_id,
                    aws_secret_access_key=aws_secret_access_key)

s3_input = s3.Bucket(source_aws_bucket_name)


# define function to write out data
def writeout(bucket_name, filename, data, files_written):
    if verbose:
        print(f"writing to {bucket_name}{filename}")
        pprint(data)
    s3_outfile = s3.Object(bucket_name, filename)
    s3_outfile.put(Body=json.dumps(data))
    print(f"*** {files_written+1} files have been written")
    return


# reset variables when we need to start writing the next file
def initialize_next_file(files_written):
    tweets_pulled_per_file = 0
    outdata =  [ dict() ] * tweets_per_outfile
    outfilename = target_path + "tweet_chunk_" + str(files_written).zfill(5)
    return (tweets_pulled_per_file, outdata, outfilename)


# initialize variables for loop
print("Starting scanning through items in bucket")
files_written = 0
total_tweets_processed = 0
tweets_pulled_per_file, outdata, outfilename = initialize_next_file(files_written)

for file in s3_input.objects.filter(Prefix=source_path):
    if tweets_pulled_per_file == 0:
        print(f"Collecting and writing data to file {outfilename}")

    if verbose: pprint(file)

    body = json.loads(file.get()['Body'].read())
    if verbose:
        pprint(body)
        print("\n" + "-"*30 + "\n")
    outdata[tweets_pulled_per_file] = body

    tweets_pulled_per_file += 1
    if verbose: print(f"\tTweets written for this file: {tweets_pulled_per_file}")
    total_tweets_processed += 1

    # This section only runs on the first iteration or when the tweets
    # per file limit has bee reached
    if tweets_pulled_per_file >= tweets_per_outfile:

        writeout(target_aws_bucket_name, outfilename, outdata, files_written)

        files_written += 1
        tweets_pulled_per_file, outdata, outfilename = initialize_next_file(files_written)


# One last write once loop finishes - have to write data even if last file isn't full
if tweets_pulled_per_file > 0: #in case tweets pefectly divides into files written
    writeout(target_aws_bucket_name, outfilename, outdata[0:tweets_pulled_per_file],
            files_written)
    files_written += 1

# END OF SCRIPT / PRINT SUMMARY
script_end_time = datetime.now()
print("\n*** FILE CONSOLIDATION PROCESS COMPLETE ***\n")
print(f"Current system time is: {script_end_time}")
print(f"Script ran for {script_end_time - script_start_time} (H:MM:SS.XXX)")
print(f"{files_written} files have been written")

print(f"{total_tweets_processed} tweets were processed")
print(f"input data from: s3://{source_aws_bucket_name}/{source_path}")
print(f"output data in: s3://{target_aws_bucket_name}/{target_path}")


