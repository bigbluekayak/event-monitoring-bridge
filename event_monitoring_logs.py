'''
Author: Martin Eley
Email: meley@salesforce.com
Created: 20th May 2024

Required environment variables:
- HOST
- CLIENT_ID
- CLIENT_SECRET
- API_VERSION
- COR_API_KEY

TODO: License to go here

© Copyright Salesforce
'''
import requests
import os
import csv
import pandas
import io
import redis
import datetime
import celery
from urllib.parse import urlparse
import logging
from sf_utils import get_token

logger = logging.getLogger(__name__)

app = celery.Celery('event-monitoring-bridge', broker=os.environ['REDIS_URL'])

host = os.environ['HOST']

def sf_token_header(token):
    return {'Authorization': 'Bearer ' + token}

def cor_token_header(api_key):

    return {
        'Authorization': f'Bearer {api_key}',
        'Content-Type': "application/json"
    }

def last_run():
    rx = get_redis()

    x = rx.get('last_run')
    if x:
        return x
    else:
        return datetime.datetime.now().strftime('%Y-%m-%dT%H:%M:%SZ')

def send_to_cor(log_entries):
    url = "https://ingress.coralogix.com/logs/v1/singles"

    api_key = os.environ['COR_API_KEY']

    header = cor_token_header(api_key)

    r = requests.post(url, headers=header, data=log_entries)
    if r.status_code == 200:
        logs_sent = len(log_entries)
        logger.info(f"successfully sent {logs_sent} to Coralogix")
    else:
        logger.error(f"Error: {r.status_code}, {r.text}")
         
def get_redis():
    url = urlparse(os.environ.get("REDIS_URL"))
    if 'PYTHONDEVMODE' in os.environ: # Development, set SSL to false
        return redis.Redis(host=url.hostname, port=url.port, password=url.password, ssl=False, ssl_cert_reqs=None, decode_responses=True)
    else: # Production, set SSL to true
        return redis.Redis(host=url.hostname, port=url.port, password=url.password, ssl=True, ssl_cert_reqs=None, decode_responses=True)

def get_logs(token):    
    logs_path = "/services/data/" + os.environ['API_VERSION'] + "/query/?q="
    
    # Get log files older than last run time
    query = "SELECT Id, EventType, Interval, LogDate, LogFile FROM EventLogFile WHERE Interval = 'Hourly' AND LogDate >= " + last_run()    

    url = host + logs_path + query


    r = requests.get(url, headers=sf_token_header(token))

    if r.status_code == 200:
        logs = r.json()

        length = len(logs['records'])
        logger.info(f"Found {length} logs")
    
        for log in logs['records']:
            get_log(token, log)
            # merge_and_send(log['EventType'], log) # CHANGED HERE
        
        rx = get_redis()
        rx.set('last_run', datetime.datetime.now().strftime('%Y-%m-%dT%H:%M:%SZ'))
    else:
        logger.error(f"Error: {r.status_code}, {r.text}")
        return None
    
def merge_and_send(event_type, log_file):
    # Get Salesforce Event Logs into Coralogix log format and send

    logger.info(f"Processing {log_file}")

    f = io.StringIO(log_file)
    reader = csv.reader(f)
    pandas_df = pandas.DataFrame(reader)

    # Set headers
    column_headers = pandas_df.iloc[0].values
    pandas_df.columns = column_headers
    pandas_df.drop(pandas_df.index[0], inplace = True)

    # Set Application and Subsystem and rename Timestamp_Derived to Timestamp
    pandas_df['applicationName'] = 'Salesforce'
    pandas_df['subsystemName'] = event_type

    # Set TIMESTAMP_DERIVED to datetime
    # calculate unix epoch
    pandas_df['TIMESTAMP_DERIVED'] = pandas.to_datetime(pandas_df['TIMESTAMP_DERIVED'], format='%Y-%m-%dT%H:%M:%S.%fZ')
    pandas_df['TIMESTAMP_DERIVED'] = (pandas_df['TIMESTAMP_DERIVED'] - pandas.Timestamp("1970-01-01")) // pandas.Timedelta("1ms")
    
    pandas_df.rename(columns = {'TIMESTAMP_DERIVED':'timestamp'}, inplace = True)

    # DROP TIMESTAMP column
    del pandas_df['TIMESTAMP']
    
    # Update columns to get ready for Coralogix
    # Add text columns
    if 'text' not in pandas_df.columns:
        pandas_df['text'] = ''

    pandas_df['text'] = pandas_df.apply(lambda x: x.to_json(), axis=1)

    # Remove columns that are not needed
    for col in pandas_df.columns:
        if col == 'timestamp' or col == 'applicationName' or col == 'subsystemName' or col == 'text':
            continue
        else:
            pandas_df.drop(col, axis = 1, inplace = True)

    # Send to Coralogix
    logger.info("Sending to Coralogix...")
    send_to_cor(pandas_df.to_json(orient='records'))

def get_log(token, log):
    logger.info(f"Retrieving {log['LogFile']}")

    url = host + log['LogFile']
    r = requests.get(url, headers=sf_token_header(token))

    if r.status_code == 200:
        merge_and_send(log['EventType'], r.text)
    else:
        logger.error(f"Error: {r.status_code}, {r.text}")

@app.task
def process():
    if os.environ['CLIENT_ID'] and os.environ['CLIENT_SECRET'] and os.environ['HOST'] and os.environ['API_VERSION'] and os.environ['COR_API_KEY'] and os.environ['REDIS_URL']:
        logger.info("Getting Salesforce token...")
        token = get_token(os.environ['HOST'], os.environ['CLIENT_ID'], os.environ['CLIENT_SECRET'])

        if token:
            logger.info("Getting logs...")
            get_logs(token)
    else:
        raise RuntimeError("Set up environment variables before running.")

    print('Done')  