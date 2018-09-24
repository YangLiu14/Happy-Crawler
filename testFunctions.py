#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Sun Sep 23 20:13:11 2018

@author: lander14
"""


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



       


print('on page {} ... '.format(1))

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

         

url = 'https://www.wg-gesucht.de/wg-zimmer-in-Muenchen.90.0.1.{}.html'.format(1)          
bc = basic_crawler(url, safetime=(6,10))
soup = bc.soup

# print(bc.response.status_code)
# print(bc.soup.prettify())

posts = soup.find_all('div',class_='offer_list_item')

def get_situation_details(post):
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
        

for p in posts:
    title_block = p.find('h3', class_='truncate_title')
    titles.append(title_block.text.strip())
    links.append('https://www.wg-gesucht.de/' + title_block.a['href'])
    detail_block = p.find('div', class_= 'detail-size-price-wrapper').text
    size, price = wg_spider.detail_info2size_and_price(detail_block)
    sizes.append(size)
    prices.append(price)
    
    get_situation_details(p)



