<h1> Nutriment table extraction </h1>

This is a contribution to Open Food Fact work aiming at extracting Nutriment table informations from packaging pictures.

<h2>This work assumes that:</h2>
- OFF product information contains a cropped and rotated picture for nutriments
- OFF product has an OCR output available in JSON format provided by Google Computer Vision API
- the taxonomy of nutriments has been pulled from https://github.com/openfoodfacts/openfoodfacts-server/blob/master/taxonomies/nutriments.txt

<h2>How to use this package:</h2>
- getNutriments.py can be included in any python script (import getNutriments)
- 3 test products are provided in the "/data" folder (image & OCR)
- the Example.py provide a "hello world" example of calling all functions available in getNutriments

<h2>Details of getNutriments.py functions</h2>
- **get_taxonomy():** this method build a list of known nutriments from the txt file available on OFF Github.
- **ocr_json_load(file):** this method load the JSON of OCR content
- **gn.show_ocr_source_image(image):** this method brings up the nutriment source picture in a popup window; It's optional and comment by default in Example.py
- **ocr_json_extract(data):** this method read OCR JSON and extract from it the text content, the language (needed to match with taxonomy of nutriments later on), and the dimension of table from bounding box (will be used to set a tolerance on later algo that try and count number of line/columns in table)
- **find_nb_columns(content,columns = None):** this methods tries and determine the number of columns in the nutriment tables. It uses a Kmeans classification on bounding boxes coordinated, simulates the Kmeans with 1 to 10 columns and picks up the ideal one based on the "elbow" graphical approach on inertia factor. Alternatively, a number of columns can be forced (like in Example.py where number of columns in forced to 4)
- **build_nutriment_table(content, kmeans_tmp, eps):** this method tries to determine the number of columns using a DBSCAN algorithm. DBSCAN advantage is that it does not require a target number of groups as an input, which is more relevant that kmeans in trying to count lines. indeed columns will often be 2,3 or 4, but number of line might vary much more. The "epsilon" factore of DBSCAN is set to "1/50th of picture heighth". This is arbitrary and set from empirical experiement. Once number of line and columns are both identified, this methods produces a table where OCR content is allocated to lines/columns
- **clean_nutriment_table(nut_table_raw, nut_tax, langu, threshold = 1):** this methods loops through raw nutriment table and will first try and match it with nutriment taxonomy. If a satisfying result is obtained (empirical experiement concluded that 70 was the most viable threshold, thus set by default), the text is considered a nutriment. The routine will then scan other columns to try and spot a quantity, by measuring occurences of digits and "g" or "kg". All outputs are consolidated in a nut_table_clean table.

<h2>Status and next steps</h2>
- OCR extraction seems to include on first line  a condensed version of the entire texts of the pix. This first line is therefore purposedly ignored in the code since it messes up with nutriment recognition, but is this really scalable? will it be true for all products?
- nb of line is estimated with a DBSCAN: empiric approach conclused on EPS being optimizedon Length of image / 50, is that scalable? will it be the case on all picture
- Kmeans is used to spot nb of columns, but seems forcing it to 4 has better result. Is that scalable? will it be the case with all pictures?
