import requests
import json
import datetime
import keyring

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
        self._client_id=keyring.get_password('Strava','client_id')#'43801'
        self._client_secret=keyring.get_password('Strava','client_secret')#51cfd621f26e736c47193e9b4cece0d0d216db37'
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
            token_json=token_str.json()
            print('NEW CREDS',token_json)
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
        print('Trying to Refresh Token')
        refresh_base_url="https://www.strava.com/api/v3/oauth/token"
        refresh_url=refresh_base_url+\
        '?client_id='+self._client_id+\
        '&client_secret='+self._client_secret+\
        '&grant_type=refresh_token'+\
        '&refresh_token='+self.refresh_token
        r=requests.post(refresh_url)
        if r.status_code==200:
            return r
        else:
            print('Could not refresh token')
            exit()

    def store_creds(self,r):
        print('JSON',r)
        if len(r) > 0:
            try:
                with open(self.storage,'w') as outfile:
                    json.dump(r,outfile)
            except:
                print("Issue with credentials")
        else:
            print("No Response")

    def get_activities(self, before='',after='',page=1,per_page=30):
        api_call_headers = {'Authorization': 'Bearer ' + self.access_token}
        activities_url="https://www.strava.com/api/v3/athlete/activities?"
        try:
            if self.valid_token():
                r=requests.get(activities_url, headers=api_call_headers, verify=False)
            else:
                self.refresh()
                r=requests.get(activities_url, headers=api_call_headers, verify=False)
            if r.status_code==200:
                return r
            else:
                print('Could not get Weight')
                return r
            return r
        except:
            print('Something went wrong')
            return('API Problem')

if __name__=="__main__":
    strv=Strava()
    print(strv.access_token)
    print(json.dumps(strv.get_activities().json(), indent=4, sort_keys=True))
