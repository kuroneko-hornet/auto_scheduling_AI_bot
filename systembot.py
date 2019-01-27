#  Licensed under the Apache License, Version 2.0 (the "License"); you may
#  not use this file except in compliance with the License. You may obtain
#  a copy of the License at
#
#       https://www.apache.org/licenses/LICENSE-2.0
#
#  Unless required by applicable law or agreed to in writing, software
#  distributed under the License is distributed on an "AS IS" BASIS, WITHOUT
#  WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied. See the
#  License for the specific language governing permissions and limitations
#  under the License.
# settings.py

from __future__ import unicode_literals
#WebhookParserとapiはfnからimport
import functions as fn
import make_sche as sche
from pyknp import (KNP,Juman)
from argparse import ArgumentParser
from flask import Flask, request, abort
import ssl
context = ssl.SSLContext(ssl.PROTOCOL_TLSv1_2)
context.load_cert_chain('/etc/letsencrypt/live/katfuji-syssei.com/fullchain.pem', '/etc/letsencrypt/live/katfuji-syssei.com/privkey.pem')

app = Flask(__name__)

def confirm(event, sche_dict):
    conf_list = ["「Yes」", "「No」"]
    items = [fn.QuickReplyButton(action=fn.MessageAction(label=f"{conf}", text=f"{conf}")) for conf in conf_list]
    messages = fn.TextSendMessage(
        text="予定\ntitle:{0}\nplace:{1}\n日時:{2:%m/%d\t%H:%M}\nを追加していいですか？".format(sche_dict["title"], sche_dict["place"],fn.time_changer(sche_dict["timestamp"])),
        quick_reply=fn.QuickReply(items=items)
    )
    fn.line_bot_api.reply_message(event.reply_token, messages=messages)

@app.route("/")
def hello_world():
    return "system_bot2018."

#knpの準備 時間がかかるため、ここで準備しとく
knp_for_mrph_list = KNP()
jumanapp = Juman()

help = '私は、自動スケジューリングbotです。\n\
グループまたは個人チャットで会話からスケジュールを提案します。\n\
スケジュールは\n\
・「タイトル」\n\
・「予定地」\n\
・「予定時刻」\n\
の要素を持ちます。\n\n\
使い方は以下の通りです。\n\n\
[自動スケジューリング機能]\n\
日常的な会話をしてください。\n\
会話を読み取り、スケジュールを提案いたします。\n\
会話の途中でも私の理解している事が知りたい時は「スケジューラ」とコメントしてください。\n\n\
[リマインド機能]\n\
予定の24時間前に通知します。\n\n\
[手動スケジューリング機能]\n\
「add (時刻) (タイトル) (予定地)」とのコメントで、スケジュールを登録します。\n\n\
[確認機能]\n\
「view」とのコメントで、スケジュール一覧を確認できます。\n\n\
[削除機能]\n\
「delete (タイトル)」とのコメントで、スケジュールを削除できます。\n\n\
では後は聞きに徹します。'

@app.route("/callback", methods=['POST'])
def callback():
    # get X-Line-Signature header value
    signature = request.headers['X-Line-Signature']
    # get request body as text
    body = request.get_data(as_text=True)
    app.logger.info("Request body: " + body)
    #webhook body
    try:
            events = fn.parser.parse(body, signature)
    except InvalidSignatureError:
            abort(400)
    for event in events:
        if not isinstance(event, fn.MessageEvent):
            continue
        if not isinstance(event.message, fn.TextMessage):
            continue
        message=event.message.text
        if "room" == event.source.type:
            address_id=event.source.room_id
        elif "group" == event.source.type:
            address_id=event.source.group_id
        else:
            address_id=event.source.user_id
        fn.sq.reg_group(address_id)
        state = fn.sq.get_candidate_state(address_id)
        if message == 'help':
            fn.send_message(address_id,help)
        elif  message.count('add'):
            if 'add' == fn.remind_adder(address_id,event.timestamp/1000,message):
                print('OK [ADD]')
        elif message.count('view'):
            if 'view' == fn.remind_viewer(address_id):
                print('OK [VIEW]')
        elif message.count('delete'):
            if 'delete' == fn.remind_deleter(address_id,message):
                print('OK [DELETE]')
        elif state and message == "「Yes」":
            fn.sq.change_candidate_state(address_id,False)
            noti_dict = fn.sq.get_candidate(address_id)
            fn.add_notification(address_id,noti_dict['title'],noti_dict['timestamp'],noti_dict['place'])
            fn.send_message(address_id, "追加しました。")
            fn.sq.delete_candidate(address_id)
        elif state and message == "「No」":
            fn.send_message(address_id, "追加しませんでした。")
            fn.sq.change_candidate_state(address_id,False)
        else:
            fn.sq.change_candidate_state(address_id,False)
            sche_dict = sche.sche_make(event.timestamp/1000, message,address_id, knp_for_mrph_list, jumanapp)
            if sche_dict != None:
                fn.sq.change_candidate_state(address_id,True)
                confirm(event, sche_dict)
        """fn.line_bot_api.reply_message(
            event.reply_token,
            fn.TextSendMessage(text='systembot - OK.')
        )"""
    return 'OK'

if __name__ == "__main__":
    arg_parser = ArgumentParser(
        usage='Usage: python ' + __file__ + ' [--port <port>] [--help]'
    )
    arg_parser.add_argument('-p', '--port', type=int, default=8000, help='port')
    arg_parser.add_argument('-d', '--debug', default=False, help='debug')
    options = arg_parser.parse_args()

    app.run(host='0.0.0.0', port=5000, ssl_context=context, threaded=True, debug=True)
