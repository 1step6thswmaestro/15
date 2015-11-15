#!/usr/bin/env python
# -*- coding: utf-8 -*-
import copy
import numpy as np
from gensim.models import word2vec
from morphs import MorphAnalyzer
from collections import defaultdict, Counter


class OpinionExtractor:

    def __init__(self, wmodel):
        if isinstance(wmodel, word2vec.Word2Vec):
            self.wmodel = wmodel
        else:
            self.wmodel = word2vec.Word2Vec.load_word2vec_format(wmodel, binary = True)
        self.morphs = MorphAnalyzer()


    def recover_line(self, tagged_line):
        line=""

        for wordnpos in tagged_line:
            word,pos = wordnpos[0].split('/')

            if pos == 'NNG' or pos == 'NNP' or pos == 'MAG' or\
               pos == 'XR' or pos == 'VV' or pos == 'VX' or pos == 'VA':
                line+=" "
                line+=word

            else:
                if word==u'ㄱ' or word==u'ㄴ' or\
                   word==u'ㄹ' or word==u'ㅁ' or word==u'ㅂ':
                    continue

                line+=word

        return line


    def get_pos_sent(self, prop_dict,x,prop_info):
        neg_line = []
        pos_line = []
        valid = False
        for data in prop_dict[x]["data"]:
            pos_cnt = 0
            neg_cnt = 0
            for wordnpos in data["line"]:
                if wordnpos[1] == 'N':
                    neg_cnt += 1
                elif wordnpos[1] == 'P':
                    pos_cnt += 1

            if pos_cnt > neg_cnt and data["marked"]:
                pos_line.append((data["line"],data["sim"]))
            elif neg_cnt > pos_cnt and data["marked"]:
                neg_line.append([data["line"],data["sim"]])
            if data["marked"]:
                valid = True

        cnt = 0
        total_pn = len(pos_line) + len(neg_line)
        try:
            prop_info["positive"]["stat"] = len(pos_line)/float(max(1, total_pn))
            prop_info["negative"]["stat"] = len(neg_line)/float(max(1, total_pn))
        except:
            pass
        for x,y in sorted(pos_line,key = lambda x:x[1],reverse = True):
            if cnt == 5:
                break
            prop_info["positive"]["reviews"].append(self.recover_line(x))
            cnt += 1

        cnt = 0

        for x,y in sorted(neg_line,key = lambda x:x[1],reverse = True):
            if cnt == 5:
                break
            prop_info["negative"]["reviews"].append(self.recover_line(x))
            cnt += 1

        return len(pos_line),len(neg_line),valid


    def pos_analyzer(self, tagged_review, idx, mark=False):
        line = {
            "front_exp": [],
            "prop": [],
            "back_exp": [],
            "line": [],
            "sim": 0.0,
            "marked": mark,
        }

        review = {
            "index": idx,
            "line": [],
        }

        expAppear = False
        propAppear = False
        propEverAppear = False

        for wordnpos in tagged_review:
            try:
                word,pos = wordnpos[0].split('/')
                if pos == 'VA' or pos == 'VV' or pos == 'MAG' or pos == 'XR':
                    if propEverAppear:
                        line["back_exp"].append(wordnpos)
                    else:
                        line["front_exp"].append(wordnpos)
                    line["line"].append(wordnpos)
                    propAppear = False
                    expAppear = True
                elif pos == 'NNG' or pos == 'NNP':
                    if expAppear and (propAppear or propEverAppear):
                        review["line"].append(copy.deepcopy(line))
                        expAppear = False
                        line ={
                            "front_exp": [],
                            "prop": [],
                            "back_exp": [],
                            "line": [],
                            "sim": 0.0,
                            "marked": mark,
                        }
                    line["prop"] = wordnpos
                    line["line"].append(wordnpos)
                    propAppear = True
                    propEverAppear = True
                elif pos == 'EF' or pos == 'SP' or pos == 'SF':
                    if expAppear and propEverAppear:
                        line["line"].append(wordnpos)
                        review["line"].append(copy.deepcopy(line))
                        expAppear = False
                    line = {
                        "front_exp": [],
                        "prop": [],
                        "back_exp": [],
                        "line": [],
                        "sim": 0.0,
                        "marked": mark,
                    }
                    propAppear = False
                    propEverAppear = False
                else: 
                    line["line"].append(wordnpos)
            except:
                pass
        if expAppear and propEverAppear:
            review["line"].append(copy.deepcopy(line))
        return review


    def deep_filter_data(self, filtered_data):
        for review in filtered_data:
            for dicti in review['line']:
                exp_list = []
                cnt = 0
                for exp in dicti["front_exp"]:
                    try:
                        sim= self.wmodel.similarity(dicti["prop"],exp)
                        if sim < 0.3:
                            exp_list.append(exp)
                        else:
                            dicti["sim"] += sim
                        cnt += 1
                    except:
                        exp_list.append(exp)
                        pass
                for exp in exp_list:
                    dicti["front_exp"].remove(exp)
                exp_list = []
                for exp in dicti["back_exp"]:
                    try:
                        sim = self.wmodel.similarity(dicti["prop"],exp)
                        cnt += 1
                        if sim <0.3:
                            exp_list.append(exp)
                        else:
                            dicti["sim"] += sim
                    except:
                        exp_list.append(exp)
                        pass
                for exp in exp_list:
                    dicti["back_exp"].remove(exp)
                if cnt>0:
                    dicti["sim"]= dicti["sim"]/float(cnt)


    def score_cluster(self, product_review, cluster_dict, prop_dict):
        total_freq = 0
        for each in cluster_dict.keys():
            cnt = 0
            prop = []
            for idx,data in enumerate(cluster_dict[each]["word"]):
                sim = self.wmodel.similarity(cluster_dict[each]["seed"],data)
                if sim < 0.5:
                    prop.append(data)
                    cluster_dict[each]["freq"] -= prop_dict[data]["freq"]
                else:
                    cnt += 1
                    cluster_dict[each]["sim"] += sim
            for wd in prop:
                cluster_dict[each]["word"].remove(wd)
            if cnt > 0:
                cluster_dict[each]["sim"] = cluster_dict[each]["sim"]/float(max(1, cnt))
            total_freq += cluster_dict[each]["freq"]
        for each in cluster_dict.keys():
            cluster_dict[each]["freq"] = cluster_dict[each]["freq"]/float(max(1, total_freq))
            cluster_dict[each]["sim"]= cluster_dict[each]["freq"]*cluster_dict[each]["sim"]
        t = []
        for x in cluster_dict.keys():
            if cluster_dict[x]["sim"] > 0.01:
                t.append((cluster_dict[x]["seed"],cluster_dict[x]["sim"],
                          cluster_dict[x]["word"],cluster_dict[x]["freq"]))
        
        temp_cnt = 0
        props = []
        tot_pos = 0
        tot_neg = 0
        ten_tot_freq = 0
        for x,y,z,i in sorted(t,key = lambda x:x[1],reverse = True):
            if temp_cnt == 10:
                break
            prop_info = {
                "name":"",
                "rate":0.0,
                "totalReviews":0,
                "negative":{
                    "stat":0.0,
                    "reviews":[],
                },
                "positive":{
                    "stat":0.0,
                    "reviews":[]
                }
            }

            word,pos = x.split('/')
            prop_info["name"] = word
            ten_tot_freq += i
            prop_info["rate"] = i
            prop_info["totalReviews"] = len(set(prop_dict[x]['idx']))
            props.append(x)
            for w in z[:7]:
                props.append(w)
            
            pos,neg,valid = self.get_pos_sent(prop_dict,x,prop_info)

            if not valid:
                continue

            tot_pos += pos
            tot_neg += neg
            temp_cnt += 1
            product_review["attributes"].append(copy.deepcopy(prop_info))
        for temp_prop in product_review["attributes"]:
            temp_prop["rate"] = temp_prop["rate"]/float(ten_tot_freq)
        total = tot_pos+tot_neg
        try:
            product_review["stat"]["positive"] = tot_pos/float(total)
            Product_review["stat"]["negative"] = tot_neg/float(total)
        except:
            pass
        return props,temp_cnt


    def get_pos_sent2(self,line):
        num_p=0
        num_n=0
        start_sent_p="<stat-pos>"
        start_sent_n="<stat-neg>"
        
        end_sent_p="</stat-pos>"
        end_sent_n="</stat-neg>"
        final_sent_arr=[]
        
        for wordnmeta in line:
            final_sent_arr.append(wordnmeta)
            if wordnmeta[1]==u'P':
                num_p+=1
            elif wordnmeta[1]==u'N':
                num_n+=1
        final_sent = self.recover_line(final_sent_arr)
        
        if num_p == num_n:
            return final_sent
        
        if num_p > num_n :
            final_sent+=end_sent_p
            start_sent_p+=final_sent
            return start_sent_p
        elif num_n > num_p:
            final_sent+=end_sent_n
            start_sent_n+=final_sent
            return start_sent_n
    

    def get_reviews(self,filtered_data,prop_dict,_props,limit,skip):
        reviews_json=[]
        review_json={
            "content":""
        }
        props = []
        review_index=[]
        for prop in _props:
            try:
                if prop.find(u'/') == -1:
                    prop = prop + u'/NNG'
                review_index.append(prop_dict[prop]['idx'])
            except:
                prop = prop[:prop.find(u'/')] + u'/NNP'
                review_index.append(prop_dict[prop]['idx'])
            props.append(prop)
        
        review_index = set(np.hstack(review_index))
       
        review_index = list(review_index)

        cnt = 0
        limit_idx = limit+skip
        
        if limit_idx > len(review_index):
            limit_idx = len(review_index)
        
        for idx in range(skip,limit_idx):
            final_sent=""
            for line in filtered_data[review_index[idx]]['line']:
                if props.count(line['prop'][0]) > 0:
                    final_sent+=self.get_pos_sent2(line['line'])
                else:
                    final_sent_arr =[]
                    for wordnmeta in line['line']:
                        final_sent_arr.append(wordnmeta)
                    final_sent+=self.recover_line(final_sent_arr)
            review_json["content"] = final_sent
            reviews_json.append(copy.deepcopy(review_json))
        return reviews_json


if __name__ == '__main__':
    pass
