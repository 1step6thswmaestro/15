#!/usr/bin/env python
# -*- coding: utf-8 -*-
import numpy as np
from gensim.models import word2vec
from morphs import MorphAnalyzer
from collections import defaultdict, Counter


class OpinionExtractor:

    def __init__(self, wmodel):
        if isinstance(wmodel, word2vec.Word2Vec):
            self.wmodel = wmodel
        else:
            self.wmodel = word2vec.Word2Vec.load_word2vec_format(wmodel, binary=True)
        self.morphs = MorphAnalyzer()


    def find_expr(self, x):
        """
        This function finds expression-like pattern from given list(splitted string).
        It returns -1 if no exepression is found.
        """
        n = len(x)
        i = 0
        while i < n:
            try:
                if x[i].split('/')[-1] in ['VA', 'XR'] and\
                   self.wmodel.similarity(x[i], x[0]) >= 0.15:
                    return i
            except:
                pass
            j = i; s = []
            while j < n:
                tag = x[j].split('/')[-1]
                if tag not in ['JX', 'JKS', 'MAG', 'NNG']:
                    break
                if tag != 'MAG':
                    s.append(tag)
                if tag == 'NNG':
                    break
                j += 1
            try:
                if tuple(s) in [('JX', 'NNG'), ('JKS', 'NNG')] and\
                   self.wmodel.similarity(x[j], x[0]) >= 0.15:
                    return j
            except:
                pass
            i += 1
        return -1


    def find_props_idx(self, review):
        """
        This function finds property-like patterns from given list(or string).
        It has dependency on `find_expr` function.
        """
        if not isinstance(review, list):
            x = review.split()
        else:
            x = review
        ret = []
        i = 0; n = len(review)
        while i < n:
            if x[i].split('/')[-1] in ['NNP', 'NNG']:
                j = i+1
                while j < n:
                    tag = x[j].split('/')[-1]
                    if len(tag) == 2 and tag[0] in ['S', 'E']:
                        break
                    j += 1
                expr = self.find_expr(x[i:j])
                if expr != -1:
                    ret.append((i, expr, j))
                i = j
            i += 1
        return ret


    def find_props(self, review):
        if not isinstance(review, list):
            x = review.split()
        else:
            x = review
        return [x[y[0]] for y in self.find_props_idx(x)]


    def score_cluster_classic(self, cluster, data, window=3):
        """
        **{Co,No}-Occurence-Count counts only in 'window' words ahead of each noun;
        E.g. let window = 2 and data = ['NNG(noun) NNG NNG NNG NNG VA'], then
             score for the noun is zero, but the score is 2 with window = 5.
        """
        ret = np.zeros(2)
        for _line in data:
            if isinstance(_line, str):
                line = _line.decode('utf-8').split()
            elif isinstance(_line, list):
                line = _line
            else:
                line = _line.split()
            for c in cluster:
                for i in xrange(len(line)):
                    if line[i] == c:
                        j = 1
                        found = False
                        while j <= window and i+j < len(line):
                            if line[i+j].split('/')[-1] in ['XR', 'VA']:
                                ret[0] += 2
                                found = True 
                            elif line[i+j].split('/')[-1] in ['MAG', 'VV']:
                                ret[0] += 1
                                found = True
                            j += 1
                        if not found:
                            ret[1] += 1
        return float(ret[0]) * np.log(max(1, ret[0])) / float(max(1, ret[1] + ret[0]))


    def score_cluster_frequency(self, cluster, centroid, data):
        """
        Calculate score for the given cluster, using formula above.
        """
        ret = 0
        for _line in data:
            if isinstance(_line, str):
                line = _line.decode('utf-8').split()
            elif isinstance(_line, list):
                line = _line
            else:
                line = _line.split()
            cnt = Counter(line)
            ret += np.sum([2 * cnt[x] if x == centroid else cnt[x]\
                           for x in cnt if x in cluster])
        return np.log(ret)


    def score_cluster_rev_1(self, cluster, centroid, data, window=3):
        """
        *For now, it's using simple multiplication to combine these two scores,
         but it can be improved!
        """
        score = self.score_cluster_classic(cluster, data, window)
        score *= self.score_cluster_frequency(cluster, centroid, data)
        return score


    def score_cluster_similarity(self, cluster, centroid):
        """
        Score cluster using above formula.
        """
        ret = -1.0
        for x in cluster:
            if x == centroid:
                continue
            try:
                ret = max(ret, 1-self.wmodel.similarity(x, centroid))
            except:
                pass
        return 2.0 - ret


    def score_cluster_rev_2(self, cluster, centroid, data, window=3):
        """
        For now, it's using simple multiplication. But it can be improved.
        """
        score = self.score_cluster_rev_1(cluster, centroid, data, window) *\
                self.score_cluster_similarity(cluster, centroid)
        return score


    def find_expr_tagged(self, x):
        return self.find_expr([y[0] for y in x])


    def find_props_with_exprs_tagged_idx(self, tagged):
        return self.find_props_idx([y[0] for y in tagged])


    def find_props_with_exprs_tagged(self, tagged):
        return [tagged[x[0]:x[2]+1] for x in self.find_props_with_exprs_tagged_idx(tagged)]


    def get_summarized_reviews(self, aprop, tagged):
        if not isinstance(tagged, list) or len(tagged) == 0:
            return defaultdict(list)

        ret = defaultdict(list)

        for rev in tagged:
            pidx = self.find_props_with_exprs_tagged_idx(rev)
            for idx in pidx:
                prop = rev[idx[0]][0]
                sentiment = rev[idx[1]][1]
                try:
                    ret[aprop.predict(self.wmodel[prop])[0]].append(
                            (self.morphs.reconstruct(rev[idx[0]:idx[2]+1]), sentiment))
                except:
                    pass

        return ret
            

if __name__ == '__main__':
    pass
