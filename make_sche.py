from __future__ import unicode_literals

from dotenv import load_dotenv
from pathlib import Path  # python3 only
from datetime import (
    datetime,timedelta
)
import functions as fn
import os
import sys
import requests
import json
import re
from pyknp import (KNP, Juman)

ok_pattern = r'(おけ|り|了解|いい|おっけ|わかった|うい)'
reg_pattern = r'(スケジューラ)'

load_dotenv()
# OR, the same with increased verbosity:
load_dotenv(verbose=True)
# OR, explicitly providing path to '.env'
env_path = Path('.') / '.env'
load_dotenv(dotenv_path=env_path)

d_URL = "https://api.apigw.smt.docomo.ne.jp/gooLanguageAnalysis/v1/entity?APIKEY="
d_KEY = os.getenv('DOCOMO_API_KEY', None)
if d_KEY is None:
    print('Specify DOCOMO_API_KEY as environment variable.')
    sys.exit(1)

def titlemake(knp_mrph_list, schedule_dict):
    path = os.getcwd() + '/events.txt'
    with open(path) as f:
        events = [s.strip() for s in f.readlines()]
    for mrph in knp_mrph_list: # 各形態素へのアクセス
        if mrph.hinsi == '名詞':
            for event in events:
                if mrph.imis.count(event):
                    schedule_dict['title'] = mrph.genkei
                    break
    if not 'title' in schedule_dict:
        schedule_dict['title'] = 'None'
    print("   update(title):",schedule_dict['title'])
    return schedule_dict

def knp_locmake(knp_mrph_list, schedule_dict):
    for mrph in knp_mrph_list: # 各形態素へのアクセス
        if (mrph.imis.count('地名') or mrph.imis.count('場所')) and mrph.hinsi == '名詞':
            schedule_dict['place'] = mrph.genkei
            break
    if not 'place' in schedule_dict:
        schedule_dict['place'] = 'None'
    print("update(location):",schedule_dict['place'])
    return schedule_dict

def locmake(message, schedule_dict):
    # docomoAPI
    url = "{}{}".format(d_URL, d_KEY)
    headers = {'Content-Type': 'application/json'}
    payload = {
        "requests_id": "",
        "sentence": message,
        "class_filter": "ART|ORG|LOC"
    }
    response = requests.post(url, data=json.dumps(payload), headers=headers)
    result = json.loads(response.text)
    # 解析結果の処理
    if 'ne_list' in result.keys():
        for name, _type in result["ne_list"]:
            schedule_dict['place'] = name
    if not 'place' in schedule_dict:
        schedule_dict['place'] = 'None'
    return schedule_dict

def analysis_mrphList(mrphList,schedule_dict):
    print("\n--------------\n|    解析    |\n--------------")
    for mrph in mrphList:
        print("見出し:%s, 品詞:%s, 品詞細分類:%s, 意味情報:{%s}" \
        % (mrph.midasi, mrph.hinsi, mrph.bunrui, mrph.imis))
    schedule_dict = titlemake(mrphList, schedule_dict)
    schedule_dict = knp_locmake(mrphList, schedule_dict)
    return schedule_dict

def sche_make(now, message ,address_id, knp_for_mrph_list, jumanapp):
    print("\n-------------------\n|    make_sche    |\n-------------------")
    #databaseから取ってくる
    schedule_dict = fn.get_candidate(address_id)
    print(" load sche_dict :",schedule_dict)
    result = re.search(ok_pattern, message)
    reg_result = re.search(reg_pattern, message)
    if result or reg_result:
        check = fn.check_sche_dict(schedule_dict)
        if check[0]:
            return schedule_dict
        elif reg_result:
            for i in range(len(check[1])):
                fn.send_message(address_id,"{0}を埋めてもっかい".format(check[1][i]))
            return None
        else:
            return None
    #titleとplaceの抽出
    schedule_dict = analysis_mrphList(jumanapp.analysis(message).mrph_list(), schedule_dict)
    #timstampの抽出
    schedule_dict = fn.timemake(now, message, schedule_dict)

    print("  add sche_dict :",schedule_dict,'\n')
    fn.add_candidate(address_id,schedule_dict['title'],schedule_dict['timestamp'],schedule_dict['place'])
    return None

#now = float(datetime.now().strftime('%s'))
#path = os.getcwd() + '/samplemessage1.txt'
#with open(path) as f:
#    sample1 = f.read()
#docomo(now, sample1)
#path = os.getcwd() + '/samplemessage2.txt'
#with open(path) as f:
#    sample2 = f.read()
#docomo(now, sample2)
#path = os.getcwd() + '/samplemessage3.txt'
#with open(path) as f:
#    sample3 = f.read()
#docomo(now, sample3)
