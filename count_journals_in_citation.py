# -*- coding: utf8 -*- 

import re
import pymongo
import codecs
import urlparse
import requests
from nltk import word_tokenize

if __name__ == "__main__":


    mongo = pymongo.Connection('127.0.0.1')
    impact_db = mongo['impact']
    
    journals_collection = impact_db['journals']
    citations_collection = impact_db['citations']
    articles_collection = impact_db['articles']

    citations_cursor = citations_collection.find()
    articles_cursor = articles_collection.find()

    cits_with_recognized_journals = [cit for cit in citations_cursor if 'journal_id' in cit.keys()]
    articles_with_recognized_journals = [a for a in articles_cursor if 'journal_id' in a.keys()]
    print len(cits_with_recognized_journals)
    print len(articles_with_recognized_journals)

