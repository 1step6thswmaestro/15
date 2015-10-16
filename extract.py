#!/usr/bin/env python
# -*- coding: utf-8 -*-
import numpy as np


class OpinionExtractor:

    def __init__(self):
        pass


    def find_expr(self, x):
        for i in xrange(len(x)):
            if x[i].split('/')[-1] == 'VA':
                return i
        for i in xrange(len(x)):
            if x[i].split('/')[-1] in ['XR', 'MAG']:
                return i
        return -1


    def find_props(self, review):
        if not isinstance(review, list):
            sent = review.split()
        else:
            sent = review
        ptr = 0
        ret = []
        while ptr < len(sent):
            if sent[ptr].split('/')[-1] in ['NNG', 'NNP']:
                last = ptr
                while ptr < len(sent) and not sent[ptr].split('/')[-1].startswith('E'):
                    ptr += 1
                i = self.find_expr(sent[last:ptr+1])
                if i >= 0:
                    ret.append(sent[last])
            ptr += 1
        return ret


    """
    Currently not used...
    def score_cluster_model(self, model, cluster, props):
        return np.sum([
                np.sum([x[1] for x in model.most_similar(c, topn=50) if x[0] in props and x[1] > 0.5])\
                for c in cluster
            ])
    """


    def score_cluster_expr(self, cluster, data, window=3):
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


    def find_expr_tagged(self, x):
        for i in xrange(len(x)):
            if x[i][0].split('/')[-1] == 'VA':
                return i
        for i in xrange(len(x)):
            if x[i][0].split('/')[-1] in ['XR', 'MAG']:
                return i
        return -1


    def find_props_with_exprs_tagged(self, tagged):
        ptr = 0
        ret = []
        sent = tagged
        while ptr < len(sent):
            if sent[ptr][0].split('/')[-1] in ['NNG', 'NNP']:
                last = ptr
                while ptr < len(sent) and not sent[ptr][0].split('/')[-1].startswith('E') \
                      and not sent[ptr][0].split('/')[-1].startswith('S'):
                    ptr += 1
                i = self.find_expr_tagged(sent[last:ptr+1])
                if i >= 0:
                    ret.append(sent[last:ptr+1])
            ptr += 1
        return ret


    def find_props_with_exprs_tagged_idx(self, tagged):
        ptr = 0
        ret = []
        sent = tagged
        while ptr < len(sent):
            if sent[ptr][0].split('/')[-1] in ['NNG', 'NNP']:
                last = ptr
                while ptr < len(sent) and not sent[ptr][0].split('/')[-1].startswith('E') \
                      and not sent[ptr][0].split('/')[-1].startswith('S'):
                    ptr += 1
                i = self.find_expr_tagged(sent[last:ptr+1])
                if i >= 0:
                    ret.append((last, ptr, last+i))
            ptr += 1
        return ret


if __name__ == '__main__':
    pass
