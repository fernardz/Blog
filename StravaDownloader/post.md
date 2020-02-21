# Building a Fitness Tracking Dashboard with Python. Pt 1 Strava and Fitbit API interface
I'm terrible at keeping in shape. I have found that in order for me to do well I have to have a pretty involved tracking program. In the past I have used excel and a bunch of colors, but frankly that's a little more that I want to do, plus I want a nicer display.

So first steps are going to be to get all my workout data (from Strava since Garmin Connect's API is a bit harder to pull from/ get authorized). Then I need to pull my weight and calorie information from the Fitbit API (because MyFitnessPal doesn't have an API that is open for personal information).

Then I will have to figure out how to store these in a database since I don't want to make a bunch of API calls and I kinda like having all my data on my own local storage.

Finally create a quick flask app and push it all into a docker container that I can run of a Raspberry Pi.

## Getting the data
### Strava API

Strava actually has fantastic API documentation and the process to obtain an account is very easy. Head out to Strava to get strated.

Strava uses Oauth2.0, there are quite a few libraries that make Oauth pretty easy. However I prefer to just create a class and use requests instead.

There is also a small gotcha. There standard access token that is listed on the API page does not have access to read activities, just basic user stats and profile. Because of that we will have to issue a new auth token with the right scope.

Im a bit lazy so Im not going to write anything to handle the initial authorization of the API for the right scope. Using Postman I can just issue the first set of credentials.

From the [Strava API getting started guide](http://developers.strava.com/docs/getting-started/) we can follow to obtain our first set of token credentials and authorize our app to access get the correct access.

The important part to be able to get the activities is to set scope to `activity:read_all`.

We will end up with a JSON of our Credentials
```json
{
  "token_type":"Bearer",
  "access_token":"ACCESSTOKEN",
  "expires_at":1581988494,
  "expires_in":12578,
  "refresh_token":"REFRESHTOKEN"}
```
Since this is a simple program, I'm not going to worry about how to store the credentials and just list save them to `creds.txt`.

We can now use that token to access the API and if necessary refresh our token for a new one.

We can make calls to the API endpoint from here with the `requests` python package.

```Python
import requests
api_header={'Authorization':'Bearer '+access_token}
api_endpoint="https://www.strava.com/api/v3/athelete/activities?"
r=request.get(api_endpoint, headers=api_header, verify=False)
```

Since we are going to be using this quite a bit, I created a class to handle the refresh and the call to get the activities.

```Python
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
        if r.status_code=200:
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

```
We make sure to check if the acess token is valid, create one method to get all activities. The endpoint does allow to select between dates but frankly I'm only intersted in the last 30 activities.

Now I need to get the second part of my fitness journey, how fat am I getting and how much did those extra beers I drank this weekend push me over my calorie goal. To do that I turn to the Fitbit Api.

### Fitbit API
Fitbit is also pretty good with their documentation regarding setting up an API and providing the correct authorizations.

First we will have to create our application and get our approvals at the [Dev Portal](https://dev.fitbit.com).

Now we can make it easier for ourselves by going over their [interactive oauth tutorial](https://dev.fitbit.com/apps/oauthinteractivetutorial) so we don't have to search for all the correct urls for the authorization. I choose to use the code authorization since this will be a server side application.

Using Postman I once again get the necessary credentials and store them in `creds_fitbit.txt`. Again normally you would store them somewhere substantially safer.

The class is almost the same as the one we made before for Strava. The main changes are that the token does not have a `expires at` data field. This could be set once we look at it initially.

We actually get that field making a call to the `https://api.fitbit.com/1.1/oauth2/introspect'` endpoint. So when we initialize the class we check against that. If the token is not valid it is set to 0 and we use `refresh` method to generate a new token.

The one thing that is also different is the method in which a refreshed token is generated needs to have a base64 encoded Basic Auth passed with the encoded value `client_id:client_secret`.

```Python
import requests
import json
import datetime
import keyring
import base64

class Fitbit():
    def __init__(self):
        self.storage='creds_fitbit.txt'
        try:
            with open(self.storage,'r') as f:
                datastore=json.load(f)
        except IOError:
            print("Credentials do not exist, need to creade creds.txt")
            exit()
        # Probably should be here, at least use keyring instead
        self._client_id=keyring.get_password('Fitbit','client_id')
        self._client_secret=keyring.get_password('Fitbit','client_secret')
        self.access_token=datastore['access_token']
        self.expires_in=datastore['expires_in']
        self.refresh_token=datastore['refresh_token']
        self.user_id=datastore['user_id']
        self.client_encoded=base64.b64encode((self._client_id+':'+self._client_secret).encode("utf-8")).decode("utf-8")
        self.validate_initial_token()
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

    def validate_initial_token(self):
        base_url='https://api.fitbit.com/1.1/oauth2/introspect'
        api_call_headers = {'Authorization': 'Bearer ' + self.access_token}
        data={'token':self.access_token}

        r=requests.post(base_url,headers=api_call_headers,data=data)
        if r.status_code==200:
            check=r.json()
            if check['active']:
                self.expires_at=check['exp']
            else:
                self.expires_at=0
        else:
            print('Bad stuff happening')

    def valid_token(self):
        if self.expires_at>=datetime.datetime.utcnow().timestamp():
            return True
        else:
            return False

    def refresh(self):
        print('Trying to Refresh Token')
        refresh_base_url="https://api.fitbit.com/oauth2/token"
        auth_header={"Authorization":"Basic "+self.client_encoded}
        data={'grant_type':'refresh_token','refresh_token':self.refresh_token, 'expires_in':28800}
        r=requests.post(refresh_url, headers=auth_header, data=data)
        if r.status_code==200:
            self.expires_in=r.json()['expires_in']
            self.expires_at=datetime.datetime.utcnow().timestamp+int(self.expires_in)
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

    def get_weight(self, date=datetime.datetime.now().strftime('%Y-%m-%d'),period='30d'):
        api_call_headers = {'Authorization': 'Bearer ' + self.access_token,
        'Accept-Language':'en_US'}
        base_url='https://api.fitbit.com/1/user/'+self.user_id
        endpoint='/body/log/weight/date/'+date+'/'+period+'.json'

        try:
            if self.valid_token():
                r=requests.get(base_url+endpoint, headers=api_call_headers)
            else:
                self.refresh()
                r=requests.get(base_url+endpoint, headers=api_call_headers)
            if r.status_code==200:
                return r
            else:
                print('Could not get Weight')
                return r
        except:
            print('Something went wrong')
            return 'API Problem'

    def get_calories(self, date=datetime.datetime.now().strftime('%Y-%m-%d'),period='30d'):
        api_call_headers = {'Authorization': 'Bearer ' + self.access_token,
        'Accept-Language':'en_US'}
        base_url='https://api.fitbit.com/1/user/'+self.user_id
        endpoint='/foods/log/caloriesIn/date/'+date+'/'+period+'.json'

        try:
            if self.valid_token():
                r=requests.get(base_url+endpoint, headers=api_call_headers)
            else:
                self.refresh()
                r=requests.get(base_url+endpoint, headers=api_call_headers)
            if r.status_code==200:
                return r
            else:
                print('Could not get Weight')
                return r
        except:
            print('Something went wrong')
            return 'API Problem'

if __name__=="__main__":
    fbit=Fitbit()
    print(fbit.access_token)
    print(json.dumps(fbit.get_weight().json(), indent=4, sort_keys=True))
    print(json.dumps(fbit.get_calories().json(), indent=4, sort_keys=True))
```

Obviously there is significantly better Oauth2 libaries out there for python, and frankly its probably a better idea to use those. But sometimes its worthwhile to go the long way around to make sure we understand everything that is happening in our program.

Now that we have ways to get our activities, weights and calories we need to create a pipeline to automate the information. We will do that in the next post.
