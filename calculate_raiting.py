# -*- coding: utf8 -*- 

import re
import pymongo


if __name__ == "__main__":

    mongo = pymongo.Connection('127.0.0.1')
    impact_db = mongo['impact']
    articles_collection = impact_db['articles']
    journals_collection = impact_db['journals']
    citations_collection = impact_db['citations']

    articles_cursor = articles_collection.find()

    articles_list = [article for article in articles_cursor if 'journal_id' in article.keys()]
    
    raiting = 0
    for article in articles_list:
        article_id = article['_id']
        article_raiting = float(journals_collection.find({'_id' : article['journal_id']})[0]['cites_doc_2years'].replace(',', '.'))
        article_raiting = article_raiting + 1
        #citations_cursor = citations_collection.find({'cited_articles' : {'$in' : [article_id]}})
        citations_cursor = citations_collection.find({'cited_articles' : [article_id]})
        citations_list = [citation for citation in citations_cursor if 'journal_id' in citation.keys()]

        citations_raiting_list = []
        for citation in citations_list:
            citation_raiting = float(journals_collection.find({'_id' : citation['journal_id']})[0]['cites_doc_2years'].replace(',', '.'))
            citations_raiting_list.append(citation_raiting)
        raiting = raiting + article_raiting * sum(citations_raiting_list)

    print raiting




