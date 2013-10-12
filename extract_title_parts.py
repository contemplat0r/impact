# -*- coding: utf8 -*- 

import re
import pymongo
import codecs
import urlparse
import requests
from nltk import word_tokenize


digit_regex = re.compile('\d+')
white_regex = re.compile('\s+')

remove_symbol_seq_list = [',', '-', ':', u'\u2026', '. ']

separator_sequence = ' - '

replace_regex_list = [digit_regex, white_regex]

and_synonims = ['and', '&']

proxies = {
          "http": "http://192.168.2.1:5432",
            "https": "http://192.168.2.1:443",
            }

headers = {'User-Agent': 'Mozilla/5.0 (X11; Linux i686; rv:10.0.7) Gecko/20100101 Firefox/10.0.7 Iceweasel/10.0.7'}

def extract_site(url):
    parse_url = urlparse.urlparse(url)
    return parse_url.scheme + '://' + parse_url.netloc

def web_get_html(url, headers, proxies):
    req = None 
    html = ''
    try:
        req = requests.get(url, proxies=proxies,  headers=headers)
    except requests.exceptions.ConnectionError:
        print 'Catch ConnectionError'
    if req != None:
        html = req.text
    return html


def detect_journals_by_cit_url(journals, citation, headers, f):
    f.write('Detect journals by cit url start\n')
    matched_journals_list = []
    if 'article_url' in citation.keys():
        cit_url = citation['article_url']
        #f.write('Citation url: %s\n' % cit_url)
        citation_site_html = None
        citation_site_root_html = None
        if cit_url != '':
            f.write('Citation url: %s\n' % cit_url)
            parse_cit_url = urlparse.urlparse(cit_url)
            site = parse_cit_url.scheme + '://' + parse_cit_url.netloc
            path = parse_cit_url.path
            f.write('site: %s path: %s\n' % (site, path))
            pdf_regex = re.compile('[Pp][Dd][Ff]')
            match_pdf = pdf_regex.search(path)
            citation_site_root_html = web_get_html(site, headers, proxies)
            if not match_pdf and path.find('.') == -1:
                citation_site_html = web_get_html(cit_url, headers, proxies)
            if citation_site_root_html == None:
                f.write('cite root html is None\n')
            if citation_site_html == None:
                f.write('cite html is None\n')
            for journal in journals:
                f.write('%s\n' % journal['title'])
                if citation_site_root_html != None and citation_site_root_html.find(journal['title']) != -1:
                    matched_journals_list.append({'journal' : journal, 'url' : site, 'site_root' : True})
                elif citation_site_html != None and citation_site_html.find(journal['title']) != -1:
                    matched_journals_list.append({'journal' : journal, 'url' : cit_url, 'site_root' : False})
        #if matched_journals_list != [] and len(matched_journals_list) == 1:
        else:
            f.write('None cit url\n')
    return matched_journals_list

def split_by_sequence(title_container_str, separator_sequence):
    split_result_list = title_container_str.split(separator_sequence)[1:]
    return [item.strip() for item in split_result_list]

def extract_significant_fragment_part(title_str_fragment):
    significant_part = title_str_fragment
    last_comma_index = title_str_fragment.rfind(',')
    if last_comma_index != -1:
        significant_part = title_str_fragment[0:last_comma_index]
    return significant_part

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

def part_to_pattern(title_part):
    title_part_tokens = word_tokenize(title_part)
    in_brackets_part = []
    out_brackets_part = []
    if '(' in title_part_tokens and ')' in title_part_tokens:
        l_bracket_index = title_part_tokens.index('(')
        r_bracket_index = title_part_tokens.index(')')
        in_brackets_part = title_part_tokens[l_bracket_index + 1:r_bracket_index]
        out_brackets_part = title_part_tokens[:l_bracket_index] + title_part_tokens[r_bracket_index + 1:]
    else:
        out_brackets_part = title_part_tokens
    return {'token_list' : out_brackets_part, 'bracket_part_token_list' : in_brackets_part}

def detect_and(title_pattern):
    tokens = title_pattern['token_list']
    in_bracket_tokens = title_pattern['bracket_part_token_list']
    if ('and' or '&') in tokens:
        title_pattern['token_list'] = [token for token in tokens if token not in and_synonims]
        title_pattern['and_present'] = 'True'
    if ('and' or '&') in in_bracket_tokens:
        title_pattern['in_bracket_tokens'] = [token for token in in_bracket_tokens if token not in and_synonims]
        title_pattern['and_present'] = 'True'
    return title_pattern

def is_subset(first_lst, second_lst):
    return set(first_lst).issubset(set(second_lst))

def detect_all_corrsponding_journals(pattern_lst, journal_lst):
    corresponding_journals = []
    for journal in journal_lst:
        tokenized_title = journal['tokenized_title']
        if is_subset(pattern_lst, tokenized_title):
            corresponding_journals.append(journal)
    return corresponding_journals

def detect_journal_by_already_recoginzed_url(citation, journals):
    journal_id = None
    url = extract_site(citation['article_url'])
    for journal in journals:
        if url == journal['url']:
            journal_id = journal['_id']
            break
    return journal_id



def detect_single_capital(title_pattern):
    single_capital_list = []
    indexes_list = []
    tokens = title_pattern['token_list']
    in_bracket_tokens = title_pattern['bracket_part_token_list']
    i = 0
    for token in tokens:
        if len(token) == 1 and token.isupper():
            if token not in sigle_capital_list:
                single_capital_list.append(token)
            indexes_list.append(i)
        i = i + 1
    for index in indexes_list:
        pass

if __name__ == "__main__":

    mongo = pymongo.Connection('127.0.0.1')
    impact_db = mongo['impact']
    
    journals_collection = impact_db['journals']
    citations_collection = impact_db['citations']

    f = codecs.open('significant_parts.txt', 'w', encoding='utf-8')

    dashes_count = 0
    identified_journals = 0
    not_exist_journal_names = 0
    many_corresponding_journals = 0

    for citation in citations_collection.find():
        if ('journal_id' in citation.keys()) == False:
            journal_title = citation['article_journal']
            #f.write('%s\n' % journal_title)
            citation_id = citation['_id']
            pattern_list = []
            if journal_title.find(separator_sequence) != -1:
                dashes_count = dashes_count + 1
                fragment_list = split_by_sequence(journal_title, separator_sequence)
                for fragment in fragment_list:
                    significant_part = extract_significant_fragment_part(fragment)
                    cleared_significant_part = clear_title_part(significant_part, remove_symbol_seq_list, replace_regex_list)
                    pattern = part_to_pattern(cleared_significant_part)
                    new_part = ''
                    for token in pattern['token_list']:
                        new_part = new_part + token + ' '
                    new_part = new_part.strip().upper()
                    pattern_list.append(new_part)

                found_journals_cursor = None
                if pattern_list[0] != '':
                    found_journals_cursor = journals_collection.find({'normalized_title' : {'$regex' : pattern_list[0]}})

                if found_journals_cursor != None and found_journals_cursor.count() == 0:
                    not_exist_journal_names = not_exist_journal_names + 1
                elif found_journals_cursor != None and found_journals_cursor.count() == 1: 
                    identified_journals = identified_journals + 1
                    citations_collection.update({'_id' : citation_id}, {'$set' : {'journal_id' : found_journals_cursor[0]['_id']}})
                elif found_journals_cursor != None and found_journals_cursor.count() > 1:
                    f.write('%s found %s matches\n' % (journal_title, str(found_journals_cursor.count())))
                    #many_corresponding_journals = many_corresponding_journals + 1
                    found_journals = [journal for journal in found_journals_cursor]
                     
                    if ('article_url' in citation.keys()) and (citation['article_url'] != '') and (('url_checked' in citation.keys())) == False:
                        journal_id = detect_journal_by_already_recoginzed_url(citation, found_journals)
                        if journal_id != None:
                            f.write('Journal detected already recogized by url\n')
                            identified_journals = identified_journals + 1
                            citations_collection.update({'_id' : citation_id}, {'$set' : {'journal_id' : journal_id}})
                        else:
                            detected_by_url_journals = detect_journals_by_cit_url(found_journals, citation, headers, f)
                            if len(detected_by_url_journals) == 1:
                                identified_journals = identified_journals + 1
                                detected_journal = detected_by_url_journals[0]['journal']
                                detected_journal_id = detected_journal['_id']
                                citations_collection.update({'_id' : citation_id}, {'$set' : {'journal_id' : detected_journal_id}})
                                if detected_journal['url'] == '' and detected_by_url_journals[0]['site_root'] == True:
                                    journals_collection.update({'_id' : detected_journal_id}, {'$set' : {'url' : detected_by_url_journals[0]['url']}})
                                f.write('Journal detected by citation url\n')
                            else:
                                many_corresponding_journals = many_corresponding_journals + 1

                        citations_collection.update({'_id' : citation_id}, {'$set' : {'url_checked' : True}})
                    else:
                        many_corresponding_journals = many_corresponding_journals + 1
        f.write('\n'*2)
    f.close()

    print 'Citaions total: ', citations_collection.count(), ' Not exist journal names: ', not_exist_journal_names,  ' Identified journals: ', identified_journals, ' Many corresponding journals: ', many_corresponding_journals, ' Dashes total: ', dashes_count
