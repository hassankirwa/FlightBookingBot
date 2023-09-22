import requests

# Replace with your Amadeus API credentials
client_id = 'ChvaxFiAytN1BWsA7AY3ltaWBB4V4ILG'
client_secret = 'yXuoFPhLLaby1RKY'

# Define the token endpoint
token_url = 'https://test.api.amadeus.com/v1/security/oauth2/token'

# Define the payload for the POST request
payload = {
    'grant_type': 'client_credentials',
    'client_id': client_id,
    'client_secret': client_secret
}

# Send the POST request to obtain the OAuth2 token
response = requests.post(token_url, data=payload)

# Check if the request was successful (HTTP status code 200)
if response.status_code == 200:
    # Parse the JSON response to extract the access token
    access_token = response.json()['access_token']
    print(f'Access Token: {access_token}')
else:
    print(f'Error: Unable to obtain access token. Status code: {response.status_code}')
