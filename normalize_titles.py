# -*- coding: utf8 -*- 

import re
import pymongo
import codecs

def normalize_title_string(title_str, remove_symbols_list, replace_regex_list):
    for symbol in remove_symbols_list:
        title_str = title_str.replace(symbol, ' ')
    for regex in replace_regex_list:
        title_str = regex.sub(' ', title_str)
    title_str.replace(' & ', ' and ')
    title_str = title_str.strip()
    return title_str.upper()


if __name__ == "__main__":

    mongo = pymongo.Connection('127.0.0.1')
    impact_db = mongo['impact']
    
    citations_collection = impact_db['citations']
    journals_collection = impact_db['journals']
    
    remove_symbols_list = [',', '-', ':', u'\u2026', '.']

    digit_regex = re.compile('\d+')
    white_regex = re.compile('\s+')

    replace_regex_list = [digit_regex, white_regex]

    journals_collection = impact_db['journals']

    f = codecs.open('normalized_titles.txt', 'w', encoding='utf-8')
    for journal in journals_collection.find():
        title = journal['title']
        journal_id = journal['_id']
        normalized_title = normalize_title_string(title, remove_symbols_list, replace_regex_list)
        journals_collection.update({'_id': journal_id}, {'$set' : {'normalized_title' : normalized_title}})
        f.write('%s\n\n' % normalized_title)
        #journal['normalized_title'] = normalized_title
        #journals_collection.save(journal)
        
        #journal['normalized_title'] = normalize_title_string(journal['title'], remove_symbols_list, replace_regex_list)
        #journal.save
    f.close()
