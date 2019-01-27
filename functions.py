import os
import sys
import time
import random
import re
from datetime import (
    datetime,timedelta
)
import sql_run as sq
from linebot import (
    LineBotApi, WebhookParser
)
from linebot.exceptions import (
    InvalidSignatureError
)
from linebot.models import (
    MessageEvent, TextMessage, TextSendMessage,QuickReplyButton, MessageAction, QuickReply
)
###追加###
import ssl
context = ssl.SSLContext(ssl.PROTOCOL_TLSv1_2)
context.load_cert_chain('/etc/letsencrypt/live/katfuji-syssei.com/fullchain.pem', '/etc/letsencrypt/live/katfuji-syssei.com/privkey.pem')
#環境変数用
from dotenv import load_dotenv
load_dotenv()
# OR, the same with increased verbosity:
load_dotenv(verbose=True)
# OR, explicitly providing path to '.env'
from pathlib import Path  # python3 only
env_path = Path('.') / '.env'
load_dotenv(dotenv_path=env_path)

# 環境変数からchannel_secret・channel_access_tokenを取得
channel_secret = os.getenv('LINE_CHANNEL_SECRET',None)
channel_access_token = os.getenv('LINE_CHANNEL_ACCESS_TOKEN',None)

if channel_secret is None:
    print('Specify LINE_CHANNEL_SECRET as environment variable.')
    sys.exit(1)
if channel_access_token is None:
    print('Specify LINE_CHANNEL_ACCESS_TOKEN as environment variable.')
    sys.exit(1)

line_bot_api = LineBotApi(channel_access_token)
parser = WebhookParser(channel_secret)

def time_changer(unix_time):
    time=datetime.fromtimestamp(unix_time) + timedelta(hours=9)
    return time

def send_message(id,sendmessage):
    line_bot_api.push_message(id,TextSendMessage(text=sendmessage))
    print("\n----------------------\n|    send message    |\n----------------------")
    print('message :'+sendmessage,'\n')

def slash(now,text):
    #print('slash')
    list = []
    now = datetime.utcfromtimestamp(now) + timedelta(hours=9)
    pattern = r'((\d{4})(/|-))?(\d{1,2})(/|-)(\d{1,2})'
    match = re.search(pattern, text)
    if match:
        # difine month,day
        day = int(match.group(6))
        month = int(match.group(4))
        if move_up(day,'day',month):
            month += 1
            day = 1
        #define year
        if match.group(2) != None:
            year = int(match.group(2))
        else:
            year = int("{0:%Y}".format(now))
        if move_up(month, 'month'):
            year += 1
            month = 1
        t = datetime.strptime('{0}/{1}/{2} 00:00:00'.format(year,month,day),'%Y/%m/%d %H:%M:%S')
        if now > t:
            return []
        t -= timedelta(hours=9)
        list.append(t.timestamp())
        print(datetime.utcfromtimestamp(list[0]) + timedelta(hours=9))
    else:
        return []
    return list

def colon(now, text):
    #print('colon')
    list = []
    now = datetime.utcfromtimestamp(now) + timedelta(hours=9)
    pattern = r'(\d{1,2}):(\d{1,2})'
    match = re.search(pattern, text)
    if match:
        year = int("{0:%Y}".format(now))
        month = int("{0:%m}".format(now))
        day = int("{0:%d}".format(now))
        t = datetime.strptime('{0}/{1}/{2} {3}:{4}:00'.format(year, month, day, match.group(1), match.group(2)), '%Y/%m/%d %H:%M:%S')
        t -= timedelta(hours=9)
        list.append(t.timestamp())
        print(datetime.utcfromtimestamp(list[0]) + timedelta(hours=9))
    else:
        return []
    return list

def not_specified(now, text):
    #print('not_specified')
    list = []
    pattern = r'(\d+(分|(時間)|日|(週間))後)|((明日)|(明後日)|(明々後日))'
    time_pattern = r'\d*'
    match = re.search(pattern, text)
    if match:
        result = match.group()
        if result.count("分後"):
            list.append(now + float(re.search(time_pattern, result).group()) * 60)
        elif result.count("時間"):
            list.append(now + float(re.search(time_pattern, result).group()) * 60*60)
        elif result.count("日後"):
            list.append(now + float(re.search(time_pattern, result).group()) * 60*60*24)
        elif result.count("週間"):
            list.append(now + float(re.search(time_pattern, result).group()) * 60*60*24*7)
        elif result.count("明日"):
            list.append(now + 60*60*24)
        elif result.count("明後日"):
            list.append(now + 2*60*60*24)
        elif result.count("明々後日"):
            list.append(now + 3*60*60*24)
    else:
        return []
    list.append("title{0}".format(random.randint(0,1000)))
    list.append("place{0}".format(random.randint(0,1000)))
    print(datetime.utcfromtimestamp(list[0]) + timedelta(hours=9))
    return list

def move_up(n,mode,*month):
    if mode == 'month':
        range = 12
    elif mode == 'day':
        if month[0] == 2:
            range = 28
        elif month[0] in [1,3,5,7,8,10,12]:
            range = 31
        elif month[0] in [4,6,9,11]:
            range = 30
    elif mode == 'hour':
        range = 24
    else:
        range = 60
    if n > range:
        return 1
    return 0

def date_check(mode,now,**time_dict):
    if mode == 'hour':
        if time_dict['hour'] < int("{0:%H}".format(now)) or\
            (time_dict['hour'] == int("{0:%H}".format(now)) and\
            time_dict['minute'] <= int("{0:%M}".format(now))):
            return True
    elif mode == 'day':
        if time_dict['day'] < int("{0:%d}".format(now)) or\
            (time_dict['day'] == int("{0:%d}".format(now)) and\
            date_check('hour',now,minute=time_dict['minute'],hour=time_dict['hour'])):
            return True
    elif mode == 'month':
        if time_dict['month'] < int("{0:%m}".format(now)) or\
            (time_dict['month'] == int("{0:%m}".format(now)) and\
            date_check('day',now,minute=time_dict['minute'],hour=time_dict['hour'],day=time_dict['day'])):
            return True
    return False

def specified(now,text):
    #print('specified')
    list = []
    now = datetime.utcfromtimestamp(now) + timedelta(hours=9)
    pattern = r'\d+(分|時|日|月|年)'
    time_pattern = r'\d*'
    match = re.search(pattern, text)
    if match:
        #define minute
        if text.count('分'):
            minute=int(re.sub('\D','',re.search(r'\d+分',text).group()))
            if minute <= int("{0:%M}".format(now)):
                hour=1
        else:
            minute=0
            hour=0

        #define hour
        if text.count('時'):
            hour+=int(re.sub('\D','',re.search(r'\d+時',text).group()))
        else:
            hour+=int('{0:%H}'.format(now))
        day=0
        if move_up(hour,'hour'):
            day += 1
            hour = 0
        if date_check('hour',now,minute=minute,hour=hour):
            day+=1

        #difine month,day
        if text.count('日'):
            day+=int(re.sub('\D','',re.search(r'\d+日',text).group()))
        else:
            day+=int('{0:%d}'.format(now))
        month=0
        if text.count('月'):
            month += int(re.sub('\D','',re.search(r'\d+月',text).group()))
            if move_up(day,'day',month):
                month += 1
                day = 1
        else:
            month+=int("{0:%m}".format(now))
        if date_check('day',now,minute=minute,hour=hour,day=day):
            month+=1
        if date_check('month',now,minute=minute,hour=hour,day=day,month=month):
            year=1
        else:
            year=0
        if move_up(month,'month'):
            year += 1
            month = 1
        #define year
        if text.count('年'):
            year+=int(re.sub('\D','',re.search(r'\d+年',text).group()))
        else:
            year+=int("{0:%Y}".format(now))

        t = datetime.strptime('{0}/{1}/{2} {3}:{4}:00'.format(year,month,day,hour,minute),'%Y/%m/%d %H:%M:%S')
        #print(now)
        #print(t)
        if now > t:
            return []
        t -= timedelta(hours=9)
        list.append(t.timestamp())
    else:
        return []
    return list

def add_notification(address_id,title,timestamp,place):
    #24時間前に通知
    sq.reg_notification(address_id,title,timestamp,place,timestamp-(3600*24))
    return

def timemake(now, message, schedule_dict):
    d_pattern = r'(\d+(日|(週間))後)|((明日)|(明後日)|(明々後日))|(\d+(日|月|年))|(((\d{4})(/|-))?(\d{1,2})(/|-)(\d{1,2}))'
    t_pattern = r'(\d+(分|(時間))後)|(\d+(分|時))|((\d{1,2}):(\d{1,2}))'
    d_match = re.search(d_pattern, message)
    t_match = re.search(t_pattern, message)
    if d_match:
        result = d_match.group()
        print("date:" + result)
        timestamp_list = not_specified(now, result)
        if timestamp_list == []:
            timestamp_list = specified(now, result)
            if timestamp_list == []:
                timestamp_list = slash(now, result)
        if not timestamp_list == []:
            schedule_dict['timestamp'] = timestamp_list[0]
        print("")
    if t_match:
        result = t_match.group()
        print("time:" + result)
        timestamp_list = not_specified(now, result)
        if timestamp_list == []:
            timestamp_list = specified(now, result)
            if timestamp_list == []:
                timestamp_list = colon(now, result)
        if not timestamp_list == []:
            # 日付が既に入っていたら時刻のみ更新
            if 'timestamp' in schedule_dict.keys():
                jtimestamp = schedule_dict['timestamp'] + (60 * 60 * 9)
                datestamp = jtimestamp - (jtimestamp % (60 * 60 * 24))
                schedule_dict['timestamp'] = datestamp + ((timestamp_list[0] + (60 * 60 * 9)) % (60 * 60 * 24)) - (
                            60 * 60 * 9)
                print(datetime.utcfromtimestamp(schedule_dict['timestamp']) + timedelta(hours=9))
            else:
                schedule_dict['timestamp'] = timestamp_list[0]
        print("")
    if not 'timestamp' in schedule_dict:
        schedule_dict['timestamp'] = 0
    print("    update(time):",schedule_dict['timestamp'])
    return schedule_dict

def check_sche_dict(sche_dict):
    if sche_dict == {}:
        return False,['予定のタイトル','予定地','予定時刻']
    keywords = []
    for key in sche_dict:
        if 'None' == sche_dict[key] or 0 == sche_dict[key]:
            if key == 'title':
                keywords.append('予定のタイトル')
            elif key == 'place':
                keywords.append('予定地')
            elif key == 'timestamp':
                keywords.append('予定時刻')
    if len(keywords) > 0:
        return False,keywords
    return True,[]

def remind_adder(address_id,now,message):
    print("\n-------------\n|    add    |\n-------------")
    m_list = message.replace('add',' ').replace('　',' ').split()
    if len(m_list) < 3:
        send_message(address_id,'正しい形式でないと読めません...(add 時刻 タイトル 予定地)')
        return 'add'
    sche_dict = {}
    time = m_list[0]
    sche_dict = timemake(now, time, sche_dict)
    sche_dict['title'] = m_list[1]
    sche_dict['place'] = m_list[2]
    #reg_notification
    add_notification(address_id,sche_dict['title'],sche_dict['timestamp'],sche_dict['place'])
    send_message(address_id,"OK. (^□^)")
    print('added',sche_dict,'\n')
    return 'add'

def remind_viewer(address_id):
    view_str=[]
    view_res = sq.view_notification(address_id)
    for i in range(len(view_res)):
        view_str.append('予定：{1}\n場所：{2}\n時刻：{0:%m/%d %H:%M}'\
        .format(time_changer(view_res[i]['time']),view_res[i]['title'],view_res[i]['place']))
    if view_str == []:
        send_message(address_id,'お調べしたところ、\tお知らせしていないのスケジュールはありませんでした。')
        return 'view'
    send_message(address_id,'どぞ')
    send_message(address_id,'\n'.join(view_str))
    return 'view'

def remind_deleter(address_id,message):
    title = message.replace('delete',' ').replace('　',' ').split()
    if not len(title) == 1:
        send_message(address_id,'正しい形式でないと読めません...(delete タイトル)')
        return 'delete'
    sq.delete(address_id,title[0])
    return 'delete'

def add_candidate(address_id,title,timestamp,place):
    sq.reg_candidate(address_id,title,timestamp,place)

def get_candidate(address_id):
    return sq.get_candidate(address_id)
