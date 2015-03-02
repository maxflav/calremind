import gflags, httplib2, pytz, dateutil.parser, sys, string

from ConfigParser import ConfigParser
from datetime import datetime
from calendar import timegm

from apiclient.discovery import build
from oauth2client.file import Storage
from oauth2client.client import OAuth2WebServerFlow
from oauth2client.tools import run

from twilio.rest import TwilioRestClient

FLAGS = gflags.FLAGS

Config = ConfigParser()
Config.read('config.dat')

FLOW = OAuth2WebServerFlow(
    client_id=Config.get('GoogleKeys', 'clientID'),
    client_secret=Config.get('GoogleKeys', 'clientSecret'),
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
       developerKey=Config.get('GoogleKeys', 'developerKey'))

# Pull the time zone from the calendar
calendar = service.calendars().get(calendarId='primary').execute()
time_zone = pytz.timezone(calendar['timeZone'])

# Collect all events between next midnight and the midnight after that
# This will only get events that lie completely within this range, e.g. multi-day events will not work
today = datetime.today()
start_time = datetime(year=today.year, month=today.month, day=today.day + 1, tzinfo=time_zone).isoformat()
end_time   = datetime(year=today.year, month=today.month, day=today.day + 2, tzinfo=time_zone).isoformat()

# Events before this time should be alerted
before_hour   = Config.getint('UserSettings', 'beforeHour')
before_minute = Config.getint('UserSettings', 'beforeMinute')
before_time   = datetime(year=today.year, month=today.month, day=today.day + 1, hour=before_hour, minute=before_minute, tzinfo=time_zone)

reminders = []
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
    if 'summary' not in event:
      continue
    if event['status'] != 'confirmed':
      continue
    event_start = dateutil.parser.parse(event['start']['dateTime'])
    if event_start >= before_time:
      continue
    reminders.append('%s: %s' % (event_start.strftime('%I:%M %p'), event['summary']))
    # print event_start.strftime('%I:%M %p'), event['summary']
  page_token = events.get('nextPageToken')
  if not page_token:
    break

message_to_send = "You have %s early meetings tomorrow.\n%s" % (len(reminders), string.join(reminders, "\n"))

twilioClient = TwilioRestClient(
  Config.get('TwilioKeys', 'accountSid'),
  Config.get('TwilioKeys', 'authToken')
)

message = twilioClient.messages.create(
  body=message_to_send,
  to=Config.get('UserSettings', 'phone'),
  from_=Config.get('TwilioKeys', 'number')
)
print message.sid
