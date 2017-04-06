#!/usr/bin/python
# -*- coding:utf-8 -*-

# import field
import os
import re
import sys
import xml
import MySQLdb
import cPickle as pickle
import HTMLParser
from MySQLdb import cursors

DB_USER = 'root'
DB_PASSWD = 'ltj123'
DB_NAME = 'YEEYAN'
TB_NAME = 'translations'


parser = HTMLParser.HTMLParser()
#pattern_html_entity = re.compile('&(#?)([xX]?)(\w){1,8};', re.U)
pattern_newline = re.compile('</li>|</div>|<br\s{0,3}/>')
pattern_newpara = re.compile('</p>')
pattern_tags = re.compile('<.*?>')
yeezhe = re.compile('\[.*?\]')

'''
pattern_quot = re.compile('&quot;')
pattern_space = re.compile('&nbsp;')
pattern_remove = re.compile('&amp;|&lt;')
'''

if len(sys.argv) < 2:
    print 'usage:python $script_name save_path'
    exit(-1)
PARSED_SAVE_DIR = sys.argv[1]
if not os.path.exists(PARSED_SAVE_DIR):
    os.mkdir(PARSED_SAVE_DIR)

miss_trans_ids = []
miss_origi_ids = []


def connect_db(user, passwd, db, host='localhost', port=3306):
    return MySQLdb.connect(
            host=host,
            user=user,
            passwd=passwd,
            db=db,
            port=port,
            cursorclass=cursors.SSCursor,
            charset='utf8')


def select_cursor(conn):
    cur = conn.cursor()
    # conn.cursor(cursors.SSCursor)
    cur.execute('select * from '+TB_NAME)
    return cur


def close_all(conn, cur):
    cur.close()
    conn.close()


def parse_row(row):
    article_id = row[0]
    translation_content = row[1]
    original_content = row[2]

    if len(translation_content) < 2:
        miss_trans_ids.append(article_id)
    elif len(original_content) < 2:
        miss_origi_ids.append(article_id)
    else:
    	zh_path = os.path.join(PARSED_SAVE_DIR, str(article_id)+'_zh.txt')
        en_path = os.path.join(PARSED_SAVE_DIR, str(article_id)+'_en.txt')
        save_parse(zh_path, translation_content, article_id)
        save_parse(en_path, original_content, article_id)
    	'''
        translation_text = parse_html(translation_content)
        origianl_text = parse_html(original_content)
        zh_path = os.path.join(PARSED_SAVE_DIR, str(article_id)+'_zh.txt')
        en_path = os.path.join(PARSED_SAVE_DIR, str(article_id)+'_en.txt')
        save_parse(zh_path, translation_text, article_id)
        save_parse(en_path, origianl_text, article_id)
        '''


def save_parse(path, content, article_id):
    if os.path.exists(path):
        os.remove(path)
    try:
        with open(path, 'a') as fw:
            fw.write(content.encode('utf-8'))
    except IOError:
        print 'open file {} error!'.format(article_id)


def parse_html(html):
    html = decode_html_entities(html)
    html = re.sub(yeezhe, u'', html)
    html = re.sub(pattern_newline, u'', html)
    html = re.sub(pattern_newpara, u'\n', html)
    '''
    html = re.sub(pattern_quot, u'"', html)
    html = re.sub(pattern_space, u' ', html)
    html = re.sub(pattern_remove, u'', html)
    '''
    html = re.sub(pattern_tags, u'', html)
    return html


def parse_html2(html):
    return '\n'.join(xml.etree.ElementTree.fromstring(html).itertext())


def decode_html_entities(text):
    return parser.unescape(text)


def save_miss():
    try:
        with open('miss.pkl', 'wb') as fp:
            miss = {'miss_trans': miss_trans_ids, 'miss_origi': miss_origi_ids}
            pickle.dump(miss, fp, True)
    except IOError:
        print 'save miss error!'

# main field
if __name__ == '__main__':
    conn = connect_db(DB_USER, DB_PASSWD, DB_NAME)
    cur = select_cursor(conn)

    row = cur.fetchone()
    i = 0
    while i < 1000:
        parse_row(row)
        row = cur.fetchone()
        i += 1
    save_miss()
    close_all(conn, cur)
