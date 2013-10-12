# -*- coding: utf8 -*- 

import re
import pymongo
import codecs
import urlparse
import requests
from nltk import word_tokenize

def web_get_html(url, headers):
    req = requests.get(url, headers=headers)
    return req.text

def detect_journals_by_cit_url(journals, citation, headers, f):
    f.write('Detect journals by cit url start\n')
    matched_journals_list = []
    if 'article_url' in citation.keys():
        cit_url = citation['article_url']
        f.write('Citation url: %s\n' % cit_url)
        citation_site_html = None
        citation_site_root_html = None
        if cit_url != '':
            f.write('Citation url: %s\n' % cit_url)
            parse_cit_url = urlparse.urlparse(cit_url)
            site = parse_cit_url.scheme + '://' + parse_cit_url.netloc
            path = parse_cit_url.path
            pdf_regex = re.compile('\.pdf$')
            match_pdf = pdf_regex.search(path)
            citation_site_root_html = web_get_html(site, headers)
            if not match_pdf:
                citation_site_html = web_get_html(cit_url, headers)
            for journal in journals:
                f.write('%s\n' % journal['title'])
                if citation_site_root_html.find(journal['title']) != -1:
                    matched_journals_list.append({'journal' : journal, 'url' : site})
                elif citation_site_html != None and citation_site_html.find(journal['title']) != -1:
                    matched_journals_list.append({'journal' : journal, 'url' : cit_url})
        #if matched_journals_list != [] and len(matched_journals_list) == 1:
    return matched_journals_list

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
    find_lst_pattern = [item for item in out_brackets_part if item not in [',', ':', 'and', u'\u2026', '&', 'th'] and item.isdigit() != True]
    return {'token_list' : out_brackets_part, 'bracket_part_token_list' : in_brackets_part, 'find_pattern_token_list' : find_lst_pattern}

def extract_title_search_pattern(title_str, regex):
    pattern_str_parts = {'title_part_list' : [], 'maybe_title_part_list' : []}
    title_split_by_dash = title_str.split(' - ')
    title_split_by_dash = [item.strip() for item in title_split_by_dash[1:]]
    for part in title_split_by_dash:
        match = regex.match(part)
        if match:
            title = match.group('title')
            pattern_str_parts['title_part_list'].append(part_to_pattern(title))
        else:
            pattern_str_parts['maybe_title_part_list'].append(part_to_pattern(part))
    return pattern_str_parts

def extract_significant_parts(title_str):
    pass

def detect_journal_name_by_url(url):
    return ''

def compare_list_by_elements(first_lst, second_lst):
    comparation_result = False
    first_lst_len = len(first_lst)
    if first_lst_len > 0 and first_lst_len <= len(second_lst):
        temp_lst = second_lst[0:first_lst_len]
        comparation_result = ([True] == list(set([item[0] == item[1] for item in zip(first_lst, temp_lst)])))
    return comparation_result
    #return set(first_lst).issubset(set(second_lst))

def clear_list(lst):
    return [item for item in lst if item not in [',', ':', u'\u2026', 'th'] and item.isdigit() != True]

def replace_token_by_alternative(lst, token, alternative):
    alternative_lst = []
    for item in lst:
        if item != token:
            alternative_lst.append(item)
        else:
            alternative_lst.append(alternative)
    return alternative_lst

def prepare_list_to_comparation(lst):
    cleared_lst = clear_list(lst)
    prepared_list_of_lists = [cleared_lst]
    if 'and' in cleared_lst and not ('&' in cleared_lst):
        alternative_cleared_lst = replace_token_by_alternative(cleared_lst, 'and', '&')
        prepared_list_of_lists.append(alternative_cleared_lst)
    elif '&' in cleared_lst and not ('and' in cleared_lst):
        alternative_cleared_lst = replace_token_by_alternative(cleared_lst, '&', 'and')
        prepared_list_of_lists.append(alternative_cleared_lst)
    return prepared_list_of_lists

def deep_name_comparation(pattern_list, found_journals_list):
    list_to_comparation = prepare_list_to_comparation(db_search_pattern['title_part_list'][0]['token_list'])
    journals = []
    for journal in found_journals_list:
        title_part_tokens = clear_list(journal['tokenized_title'])
        compare_result = list(set([compare_list_by_elements(comparation_tokens, title_part_tokens) for comparation_tokens in list_to_comparation]))
        if True in compare_result:
            journals.append(journal)
    return journals

def find_corresponding_journals_by_name_parts(db_search_pattern, journals_collection):
    journals = []
    find_pattern_list = db_search_pattern['title_part_list']
    if find_pattern_list != []:
        found_journals_list = journals_collection.find({'tokenized_title' : {'$all' : find_pattern_list[0]['find_pattern_token_list'], '$options' : 'i'}})

        journals = [item for item in found_journals_list]

        '''
        count_found_journals = found_journals_list.count()
        if count_found_journals == 1:
            jornals = found_journals_list
        elif count_found_journals > 1:
            journals = deep_name_comparation(db_search_pattern, found_journals_list)
            '''


        '''
        f.write('%s\n' % title_str)
        for journal in find_journals_list:
            f.write('%s\n' % journal['title'])
        f.write('\n')
        '''
    else:
        pass

    return journals



if __name__ == "__main__":

    headers = {'User-Agent': 'Mozilla/5.0 (X11; Linux i686; rv:10.0.7) Gecko/20100101 Firefox/10.0.7 Iceweasel/10.0.7'}

    mongo = pymongo.Connection('127.0.0.1')
    impact_db = mongo['impact']
    
    citations_collection = impact_db['citations']
    journals_collection = impact_db['journals']
    f = codecs.open('journals_match.txt', 'w', encoding='utf-8')
    citations = citations_collection.find()
    title_names_regex = re.compile('^(?P<title>.+)[,$]')
    dashes_count = 0
    identified_journals = 0
    not_exist_journal_names = 0
    many_corresponding_journals = 0
    for citation in citations:
        title_str = citation['article_journal'].replace('\'', '')
        #f.write('%s\n' % title_str)
        if title_str.find(' - ') != -1:
            dashes_count = dashes_count + 1
            db_search_pattern = extract_title_search_pattern(title_str, title_names_regex)
            corresponding_journals_list = find_corresponding_journals_by_name_parts(db_search_pattern, journals_collection)
            '''
            find_pattern_list = db_search_pattern['title_part_list']
            if find_pattern_list != []:
                find_journals_list = journals_collection.find({'tokenized_title' : {'$all' : find_pattern_list[0]['find_pattern_token_list']}})
                f.write('%s\n' % title_str)
                for journal in find_journals_list:
                    f.write('%s\n' % journal['title'])
                f.write('\n')
                '''
            
            if len(corresponding_journals_list) == 1:
                identified_journals = identified_journals + 1
            elif len(corresponding_journals_list) > 1:
                many_corresponding_journals = many_corresponding_journals + 1
            else:
                not_exist_journal_names = not_exist_journal_names + 1
        else:
            print title_str
        #f.write('\n\n')
    f.close()

    print 'Citaions total: ', citations_collection.count(), ' Not exist journal names: ', not_exist_journal_names,  ' Identified journals: ', identified_journals, ' Many corresponding journals: ', many_corresponding_journals, ' Dashes total: ', dashes_count
    
