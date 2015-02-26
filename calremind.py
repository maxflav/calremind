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

FLOW = OAuth2WebServerFlow(
    client_id=Config.get('DeveloperKeys', 'clientID'),
    client_secret=Config.get('DeveloperKeys', 'clientSecret'),
    scope='https://www.googleapis.com/auth/calendar.readonly',
    user_agent='calremind/v1')

FLAGS.auth_local_webserver = False

storage = Storage('calendar.dat')
credentials = storage.get()
if credentials is None or credentials.invalid == True:
  credentials = run(FLOW, storage)

http = httplib2.Http()
http = credentials.authorize(http)

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
