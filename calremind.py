import gflags, httplib2, pytz

from ConfigParser import ConfigParser
from datetime import datetime
from calendar import timegm

from apiclient.discovery import build
from oauth2client.file import Storage
from oauth2client.client import OAuth2WebServerFlow
from oauth2client.tools import run

FLAGS = gflags.FLAGS

Config = ConfigParser()
Config.read('config.dat')

# Set up a Flow object to be used if we need to authenticate. This
# sample uses OAuth 2.0, and we set up the OAuth2WebServerFlow with
# the information it needs to authenticate. Note that it is called
# the Web Server Flow, but it can also handle the flow for native
# applications
# The client_id and client_secret can be found in Google Developers Console
FLOW = OAuth2WebServerFlow(
    client_id=Config.get('DeveloperKeys', 'clientID'),
    client_secret=Config.get('DeveloperKeys', 'clientSecret'),
    scope='https://www.googleapis.com/auth/calendar.readonly',
    user_agent='calremind/v1')

# To disable the local server feature, uncomment the following line:
FLAGS.auth_local_webserver = False

# If the Credentials don't exist or are invalid, run through the native client
# flow. The Storage object will ensure that if successful the good
# Credentials will get written back to a file.
storage = Storage('calendar.dat')
credentials = storage.get()
if credentials is None or credentials.invalid == True:
  credentials = run(FLOW, storage)

# Create an httplib2.Http object to handle our HTTP requests and authorize it
# with our good Credentials.
http = httplib2.Http()
http = credentials.authorize(http)

# Build a service object for interacting with the API. Visit
# the Google Developers Console
# to get a developerKey for your own application.
service = build(serviceName='calendar', version='v3', http=http,
       developerKey=Config.get('DeveloperKeys', 'developerKey'))

calendar = service.calendars().get(calendarId='primary').execute()

today = datetime.today()
time_zone = pytz.timezone(calendar['timeZone'])
start_time = datetime(year=today.year, month=today.month, day=today.day + 1, tzinfo=time_zone).isoformat()
end_time   = datetime(year=today.year, month=today.month, day=today.day + 2, tzinfo=time_zone).isoformat()

page_token = None
while True:
  events = service.events().list(
    calendarId='primary',
    timeMin=start_time,
    timeMax=end_time,
    singleEvents=True,
    pageToken=page_token,
  ).execute()
  for event in events['items']:
    print event['summary']
  page_token = events.get('nextPageToken')
  if not page_token:
    break
