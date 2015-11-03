#!/usr/bin/env python
# -*- coding: utf-8 -*-
import time
import json
import pylibmc
import numpy as np
from flask import Flask
from crawl import Crawler
from cluster import Clusterer
from collections import Counter
from morphs import MorphAnalyzer
from collections import defaultdict
from extract import OpinionExtractor
from sentiment import SentimentTagger


crawler = Crawler()
app = Flask(__name__)
parser = MorphAnalyzer()
tagger = SentimentTagger('crf/crf.model')
clusterer = Clusterer('word2vec/clean.partial.6pos.w3.m10.model')
extractor = OpinionExtractor('word2vec/clean.partial.6pos.w3.m10.model')

'Simple Cache Implementation *Possibility of improvement exists*'
memo_item = pylibmc.Client(['127.0.0.1'],
                           binary=True,
                           behaviors={'tcp_nodelay':True, 'ketama':True})


from datetime import timedelta
from flask import make_response, request, current_app
from functools import update_wrapper


def crossdomain(origin=None, methods=None, headers=None,
                max_age=21600, attach_to_all=True,
                automatic_options=True):
    if methods is not None:
        methods = ', '.join(sorted(x.upper() for x in methods))

    if headers is not None and not isinstance(headers, basestring):
        headers = ', '.join(x.upper() for x in headers)

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


def get_prod_info(id, is_refresh=False, debug=True):
    if not is_refresh and memo_item.get(str(id)) is not None:
        return memo_item[str(id)]
    
    raw = crawler.get_item_reviews(id, verbose=debug)
    parsed = parser.parse_reviews(raw, verbose=debug)

    props = np.hstack([extractor.find_props(x) for x in parsed])
    model, visual = clusterer.cluster_props(props)
    cdict = clusterer.cluster_as_dict(model, visual)
    centroids = clusterer.get_centroid(cdict)
    rank_by_expr = [(key, extractor.score_cluster_rev_2(cdict[key], centroids, parsed))\
                    for key in cdict.keys()]
    rank_by_expr = sorted(rank_by_expr, key=lambda x:x[1], reverse=True)

    tagged = tagger.label_sentence_multi(parsed)

    memo_item[str(id)] = {
            'name': crawler.get_prod_name(id),

            'raw': raw,
            'tagged': tagged,

            'centroids': centroids,
            'cluster': model,
            'cscore': rank_by_expr,
            'cdict': cdict,

            'review_summary': extractor.get_summarized_reviews(model, tagged)
    }

    return memo_item[str(id)]

@app.route('/v1/products/<int:id>/summary')
@crossdomain(origin='*')
def get_summary(id):
    info = get_prod_info(id)

    ret = {
        "attributes": []
    }


    total_clusters = len(info['cdict'].keys())
    total_props = float(np.sum([len(info['cdict'][x]) for x in info['cdict'].keys()]))

    for key in info['cdict'].keys():
        if info['cscore'][key] < 20 and total_clusters > 11:
            continue

        attr = {
            'name': info['centroids'][key],
            'rate': float(len(info['cdict'][key])) / total_props,
            'negative': {
                'stat': 0.0,
                'reviews': [x[0] for x in info['review_summary'][key] if x[1] == 'N']
            },
            'positive': {
                'stat': 0.0,
                'reviews': [x[0] for x in info['review_summary'][key] if x[1] == 'P']
            }
        }
        
        n_p = len(attr['positive']['reviews'])
        n_n = len(attr['negative']['reviews'])
        n_tot = len(info['review_summary'][key])

        attr['negative']['stat'] = float(n_n) / float(max(1, n_tot))
        attr['positive']['stat'] = float(n_p) / float(max(1, n_tot))
        
        ret['attributes'].append(attr)

    return json.dumps(ret)


@app.route('/v1/products/<int:id>/reviews')
@crossdomain(origin='*')
def get_reviews(id):
    info = get_prod_info(id)

    meaningful = set()

    for key in info['cdict'].keys():
        if info['cscore'][key] < 20 and total_clusters > 11:
            continue
        meaningful.add(key)

    ret = []

    for review in info['tagged']:
        res = {
            'attributes': [],
            'content': None
        }
        cont = []
        emphasis = extractor.find_props_with_exprs_tagged_idx(review)
        ptr = 0; eptr = 0
        while ptr < len(review):
            if eptr < len(emphasis) and ptr == emphasis[eptr][0]:
                is_pos = review[emphasis[eptr][2]][1] == 'P'
                is_neg = review[emphasis[eptr][2]][1] == 'N'
                if is_pos:
                    cont.append('<stat-pos>')
                if is_neg:
                    cont.append('<stat-neg>')
                ptr = emphasis[eptr][1]
                cont += ["".join(x[0].split('/')[:-1]) for x in review[emphasis[eptr][0]:ptr+1]]
                try:
                    c = clusterer.predict(info['cluster'], review[emphasis[eptr][0]])
                    res['attributes'].append(info['centroids'][c])
                except:
                    res['attributes'].append("".join(review[emphasis[eptr][0]][0].split('/')[:-1]))
                if is_pos:
                    cont.append('</stat-pos>')
                if is_neg:
                    cont.append('</stat-neg>')
                eptr += 1
            else:
                cont.append("".join(review[ptr][0].split('/')[:-1]))
            ptr += 1
        res['attributes'] = list(set(res['attributes']))
        res['content'] = " ".join(cont)
        ret.append(res)

    return json.dumps(ret)


def run_server():
    app.run(host='0.0.0.0')


if __name__ == '__main__':
    run_server()
