# -*- coding: utf-8 -*-
"""
Created on Fri Sep  7 21:54:26 2018

@author: zouco
"""


# note: 也可以用中文，没必要用英语

'''
 zoucongyu: to developer:
     I suggest to use 
         bc=basic_crawler(url), soup = bc.soup 
    instead of
        res = req.get(url), BeautifulSoup(res.text)
    to be more hard to detect

''' 

# import numpy as np
import pandas as pd
# import re
import os
# import random

from basic_crawler import basic_crawler
# from basic_crawler import proxy_formatter

# import matplotlib.pyplot as plt
# import time

from bs4 import BeautifulSoup


from wg_crawler import wg_spider
from wg_crawler import wg_preprocess
from wg_crawler import wg_analysis

class wg_crawler():
    '''
      This is main class, it serves as the interface. 
      The functions are realised in different classes.
      
    '''
        
    def run(self, start_page=1, end_page=10, path = 'material/', data_exists=True):
        # the default function, it will scrape some pages of the wg_gesucht and save the data in path
        if not data_exists:
            make_wg_gesucht_offline(start_page=start_page, end_page=end_page)
        self.ws = wg_spider_local()
        
        # get main page data
        self.ws.get_surface_data(start_page, end_page)
        path0 = path + 'The_wg_information_in_munich_0_{}.csv'.format(end_page-start_page)
        self.ws.df.to_csv(path0, encoding='utf-8')
        
        # go to the links to get more data to readable level
        self.ws.get_details()
        path1 = path + 'The_wg_information_in_munich_1_{}.csv'.format(end_page-start_page)
        self.ws.df.to_csv(path1, encoding='utf-8')
        
        # preprocess the data for the further analysis
        wp = wg_preprocess(self.ws.df)
        self.ws.df = wp.run()
        path2 = path + 'The_wg_information_in_munich_2_{}.csv'.format(end_page-start_page)
        self.ws.df.to_csv(path2, encoding='utf-8')
        
        self.df = self.ws.df
          
        
        
class wg_spider_local(wg_spider):
    df = None
    proxy = None
    
    def get_surface_data(self, start_page=1, end_page=10, all_pages=False):
        self.df = pd.DataFrame([], columns=['title', 'link', 'room_size', 'price', 'situation',
                               'renters_total', 'renters_male', 'renters_female', 'wanted_male', 
                               'wanted_female', 'no_gender_limit'])
        titles = []
        links = []
        sizes = []
        prices = []
        situations = []
        # The following six arrays describes the details of the situations
        renters_total = []   #1
        renters_male = []    #2
        renters_female = []  #3
        wanted_male = []     #4
        wanted_female = []   #5
        no_gender_limit = [] #6
        
        
        self.num_pages = end_page - start_page    
        
        if all_pages:
            end_page = 100  # todo: get the data from we
            
        for i in range(start_page-1, end_page):
            print('on page {} ... '.format(i))
            
            soup = self.load_soup_main(i)

            posts = soup.find_all('div',class_='offer_list_item')
            
            for p in posts:
                title_block = p.find('h3', class_='truncate_title')
                titles.append(title_block.text.strip())
                links.append('https://www.wg-gesucht.de/' + title_block.a['href'])
                
                detail_block = p.find('div', class_= 'detail-size-price-wrapper').text
                size, price = wg_spider_local.detail_info2size_and_price(detail_block)
                sizes.append(size)
                prices.append(price)

                situations, renters_total, renters_male, renters_female, wanted_male, wanted_female, no_gender_limit = self.get_situation_details(p)
            
        self.df.title = titles
        self.df.link = links
        
        self.df.room_size = sizes
        self.df.room_size = self.df.room_size.astype('float')
        
        self.df.price = prices
        self.df.price = self.df.price.astype('float')
        
        self.df.situation = situations
        self.df.renters_total = renters_total
        self.df.renters_male = renters_male
        self.df.renters_female = renters_female
        self.df.wanted_male = wanted_male
        self.df.wanted_female = wanted_female
        self.no_gender_limit = no_gender_limit
            
        
    def get_situation_details(post):
        situations = []
        renters_total = []   #1
        renters_male = []    #2
        renters_female = []  #3
        wanted_male = []     #4
        wanted_female = []   #5
        no_gender_limit = [] #6
        
        # Extract the information about the current renter
        situation_block = post.find('span', class_='noprint')
        situation_title = situation_block['title']
        situations.append(situation_title)
        
    
        title_split = situation_title.split()
        totalRenterString = title_split[0] # _er
        renterGenderString = title_split[2] #(_w,_m)
    
        num_total_renter = totalRenterString[0:renterGenderString.find("er")-1]
        num_female_renter = renterGenderString[renterGenderString.find("(")+1:renterGenderString.find("w")]
        num_male_renter = renterGenderString[renterGenderString.find(",")+1:renterGenderString.find("m")]

        renters_total.append(num_total_renter)
        renters_male.append(num_male_renter)
        renters_female.append(num_female_renter)
    
        # Extract the information about the wanted gender
        wanted_tags = post.find_all('img', class_='noprint')
        count = 0
        num_wanted_male = 0
        num_wanted_female = 0
        num_no_gender_limit = 0
        for wanted in wanted_tags:
            count = count + 1
            print(wanted["alt"] + str(count))
            content = wanted["alt"]
            if 'oder' in content:
                num_no_gender_limit += 1
            elif 'Mitbewohnerin' in content:
                num_wanted_female += 1
            elif 'Mitbewohner' in content:
                num_wanted_male += 1
            else:
                print("Error in get_situation_details: keyword not found")
    
        wanted_male.append(num_wanted_male)
        wanted_female.append(num_wanted_female)
        no_gender_limit.append(num_no_gender_limit)
        return situations, renters_total, renters_male, renters_female, wanted_male, wanted_female, no_gender_limit

        
    def get_details(self):

        cautions = []
        dates = []
        addresses = []
  
        for i in range(len(self.df.link)):
            
            soup = self.load_soup_post(i)
                        
            if soup is not None: 
                                          
                # get caution
                caution = wg_spider_local.get_caution_from_soup(soup)
                
                # get starttime
                date = wg_spider_local.get_date_from_soup(soup)
                
                # get address and zipcode
                address = wg_spider_local.get_addr_from_soup(soup)
                
            else:
                caution = None
                date = None
                address = None
            
            cautions.append(caution)
            dates.append(date)
            addresses.append(address)
            
            print('on entry {} ..'.format(i))
        
        self.df['caution'] = cautions
        self.df['date'] = dates
        self.df['address'] = addresses
        
    @staticmethod
    def load_local_html_as_soup(path):
        with open(path, 'rb') as f:
            soup = BeautifulSoup(f,'html5lib')
        return soup
              
    
    def load_soup_main(self,i):
        soup = wg_spider_local.load_local_html_as_soup('material/main_page_{}.html'.format(i))
        return soup
        
    def load_soup_post(self,i):
        page = i//20
        post = i%20
        soup = wg_spider_local.load_local_html_as_soup('material/main_page_{}/post_page{}.html'.format(page,post))
        return soup
        

    


def make_wg_gesucht_offline(start_page=1, end_page=10):
    
    for i in range(start_page-1, end_page):
        url = 'https://www.wg-gesucht.de/wg-zimmer-in-Muenchen.90.0.1.{}.html'.format(i)          
        bc = basic_crawler(url, safetime=(6,10))
        bc.save_html('main_page_{}'.format(i))
       
        soup = bc.soup   
        posts = soup.find_all('div',class_='offer_list_item')
        os.mkdir('material/main_page_{}'.format(i))
        for j in range(len(posts)):
            title_block = posts[j].find('h3', class_='truncate_title')
            link = 'https://www.wg-gesucht.de/' + title_block.a['href']
            
            bc = basic_crawler(link, safetime=(6,10))            
            bc.save_html('main_page_{}/post_page{}'.format(i,j))
            
            print('on page {} for entry {}...\n'.format(i,j))


def test():
    '''
        here you can test your program.
    '''
    
    # make_wg_gesucht_offline(start_page=2, end_page=2)
    ws = wg_spider_local()
    ws.get_surface_data(end_page=2)
    ws.get_details()

    wp = wg_preprocess(ws.df)
    ws.df = wp.run()
    print(ws.df)

    wc = wg_crawler()
    wc.run(end_page=2, data_exists=True)
    print(wc.df)
    


if __name__ == '__main__':
    
    pd.set_option('max_colwidth',200)
    pd.set_option('max_columns',None) 

    wc = wg_crawler()
    wc.run(end_page=2)
    print(wc.df)
    

    
    
    
    