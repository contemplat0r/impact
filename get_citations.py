# -*- coding: utf8 -*- 

from lxml import etree
from StringIO import StringIO
from copy import deepcopy
import os
#import glob
import requests
import pickle
#import difflib
import codecs
from random import randint
from time import sleep, time
import pymongo


scholar_base_url = 'http://scholar.google.com'
min_sleep_time = 60
max_sleep_time = 240

def timed(f):
    @wraps(f)
    def wrapper(*args, **kwds):
        start = time()
        result = f(*args, **kwds)
        elapsed = time() - start
        print "%s took %d time to finish" % (f.__name__, elapsed)
        return result
    return wrapper

def web_get_html(url, headers):
    req = requests.get(url, headers=headers)
    return req.text

def save_html(html, filename):
    success = True
    f = codecs.open(filename, 'w', encoding='utf-8')
    f.write(html)
    f.close()
    return success

def prepare_scholar_url(name, second_name):
    return 'http://scholar.google.com/scholar?as_q=&as_epq=&as_oq=&as_eq=&as_occt=any&as_sauthors=\"' + name + '+' + second_name +'\"&as_publication=&as_ylo=&as_yhi=&hl=en&as_sdt=0%2C5'

def get_html(filename):
    f = codecs.open(filename, 'r', encoding='utf-8')
    html = f.read()
    f.close()
    return html

def get_articles_description(articles_container):
    articles_description = []
    article_html_item_list = articles_container.xpath('tr[@class="cit-table item"]')
    if article_html_item_list != []:
        for article_html_item in article_html_item_list:
            article = {'name' : None, 'journal' : None, 'citations_url' : None, 'cited_by' : None}
            article_info_container = article_html_item.xpath('td[@id="col-title"]')[0]
            article_name_list = article_info_container.xpath('a[@class="cit-dark-large-link"]')
            if article_name_list != []:
                article['name'] = article_name_list[0].text
            else:
                pass
                #article_name_list = gs_ri.xpath('h3[@class="gs_rt"]')
                #article['name'] = article_name_list[0].xpath('span')[-1].tail
            article_info_list = article_info_container.xpath('span[@class="cit-gray"]')
            if len(article_info_list) == 2:
                article['journal'] = article_info_list[1].text
            article_citedby_container_list = article_html_item.xpath('td[@id="col-citedby"]/a[@class="cit-dark-link"]')
            if article_citedby_container_list != []:
                article_citedby_container = article_html_item.xpath('td[@id="col-citedby"]/a[@class="cit-dark-link"]')[0]
                article['citations_url'] = article_citedby_container.attrib['href']
                article['cited_by'] = article_citedby_container.text
            articles_description.append(article)
    return articles_description

def get_profile_next_ref(tree):
    next_ref = None
    prev_next_items = tree.xpath('//a[@class="cit-dark-link"]')
    for item in prev_next_items:
        if 'Next' in item.text:
            next_ref = item.attrib['href']
            break
    return next_ref

def get_next_ref(gs_ccl_div):
    td_tags = gs_ccl_div.xpath('div[@id="gs_n"]/center/table/tr/td')
    next_ref = None
    for td in td_tags:
        a_tags = td.xpath('a')
        for a_tag in a_tags:
            b_tags = a_tag.xpath('b')
            if b_tags != [] and b_tags[0].text == 'Next':
                next_ref =  a_tag.attrib.values().pop()
    return next_ref

def get_cited_articles(url, articles_description):
    html = web_get_html(url, headers)
    parser = etree.HTMLParser(remove_blank_text=True)
    tree = etree.parse(StringIO(html), parser)
    cit_table_list = tree.xpath('//table[@class="cit-table"]')
    cit_table = cit_table_list[0]
    next_descriptions_portion = get_articles_description(cit_table)
    cited_articles_description = [article_description for article_description in next_descriptions_portion if article_description['citations_url'] != None]
    articles_description.extend(cited_articles_description)
    if len(next_descriptions_portion) == len(cited_articles_description):
        next_ref = get_profile_next_ref(tree)
        if next_ref != None:
            print 'Is next page'
            sleep_time = randint(min_sleep_time, max_sleep_time)
            print 'Sleep: ', sleep_time
            sleep(sleep_time)
            print 'Go to next iteration...'
            articles_description = get_cited_articles(scholar_base_url + next_ref, articles_description)
        else:
            print 'None next page'
    else:
        print 'Not all articles is cited'
    return articles_description

def parse_citations_html(tree, parser):
    citations_description = []
    for gs_r in tree.xpath('//div[@class="gs_r"]'):
        citation = {}
        article_name_list = gs_r.xpath('div[@class="gs_ri"]/h3[@class="gs_rt"]/a')
        if article_name_list != []:
            citation['article_name'] = article_name_list[0].text
            citation['article_url'] = article_name_list[0].attrib['href']
        article_journal_list = gs_r.xpath('div[@class="gs_ri"]/div[@class="gs_a"]')
        if article_journal_list != []:
            article_journal = article_journal_list[0]
            if article_journal.text != None:
                citation['article_journal'] = article_journal.text
            else:
                citation['article_journal'] = None
            a_tags = article_journal.xpath('a')
            for a_tag in a_tags:
                if a_tag.text != None:
                    if citation['article_journal'] != None:
                        citation['article_journal'] = citation['article_journal'] + ' ' + a_tag.text
                    else:
                        citation['article_journal'] = a_tag.text
                if a_tag.tail != None:
                    if citation['article_journal'] != None:
                        citation['article_journal'] = citation['article_journal'] + ' ' + a_tag.tail
                    else:
                        citation['article_journal'] = a_tag.tail
        cited_by_list = gs_r.xpath('div[@class="gs_ri"]/div[@class="gs_fl"]/a')
        if cited_by_list != []:
            citations_url = cited_by_list[0].attrib['href']
            citation['citations_url'] = citations_url
            citation['cited_articles'] = []
        citations_description.append(citation)
    return citations_description

def get_all_article_citations(url, article_citations_description, recurse_depth, citations_collection, cited_article_id):
    recurse_depth = recurse_depth + 1
    print 'Recurse depth: ', recurse_depth
    html = web_get_html(url, headers)
    parser = etree.HTMLParser(remove_blank_text=True)
    tree = etree.parse(StringIO(html), parser)
    citations_container_list = tree.xpath('//div[@id="gs_ccl"]')
    citations_container = citations_container_list[0]
    citations_description = parse_citations_html(citations_container, parser)
    if citations_description != []:
        for citation in citations_description:
            citation['cited_articles'].append(cited_article_id)
        article_citations_description.append(citations_description)
        citations_collection.insert(citations_description)
    next_ref = get_next_ref(citations_container)
    if next_ref != None:
        print 'Is next page'
        sleep_time = randint(min_sleep_time, max_sleep_time)
        print 'Sleep: ', sleep_time
        sleep(sleep_time)
        print 'Go to next iteration...'
        print scholar_base_url + next_ref
        article_citations_description = get_all_article_citations(scholar_base_url + next_ref, article_citations_description, recurse_depth, citations_collection, cited_article_id)
    return article_citations_description

def get_all_author_citations(articles_description, citations_collection):
    #i = 1
    #for article in articles_description:
    for i in range(20, 30):
        if os.path.isfile('stop'):
            print 'Stop'
            exit()
        else:
            article = articles_description[i]
            print 'Article: ', i + 1
            url = article['citations_url']
            article_citations_description = get_all_article_citations(url, [], 0, citations_collection, article['_id'])
            article['cited_by'] = article_citations_description
            i = i + 1
    return articles_description


def get_journal_list(journal_html, parser):
    tree = etree.parse(StringIO(journal_html), parser)
    journals_table = tree.xpath('//table[@class="tabla_datos"]/tbody')[0]
    table_rows = journals_table.xpath('tr')
    return [{'title' : row[1].text, 'ISSN' : row[2].text, 'hindex' : row[4].text, 'cites_doc_2years' : row[10].text, 'url' : ''} for row in table_rows]

def init_journal_collection(journals_collection, journal_list):
    journals_collection.remove()
    journals_collection.insert(journal_list)

def init_articles_collection(articles_collection, articles_list):
    articles_collection.remove()
    articles_collection.insert(articles_list)
  

def save_articles_description(articles_description, filename):
    out = open(filename, 'w')
    pickle.dump(articles_description, out)
    out.close()

def get_saved_articles_description(filename):
    articles_description = None
    if os.stat(filename)[6] > 0:
        finput = open(filename, 'r')
        articles_description = pickle.load(finput)
        finput.close()
    return articles_description

def get_articles_collection(articles_collection):
    return articles_collection.find()

def save_aggregate(aggregate, filename):
    out = open(filename, 'w')
    pickle.dump(aggregate, out)
    out.close()

if __name__ == "__main__":

    headers = {'User-Agent': 'Mozilla/5.0 (X11; Linux i686; rv:10.0.7) Gecko/20100101 Firefox/10.0.7 Iceweasel/10.0.7'}

    '''
    url = 'http://scholar.google.com/citations?hl=en&user=jls0BsYAAAAJ&view_op=list_works&pagesize=100'
    articles_description = get_cited_articles(url, [])
    #articles_description = get_cited_articles(url)
    save_articles_description(articles_description, 'articles_description')
    '''

    ## Тестирования получения списка статей (Пока одна страница без следования по ссылкам на следующие
    ## пока не будет отработано преодоление защиты от поисковых роботов)
    '''
    url = 'http://scholar.google.com/scholar?start=50&q=author:%22Victor+Galitski%22&hl=en&as_sdt=0,5'
    html = web_get_html(url, headers)
    save_html(html, 'galitski-1.html')
    '''
    
    # Получение списка цитат по каждой статье (Пока одна страница).
    #complete_citations_url = scholar_base_url + articles_description[0]['citations_url']
    '''
    complete_citations_url = 'http://scholar.google.com/scholar?start=10&hl=en&as_sdt=0,5&sciodt=0,5&cites=8912105725057096399&scipsc='
    citations_html = web_get_html(complete_citations_url, headers=headers)
    save_html(citations_html, 'citations-empty-next.html')
    '''
    
    mongo = pymongo.Connection('127.0.0.1')
    impact_db = mongo['impact']

    # Получение списка журналов из scimago
    '''
    journal_html = get_html('excel.html')
    parser = etree.HTMLParser(remove_blank_text=True)
    journal_list = get_journal_list(journal_html, parser)
    #for journal in journal_list:
    #    print journal['title'], ' ', journal['ISSN'], ' ', journal['hindex'], ' ', journal['cites_doc_2years']
    journals_collection = impact_db['journals']
    init_journal_collection(journals_collection, journal_list)
    '''

    # Получение полного списка цитирования каждой статьи автора, и присоединение данного списка
    # к описанию статьи.
    #articles_description = get_saved_articles_description('articles_description')
    '''
    articles_description = get_articles_collection(impact_db['articles'])
    first_article_id = articles_description[0]['_id']
    print first_article_id
    citations_collection.update({}, {'$set' : {'cited_articles' : first_article_id}}, False, True)
    '''

    '''
    for article in articles_description:
        article['author_id'] = ['519e4d024e4decfa77abd881']
    articles_collection = impact_db['articles']
    init_articles_collection(articles_collection, articles_description)
    '''
    articles_collection = impact_db['articles']
    articles_description = articles_collection.find()
    '''
    for article in articles_description:
        print article
        '''

    start_time = time()
    citations_collection = impact_db['citations']
    articles_description = get_all_author_citations(articles_description, citations_collection)
    print time() - start_time, 'sec'
    #save_articles_description(articles_description, 'articles_description_with_citations')

