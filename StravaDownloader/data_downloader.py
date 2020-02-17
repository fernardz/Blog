import requests
import json
import datetime

filename='creds.txt'
with open(filename, 'r') as f:
    datastore = json.load(f)

client_id='43801'
client_secret='51cfd621f26e736c47193e9b4cece0d0d216db37'
access_token=datastore['access_token']
expires_at=datastore['expires_at']
expires_in=datastore['expires_in']
refresh_token=datastore['refresh_token']

if expires_at>=datetime.datetime.utcnow().timestamp():
    print("We Good")
else:
    print("We not good")
    refresh_base_url="https://www.strava.com/api/v3/oauth/token"
    refresh_url=refresh_base_url+\
    '?client_id='+client_id+\
    '&client_secret='+client_secret+\
    '&grant_type=refresh_token'+\
    '&refresh_token='+refresh_token
    print(refresh_url)
    r=requests.post(refresh_url)
    print(r)
    print(r.text)
    try:
        d=r.json()
        print(d['access_token'])
        with open('creds.txt','w') as outfile:
            outfile.write(r.text)
    except:
        print("Reauth Needed")
