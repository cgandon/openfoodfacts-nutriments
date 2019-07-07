#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Fri Jun  7 10:41:11 2019

@author: Christian Gandon

Reminder of work in progress:
    OCR extraction assumes that first line is a condensed of the entire texts of the pix. it is purposedly ignore since it messes up with nutriment recognition, is this scalable?
    nb of line is estimated with a DBSCAN. empiric approach conclused on EPS being optimizedon Length of image / 50, is that scalable?
    Kmeans is used to spot nb of columns, but seems forcing it to 4 has better result. Is that scalable?
"""

import requests as r
import pandas as pd
import os as os
import json as json
import cv2
from sklearn.cluster import KMeans
from sklearn.cluster import KMeans
from sklearn.cluster import DBSCAN
import seaborn as sns
from fuzzywuzzy import process
from fuzzywuzzy import fuzz
import numpy as np
import requests
from PIL import Image
from io import BytesIO
import matplotlib.pyplot as plt

# =============================================================================
# get product data
# =============================================================================

def get_product_data(prod):
#    prod = "3560070762255"
    url_ocr = "https://world.openfoodfacts.org/cgi/nutrition.pl?code={}&id=nutrition_fr&process_image=1&ocr_engine=google_cloud_vision&annotations=1".format(prod)
    try:
        prd_json = r.get("https://world.openfoodfacts.org/api/v0/product/{}.json".format(prod)).json()
        url_nutri = prd_json["product"]["image_nutrition_url"]
        json_ocr = r.get(url_ocr).json()["nutrition_text_from_image_annotations"]["responses"][0]
        status="ok"
#    plt.imshow(test_image)
    except:
        status="ko"
        json_ocr = None
        url_nutri = None
    return url_nutri, json_ocr, status
    

# =============================================================================
# Collect Taxonomy information
# =============================================================================

def get_taxonomy(nut_file='nutriments.txt') :
    nut_tax_raw = open(nut_file,"r").read()
    nut_tax = pd.DataFrame(columns=["langu","ref","nut"])
    for line in nut_tax_raw.split("\n"):
#    print(line)
        try:
            langu, nut = line.split(":", maxsplit=2)
            if langu=="en":
                ref = nut
            nut_tax = nut_tax.append({"langu":langu, "ref":ref, "nut":nut}, ignore_index=True)
        except:
            pass
    return nut_tax


# =============================================================================
# Load OCR JSON file
# =============================================================================

def ocr_json_load(file): # open the JSON file produced by Google Cloud Vision OCR API
    with open(file) as json_file:
        return json.load(json_file)

# =============================================================================
# Display source picture (optional)
# =============================================================================

def show_ocr_source_image(image): # show the source image up on screen
    img = cv2.imread(image,1)
    height, width, depth = img.shape
    img2 = cv2.resize(img,(int(height/10), int(width/10)))
    cv2.imshow('image',img2)
    cv2.waitKey(-1)
    cv2.destroyWindow('image')

# =============================================================================
# Extract texts, language and image size from OCR content
# =============================================================================

def ocr_json_extract(data): # extract content from OCR file with texts and bounding box coordinates
    content = pd.DataFrame(index = range(len(data)), columns=["text","kmeans_3","dbscan","x0","x1","x2","x3","y0","y1","y2","y3"])
    n = 0
    coord=''
    for items in data["textAnnotations"][1:]:
        content.loc[n,"text"]=items["description"]
        for a in [0,1,2,3]:
            for b in ['x','y']:
                coord = str(b)+str(a)
#                print(coord)
                try:
                    content.loc[n,coord]=items["boundingPoly"]["vertices"][a][b]
                except:
                    content.loc[n,coord]=0
        n+=1
    height = data["fullTextAnnotation"]["pages"][0]["height"]
    content["mean_x"] = (content["x0"] + content["x1"]) / 2
    content["mean_y"] = (content["y0"] + content["y1"]) / 2
#    sorted = content.sort_values("y3", ascending=False).sort_values("x0", ascending=True) # sort ascending by upper left point Y coordinates, then lower left point X coordinates
    return content, data["textAnnotations"][0]["locale"], height

# =============================================================================
# Determine number of columns in nutriment table
# =============================================================================

def find_nb_columns(content,columns = None):
# build columns (assumed 3 for now)
    kmeans_i = []
    kmeans_score = []
    for i in range(1,10):
        kmeans_i.append(i)
        kmeans_tmp = KMeans(n_clusters = i,
                    init="k-means++",
                    max_iter = 400,
                    n_init = 10,
                    random_state = 0)
        try:
            result_tmp = kmeans_tmp.fit(content["mean_x"].values.reshape(-1,1))
            kmeans_score.append(kmeans_tmp.inertia_)

        except:
            result_tmp = None
            kmeans_score.append(0)
    kmeans_result = pd.DataFrame()
    kmeans_result["i"] = kmeans_i
    kmeans_result["score"] = kmeans_score


    for i in kmeans_result["i"]:
        try:
            kmeans_result.loc[i,"elbow"] = (kmeans_result.loc[i,"score"]-kmeans_result.loc[i-1,"score"])/(kmeans_result.loc[i+1,"score"]-kmeans_result.loc[i,"score"])
        except:
            pass
    #sns.lineplot(x=kmeans_i,y=kmeans_score)
    if columns is None:
        best = kmeans_result.i[kmeans_result["elbow"] == kmeans_result["elbow"].max()].values[0]
        print("Best match identified: {} columns".format(best))
    else:
       best = columns
       print("forced to {} columns".format(best))
    kmeans_tmp = KMeans(n_clusters = best,
            init="k-means++",
            max_iter = 400,
            n_init = 10,
            random_state = 0)
    result_tmp = kmeans_tmp.fit(content.loc[:,"x0"].values.reshape(-1,1))
    return kmeans_tmp

# =============================================================================
# Determine number of lines and build first raw table
# =============================================================================

def build_nutriment_table(content, kmeans_tmp, eps): # map text into back into a table format

    content["kmeans_3"] = kmeans_tmp.labels_

    # build lines (better use DBSCAN when you cannot tell how many centroids in advance)
    dbscan = DBSCAN(algorithm='auto', eps=eps, metric='euclidean', metric_params=None, min_samples=1, n_jobs=None, p=None).fit(content["mean_y"].values.reshape(-1,1))
    dbscan.labels_
    content["dbscan"] = dbscan.labels_

    # consolidate results in table
    table = pd.DataFrame(dtype = str, columns= content.kmeans_3.value_counts().index.values, index = content.dbscan.value_counts().index.sort_values().values)
    for x in content["dbscan"].value_counts().index.values:
        for y in content["kmeans_3"].value_counts().index.values:
            table.loc[x,y] = content.loc[(content["kmeans_3"]==y) & (content["dbscan"]==x),"text"].str.cat(sep=" ")
    return table

# =============================================================================
# Loop through raw table and clean up nutriments, allocate quantities etc...
# =============================================================================

def clean_nutriment_table(nut_table_raw, nut_tax, langu, threshold = 70):# identify nutriment columns
#    nut_list = ["ENERGIE","PROTEINES","GLUCIDES","LIPIDES","SUCRES","ACIDES GRAS SATURES", "FIBRES ALIMENTAIRES", "SODIUM","SELS MINERAUX", "VITAMINES"]
    nut_list = nut_tax[nut_tax["langu"] == langu]["nut"]
    nut_meas =["G","KG"]
    nut_table_clean = pd.DataFrame(index=nut_list, columns = ["label found","score_label", "quantity","score_quant"])
    nut_table_clean["score_label"] = 0
    nut_table_clean["score_quant"] = 0
    for x in nut_table_raw.index:
        new_qt_score = 0
        max_qt_score = 0
        qt_col = np.nan
        for y in nut_table_raw.columns:
            max_label_score = 0
            max_i = ''
            new_label_score  = 0
            for i in nut_table_clean.index:
                new_label_score = fuzz.token_set_ratio(nut_table_raw.loc[x,y],i)  # spot best matching label
                if new_label_score > max_label_score:
                    max_label_score = new_label_score
                    max_i = i
            try:
                if max_label_score > nut_table_clean.loc[max_i,"score_label"]:
                    nut_table_clean.loc[max_i,"label found"] = nut_table_raw.loc[x,y]
                    nut_table_clean.loc[max_i,"score_label"] = max_label_score
                    for y2 in nut_table_raw.columns:
                        new_qt_score = sum([a.upper() in nut_meas or a.isdigit() for a in nut_table_raw.loc[x,y2]]) # spot best matching quantities
                        if new_qt_score > max_qt_score:
                            max_qt_score = new_qt_score
                            qt_col = y2
                    nut_table_clean.loc[max_i,"quantity"] = nut_table_raw.loc[x,qt_col]
                    nut_table_clean.loc[max_i,"score_quant"] = max_qt_score
            except:
                pass
    return nut_table_clean[nut_table_clean["score_label"]>=threshold]

# =============================================================================
# Combine all into 1 function
# =============================================================================

def get_nutriments(json_ocr,  nut_tax):
#    data = ocr_json_load(test_ocr)
    content, langu, height = ocr_json_extract(json_ocr)
    kmeans_tmp = find_nb_columns(content)
    nut_table_raw = build_nutriment_table(content, kmeans_tmp, height/50)
    nut_table_clean = clean_nutriment_table(nut_table_raw, nut_tax, langu)
    nut_table_clean["nut_from_taxonomy"] = nut_table_clean.index
    nut_table_clean.index = [a for a in range(0, len(nut_table_clean))]
    return nut_table_clean.to_json(orient='index', force_ascii = False), nut_table_clean 

# =============================================================================
# download results to JSON
# =============================================================================

def nut_table_to_JSON(nut_table_clean, file):
    nut_table_clean.to_json(file, orient='index', force_ascii = False)
    print("nutriment table exported to {}".format(file))
 
