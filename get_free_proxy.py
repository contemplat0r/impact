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

def web_get_html(url, headers):
    req = requests.get(url, headers=headers)
    return req.text

def save_html(html, filename):
    success = True
    f = codecs.open(filename, 'w', encoding='utf-8')
    f.write(html)
    f.close()
    return success

def get_html(filename):
    f = codecs.open(filename, 'r', encoding='utf-8')
    html = f.read()
    f.close()
    return html

def parse_style_container(style_container):
    abbreviations = list()
    if style_container != [] and style_container[0].text != '':
        style_strings = style_container[0].text.splitlines()
        if style_strings != []:
            for style_str in style_strings:
                #if 'inline' in style_str:
                if 'none' in style_str:
                    abbreviations.append(style_str[1:style_str.find('{')])
    return abbreviations

def parse_proxy_ip(ip_column):
    none_abbreviation_lst = parse_style_container(ip_column.xpath('span/style'))
    ip_string = str()
    for ip_container in ip_column.xpath('span'):
        child_lst = [child for child in ip_container.getchildren()]
        for child in child_lst:
            attrib_value_lst = child.attrib.values()
            if attrib_value_lst != []:
                attrib_value = attrib_value_lst[0]
                if 'none' not in attrib_value and attrib_value not in none_abbreviation_lst:
                    ip_string = ip_string + child.text.strip()
            if child.tail != None:
                ip_string = ip_string + child.tail.strip()
        #print ip_string, '\n'
        return ip_string


#def parse_proxy_table(html):
def parse_proxy_table(tree):
    proxy_list = list()
    #parser = etree.HTMLParser(remove_blank_text=True)
    #tree = etree.parse(StringIO(html), parser)
    proxy_table = tree.xpath('//table[@id="listtable"]')[0]
    #print proxy_table
    #save_html(etree.tostring(proxy_table, pretty_print=True), 'proxy_table.html')
    for row in proxy_table.xpath('tr'):
        proxy_entry = dict()
        column_lst = row.xpath('td')
        if column_lst != [] and len(column_lst) > 1:
            proxy_entry['fresh'] = column_lst[0].xpath('span')[0].text.strip()
            proxy_entry['ip'] = parse_proxy_ip(column_lst[1])
            proxy_entry['port'] = column_lst[2].text.strip()
            proxy_entry['country'] = column_lst[3].xpath('span[@class="country"]/img')[0].tail
            response_speed_container = column_lst[4].xpath('div[@class="speedbar response_time"]/div')[0].attrib['style']
            proxy_entry['response_speed'] = response_speed_container[6:response_speed_container.find('%')]
            connection_time_container = column_lst[5].xpath('div[@class="speedbar connection_time"]/div')[0].attrib['style']
            proxy_entry['connection_time'] = connection_time_container[6:connection_time_container.find('%')]
            proxy_entry['proto'] = column_lst[6].text.strip()
            proxy_entry['security'] = column_lst[7].text.strip()
            proxy_list.append(proxy_entry)
    return proxy_list
           

def next_page_url(


if __name__ == '__main__':

    headers = {'User-Agent': 'Mozilla/5.0 (X11; Linux i686; rv:10.0.7) Gecko/20100101 Firefox/10.0.7 Iceweasel/10.0.7'}
    
    #html = web_get_html('http://hidemyass.com/proxy-list/', headers)
    #save_html(html, 'free_proxy_list.html')
    html = get_html('free_proxy_list.html')
    parser = etree.HTMLParser(remove_blank_text=True)
    tree = etree.parse(StringIO(html), parser)
    #proxy_list = parse_proxy_table(html)
    proxy_list = parse_proxy_table(tree)
    print proxy_list
  
