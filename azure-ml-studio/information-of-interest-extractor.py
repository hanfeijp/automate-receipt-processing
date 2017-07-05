# The script MUST contain a function named azureml_main
# which is the entry point for this module.

# imports up here can be used to 
import pandas as pd
import urllib2
import json

# The entry point function can contain up to two input arguments:
#   Param<dataframe1>: a pandas.DataFrame
#   Param<dataframe2>: a pandas.DataFrame
def azureml_main(dataframe1 = None, dataframe2 = None):
    
    imageUrl =  dataframe1.iloc[0]['Url']

    categoryPredictionUrl =  dataframe2['Url'][0]
    categoryPredictionKey = dataframe2['Key'][0]
    categoryPrediction = getCategoryPrediction(imageUrl, categoryPredictionUrl, categoryPredictionKey)
    
    textVendorPredictionUrl = dataframe2['Url'][1]
    textVendorPredictionKey = dataframe2['Key'][1]
    logoVendorPredictionUrl = dataframe2['Url'][2]
    logoVendorPredictionKey = dataframe2['Key'][2]
    vendorPrediction = getVendorPrediction(imageUrl, logoVendorPredictionUrl, logoVendorPredictionKey, textVendorPredictionUrl, textVendorPredictionKey)
    
    print(vendorPrediction)
    #Merge dataframe
    df = pd.DataFrame({'ItemId' : [], 'Category' : [], 'CategoryConfidence' : [], 'Retailer': [], 'RetailerConfidence': [],'Total': [],'Text': []})
    df.loc[0,'ItemId'] = categoryPrediction ['ItemId']
    df.loc[0,'Category'] = categoryPrediction ['Category']
    df.loc[0,'CategoryConfidence'] = categoryPrediction ['CategoryConfidence']    
    df.loc[0,'Retailer'] = vendorPrediction['Vendor']    
    df.loc[0,'RetailerConfidence'] = vendorPrediction['VendorConfidence']
    df.loc[0,'Total'] = categoryPrediction ['Total']
    df.loc[0,'Text'] = categoryPrediction ['Text']
    
    print('Results')
    print(df)
    
    return df

def getCategoryPrediction(imageUrl, url, key):
    data = {
            "Inputs": {
                    "input1":
                    [
                        {
                                'Url': imageUrl,   
                        }
                    ],
            },
        "GlobalParameters":  {
        }
    }
        
    header = {'Content-Type':'application/json', 'Authorization':('Bearer '+ key)}
    result = extractResultFromWebServices(processRequest(url, data, header))
    print(result)
    return result
    
def getVendorPrediction(imageUrl, urlLogoPrediction, urlLogoKeyPrediction, urlTextPrediction, urlTextKeyPrediction):
    
    body = { 'url': imageUrl }; 
        
    #first, we call the prediction by logo
    headers = {'Content-Type':'application/json', 'Prediction-Key':urlLogoKeyPrediction}
    customVisionResult = extractResultFromCustomVisionApi(processRequest(urlLogoPrediction, body, headers))
    
    if customVisionResult is not None and customVisionResult['Tag'] != 'Unknown':
        print('We got prediction by logo !!!')
        df = df = {'Vendor': customVisionResult['Tag'], 'VendorConfidence': customVisionResult['Probability']}
        result = df
    else:
        #then we call the prediction by text extraction    
        print('We got prediction text.')
        
        data = {
                "Inputs": {
                        "input1":
                        [
                            {
                                    'url': imageUrl,   
                            }
                        ],
                },
            "GlobalParameters":  {
            }
        }
        
        headers = {'Content-Type':'application/json', 'Authorization':('Bearer '+ urlTextKeyPrediction)}
        result = extractResultFromWebServices(processRequest(urlTextPrediction, data, headers))
        
    return result;
    
def extractResultFromCustomVisionApi(response):
    return response['Predictions'][0];

def extractResultFromWebServices(response):
    return response['Results']['output1'][0];

def processRequest(url, data, headers):
    
    body = str.encode(json.dumps(data))
        
    req = urllib2.Request(url, body, headers)
    
    try:
        response = urllib2.urlopen(req)
    
        result = json.loads(response.read())
        
    except urllib2.HTTPError, error:
        print("The request failed with status code: " + str(error.code))
    
        # Print the headers - they include the requert ID and the timestamp, which are useful for debugging the failure
        print(error.info())
        print(json.loads(error.read()))
        
    return result;
    