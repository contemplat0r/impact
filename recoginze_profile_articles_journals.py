# -*- coding: utf8 -*- 

import re
import pymongo
import codecs
import urlparse
import requests
from nltk import word_tokenize

remove_symbol_seq_list = [',', '-', ':']

title_regex = re.compile('(?P<title>^\D+) ')
digit_regex = re.compile('\d+')
white_regex = re.compile('\s+')

separator_sequence = ' - '

replace_regex_list = [digit_regex, white_regex]

and_synonims = ['and', '&']

proxies = {
          "http": "http://192.168.2.1:5432",
            "https": "http://192.168.2.1:443",
            }

headers = {'User-Agent': 'Mozilla/5.0 (X11; Linux i686; rv:10.0.7) Gecko/20100101 Firefox/10.0.7 Iceweasel/10.0.7'}

def split_by_sequence(title_container_str, separator_sequence):
    split_result_list = title_container_str.split(separator_sequence)[1:]
    return [item.strip() for item in split_result_list]

def part_to_pattern(title_part):
    title_part_tokens = word_tokenize(title_part)
    in_brackets_part = []
    out_brackets_part = []
    abbreviation_part = []
    abbreviation_part = [token for token in title_part_tokens if len(token) > 1 and token.isupper()]
    title_part_tokens = [token for token in title_part_tokens if token not in abbreviation_part]

    if '(' in title_part_tokens and ')' in title_part_tokens:
        l_bracket_index = title_part_tokens.index('(')
        r_bracket_index = title_part_tokens.index(')')
        in_brackets_part = title_part_tokens[l_bracket_index + 1:r_bracket_index]
        out_brackets_part = title_part_tokens[:l_bracket_index] + title_part_tokens[r_bracket_index + 1:]
    else:
        out_brackets_part = title_part_tokens
    return {'token_list' : out_brackets_part, 'bracket_part_token_list' : in_brackets_part, 'abbreviation_part' : abbreviation_part}

def extract_title(title_str, title_regex):
    title = ''
    if title_str != None:
        match = title_regex.match(title_str)
        if match:
            title = match.group('title')
    return title

def clear_title_part(title_part, remove_symbol_seq_list, replace_regex_list):
    for symbol in remove_symbol_seq_list:
        title_part = title_part.replace(symbol, ' ')
    for regex in replace_regex_list:
        title_part = regex.sub(' ', title_part)
    title_part = title_part.strip()
    title_part = title_part.lstrip('\'')
    title_part = title_part.rstrip('\'')
    title_part = title_part.rstrip('-')
    title_part = title_part.lstrip('-')
    title_part = title_part.strip()
    return title_part

def clear_tilte(title, remove_symbol_seq_list):
    for symbol in remove_symbol_seq_list:
        title = title.replace(symbol, ' ')
    return title

def token_list_to_title(token_list):
    title = ''
    for token in token_list:
        title = title + token + ' '
    return title.upper().strip()

if __name__ == "__main__":

    mongo = pymongo.Connection('127.0.0.1')
    impact_db = mongo['impact']
    articles_collection = impact_db['articles']
    journals_collection = impact_db['journals']

    articles_cursor = articles_collection.find()

    f = codecs.open('article_journal_titles.txt', 'w', encoding='utf-8')
    identified_journals = 0
    for article in articles_cursor:
        article_id = article['_id']
        raw_title = extract_title(article['journal'], title_regex)
        f.write('%s\n' % raw_title)
        cleared_title = clear_tilte(raw_title, remove_symbol_seq_list)
        pattern = part_to_pattern(cleared_title)
        for key in pattern.keys():
            f.write('%s %s\n' % (key, pattern[key]))
        f.write('\n')
        major_search_pattern = token_list_to_title(pattern['token_list'])
        found_journals_cursor = journals_collection.find({'normalized_title' : {'$regex' : major_search_pattern}})
        if found_journals_cursor.count() == 1:
            articles_collection.update({'_id' : article_id}, {'$set' : {'journal_id' : found_journals_cursor[0]['_id']}})
            identified_journals = identified_journals + 1
    f.close()
    print identified_journals

