import smtplib

from email.mime.text import MIMEText
from ConfigParser import ConfigParser

Config = ConfigParser()
Config.read('config.dat')
recipient = Config.get('UserSettings', 'email')

def send(body):
  msg = MIMEText(body)

  me = 'from@example.com'

  msg['Subject'] = 'The contents of %s' % textfile
  msg['From'] = me
  msg['To'] = recipient

  # Send the message via our own SMTP server, but don't include the
  # envelope header.
  s = smtplib.SMTP('localhost')
  s.sendmail(me, [recipient], msg.as_string())
  s.quit()