#!/usr/bin/env python
# -*- coding: utf-8 -*-
import numpy as np
from gensim.models import word2vec
from collections import defaultdict, Counter
from sklearn.cluster import AffinityPropagation


class Clusterer:

    def __init__(self, wmodel):
        if isinstance(wmodel, word2vec.Word2Vec):
            self.wmodel = wmodel
        else:
            self.wmodel = word2vec.Word2Vec.load_word2vec_format(wmodel, binary=True)


    def cluster_props(self, props):
        aprop = AffinityPropagation(damping=0.9, max_iter=10000)
        data = []
        visual = []
        for prop in set(props):
            try:
                data.append(np.array(self.wmodel[prop], dtype=np.float32))
                visual.append(prop)
            except:
                pass
        data = np.array(data, dtype=np.ndarray)
        aprop.fit(data)
        return (aprop, visual)


    def cluster_as_dict(self, model, visual):
        ret = defaultdict(list)
        for idx, cluster_id in enumerate(model.labels_):
            word = visual[idx]
            ret[cluster_id].append(word)
        return ret

    def get_centroid(self, cdict):
        centroids = {}
        for key in cdict.keys():
            s = Counter(cdict[key]).most_common(2)
            centroid = s[0][0]
            try:
                if s[0][1] == s[-1][1] or s[0][1] < 5:
                    centroid = sorted([(x, self.wmodel.vocab[x].count)\
                                       for x in cdict[key]],
                                      key=lambda x: x[1], reverse=True)[0][0]
            except:
                centroid = s[0][0]
            centroids[key] = centroid
        return centroids


    def predict(self, model, word):
        return model.predict(self.wmodel[word])[0]


    def count_occurrence(self, word):
        return self.wmodel.vocab[word].count


if __name__ == '__main__':
    pass
