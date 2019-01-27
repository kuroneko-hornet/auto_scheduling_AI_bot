import pymysql.cursors
import time

def connect_db():
    return pymysql.connect(host='',
                    user='',
                    password='',
                    db='',
                    charset='utf8mb4',
                    cursorclass=pymysql.cursors.DictCursor)

sql_dict={
    'create_notifications':
        'CREATE TABLE notifications ('\
            'notification_id         INTEGER     NOT NULL AUTO_INCREMENT,'\
            'title      VARCHAR(32) NOT NULL,'\
            'time       INTEGER     NOT NULL,'\
            'place      VARCHAR(32)     NOT NULL,'\
            'group_id   INTEGER     NOT NULL,'\
            'notice_at  INTEGER     NOT NULL,'\
            'notice_fg  BOOLEAN     NOT NULL,'\
            'PRIMARY KEY(notification_id)'\
        ')',
    'create_groups':
        'CREATE TABLE group_table ('\
            'group_id       INTEGER         NOT NULL AUTO_INCREMENT,'\
            'address_id     VARCHAR(64)     NOT NULL UNIQUE,'\
            'PRIMARY KEY(group_id)'\
        ')',
    'create_candidate':
        'CREATE TABLE candidate_table ('\
            'group_id   INTEGER     NOT NULL,'\
            'title      VARCHAR(32),'\
            'timestamp  INTEGER,'\
            'place      VARCHAR(32),'\
            'PRIMARY KEY(group_id)'\
        ')',
    'create_candidate_state':
        'CREATE TABLE candidate_state ('\
            'group_id   INTEGER     NOT NULL,'\
            'state      BOOLEAN     NOT NULL,'\
            'PRIMARY KEY(group_id)'\
        ')',
    'get_group_id':'SELECT group_id FROM group_table WHERE address_id = ',
    'get_address_id':'SELECT address_id FROM group_table WHERE group_id = ',
    'get_candidate':
        'SELECT title,timestamp,place from candidate_table WHERE group_id =',
    'get_candidate_state':
        'SELECT state from candidate_state WHERE group_id =',
    'get_message_text':
        'SELECT text FROM MESSAGES WHERE group_id = ',# AND trans_at > {0}'
    'get_notifications':'SELECT * FROM notifications',
    'insert_group':'INSERT IGNORE INTO group_table (address_id) VALUES ',
    'insert_message':'INSERT INTO messages (group_id,trans_at,text) VALUES ',
    'insert_notification':
        'INSERT INTO notifications (title,time,place,group_id,notice_at,notice_fg) VALUES ',
    'insert_candidate':
        'INSERT INTO candidate_table (title,timestamp,place,group_id) VALUES ',
    'change_flag_True':
        'UPDATE notifications SET notice_fg = True WHERE ',
    'change_candidate_state':
        'INSERT INTO candidate_state (group_id,state) VALUES ',
    'delete_candidate':
        'DELETE FROM candidate_table WHERE group_id = ',
    'delete_notification':
        'DELETE FROM notifications WHERE ',# "gourp_id = {0} AND title = '{1}'"
    'view_notification':
        'SELECT * FROM notifications WHERE notice_fg = FALSE AND group_id = '
}

def create_table():
    conn = connect_db()
    try:
        with conn.cursor() as cursor:
            #sql = sql_dict['create_notifications']
            #cursor.execute(sql)
            #sql = sql_dict['create_groups']
            #cursor.execute(sql)
            sql = sql_dict['create_candidate']
            #cursor.execute(sql)
            #sql = sql_dict['create_candidate_state']
            cursor.execute(sql)
            conn.commit()
    finally:
        conn.close()

def get_notifications():
    conn = connect_db()
    try:
        with conn.cursor() as cursor:
            sql = sql_dict['get_notifications']
            cursor.execute(sql)
            res = cursor.fetchall()
    finally:
        conn.close()
    return res

def get_address_id(group_id):
    conn = connect_db()
    try:
        with conn.cursor() as cursor:
            sql = sql_dict['get_address_id'] + '{0}'.format(group_id)
            cursor.execute(sql)
            res = cursor.fetchall()
            address_id = res[0]['address_id']
    finally:
        conn.close()
    return address_id

def change_flag_True(group_id,title):
    conn = connect_db()
    try:
        with conn.cursor() as cursor:
            sql = sql_dict['change_flag_True'] + "group_id = {0} AND title = '{1}'".format(group_id,title)
            cursor.execute(sql)
            conn.commit()
    finally:
        conn.close()

def reg_group(address_id):
    conn = connect_db()
    try:
        with conn.cursor() as cursor:
            sql = sql_dict['insert_group']+"('{0}')"\
             .format(address_id)
            cursor.execute(sql)
            conn.commit()
    finally:
        conn.close()

def reg_message(address_id,trans_at,text):
    conn = connect_db()
    try:
        with conn.cursor() as cursor:
            sql = sql_dict['insert_group'] + "('{0}')".format(address_id)
            cursor.execute(sql)
            sql = sql_dict['get_group_id'] + "'{0}'".format(address_id)
            cursor.execute(sql)
            result = cursor.fetchall()
            for i in range(len(result)):
                group_id = result[i]['group_id']
                sql = sql_dict['insert_message'] + "({0},{1},'{2}')"\
                .format(group_id,trans_at,text)
                cursor.execute(sql)
            conn.commit()
    finally:
        conn.close()

def reg_notification(address,title,time,place,notice_at):
    conn = connect_db()
    try:
        with conn.cursor() as cursor:
            sql = sql_dict['get_group_id'] + "'{0}'".format(address)
            cursor.execute(sql)
            result = cursor.fetchall()
            for i in range(len(result)):
                group_id = result[i]['group_id']
                sql =  sql_dict['insert_notification']+"('{0}',{1},'{2}',{3},{4},{5})"\
                .format(title,time,place,group_id,notice_at,'false')
                cursor.execute(sql)
            conn.commit()
    finally:
        conn.close()

def reg_candidate(address,title,timestamp,place):
    conn = connect_db()
    try:
        with conn.cursor() as cursor:
            sql = sql_dict['get_group_id'] + "'{0}'".format(address)
            cursor.execute(sql)
            result = cursor.fetchall()
            for i in range(len(result)):
                group_id = result[i]['group_id']
                sql =  sql_dict['insert_candidate']+"('{0}',{1},'{2}',{3})"\
                 "ON DUPLICATE KEY UPDATE "\
                 "title = VALUES (title),"\
                 "timestamp = VALUES (timestamp),"\
                 "place = VALUES (place)"\
                 .format(title,timestamp,place,group_id)
                cursor.execute(sql)
            conn.commit()
    finally:
        conn.close()

def get_candidate(address):
    conn = connect_db()
    try:
        with conn.cursor() as cursor:
            sql = sql_dict['get_group_id'] + "'{0}'".format(address)
            cursor.execute(sql)
            result = cursor.fetchall()
            for i in range(len(result)):
                group_id = result[i]['group_id']
                sql =  sql_dict['get_candidate']+'{0}'.format(group_id)
                cursor.execute(sql)
                res = cursor.fetchall()
            conn.commit()
    finally:
        conn.close()
    if res == ():
        return {}
    return res[0]

def delete_candidate(address):
    conn = connect_db()
    try:
        with conn.cursor() as cursor:
            sql = sql_dict['get_group_id'] + "'{0}'".format(address)
            cursor.execute(sql)
            result = cursor.fetchall()
            for i in range(len(result)):
                group_id = result[i]['group_id']
                sql =  sql_dict['delete_candidate']+'{0}'.format(group_id)
                cursor.execute(sql)
            conn.commit()
    finally:
        conn.close()

def view_notification(address):
    conn = connect_db()
    try:
        with conn.cursor() as cursor:
            sql = sql_dict['get_group_id'] + "'{0}'".format(address)
            cursor.execute(sql)
            result = cursor.fetchall()
            sql = sql_dict['view_notification']+'{0}'.format(result[0]['group_id'])
            cursor.execute(sql)
            res = cursor.fetchall()
    finally:
        conn.close()
    return res

def delete(address,title):
    conn = connect_db()
    try:
        with conn.cursor() as cursor:
            sql = sql_dict['get_group_id'] + "'{0}'".format(address)
            cursor.execute(sql)
            result = cursor.fetchall()
            group_id = result[0]['group_id']
            sql =  sql_dict['delete_notification'] + "(group_id = {0} AND title = '{1}')".format(group_id,title)
            print("sql :",sql)
            cursor.execute(sql)
            conn.commit()
    finally:
        conn.close()

def change_candidate_state(address,state):
    conn = connect_db()
    try:
        with conn.cursor() as cursor:
            sql = sql_dict['get_group_id'] + "'{0}'".format(address)
            cursor.execute(sql)
            result = cursor.fetchall()
            for i in range(len(result)):
                group_id = result[i]['group_id']
                sql =  sql_dict['change_candidate_state']+\
                "({0},{1})"\
                 " ON DUPLICATE KEY UPDATE state = VALUES (state)"\
                 .format(group_id,state)
                cursor.execute(sql)
            conn.commit()
    finally:
        conn.close()

def get_candidate_state(address):
    conn = connect_db()
    try:
        with conn.cursor() as cursor:
            sql = sql_dict['get_group_id'] + "'{0}'".format(address)
            cursor.execute(sql)
            result = cursor.fetchall()
            for i in range(len(result)):
                group_id = result[i]['group_id']
                sql =  sql_dict['get_candidate_state']+'{0}'.format(group_id)
                cursor.execute(sql)
                res = cursor.fetchall()
            conn.commit()
    finally:
        conn.close()
    if res == ():
        return False
    return res[0]['state']
