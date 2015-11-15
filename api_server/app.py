# -*- coding: utf-8 -*-
import time
import json
import urllib
import pylibmc
import hashlib
from flask import Flask
import numpy as np
from crawl import Crawler
from cluster import Clusterer
from collections import Counter
from morphs import MorphAnalyzer
from collections import defaultdict
from extract import OpinionExtractor
from sentiment import SentimentTagger
from recommend import ProductRecommender

initialize_begin = time.time()

crawler = Crawler()
app = Flask(__name__)
parser = MorphAnalyzer()
tagger = SentimentTagger('crf/crf.model')
clusterer = Clusterer('word2vec/clean.partial.6pos.w3.m10.model')
extractor = OpinionExtractor('word2vec/clean.partial.6pos.w3.m10.model')
recommender = ProductRecommender('word2vec/clean.partial.6pos.w3.m10.model', tagger, extractor, clusterer)

"""
with open('./data/results.list.json', 'r') as f:
    crawled_items = json.loads(f.read())
with open('./data/categories.json', 'r') as f:
    crawled_categories = json.loads(f.read())
"""
crawled_items = []
crawled_categories = []

memo_item = pylibmc.Client(['127.0.0.1'], binary=True, behaviors={'tcp_nodelay': True, 'ketama': True})

print 'API Ready! Elapsed: %d' % (time.time() - initialize_begin)
from flask import make_response, request, current_app
from functools import update_wrapper
from datetime import timedelta


def crossdomain(origin = None, methods = None, headers = None, max_age = 21600,\
                attach_to_all = True, automatic_options = True):
    if methods is not None:
        methods = ', '.join(sorted((x.upper() for x in methods)))
    if headers is not None and not isinstance(headers, basestring):
        headers = ', '.join((x.upper() for x in headers))
    if not isinstance(origin, basestring):
        origin = ', '.join(origin)
    if isinstance(max_age, timedelta):
        max_age = max_age.total_seconds()

    def get_methods():
        if methods is not None:
            return methods
        options_resp = current_app.make_default_options_response()
        return options_resp.headers['allow']

    def decorator(f):

        def wrapped_function(*args, **kwargs):
            if automatic_options and request.method == 'OPTIONS':
                resp = current_app.make_default_options_response()
            else:
                resp = make_response(f(*args, **kwargs))
            if not attach_to_all and request.method != 'OPTIONS':
                return resp
            h = resp.headers
            h['Access-Control-Allow-Origin'] = origin
            h['Access-Control-Allow-Methods'] = get_methods()
            h['Access-Control-Max-Age'] = str(max_age)
            if headers is not None:
                h['Access-Control-Allow-Headers'] = headers
            return resp

        f.provide_automatic_options = False
        return update_wrapper(wrapped_function, f)

    return decorator


def get_prod_info(id, is_refresh = False, debug = True):
    if not is_refresh and memo_item.get(str(id)) is not None:
        return memo_item[str(id)]
    raw = crawler.get_item_reviews(id, verbose=debug)
    parsed = parser.parse_reviews(raw, verbose=debug)
    tagged = tagger.label_sentence_multi(parsed)
    memo_item[str(id)] = {'name': crawler.get_prod_name(id),
                          'raw': raw,
                          'tagged': tagged}
    return memo_item[str(id)]


def preprocess_info(info):
    
    if info.get('filtered_data') is None:
        idx = 0
        reviews = info['tagged']
        info['filtered_data'] = []
        for r in reviews:
            info['filtered_data'].append(extractor.pos_analyzer(r, idx, mark=True))
            idx += 1
            
        extractor.deep_filter_data(info['filtered_data'])


    if info.get('cluster_dict') is None or\
       info.get('prop_dict') is None or\
       info.get('aprop') is None:
        info['cluster_dict'],\
        info['prop_dict'],\
        info['aprop'] = clusterer.cluster_prop(info['filtered_data'])


    if info.get('props') is None or\
       info.get('summary') is None or\
       info.get('prop_cnt') is None:

        info['summary'] = {'stat': {'positive': 0.0,
                                   'negative': 0.0},
                           'attributes': []}
        info['props'],\
        info['prop_cnt'] = extractor.score_cluster(info['summary'], info['cluster_dict'], info['prop_dict'])




@app.route('/v1/products/<int:id>/summary')
@crossdomain(origin='*')
def get_summary(id):
    info = get_prod_info(id)

    preprocess_info(info)

    return json.dumps(info['summary'])


def parse_querystring(text):
    ret = {}
    items = text.split('&')
    for item in items:
        t = item.split('=')
        ret[urllib.unquote(t[0])] = urllib.unquote(t[1])

    return ret


@app.route('/v1/products/<int:id>/reviews')
@crossdomain(origin='*')
def get_reviews(id):
    """Parse arguments."""
    arguments = parse_querystring(request.query_string)
    arguments['limit'] = int(arguments['limit'])
    arguments['skip'] = int(arguments['skip'])

    try:
        every_property = False
        arguments['where'] = json.loads(arguments['where'])
        if arguments['where'].get('attributes') is None or len(arguments['where']['attributes']) == 0:
            every_property = True
    except:
        every_property = True

    info = get_prod_info(id)
    preprocess_info(info)

    if every_property:
        props = info['props']
    else:
        props = arguments['where']['attributes']

    print " ".join(props)

    result = extractor.get_reviews(info['filtered_data'], info['prop_dict'], props, arguments['limit'], arguments['skip'])

    return json.dumps(result)


def get_category_item_cached(category):
    return [ x for x in crawled_items if x['category'] == category and x['price'].strip() != u'\ud310\ub9e4\uc911\ub2e8' ]


@app.route('/v1/categories')
@crossdomain(origin='*')
def get_category_list():
    return json.dumps(crawled_categories)


@app.route('/v1/category/<int:id>/properties')
@crossdomain(origin='*')
def get_property_list(id, is_refresh = False):
    if not is_refresh and memo_item.get('cat' + str(id)) is not None:
        return memo_item['cat' + str(id)]
    ret = json.dumps(recommender.get_prop_list(get_category_item_cached(unicode(id))))
    memo_item['cat' + str(id)] = ret
    return memo_item['cat' + str(id)]


@app.route('/v1/recommendations')
@crossdomain(origin='*')
def get_recommendation(is_refresh = False):
    """Parse arguments."""
    args_key = hashlib.sha256(request.query_string).hexdigest()

    if not is_refresh and memo_item.get(args_key) is not None:
        return memo_item[args_key]

    arguments = parse_querystring(request.query_string)
    arguments['where'] = json.loads(arguments['where'])

    category = arguments['where']['category']
    attributes = arguments['where']['attributes']

    memo_item[args_key] = json.dumps(recommender.get_recommended(get_category_item_cached(category), attributes))
    return memo_item[args_key]


@app.route('/v1/product/<int:id>/evalution', methods=['POST', 'OPTIONS'])
@crossdomain(origin='*', methods=['POST', 'OPTIONS'])
def get_summary_of_custom_review(id):
    c_review = [request.form['review']]
    c_parsed = parser.parse_reviews(c_review, verbose=True)
    c_tagged = tagger.label_sentence_multi(c_parsed)
    info = get_prod_info(id)
    product_review = {'stat': {
                            'positive': 0.0,
                            'negative': 0.0
                      },
                      'attributes': []}

    reviews = info['tagged']

    filtered_data = [extractor.pos_analyzer(c_tagged[0], 0, mark=True)]
    for r in reviews:
        filtered_data.append(extractor.pos_analyzer(r, 0, mark=False))

    extractor.deep_filter_data(filtered_data)
    cluster_dict, prop_dict, aprop = clusterer.cluster_prop(filtered_data)
    props, prop_cnt = extractor.score_cluster(product_review, cluster_dict, prop_dict)

    return json.dumps(product_review)


def run_server():
    app.run(host='0.0.0.0', debug=True)


if __name__ == '__main__':
    run_server()
