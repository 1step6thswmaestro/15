# -*- coding: utf-8 -*-
import numpy as np
from gensim.models.word2vec import Word2Vec


class ProductRecommender:
    
    def __init__(self, wmodel, sentiment_tagger, opinion_extractor, clusterer):
        if isinstance(wmodel, Word2Vec):
            self.wmodel = wmodel
        else:
            self.wmodel = Word2Vec.load_word2vec_format(wmodel, binary=True)
        self.tagger = sentiment_tagger
        self.extractor = opinion_extractor
        self.clusterer = clusterer
            
    
    def preprocess(self, item):
        try:
            if item.get('tagged') is None:
                item['tagged'] = self.tagger.label_sentence_multi(item['cleaned'])

            if item.get('prop_data') is None:
                item['prop_data'] = [self.extractor.pos_analyzer(x, 0, mark=True) for x in item['tagged']]
                self.extractor.deep_filter_data(item['prop_data'])

            if item.get('aprop') is None:
                r = self.clusterer.cluster_prop(item['prop_data'])
                item['cluster_dict'] = r[0]
                item['prop_dict'] = r[1]
                item['aprop'] = r[2]
        except:
            return False
        return True

    
    def score_product_wrt_property(self, item, prop, verbose=False):
        """
        Calculate score of an item with regard to given property.
        
        :param prop: Property Name.
        :type prop: unicode
        :param item: Information about the item(standard form - which has 'category', 'parsed', 'cleaned', and 'reviews' field).
        :type item: dict
        :param verbose: Print debug messages if verbose is True.
        :type verbose: bool
        """

        positive = 0
        non_positive = 0
        
        self.preprocess(item)
        
                
        "Internal function for calculating senetiment score of the sentence(review)."
        def get_sentiment(sentence):
            occur = [0, 0]
            for x in sentence:
                if x[1] != 'O':
                    occur[x[1] == 'N'] += 1
            
            if occur[0] > occur[1]:
                return 'P'
            elif occur[1] > occur[0]:
                return 'N'
            else:
                return 'O'
            
        
        "Internal function for cluster prediction of given property."
        def get_cluster(cluster, prop):
            try:
                return cluster.predict(self.wmodel[prop])[0]
            except:
                return None


        prop_cluster = get_cluster(item['aprop'], prop)
        
        data_wrt_prop = np.hstack([y['line'] for y in np.hstack(item['prop_data'])])
        data_wrt_prop = [x for x in data_wrt_prop if get_cluster(item['aprop'], x['prop'][0]) == prop_cluster]
        
        for data in data_wrt_prop:
            if get_sentiment(data['line']) == 'P':
                positive += 1
            else:
                non_positive += 1
        
        return (
                float(positive * np.log(1+positive)) / float(max(1, positive + non_positive)),
                 positive, non_positive
               )
    

    def score_product_wrt_properties(self, item, props, verbose=False):
                
        scores = [self.score_product_wrt_property(item, p, verbose) for p in props]
        
        return (
                np.sum([x[0] for x in scores]),
                [(x[1], x[2]) for x in scores]
              )
        
    
    def get_recommended(self, items, props, verbose=False):
        """
        returns: [{
          'productId': item['id'],
          'title': item['name'],
          'lprice': item['price'].split()[0].strip(),
          'image': item['image'],
          'score': score,
          'reasons': [u'X가 Y번 등장(긍정 비율:Z%)', ...], # 상위 5개까지만.
        }] (sorted according to score)
        """
        
        scores_total = [self.score_product_wrt_properties(item, props, verbose) for item in items]
        ret = []
        
        for item_idx, scores in enumerate(scores_total):
            if scores is None:
                continue

            idx_sorted = sorted(range(len(scores[1])), key=lambda x: scores[1][x][0], reverse=True)

            data = {
                'productId': items[item_idx]['id'],
                'title': items[item_idx]['name'],
                'lprice': items[item_idx]['price'].split()[0],
                'image': items[item_idx]['image'],
                'score': scores[0],
                'reasons': [],
            }

            for idx in idx_sorted[:10]:
                target_prop = "".join(props[idx].split("/")[:-1])
                if len(target_prop) == 0:
                    continue
                target_pos, target_nonpos = scores[1][idx]
                data['reasons'].append(target_prop+u'이(가) '+unicode(target_pos+target_nonpos)+\
                                       u'번 언급(긍적 비율 '+\
                                       unicode(int(100*float(target_pos)/float(max(1, target_pos+target_nonpos))))+\
                                       u'%).')

            ret.append(data)
        
        return ret
    
    
    def get_prop_list(self, items, verbose=False):
        
        ret = []
        delete_list = []

        for item in items:
            
            if not self.preprocess(item):
                delete_list.append(item)
                continue
            
            props_sorted = [item['cluster_dict'][x] for x in item['cluster_dict'].keys()]
            props_sorted = sorted(props_sorted, key=lambda x: x['freq'], reverse=True)
            
            for prop in props_sorted[:5]:
                if prop['freq'] < 6:
                    break
                ret.append(prop['seed'])
    
        for deletion in delete_list:
            len_b = len(items)
            items.remove(deletion)
            assert len_b-1 == len(items)
            
        return list(set(ret))
