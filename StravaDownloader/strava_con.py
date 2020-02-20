import requests
import json
import datetime

class Strava():
    def __init__(self):
        self.storage='creds.txt'
        try:
            with open(self.storage,'r') as f:
                datastore=json.load(f)
        except IOError:
            print("Credentials do not exist, need to creade creds.txt")
            exit()
        # Probably should be here, at least use keyring instead
        self._client_id='43801'
        self._client_secret='51cfd621f26e736c47193e9b4cece0d0d216db37'
        self.access_token=datastore['access_token']
        self.expires_at=datastore['expires_at']
        self.expires_in=datastore['expires_in']
        self.refresh_token=datastore['refresh_token']

        self.set_access_token()

    def set_access_token(self):
        if self.valid_token():
            self.access_token=self.access_token
        else:
            token_str=self.refresh()
            token_json=token_str
            self.store_creds(token_json)
            try:
                self.access_token=token_json['access_token']
                self.expires_in=token_json['expires_in']
            except:
                print("Could not set new token values")
                exit()

    def valid_token(self):
        if self.expires_at>=datetime.datetime.utcnow().timestamp():
            return True
        else:
            return False

    def refresh(self):
        refresh_base_url="https://www.strava.com/api/v3/oauth/token"
        refresh_url=refresh_base_url+\
        '?client_id='+self._client_id+\
        '&client_secret='+self._client_secret+\
        '&grant_type=refresh_token'+\
        '&refresh_token='+self.refresh_token
        r=requests.post(refresh_url)
        return r

    def store_creds(self,r):
        try:
            with open(self.storage,'w') as outfile:
                outfile.write(r.json())
        except:
            print("Issue with credentials")

    def get_activities(self, before='',after='',page=1,per_page=30):
        api_call_headers = {'Authorization': 'Bearer ' + self.access_token}
        activities_url="https://www.strava.com/api/v3/athlete/activities?"
        try:
            if self.valid_token():
                r=requests.get(activities_url, headers=api_call_headers, verify=False)
            else:
                self.refresh()
                r=requests.get(activities_url, headers=api_call_headers, verify=False)
            return r
        except:
            print('Something went wrong')
            return('API Problem')

if __name__=="__main__":
    strv=Strava()
    print(strv.access_token)
    print(strv.get_activities().json())