#!/usr/bin/env python
# -*- coding: utf-8 -*-
import numpy as np
from gensim.models import word2vec
from sklearn.cluster import AffinityPropagation
from collections import defaultdict


class Clusterer:

    def __init__(self, w2v):
        self.wmodel = word2vec.Word2Vec.load_word2vec_format(w2v, binary=True)


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


    def predict(self, model, word):
        return model.predict(self.wmodel[word])[0]


    def count_occurrence(self, word):
        return self.wmodel.vocab[word].count


if __name__ == '__main__':
    pass
