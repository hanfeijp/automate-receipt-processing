# The script MUST contain a function named azureml_main
# which is the entry point for this module.

# imports up here can be used to 
import pandas as pd
import json
import time
import requests
from io import StringIO
import dateutil.parser as dparser
import re

# url for Microsoft's Cognitive Services - Custom Vision API - OCR
_ocrurl = 'https://westus.api.cognitive.microsoft.com/vision/v1.0/ocr'
_cvurl = 'https://southcentralus.api.cognitive.microsoft.com/customvision/v1.0/Prediction/this-will-be-a-string-unique-to-your-trained-model

# maximum number of retries when posting a request
_maxNumRetries = 10

# The entry point function can contain up to two input arguments:
#   Param<dataframe1>: a pandas.DataFrame
#   Param<dataframe2>: a pandas.DataFrame
def azureml_main(dataframe1 = None, dataframe2 = None):

    # Get the OCR key
    VISION_API_KEY = str(dataframe2['Col1'][0])
    IRIS_API_KEY = str(dataframe2['Col2'][0])

    # Load the file containing image url and label
    df_url_label = dataframe1
            
    # create an empty pandas data frame
    df = pd.DataFrame({'Text' : [], 'Category' : [], 'ReceiptID' : [], 'CVClass' : [], 'InferedTotal': []})

    # extract image url, setting OCR API parameters, process request
    for index, row in df_url_label.iterrows():
        imageurl = row['file']
        reqbody = { 'url': imageurl } ; 
        reqfile = None

        # setting OCR parameters
        ocr_params = { 'language': 'en', 'detectOrientation ': 'true'} 
        ocr_headers = dict()
        ocr_headers['Ocp-Apim-Subscription-Key'] =  VISION_API_KEY
        ocr_headers['Content-Type'] = 'application/json' 

        # setting IRIS parameters
        cv_params = {} 
        cv_headers = dict()
        cv_headers['Prediction-Key'] =  IRIS_API_KEY
        cv_headers['Content-Type'] = 'application/json' 

        try:
            ocr_result = processRequest( _ocrurl, reqbody, reqfile, ocr_headers, ocr_params )
        except:
            ocr_result = None

        if ocr_result is not None:
            # extract text
            text = extractText(ocr_result)
            total = extractTotal(text)

            # populate dataframe
            df.loc[index,'Text'] = text
            df.loc[index, 'InferedTotal'] = total
        else:
            # populate dataframe
            df.loc[index,'Text'] = None
            df.loc[index, 'InferedTotal'] = None
        
        try:
            cv_result = processRequest( _cvurl, reqbody, reqfile, cv_headers, cv_params )
        except:
            cv_result = None
            
        if cv_result is not None:
            # extract text
            text = extractCV(cv_result);         
            # populate dataframe
            df.loc[index,'CVClass'] = text
        else:
            # populate dataframe
            df.loc[index,'CVClass'] = None

        # 'Category' is the label
        df.loc[index,'Category'] = row['category']
        df.loc[index,'ReceiptID'] = row['file']
        
    return df

# Extract amounts from text
def extractTotal(text):    
    pattern = re.compile(r'[0-9]{1,3}[. ,][0-9]{2} ');

    amount_array = []

    for amounts in re.findall(pattern, text):
        amounts = amounts.replace(' ','.')
        amounts = amounts.replace(',','.')
        amounts = amounts[0:-1]
        amount_array.append(amounts)  

    if amount_array:
        return max(amount_array)
    else:
        return None
        
# Extract text only from OCR's response
def extractText(result):
    text = ""
    for region in result['regions']:
        for line in region['lines']:
            for word in line['words']:
                text = text + " " + word.get('text')
    return text

# Extract top result only from IRIS response
def extractCV(result):
    if result['Predictions'][0]:
        return str(result['Predictions'][0]['Tag'])
    else:
        return ""
      
# Process request
def processRequest( endpoint_url, image_url, image_file, headers, params ):

    retries = 0
    result = None

    while True:
        response = requests.request( 'post', endpoint_url, json = image_url, data = image_file, headers = headers, params = params )

        if response.status_code == 429: 
            print( "Message: %s" % ( response.json()['message'] ) )

            if retries <= _maxNumRetries: 
                time.sleep(1) 
                retries += 1
                continue
            else: 
                print( 'Error: failed after retrying!' )
                break

        elif response.status_code == 200 or response.status_code == 201:
            if 'content-length' in response.headers and int(response.headers['content-length']) == 0: 
                result = None 
            elif 'content-type' in response.headers and isinstance(response.headers['content-type'], str): 
                if 'application/json' in response.headers['content-type'].lower(): 
                    result = response.json() if response.content else None 
                elif 'image' in response.headers['content-type'].lower(): 
                    result = response.content
        else:
            print(response.json()) 
            print( "Error code: %d" % ( response.status_code ) ); 
            print( "Message: %s" % ( response.json()['message'] ) ); 

        break

    return result 