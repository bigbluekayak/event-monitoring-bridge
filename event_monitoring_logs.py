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

host = os.environ['HOST']

def sf_token_header(token):
    return {'Authorization': 'Bearer ' + token}

def cor_token_header(api_key):

    return {
        'Authorization': api_key,
        'Content-Type': "application/json"
        }

def last_run():
    # TODO: get Redis connection from env variable
    r = redis.Redis(host='localhost', port=6379, db=0, decode_responses=True)
    x = r.get('last_run')
    if x:
        print(x)
        return x
    else:
        return datetime.datetime.now().strftime('%Y-%m-%dT%H:%M:%SZ')

def send_to_cor(log_entries):
    url = "https://ingress.coralogix.com/logs/v1/singles"

    api_key = os.environ['COR_API_KEY']

    header = cor_token_header(api_key)
    print(header)

    r = requests.post(url, headers=header, data=log_entries)
    if r.status_code == 200:
        print(r.text)
    else:
        print(f"Error: {r.status_code}, {r.text}")

def get_token(client_id, client_secret):
    # Use Client Credentials Flow to get a token.
    # Make sure to rotate secrets as needed.  https://help.salesforce.com/s/articleView?id=sf.connected_app_rotate_consumer_details.htm&language=en_US&type=5

    token_path = "/services/oauth2/token"

    url = host + token_path

    print(url)

    payload = {
        'grant_type': 'client_credentials',
        'client_id': client_id,
        'client_secret': client_secret
    }
   
    r = requests.post(url, data=payload)
    if r.status_code == 200:
        return r.json()['access_token']
    else:
        print(f"Error: {r.status_code}")
        return None
    
def get_logs(token):
    rx = redis.Redis(host='localhost', port=6379, db=0)

    logs_path = "/services/data/" + os.environ['API_VERSION'] + "/query/?q="
    
    # Get log files older than last run time
    query = "SELECT Id, EventType, Interval, LogDate, LogFile FROM EventLogFile WHERE Interval = 'Hourly' AND LogDate >= " + last_run()    
    print(query)
    url = host + logs_path + query
    print(url)
    r = requests.get(url, headers=sf_token_header(token))
    if r.status_code == 200:
        rx.set('last_run', datetime.datetime.now().strftime('%Y-%m-%dT%H:%M:%SZ'))
        return r.json()
    else:
        print(f"Error: {r.status_code}, {r.text}")
        return None
    
def merge_and_send(event_type, log_file):
    # Get Salesforce Event Logs into Coralogix log format and send

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
            #pandas_df['text'] = pandas_df['text'] + col + "=" + pandas_df[col] + '|'
            pandas_df.drop(col, axis = 1, inplace = True)

    # Send to Coralogix
    print("Sending to Coralogix...")
    send_to_cor(pandas_df.to_json(orient='records'))

def get_log(token, log):
    print(f"Retrieving {log['LogFile']}")

    url = host + log['LogFile']
    r = requests.get(url, headers=sf_token_header(token))

    if r.status_code == 200:
        merge_and_send(log['EventType'], r.text)
    else:
        print(f"Error: {r.status_code}")

if os.environ['CLIENT_ID'] and os.environ['CLIENT_SECRET']:
    print("Getting token...")
    token = get_token(os.environ['CLIENT_ID'], os.environ['CLIENT_SECRET'])

    if token:
        print("Getting logs...")
        logs = get_logs(token)
        
        if logs:
            length = len(logs['records'])
            print(f"Found {length} logs")
            
            for x in logs['records']:
                get_log(token, x)
                
else:
    print("Error: Missing environment variables")