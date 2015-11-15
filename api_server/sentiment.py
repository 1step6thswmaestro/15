#!/usr/bin/env python
# -*- coding: utf-8 -*-
import uuid


class SentimentTagger:

    def __init__(self, model_file, template_type=1):
        self.model_file = model_file
        self.template_type = template_type


    def test_model(self, data, test_fn='crf.test', test_out_fn='crf.test.out',\
                   remove_after=False):
        """
        Test CRF++ model.
        Usage: print test_model([[\
              ('I/Noun','O'),('love/Verb','P'),('chicken/Noun','O')], ...],\
            'crf.model')
        """
        fout = file('crf/' + test_fn, 'w')
        for sentence in data:
            for word in sentence:
                if self.template_type == 2:
                    if isinstance(word[0], unicode):
                        print >> fout, "\t".join(list(word[0].split('/'))+\
                                                 [word[1]]).encode('utf-8')
                    else:
                        print >> fout, "\t".join(list(word[0].split('/'))+[word[1]])
                else:
                    if isinstance(word[0], unicode):
                        print >> fout, "\t".join(word).encode('utf-8')
                    else:
                        print >> fout, "\t".join(word)
            print >> fout, ''
        fout.close()
        
        from os import system, remove
        test_cmd = 'crf_test -m %s %s > %s' % (self.model_file, 'crf/' + test_fn,\
                                               test_out_fn)
        print 'Executing %s' % test_cmd
        system(test_cmd)
        
        print 'Parsing result...'
        fin = file(test_out_fn, 'r')
        cross = [[0,0], [0,0]]
        tagged = []; temp = []
        columns = 3 + int(self.template_type == 2)
        
        for _line in fin:
            
            line = _line.decode('utf-8').split()

            if len(line) != columns:
                tagged.append(temp)
                temp = []
                continue

            e = line[-2]
            r = line[-1]
            temp.append(line)

            if e == 'O':
                if r != 'O':
                    cross[0][1] += 1
                else:
                    cross[1][1] += 1
            else:
                if r == e:
                    cross[0][0] += 1
                else:
                    cross[1][0] += 1
        fin.close()
        
        if len(temp) > 0:
            tagged.append(temp)
            temp = []
        
        tp = cross[0][0]
        fp = cross[0][1]
        fn = cross[1][0]
        tn = cross[1][1]

        rec = (float(tp) / float(max(1.0, tp + fn)))
        prc = (float(tp) / float(max(1.0, tp + fp)))

        ret = {
            'recall': rec,
            'precision': prc,
            'f1': (2*rec*prc / max(1.0, prc+rec)),
            'tagged': tagged
        }

        if remove_after:
            try:
                remove('crf/' + test_fn)
                remove(test_out_fn)
            except:
                pass
        
        return ret


    def label_sentence(self, sentence):
        if not isinstance(sentence, list):
            sentence = sentence.split()

        if self.template_type == 2:
            return [("/".join(x[:2]),x[3]) for x in \
                    self.test_model([zip(sentence, ['O']*len(sentence))],
                        test_fn=str(uuid.uuid1()), test_out_fn=str(uuid.uuid1()),
                        remove_after=True)['tagged'][0]]
        else:
            return [(x[0],x[2]) for x in \
                    self.test_model([zip(sentence, ['O']*len(sentence))],
                        test_fn=str(uuid.uuid1()), test_out_fn=str(uuid.uuid1()),
                        remove_after=True)['tagged'][0]]


    def label_sentence_multi(self, sentences):
        if self.template_type == 2:
            return [[("/".join(x[:2]),x[3]) for x in review]\
                    for review in self.test_model([zip(s, ['O']*len(s))\
                    for s in sentences],
                    remove_after=True,
                    test_fn=str(uuid.uuid1()),
                    test_out_fn=str(uuid.uuid1()))['tagged']]
        else:
            return [[(x[0], x[2]) for x in review]\
                    for review in self.test_model([zip(s, ['O']*len(s))\
                    for s in sentences],
                    remove_after=True,
                    test_fn=str(uuid.uuid1()),
                    test_out_fn=str(uuid.uuid1()))['tagged']]
