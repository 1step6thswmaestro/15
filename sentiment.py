#!/usr/bin/env python
# -*- coding: utf-8 -*-
import uuid


class SentimentTagger:

    def __init__(self, model_fn):
        self.model_fn = model_fn


    def test_model(self, data, test_fn='crf.test', test_out_fn='crf.test.out', remove_after=False):
        """
        Test CRF++ model.
        Usage: print test_model([[('I/Noun','O'),('love/Verb','P'),('chicken/Noun','O')], ...], 'crf.model')
        """
        fout = file(test_fn, 'w')
        for sentence in data:
            for word in sentence:
                if isinstance(word[0], unicode):
                    print >> fout, "\t".join(list(word[0].split('/'))+[word[1]]).encode('utf-8')
                else:
                    print >> fout, "\t".join(list(word[0].split('/'))+[word[1]])
            print >> fout, ''
        fout.close()
        
        from os import system, remove
        test_cmd = 'crf_test -m %s %s > %s' % (self.model_fn, test_fn, test_out_fn)
        print 'Executing %s' % test_cmd
        system(test_cmd)
        
        print 'Parsing result...'
        fin = file(test_out_fn, 'r')
        cross = [[0,0], [0,0]]
        tagged = []; temp = []
        
        for _line in fin:
            
            line = _line.decode('utf-8').split()

            if len(line) != 4:
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
            'Rec': rec,
            'Prc': prc,
            'F1': (2*rec*prc / max(1.0, prc+rec)),
            'tagged': tagged
        }

        if remove_after:
            try:
                remove(test_fn)
                remove(test_out_fn)
            except:
                pass
        
        return ret


    def label_sentence(self, sentence):
        if not isinstance(sentence, list):
            sentence = sentence.split()

        return [("/".join(x[:2]),x[3]) for x in \
                self.test_model([zip(sentence, ['O']*len(sentence))],
                    test_fn=str(uuid.uuid1()), test_out_fn=str(uuid.uuid1()),
                    remove_after=True)['tagged'][0]]

    def label_sentence_multi(self, sentences):
        return [[("/".join(x[:2]),x[3]) for x in review] for review in self.test_model([zip(s, ['O']*len(s)) for s in sentences], remove_after=True, test_fn=str(uuid.uuid1()), test_out_fn=str(uuid.uuid1()))['tagged']]


"Simple tests"
if __name__ == '__main__':
    a = SentimentTagger('crf/crf.model')
    assert len(a.label_sentence_multi(
        [[u'\ub514\uc790\uc778/NNG',
        u'\uad1c\ucc2e/VA',
        u'\uad6c/EC',
        u'\uc870\uc6a9/XR',
        u'\ud558/XSA',
        u'\ub124\uc694/EF',
        u'\uc18d\ub3c4/NNG',
        u'\ub3c4/JX',
        u'\ub808\uc774\ub4dc/NNP',
        u'5/SN',
        u'\uc5d0\uc11c/JKB',
        u'\ub098\uc624/VV',
        u'\uc544/EC',
        u'\uc8fc\ub2c8/NNP',
        u'\uc644\uc804/NNG',
        u'\ud3b8/NNB',
        u'\ud558/VV',
        u'\u3142\ub2c8\ub2e4/EF',
        u'\u314b\u314b/SS',
        u'\ub9e5\ud504\ub85c/NNP',
        u'\ud3b8\uc9d1/NNG',
        u'\ud658\uacbd/NNG',
        u'\uc5d0\uc120/JKB',
        u'\uc774/MM',
        u'\ub9cc\ud558/XSA',
        u'\u3134/ETM',
        u'\uac8c/NNB',
        u'\uc5c6/VA',
        u'\ub124\uc694/EF',
        u'4/SN',
        u'\ubca0\uc774/NNB',
        u'\ub294/JX',
        u'\ubd80\uc871/NNG',
        u'\ud558/XSV',
        u'\uace0/EC',
        u'8/SN',
        u'\ubca0\uc774/NNB',
        u'\uac00/JKS',
        u'\ubd80\ub2f4/NNG',
        u'\uc2a4\ub7fd/XSA',
        u'\u3134/ETM',
        u'\ubd84/NNG',
        u'\ub4e4/XSN',
        u'\uc740/JX',
        u'\ud6cc\ub96d/XR',
        u'\ud558/XSA',
        u'\u3134/ETM',
        u'\uc120\ud0dd/NNG',
        u'\uc774/VCP',
        u'\u3139/ETM',
        u'\uac81/NNB',
        u'\ub2c8\ub2e4/EF',
        u'./SF',
        u'\uc801\uadf9/NNG',
        u'\ucd94\ucc9c/NNG',
        u'\ud558/XSV',
        u'\u3142\ub2c8\ub2e4/EF',
        u'R2/NNP'],
        [u'\uc5c4\ub9c8/NNG',
        u'\uc120\ubb3c/NNG',
        u'\ub85c/JKB',
        u'\uad6c\uc785/NNG',
        u'\ud558/XSV',
        u'\uc558/EP',
        u'\uc2b5\ub2c8\ub2e4/EF',
        u'./SF',
        u'\uc544\ubb34\ub798\ub3c4/MAG',
        u'\uc2e0\uc0c1/NNG',
        u'\uc740/JX',
        u'\uac00\uaca9/NNG',
        u'\uc774/JKS',
        u'\ube44\uc2f8/VA',
        u'\uc11c/EC',
        u'\uc880/MAG',
        u'\uc9c0\ub098/VV',
        u'\u3134/ETM',
        u'\uac70/NNB',
        u'\uc9c0\ub9cc/EC',
        u'\uc800\ub834/XR',
        u'\ud558/XSA',
        u'\uac8c/EC',
        u'\uc798/MAG',
        u'\uc0b4/VV',
        u'\uc11c/EC',
        u'\uc88b/VA',
        u'\uc544\uc694/EF',
        u'\uc0c9\uac10/NNG',
        u'\ub3c4/JX',
        u'\uc88b/VA',
        u'\uace0/EC',
        u'\uc7ac\uc9c8/NNG',
        u'\ub3c4/JX',
        u'\uace0\uae09/NNG',
        u'\uc2a4\ub7fd/XSA',
        u'\uc5b4/EC',
        u'\ubcf4\uc774/VV',
        u'\u3142\ub2c8\ub2e4/EF',
        u'\uc0ac\uc774\uc988/NNG',
        u'\ub294/JX',
        u'\uc810\ud37c/NNG',
        u'\uc774/VCP',
        u'\ub2c8\ub9cc\ud07c/EC',
        u'\ub109\ub109/XR',
        u'\ud558/XSA',
        u'\u3134/ETM',
        u'\uc2a4\ud0c8/NNG',
        u'\uc774/VCP',
        u'\u3134/ETM',
        u'\uac83/NNB',
        u'\uac19/VA',
        u'\uc2b5\ub2c8\ub2e4/EF',
        u'./SF',
        u'(/SS',
        u'\uc57d\uac04/MAG',
        u'\ub9c8\ub974\uc2e0/NNP',
        u'\ubd84/NNG',
        u'\ub4e4/XSN',
        u'\uc740/JX',
        u'\ub531/MAG',
        u'\ub9de/VV',
        u'\uac8c/EC',
        u'\uad6c\uc785/NNG',
        u'\ud558/XSV',
        u'\uc2dc/EP',
        u'\ub294/ETM',
        u'\uac8c/NNB',
        u'\uc88b/VA',
        u'\uc744/ETM',
        u'\ub4ef/NNB',
        u'\ud558/VV',
        u'\uc544\uc694/EF',
        u')/SS',
        u'\uc5c4\ub9c8/NNG',
        u'\uac00/JKS',
        u'\uc88b/VA',
        u'\uc544\uc0ac/EC',
        u'\uc2dc/EP',
        u'\uc5b4\uc11c/EC',
        u'\uc800/XPN',
        u'\ub3c4\ub300\uccb4/MAG',
        u'\ub85c/JKB',
        u'\ub9cc\uc871/NNG',
        u'\ud558/XSV',
        u'\u3142\ub2c8\ub2e4/EF',
        u'./SF']]
    )) == 2
    print 'Passed!'
