#!/usr/bin/env python
# -*- coding: utf-8 -*-
import requests
from bs4 import BeautifulSoup


class Crawler:

    def __init__(self, LIMIT=30):
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


    def get_category_collection_list(self):
        name = [
                u'패션의류',
                u'패션잡화',
                u'화장품/미용',
                u'디지털/가전',
                u'가구/인테리어',
                u'출산/육아',
                u'식품',
                u'스포츠/레저',
                u'생활/건강',
                u'여행/문화',
                u'면세점',
               ]
        ret = []

        for i in xrange(11):
            ret.append({
                    'id': 50000000 + i,
                    'name': name[i],
                })

        return ret


    def get_category_list(self, col_id):
        url = 'http://shopping.naver.com/category/category.nhn?cat_id=' + str(col_id)
        soup = BeautifulSoup(requests.get(url).text, 'lxml')

        ret = []

        for categories in soup.find_all(class_='category_list'):
            for category in categories.find_all('li'):
                if category.find('a') and category.find('a').get('href'):
                    try:
                        ret.append((category.find('a')['href'].split('id=')[1].split('&')[0], category.text))
                    except:
                        pass

        return ret


    def get_category_item_list(self, cat_id, pages=3):
        for page in xrange(1,pages+1):
            url = 'http://shopping.naver.com/search/list.nhn?pagingIndex='+str(page)+\
                  '&pagingSize=40&productSet=model&viewType=list&sort=review&searchBy=none&cat_id='+str(cat_id)+\
                  '&frm=NVSHMDL&sps=Y'
            soup = BeautifulSoup(requests.get(url).text, 'lxml')

            ret = []

            for item, img in zip(soup.find_all(class_='info'), soup.find_all(class_='_productLazyImg')):
                try:
                    title = item.find(class_='tit')
                    ret.append({
                            'name': title.text,
                            'id': int(title['href'].split('nv_mid=')[1].split('&')[0]),
                            'image': img['data-original'],
                            'price': item.find(class_='price').text.split(u'가격비교')[0].strip()
                        })
                except:
                    print 'Exception @', item

        return ret


    def get_category_name(self, cat_id):
        url = 'http://shopping.naver.com/search/list.nhn?cat_id=' + str(cat_id)
        soup = BeautifulSoup(requests.get(url).text, 'lxml')
        return soup.find(class_='category_tit').\
               find_all('span', class_='pic')[-1].\
               text.split(u"선택해제")[0].strip()


if __name__ == '__main__':
    pass
