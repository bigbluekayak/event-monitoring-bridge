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
import logging

logger = logging.getLogger(__name__)

def get_token(host, client_id, client_secret):
    """
    The function `get_token` uses the Client Credentials Flow to retrieve an access token from a
    specified host using the provided client ID and client secret.
    
    :param host: The `host` parameter in the `get_token` function represents the base URL of the
    Salesforce instance where you want to obtain the access token. It typically looks like
    `https://login.salesforce.com` for production environments or `https://test.salesforce.com` for
    sandbox environments
    :param client_id: The `client_id` parameter typically refers to the unique identifier assigned to
    your application when you register it with the authorization server (in this case, Salesforce). It
    is used to identify your application when making requests for authentication and authorization
    :param client_secret: The `client_secret` parameter in the `get_token` function is a confidential
    value that is used in conjunction with the `client_id` to authenticate the client application when
    requesting an access token using the Client Credentials Flow. It serves as a way to verify the
    identity of the client application to the authorization
    :return: The function `get_token` returns the access token if the request is successful (status code
    200). If there is an error (status code other than 200), it returns `None`.
    """  
    token_path = "/services/oauth2/token"

    url = host + token_path

    payload = {
        'grant_type': 'client_credentials',
        'client_id': client_id,
        'client_secret': client_secret
    }
   
    r = requests.post(url, data=payload)
    if r.status_code == 200:
        logger.info("Successfully retrieved token")
        return r.json()['access_token']
    else:
        logger.error(f"Error: {r.status_code}")
        return None