import time
import functions as fn
import sys

now_time = time.time()
notifications = fn.sq.get_notifications()

for i in range(len(notifications)):
    print('notification :',notifications[i])
    noti = notifications[i]
    if noti['notice_fg'] == False:
        if noti['notice_at'] <= now_time:
            address_id = fn.sq.get_address_id(noti['group_id'])
            t = fn.time_changer(noti['time'])
            noti_text = "{0:%m/%d %H:%M} に予定があります。\n予定：{1}\n場所：{2}"\
            .format(t,noti['title'],noti['place'])
            fn.send_message(address_id,noti_text)
            fn.sq.change_flag_True(noti['group_id'],noti['title'])
