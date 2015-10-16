#!/usr/bin/env python
# -*- coding: utf-8 -*-
import requests
from bs4 import BeautifulSoup


class Crawler:

    def __init__(self):
        pass


    def get_item_reviews(self, item_id):
        crawl = []
        base_url = 'http://shopping.naver.com/detail/section_user_review.nhn?' + ('nv_mid=%d&page=' % item_id)
        for i in xrange(1,4001):
            url = base_url + str(i)
            d  = BeautifulSoup(requests.get(url).text, 'lxml')
            is_empty = True
            for each in d.find_all(class_='atc'):
                is_empty = False
                crawl.append(each.text.strip())
            if is_empty:
                break
        return crawl


if __name__ == '__main__':
    pass
