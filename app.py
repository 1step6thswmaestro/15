#!/usr/bin/env python
# -*- coding: utf-8 -*-
import json
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
clusterer = Clusterer('word2vec/clean.partial.6pos.w3.m10.model')
parser = MorphAnalyzer()
tagger = SentimentTagger('crf/crf.model')
extractor = OpinionExtractor()
app = Flask(__name__)


memo_item = {}
def fetch_reviews(id):
    if memo_item.get(id) is not None:
        return memo_item[id]
    
    raw = crawler.get_item_reviews(id)
    parsed = parser.parse_reviews(raw)
    props = np.hstack([extractor.find_props(x) for x in parsed])
    model, visual = clusterer.cluster_props(props)
    cdict = clusterer.cluster_as_dict(model, visual)
    rank_by_expr = sorted([(key, extractor.score_cluster_expr(cdict[key], parsed)) for key in cdict.keys()],
                          key=lambda x:x[1], reverse=True)
    tagged = tagger.label_sentence_multi(parsed)
    centroids = {}
    for key in cdict.keys():
        s = Counter(cdict[key]).most_common(2)
        centroid = s[0][0]
        if s[0][1] == s[-1][1] or s[0][1] < 3:
            centroid = sorted([(x, clusterer.count_occurrence(x)) for x in cdict[key]],
                              key=lambda x: x[1], reverse=True)[0][0]
        centroids[key] = "".join(centroid.split('/')[:-1])

    memo_item[id] = (
        tagged, model, cdict, rank_by_expr, centroids
    )

    return memo_item[id]


@app.route('/v1/products/<int:id>/summary')
def get_summary(id):
    tagged, model, cdict, rank_by_expr, centroids = fetch_reviews(id)

    result = []
    for line in tagged:
        result.append(extractor.find_props_with_exprs_tagged(line))

    meaningful = set([x[0] for x in filter(lambda x:x[1]>2, rank_by_expr)])
    tmp = defaultdict(list)

    for _ in result:
        for line in _:
            try:
                c = clusterer.predict(model, line[0][0])
                if c in meaningful:
                    tmp[c].append((line[0][0], line))
            except:
                pass

    total = np.sum([len(x) for x in tmp.values()])
    stat = {
        "attributes": []
    }


    for key in tmp.keys():
        s = Counter([x[0] for x in tmp[key]]).most_common(2)
        centroid = s[0][0]
        if s[0][1] == s[-1][1] or s[0][1] < 3:
            centroid = sorted([(x[0], clusterer.count_occurrence(x[0])) for x in tmp[key]],
                              key=lambda x: x[1], reverse=True)[0][0]
        attr = {
            'name': centroid,
            'rate': float(len(tmp[key])) / float(total),
            'negative': {
                'stat': 0.0,
                'reviews': []
            },
            'positive': {
                'stat': 0.0,
                'reviews': []
            }
        }
        
        total = 0
        for _ in tmp[key]:
            i = extractor.find_expr_tagged(_[1])
            x = _[1][i]
            if x[1] == 'N':
                attr['negative']['reviews'].append(
                        " ".join(["".join(x[0].split('/')[:-1]) for x in _[1]])
                    )
            if x[1] == 'P':
                attr['positive']['reviews'].append(
                        " ".join(["".join(x[0].split('/')[:-1]) for x in _[1]])
                    )
            total += 1

        n_p = len(attr['positive']['reviews'])
        n_n = len(attr['negative']['reviews'])
        attr['negative']['stat'] = float(n_n) / float(total)
        attr['positive']['stat'] = float(n_p) / float(total)
        
        stat['attributes'].append(attr)

    return json.dumps(stat)


@app.route('/v1/products/<int:id>/reviews')
def get_reviews(id):
    tagged, model, cdict, rank_by_expr, centroids = fetch_reviews(id)
    meaningful = set([x[0] for x in filter(lambda x:x[1]>2, rank_by_expr)])

    ret = []

    for review in tagged:
        res = {
            'attributes': [],
            'content': None
        }
        cont = []
        emphasis = extractor.find_props_with_exprs_tagged_idx(review)
        ptr = 0; eptr = 0;
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
                    c = clusterer.predict(model, review[emphasis[eptr][0]])
                    res['attributes'].append(centroids[c])
                except:
                    res['attributes'].append("".join(review[emphasis[eptr][0]][0].split('/')[:-1]))
                if is_pos:
                    cont.append('</stat-pos>')
                if is_neg:
                    cont.append('</stat-neg>')
            else:
                cont.append("".join(review[ptr][0].split('/')[:-1]))
            ptr += 1
        res['attributes'] = list(set(res['attributes']))
        res['content'] = " ".join(cont)
        ret.append(res)

    return json.dumps(ret)


def run_server():
    app.run(host='0.0.0.0')


def test():
    import time
    print get_summary(5599916904)
    time.sleep(10)
    print get_reviews(5599916904)


if __name__ == '__main__':
    # test()
    run_server()
