#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Fri Jun  7 10:41:11 2019

@author: Christian Gandon

"""
import getNutriments as gn

# available products for test in Git default repo: 3560070762255, 00031858, 20000660
test_product = input(prompt="Enter a product code: ")
test_image = 'data/'+test_product+'.jpg'
test_ocr = 'data/'+test_product+'.json'

try:
    nut_tax
    print('taxonomy already loaded')
except:
    nut_tax = gn.get_taxonomy()
    print('loading taxonomy => done')

data = gn.ocr_json_load(test_ocr)
#gn.show_ocr_source_image(test_image)
content, langu, height = gn.ocr_json_extract(data)
kmeans_tmp = gn.find_nb_columns(content)
nut_table_raw = gn.build_nutriment_table(content, kmeans_tmp, height/50)
nut_table_clean = gn.clean_nutriment_table(nut_table_raw, nut_tax, langu)
gn.nut_table_to_JSON(nut_table_clean, 'data/nut_table_'+test_product+'.json')


import json
json_test = json.load(open('data/nut_table_'+test_product+'.json'))

