#!/usr/bin/python
# -*- coding:utf-8 -*-

# import field
import os
import math
from optparse import OptionParser


def option_parse():
    parser = OptionParser()
    parser.add_option(
            '-s', '--src', dest='DATA_DIR',
            help='source data directory', metavar='directory')
    parser.add_option(
            '-d', '--des', dest='SAVE_DIR',
            help='save data directory', metavar='directory')
    parser.add_option(
            '-n', '--number', dest='MERGE_NUM', metavar='number')
    (options, args) = parser.parse_args()
    if not options.DATA_DIR or not options.SAVE_DIR:
        print 'need options!!!'
        exit(-1)
    return options


def list_fileid(path):
    files = os.listdir(path)
    file_ids = [f[:-3] for f in files]
    return list(set(file_ids))


def merge_file(fileids, options):
    save_dir = options.SAVE_DIR
    data_dir = options.DATA_DIR
    merge_num = int(options.MERGE_NUM)
    part = int(math.floor(len(fileids) / merge_num))
    for idx in range(merge_num):
        start = idx*part
        end = (idx+1)*part
        if idx == merge_num - 1:
            end = len(fileids)
        en_save_path = os.path.join(save_dir, str(idx)+'_en')
        zh_save_path = os.path.join(save_dir, str(idx)+'_zh')
        id_save_path = os.path.join(save_dir, str(idx)+'_id')
       # if os.path.exists(en_save_path):
       #     os.remove(en_save_path)
       # if os.path.exists(zh_save_path):
       #     os.remove(zh_save_path)
        if os.path.exists(id_save_path):
            os.remove(id_save_path)
        with open(en_save_path, 'a') as en_fw, open(zh_save_path, 'a') as zh_fw, open(id_save_path, 'a'), open(id_save_path, 'a') as id_fw:
            for fileid in fileids[start:end]:
                en_data_path = os.path.join(data_dir, fileid+'_en')
                zh_data_path = os.path.join(data_dir, fileid+'_zh')
                id_fw.write(str(fileid)+'\n')
                id_fw.write('<blank>\ngoogle\n<blank>\n')
               # with open(en_data_path, 'r') as en_fr, open(zh_data_path, 'r') as zh_fr:
               #     en_fw.write(en_fr.read())
               #     en_fw.write('<blank>\ngoogle\n<blank>\n')
               #     zh_fw.write(zh_fr.read())
               #     zh_fw.write('<blank>\ngoogle\n<blank>\n')


# main field
if __name__ == '__main__':
    options = option_parse()
    fileids = list_fileid(options.DATA_DIR)
    merge_file(fileids, options)
