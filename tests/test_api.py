# -*- coding: utf-8 -*-
"""
To import from the parent directory
"""
import os,sys,inspect
currentdir = os.path.dirname(os.path.abspath(inspect.getfile(inspect.currentframe())))
parentdir = os.path.dirname(currentdir)
sys.path.insert(0,parentdir)

import requests as r
import json


def test_summary(api_server):
    data = json.loads(r.get('http://1.lucent.me:5000/v1/products/5599916904/summary').text)
    assert data.get('attributes') is not None
    assert len(data['attributes']) > 8
    assert data['attributes'][0].get('rate') is not None
    assert data['attributes'][0].get('rate') > 0.0

    assert data['attributes'][0].get('name') is not None
    assert data['attributes'][0].get('negative') is not None
    assert data['attributes'][0].get('positive') is not None

    assert isinstance(data['attributes'][0].get('rate'), float)
    assert isinstance(data['attributes'][0].get('name'), str) or\
           isinstance(data['attributes'][0].get('name'), unicode)
    assert isinstance(data['attributes'][0].get('positive'), dict)
    assert isinstance(data['attributes'][0].get('negative'), dict)
    assert isinstance(data['attributes'][0]['positive'].get('stat'), float)
    assert isinstance(data['attributes'][0]['negative'].get('stat'), float)
    assert isinstance(data['attributes'][0]['negative'].get('reviews'), list)
    assert isinstance(data['attributes'][0]['positive'].get('reviews'), list)

    length = len(data['attributes'])
    """
    Uncomment this when sentiment tagger works better... T_T
    assert sum([int(attr['positive']['stat'] + attr['negative']['stat'] > 0.0)\
                for attr in data['attributes']]) == length
    """

    assert sum([attr['rate'] for attr in data['attributes']]) == 1.0


def test_reviews(api_server):
    data = json.loads(r.get('http://1.lucent.me:5000/v1/products/5599916904/reviews').text)
    assert isinstance(data, list)
    assert len(data) > 0
    length = len(data)
    
    assert sum([int(rev.get('attributes') is not None) for rev in data]) == length
    assert sum([int(isinstance(rev['attributes'], list)) for rev in data]) == length

    assert sum([int(rev.get('content') is not None) for rev in data]) == length
    assert sum([int(isinstance(rev['content'], unicode) or\
                    isinstance(rev['content'], str)) for rev in data]) == length


# TODO: Design API specification and code.
def test_recommend(api_server):
    pass
