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


    def cluster_prop(self, filtered_data):
        prop_dict={}

        for review in filtered_data:
            for dicti in review['line']:
                if not prop_dict.has_key(dicti["prop"][0]):
                    prop_dict[dicti["prop"][0]]={"freq":0,"data":[],"idx":[]}

                prop_dict[dicti["prop"][0]]['idx'].append(review['index'])
                prop_dict[dicti["prop"][0]]["freq"] += 1
                prop_dict[dicti["prop"][0]]["data"].append(dicti)

        d_list=[]
        word_list=[]

        for word in prop_dict:
            try:
                d_list.append(self.wmodel[word])
                word_list.append(word)
            except:
                pass

        Aprop = AffinityPropagation(damping=0.6, convergence_iter=100, max_iter=10000)
        Aprop.fit(d_list)
        cluster_dict = {}

        for idx, each in enumerate(Aprop.labels_):
            vec = d_list[idx]
            if not cluster_dict.has_key(each):
                cluster_dict[each] = {"word":[],"freq":0,"seed":"","sim":0.0}
            cluster_dict[each]["word"].append(word_list[idx])

        total_freq=0

        for each in cluster_dict.keys():
            target_group_id = each
            group_id = each

            last_group_id = target_group_id

            cluster_freq=0
            max_seed=""
            max_freq=0

            for idx,data in enumerate(cluster_dict[each]["word"]):
                cluster_freq+=prop_dict[data]["freq"]
                if prop_dict[data]["freq"] > max_freq:
                    max_freq=prop_dict[data]["freq"]
                    max_seed=data

            cluster_dict[each]["freq"]=cluster_freq
            cluster_dict[each]["seed"]=max_seed

        return (cluster_dict, prop_dict, Aprop)


if __name__ == '__main__':
    pass
