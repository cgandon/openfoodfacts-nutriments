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
import time
import seaborn as sns

start = time.time()
# get a local test product list
product_list = list(pd.read_csv("OFF_sub.csv")["code"])

exec_time = pd.DataFrame(columns=["prod", "time"])

count = 0
skipped = 0
export_csv = pd.DataFrame()
# limit the loop to a few occurences for testing
max_nb_test = 100

for prod in product_list:
    # reset temp variables
    nut_json = None
    nut_table_clean = None

    #    prod= '0000000011686'
    if count == max_nb_test:
        break  

    # get OCR and JSON data from product code
    url_nutri, json_ocr, status = gn.get_product_data(prod)   

    # is data well retrieved? if not skip to next product
    if status=="ok":
        p_start = time.time()
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
        #gn.nut_table_to_JSON(nut_table_clean, 'data/'+prod+'.json')
        #for prod by prod export
        # nut_table_clean.to_csv("data/{}.csv".format(prod))

        # for 1 shot consolidated export
        # add image URL for easier manual check
        nut_table_clean["product"] = None
        nut_table_clean["url"] = None
        new_line = []
        new_line.insert(0,{"product":prod,"url":url_nutri})

#        nut_table_clean = pd.concat([pd.DataFrame(new_line), nut_table_clean], ignore_index=True, sort=False)
        export_csv = pd.concat([export_csv, pd.DataFrame(new_line), nut_table_clean], ignore_index=True, sort=False)
      
        p_end = time.time()
        p_duration = p_end-p_start
        p_time = []
        p_time.insert(0,{"product":prod,"time":p_duration})
        exec_time = pd.concat([pd.DataFrame(p_time),exec_time], ignore_index=True, sorted = False)
    else:
        skipped += 1
        
        pass
export_csv.to_csv("data/export.csv", sep="|")

end = time.time()
process_time = round(end-start,2)
processed = max_nb_test + skipped
print("Job done in {} seconds ({} sec per product), \n nb products: {}, \n processed: {}, \n skipped: {}.".format(process_time,(round(process_time/max_nb_test,2)),max_nb_test,processed,skipped))