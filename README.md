# Salesforce - Coralogix - Event Bridge
## Send Salesforce Event Monitoring Logs to Coralogix
Author Martin Eley

Email meley@salesforce.com

Created 20th May 2024

**THE SOFTWARE IS PROVIDED “AS IS”, WITHOUT WARRANTY OF ANY KIND, EXPRESS OR IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY, FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT.**

### Installation instructions
Follow these instructions to deploy the Salesforce - Coralogix Event Bridge to Heroku.

You will need the following Heroku credits

* 2 Dyno Units, these are used for two Standard-1x Dynos which run the bridge
* 1000 General Purpose Add-on Credits, these are used to provision:
    * Redis Premium-0 which is used to store the last run time and act as a work queue for the asynchronous job which retrieves and uploads the log files
    * Coralogix, Compact-cerebrum 25GB, which provides you with an observability platform where the logs are uploaded to, and 25GB daily log limit

#### Create connected app in Salesforce
You will need to create a Connected App in Salesforce in order to get the Client Id and Secret.  Follow [these instructions](https://help.salesforce.com/s/articleView?id=sf.connected_app_client_credentials_setup.htm&type=5) on how to set up a Connected App in Salesforce.

We recommend that you use the SCOPE TO GO HERE scope.

This application uses the Client Credentials Flow, details of which can be found [here](https://help.salesforce.com/s/articleView?id=sf.remoteaccess_oauth_client_credentials_flow.htm&type=5).

#### Install bridge on Heroku

Use the Client Id and Secret from the steps above to populate environment variables.  You will also need a Coralogix API key.

Follow [these instructions](https://coralogix.com/docs/send-your-data-api-key/) on how to generate a Coralogix API key.

Once you have your Salesforce Client Id, Secret and Coralogix API key you can deploy the bridge to Heroku using the button below.

[![Deploy](https://www.herokucdn.com/deploy/button.svg)](https://www.heroku.com/deploy?template=https://github.com/bigbluekayak/event-monitoring-bridge)

(c) copyright Salesforce 2024
