#!/usr/bin/env python
# -*- coding: utf-8 -*-
import requests
from bs4 import BeautifulSoup


class Crawler:

    def __init__(self, LIMIT=5):
        self.LIMIT = LIMIT
        pass


    def get_item_reviews(self, item_id, verbose=False):
        crawl = []
        base_url = 'http://shopping.naver.com/detail/section_user_review.nhn?' + ('nv_mid=%d&page=' % item_id)
        for i in xrange(1,self.LIMIT+1):
            url = base_url + str(i)
            d  = BeautifulSoup(requests.get(url).text, 'lxml')
            is_empty = True
            for each in d.find_all(class_='atc'):
                is_empty = False
                crawl.append(each.text.strip())
            if is_empty:
                break
            if verbose:
                print 'Crawling %d/%d..' % (i, self.LIMIT)
        return crawl


    def get_category_prodid(self, cate_id, pages=3):
        urlbase = 'http://shopping.naver.com/search/list.nhn?pagingSize=40&productSet=model&sort=review&cat_id=%d&pagingIndex=' % cate_id
        ret = []
        for i in xrange(1,pages+1):
            url = urlbase + str(i)
            soup = BeautifulSoup(requests.get(url).text, 'lxml')
            items = soup.find_all(class_='info')
            for item in items:
                if item.find(class_='price').find('em'):
                    ret.append(int(item.find('a')['href'].split('mid=')[1].split('&')[0]))
        return ret


    def get_prod_name(self, prod_id):
        url = 'http://shopping.naver.com/detail/detail.nhn?nv_mid=%d' % prod_id
        return BeautifulSoup(requests.get(url).text, 'lxml').find(class_='h_area').find('h2').text


if __name__ == '__main__':
    pass
