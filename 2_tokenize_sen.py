#!/usr/bin/python
# -*- coding:utf-8 -*-

# import field
import os
import re
import sys

line_break = re.compile('[\r\n]')

en_sen_end = re.compile('(?<!\w\.\w.)(?<![A-Z][a-z]\.)(?<![A-Z]\.)(?<=[\.\?!])\s')
# en_sen_end = re.compile(u'(\.{3}|[\.\?!]["”]|[\.\?!])\s?([^a-z])')
zh_sen_end = re.compile(u'([。？！!\?][”"]|[!\?。？！；]|\.{3}|:\)|:\()')

end_mark = re.compile(u'.*[\.\?!]$')
start_mark = re.compile(u'^[A-Z0-9\u4e00-\u9fa5\[\(].*')

dot = re.compile('(?<![\.\]])(\.)(?![\.\w])')

zh_ch = re.compile(u'[\u4e00-\u9fa5]')

if len(sys.argv) < 3:
    print 'usage:python $script_name $data_dir $save_dir'
    exit(-1)
DATA_DIR = sys.argv[1]
SAVE_DIR = sys.argv[2]


def list_files(path):
    return os.listdir(path)


def pre_process(doc, file_lang):
    if file_lang == 'zh':
        doc = re.sub(dot, u'。', doc)
    return doc


def get_sentences(doc, file_lang):
    sentences = []
    for line in re.split(line_break, doc):
        line = line.strip()
        if not line:
            continue
        '''
        if file_lang == 'en':
            line = re.sub(en_sen_end, r'\1\2', line)
            for sent in re.split(r'', line):
                sent = sent.strip()
                if not sent:
                    continue
                sentences.append(sent)
        '''
        if file_lang == 'en':
            for sent in re.split(en_sen_end, line):
                sent = sent.strip()
                if not sent or sent == '.' or len(re.findall(zh_ch, sent)) > 1:
                    continue
                sentences.append(sent)
        elif file_lang == 'zh':
            line = re.sub(zh_sen_end, r'\1', line)
            for sent in re.split(r'', line):
                sent = sent.strip()
                if not sent or sent == u'。' or len(re.findall(zh_ch, sent)) < 1:
                    continue
                sentences.append(sent)
        else:
            pass
    return sentences


def merge_sentence(sentences):
    sens = []
    temp = []
    for sen in sentences:
        if not re.match(end_mark, sen):
            if re.match(start_mark, sen):
                if len(temp) > 0:
                    sens.append(' '.join(temp))
                    temp = []
            temp.append(sen)
        else:
            if re.match(start_mark, sen):
                if len(temp) > 0:
                    sens.append(' '.join(temp))
                sens.append(sen)
            else:
                temp.append(sen)
                sens.append(' '.join(temp))
            temp = []
    if len(temp) > 0:
        sens.append(' '.join(temp))
    return sens


def process(fs):
    for fs in file_lists:
        with open(os.path.join(DATA_DIR, fs), 'r') as fr:
            content = fr.read()
            sentences = []
            file_lang = fs[-2:]
            content = pre_process(content.decode('utf-8'), file_lang)
            sentences = get_sentences(content, file_lang)
            save_path = os.path.join(SAVE_DIR, fs)
            if os.path.exists(save_path):
                os.remove(save_path)
            with open(save_path, 'a') as fw:
                sentences = merge_sentence(sentences)
                sentences = [(sent+'\n').encode('utf-8') for sent in sentences]
                fw.writelines(sentences)


# main field
if __name__ == '__main__':
    file_lists = list_files(DATA_DIR)
    process(file_lists)
