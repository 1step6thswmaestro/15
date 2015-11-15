# -*- coding: utf-8 -*-
"""
To import from the parent directory
"""
import os,sys,inspect
currentdir = os.path.dirname(os.path.abspath(inspect.getfile(inspect.currentframe())))
parentdir = os.path.dirname(currentdir)
sys.path.insert(0,parentdir) 

from extract import OpinionExtractor
from morphs import MorphAnalyzer
from cluster import Clusterer
from crawl import Crawler


def test_whole():
    extractor = OpinionExtractor('word2vec/clean.partial.6pos.w3.m10.model')
    clusterer = Clusterer('word2vec/clean.partial.6pos.w3.m10.model')
    parser = MorphAnalyzer()
    crawler = Crawler(100)


    def extract_property(reviews):
        props = []

        for r in reviews:
            props += extractor.find_props(r)

        props = list(set(props))
        aprop, visual = clusterer.cluster_props(props)
        cdict = clusterer.cluster_as_dict(aprop, visual)
        centroids = clusterer.get_centroid(cdict)

        t = []

        for x in centroids.keys():
            t.append((centroids[x],\
                      extractor.score_cluster_rev_2(\
                          cdict[x], centroids[x], reviews), x))

        ret = []

        for x,y,z in sorted(t, key=lambda x:x[1], reverse=True):
            ret.append((x, y, cdict[z][:5]))

        return ret

    res = extract_property(
            parser.parse_reviews(crawler.get_item_reviews(5749367460)))

    assert len(res) > 8
    assert res[0][1] > 23.0


if __name__ == '__main__':
    test_whole()
