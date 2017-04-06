#!/usr/bin/python
# -*- coding:utf-8 -*-

# import field
from __future__ import division
import os
import re
import md5
import math
import random
import nltk
import requests
import urllib
import jieba.analyse
import jieba
import gensim
import numpy as np
from optparse import OptionParser
from collections import Counter

LIGHTING_QUERY_URL = 'http://lighting.caiyunapp.com:9090/?'
BAIDU_QUERY_URL = 'http://api.fanyi.baidu.com/api/trans/vip/translate'
appid = '20160818000027001'
appkey = 'IgyGDA9DksB1XbAEbqQO'


zh_char = re.compile(u'[\u4e00-\u9fa5]+')
normal_word = [u'的', u'你', u'我', u'他', u'它', u'啊', u'呢', u'哦']
punction_pattern = re.compile("(?<![\s\.])([\.\?!',])")
model = None
options = None


def init_option_parse():
    parser = OptionParser()
    parser.add_option(
            '-s', '--src', dest='DATA_DIR',
            help='source data directory', metavar='DIRECTORY')
    parser.add_option(
            '-d', '--des', dest='SAVE_DIR',
            help='save data directory', metavar='DIRECTORY')
    parser.add_option(
            '-e', '--engine', dest='engine',
            help='translate engine', metavar='l(lighting)|b(baidu)',
            default='l')
    parser.add_option(
            '-m', '--model', dest='MODEL_PATH',
            help='word2vec model path',
            default='/ldata/gongli/wiki/model/wiki.zh.text.model')
    global options
    (options, args) = parser.parse_args()
    if not options.DATA_DIR or not options.SAVE_DIR:
        parser.error('options -s and -d need designation!')


def load_w2c_model(model_path):
    global model
    model = gensim.models.Word2Vec.load(model_path)


def list_fileid(path):
    files = os.listdir(path)
    file_ids = [f[:-3] for f in files]
    return set(file_ids)


def tokenize(content):
    return re.sub(punction_pattern, ' \1 ', content)


def get_translate(content):
    engine = options.engine
    result = ''
    if engine == 'l':
        tokens = map(str.lower, nltk.word_tokenize(content))
        sentence = ' '.join(tokens)
        encode_content = urllib.quote(sentence)
        r = requests.get(LIGHTING_QUERY_URL+encode_content)
        if r.status_code != requests.codes.ok:
            print 'retry!'
            r = requests.get(LIGHTING_QUERY_URL+encode_content)
        r.encoding = 'utf-8'
        result = (r.text)[16:-2].encode('utf-8')
    elif engine == 'b':
        salt = random.randint(32768, 65536)
        sign = appid + content + str(salt) + appkey
        m1 = md5.new()
        m1.update(sign)
        sign = m1.hexdigest()
        query_content = {
                'appid': appid,
                'q': content,
                'from': 'en',
                'to': 'zh',
                'salt': str(salt),
                'sign': sign
                }
        r = requests.get(BAIDU_QUERY_URL, params=query_content)
        while r.status_code != requests.codes.ok or 'error_code' in r.json():
            print 'retry!'
            r = requests.get(BAIDU_QUERY_URL, params=query_content)
        r.encoding = 'utf-8'
        result = r.json()[u'trans_result'][0][u'dst'].encode('utf-8')
    else:
        pass
    return result


def w2c_similarity(sent2list1, sent2list2, freq,  threshold=0.5):
    sim = 0.0
    filter_sent_list1 = filter(lambda x: x in model, sent2list1)
    filter_sent_list2 = filter(lambda x: x in model, sent2list2)
    # sent_set1 = set(filter_sent_list1)
    # sent_set2 = set(filter_sent_list2)
    # sent_list1 = list(sent_set1)
    # sent_list2 = list(sent_set2)
    sent_list1 = filter_sent_list1
    sent_list2 = filter_sent_list2
    len1 = len(sent_list1)
    len2 = len(sent_list2)
    if len1 == 0 or len2 == 0:
        sim = 0.0
    else:
        word_sim_mat = np.zeros((len1, len2))
        for i, word1 in enumerate(sent_list1):
            for j, word2 in enumerate(sent_list2):
                # weight = 1 - 1 / (freq[word2] + 1)
                weight = 1.0
                word_sim_mat[i, j] = model.similarity(word1, word2) * weight
        similar_words = (word_sim_mat > threshold).sum()
        total_words = len(set(sent_list1) | set(sent_list2))
        sim = similar_words / total_words
    return sim


def segment(text):
    seg_text = jieba.lcut(text.replace(' ', ''))
    return seg_text


def filter_nosense_word(word):
    if word in normal_word or not re.match(zh_char, word):
        return False
    return True


# en zh
def get_similarity(sent1, sent2, freq):
    origin_sent1_seg = nltk.word_tokenize(sent1)
    origin_sent1_seg_filter = filter(
            lambda x: re.match('[\w\'\.\-]+', x),
            origin_sent1_seg)
    origin_sent1_seg_lower = map(str.lower, origin_sent1_seg_filter)
    sent2_filter = re.findall('[\w\'\.\-]+', sent2)
    sent2_filter_lower = []
    for item in sent2_filter:
        sent2_filter_lower.append(item.lower())
    special_words = len(set(origin_sent1_seg_lower) & set(sent2_filter_lower))
    sent1_trans = get_translate(sent1)
    sent1_seg = segment(sent1_trans)  # en
    sent2_seg = segment(sent2)  # zh
    sent1_seg = filter(filter_nosense_word, sent1_seg)
    sent2_seg = filter(filter_nosense_word, sent2_seg)
    w2c_sim = w2c_similarity(sent1_seg, sent2_seg, freq) + special_words * 0.3
    return w2c_sim


# en zh
def similarity_matrix(sent1, sent2, direction, freq, init_probe_wide=4):
    sent1_len = len(sent1)
    sent2_len = len(sent2)
    sim_mat = np.zeros((sent1_len, sent2_len))
    if direction == 1:
        for i in range(sent1_len):
            probe_wide = max(len(re.findall(',', sent1[i])), init_probe_wide)
            base_i = int(math.ceil(i * (sent2_len/sent1_len)))
            for j in range(base_i-probe_wide, base_i+probe_wide+1):
                if j < 0 or j > sent2_len-1:
                    continue
                sim_mat[i, j] = get_similarity(sent1[i], sent2[j], freq)
    else:  # direction = -1
        for i in range(sent2_len):
            base_i = i * (sent2_len/sent1_len)
            for j in range(base_i-init_probe_wide, base_i+init_probe_wide+1):
                if j < 0 or j > sent1_len-1:
                    continue
                sim_mat[j, i] = get_similarity(sent1[j], sent2[i], freq)
    return sim_mat


def filter_error_align_sent(align_sents):
    correct_align_sents = []
    for sent1, sent2 in align_sents:
        if len(sent1) == 0 or len(sent2) == 0:
            continue
        if len(sent1) < 2 * len(sent2) * 2:
            correct_align_sents.append((sent1, sent2))
    loss = 1 - (len(correct_align_sents) + 1)/(len(align_sents) + 1)
    print 'align sentence loss rate:%f' % loss
    return correct_align_sents


def find_align(sim_mat, en_lines, zh_lines):
    align_sents = []
    max_idx = np.argmax(sim_mat, axis=1)
    last_col = 0
    temp = []
    i = 0  # count the miss align sentence
    for row, col in enumerate(max_idx):
        if sim_mat[row, col] <= 0.2:
            i += 1
            continue
        if col == last_col:
            temp.append(en_lines[row])
        else:
            align_sents.append((' '.join(temp), zh_lines[last_col]))
            last_col = col
            temp = []
            temp.append(en_lines[row])
    loss = 1 - (i + 1)/(len(max_idx) + 1)
    print 'sentence loss rate:%f' % loss
    align_sents = filter_error_align_sent(align_sents)
    align_lines = map(concate_line, align_sents)
    return align_lines


def concate_line(item):
    return ''.join(item)+'\n'


def align_sen(en_file, zh_file, target_file):
    with open(en_file, 'r') as en_f, open(zh_file, 'r') as zh_f:
        en_lines = map(str.strip, en_f.readlines())
        zh_lines = map(str.strip, zh_f.readlines())
        # freq = Counter(jieba.lcut(''.join(zh_lines)))
        freq = 1
        en_len = len(en_lines)
        zh_len = len(zh_lines)
        '''
        if max(en_len, zh_len) / min(en_len, zh_len) > 3:
            print 'file %s and %s not align!' % (en_file, zh_file)
            return
        '''
        en2zh = similarity_matrix(en_lines, zh_lines, 1, freq)
        # zh2en = similarity_matrix(en_lines, zh_lines, -1)
        double_direction = en2zh
        align_lines = find_align(double_direction, en_lines, zh_lines)
        if os.path.exists(target_file):
            os.remove(target_file)
        with open(target_file, 'a') as fw:
            fw.writelines(align_lines)

# main field
if __name__ == '__main__':
    init_option_parse()
    jieba.load_userdict('dict.txt')
    jieba.disable_parallel()
    load_w2c_model(options.MODEL_PATH)
    file_ids = list_fileid(options.DATA_DIR)
    for file_id in file_ids:
        print file_id
        en_file_path = os.path.join(options.DATA_DIR, file_id+'_en')
        zh_file_path = os.path.join(options.DATA_DIR, file_id+'_zh')
        save_path = os.path.join(options.SAVE_DIR, file_id)
        align_sen(en_file_path, zh_file_path, save_path)
