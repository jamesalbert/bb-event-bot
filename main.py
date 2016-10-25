from configparser import ConfigParser
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.keys import Keys
from datetime import datetime, timedelta
from pytz import timezone
from os import environ

conf = ConfigParser()
conf.read('config.ini')
username = environ['BB_USERNAME']
password = environ['BB_PASSWORD']
now = datetime.now(timezone(conf['time']['timezone']))
schedule = list()
alerts = list()

def find_next_day(event):
    for i in range(1, 8):
        future = now + timedelta(days=i)
        future_day = future.strftime('%A')
        if future_day == event['day']:
            return future.replace(hour=event['hour'], minute=event['minute'])
    return None

def parse_event(event):
    day, time, name = event.split(' - ')
    period = 'am' if 'am' in time else 'pm'
    time, _ = time.split(period)
    hour, minute = map(int, time.split(':') if ':' in time else [time, '0'])
    if period == 'pm':
        hour += 12 % 24
    time = '{0} {1}:{2}{3} PST'.format(day, hour % 12, minute or '00', period)
    return {
        'day': day,
        'time': time,
        'hour': hour,
        'minute': minute,
        'period': period,
        'name': name
    }

def get_countdown(date):
    diff = date - now
    days = diff.days
    hours = diff.seconds//3600
    minutes = (diff.seconds//60)%60
    return {
        'days_until': days,
        'day_unit': 'days' if days > 1 else 'day',
        'hours_until': hours,
        'hour_unit': 'hours' if hours > 1 else 'hour',
        'minutes_until': minutes,
        'minute_unit': 'minutes' if minutes > 1 else 'minute'
    }

for event in conf['events'].values():
    event_info = parse_event(event)
    date = find_next_day(event_info)
    countdown = get_countdown(date)
    schedule.append({**event_info, **countdown})

for event in schedule:
    if event['days_until'] <= int(conf['time']['threshold']):
        alerts.append(conf['messages']['alert'].format(**event))

driver = webdriver.Chrome()
driver.get(conf['urls']['chat'])
driver.find_element_by_id('userBarName').click()
driver.find_element_by_name('j_username').send_keys(username)
driver.find_element_by_name('j_password').send_keys(password)
driver.find_element_by_xpath('//input[@type="submit"]').click()

wait = WebDriverWait(driver, 60)
wait.until(EC.presence_of_element_located((By.XPATH, '//iframe[@src="/shows/big_brother/live_feed/chat/"]')))
driver.get(chat_url)

wait.until(EC.presence_of_element_located((By.CLASS_NAME, 'name')))
names = driver.find_elements_by_class_name('name')
names = {name.text for name in names}

for alert in alerts:
    driver.find_element_by_class_name('textarea-message-input').send_keys(alert+Keys.ENTER)

driver.close()
