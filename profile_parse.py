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
from time import sleep

def web_get_html(url, headers):
    req = requests.get(url, headers=headers)
    return req.text

def save_html(html, filename):
    success = True
    f = codecs.open(filename, 'w', encoding='utf-8')
    f.write(html)
    f.close
    return success

def get_html(filename):
    f = codecs.open(filename, 'r', encoding='utf-8')
    html = f.read()
    f.close()
    return html

def get_profile_next_ref(tree):
    next_ref = None
    #prev_next_items = tree.xpath('//form[@id="citationsForm"]/div[@class="g-section cit-dgb"]/div/table/tr/td/a[@class="cit-dark-link"]')
    prev_next_items = tree.xpath('//a[@class="cit-dark-link"]')
    for item in prev_next_items:
        if 'Next' in item.text:
            next_ref = item.attrib['href']
            break
    return next_ref


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

def get_cited_articles(url, articles_description):
    html = get_html('kaibyshev-profile-citations-python.html')
    #html = get_html('kaibyshev-profile-citations-nonempty.html')
    #html = get_html('kaibyshev-profile-citations-last.html')
    parser = etree.HTMLParser(remove_blank_text=True)
    tree = etree.parse(StringIO(html), parser)
    cit_table_list = tree.xpath('//table[@class="cit-table"]')
    cit_table = cit_table_list[0]
    next_descriptions_portion = get_articles_description(cit_table)
    cited_articles_description = [article_description for article_description in next_descriptions_portion if article_description['citations_url'] != None]
    articles_description.extend(cited_articles_description)
    if len(next_descriptions_portion) == len(cited_articles_description):
        next_ref = get_profile_next_ref(tree)
        print next_ref
        if next_ref != None:
            #articles_description = get_cited_articles(next_ref, articles_description)
            print 'Is next page'
        else:
            print 'None next page'
    else:
        print 'Not all articles is cited'

    return articles_description


if __name__ == "__main__":

    headers = {'User-Agent': 'Mozilla/5.0 (X11; Linux i686; rv:10.0.7) Gecko/20100101 Firefox/10.0.7 Iceweasel/10.0.7'}

    #url = 'http://scholar.google.com/citations?user=jls0BsYAAAAJ&hl=en&oi=ao'
    #url = 'http://scholar.google.com/citations?hl=en&user=jls0BsYAAAAJ&pagesize=100&view_op=list_works&cstart=100'
    url = 'http://scholar.google.com/citations?hl=en&user=jls0BsYAAAAJ&pagesize=100&view_op=list_works&cstart=300'
    html = web_get_html(url, headers)
    save_html(html, 'kaibyshev-profile-citations-last.html')

    #html = get_html('kaibyshev-profile-citations-python.html')

    #print get_cited_articles(url, [])
    get_cited_articles(url, [])
