#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Fri Jun  7 10:41:11 2019

@author: Christian Gandon

"""
import getNutriments as gn
import pandas as pd
import matplotlib.pyplot as plt
from PIL import Image
import json

# get a local test product list
product_list = list(pd.read_csv("OFF_sub.csv")["code"])

count = 0
# limit the loop to a few occurences for testing
max_nb_test = 20

for prod in product_list[:1000]:
#    prod= '0000000011686'
    if count == max_nb_test:
        break  

    # get OCR and JSON data from product code
    url_nutri, json_ocr, status = gn.get_product_data(prod)   

    # is data well retrieved? if not skip to next product
    if status=="ok":
        count+=1
        print(prod)
    # get taxonomy (only needed first time)
        try:
            nut_tax
            print('taxonomy already loaded')
        except:
            nut_tax = gn.get_taxonomy()
            print('loading taxonomy => done')
    
    # get nutriment tables as json + csv + to local drive
        nut_json, nut_table_clean = gn.get_nutriments(json_ocr,  nut_tax)
        gn.nut_table_to_JSON(nut_table_clean, 'data/'+prod+'.json')
        # add image URL for easier manual check
        nut_table_clean = nut_table_clean.append([url_nutri], ignore_index=True)
        nut_table_clean.to_csv("data/{}.csv".format(prod))

    else:
        pass
