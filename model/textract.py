import os
import boto3
from dotenv import load_dotenv
import cv2
import numpy as np
import pandas as pd

load_dotenv()

AWS_REGION = os.getenv('AWS_REGION')
AWS_ACCESS_KEY_ID=os.getenv('AWS_ACCESS_KEY_ID')
AWS_SECRET_ACCESS_KEY=os.getenv('AWS_SECRET_ACCESS_KEY')


def process_expense_analysis(image, client):
    _, encoded_image = cv2.imencode('.jpg', image)

    # Convert the encoded image data to a bytearray
    imageBytes = np.array(encoded_image).tobytes()        

    response = client.analyze_expense(
        Document={'Bytes': imageBytes})
    
    recipt = {}
    recipt['summary'] = extract_summary(response['ExpenseDocuments'][0]['SummaryFields'])

    recipt['table'] = get_table_field(response['ExpenseDocuments'][0]['LineItemGroups'])
    return recipt


def get_table_field(table_field):
    table = {}
    for line in table_field[0]['LineItems']:
        for field in line['LineItemExpenseFields']:
            try:
                table[field['Type']['Text']].append(field['ValueDetection']['Text'])
            except KeyError:
                table[field['Type']['Text']]=[]
                table[field['Type']['Text']].append(field['ValueDetection']['Text'])
    try:
        df = pd.DataFrame(table)
        print(df)
    except ValueError:
        print("----x-----"*10)
        print("Faced Error as not equal number of rows extracted")
        print("----x-----"*10)

    return table


def extract_summary(summary_field):
    vendor_info = ['VENDOR_NAME','VENDOR_ADDRESS','VENDOR_GST_NUMBER','VENDOR_PHONE']
    recipt_details = ['AMOUNT_PAID','INVOICE_RECEIPT_DATE','INVOICE_RECEIPT_ID','SERVICE_CHARGE','SUBTOTAL','TAX','TOTAL']
    reciver_details = ['TAX_PAYER_ID','RECEIVER_NAME']
    OTHER = ['Item Count:','Qty Count :']
    response = {}
    response['Vendor']={}
    response['Recipt_details']={}    
    response['Recipt_details']['OTHER']={}    
    response['Customer']={}

    for item in summary_field:
        if item['Type']['Text'] in vendor_info:
            response['Vendor'][item['Type']['Text']]=item['ValueDetection']['Text']
        elif item['Type']['Text'] in recipt_details:
            response['Recipt_details'][item['Type']['Text']] = item['ValueDetection']['Text']
        elif item['Type']['Text'] == 'OTHER' and item['LabelDetection']['Text'] in OTHER:
            response['Recipt_details']['OTHER'][item['LabelDetection']['Text']]= item['ValueDetection']['Text']
        elif item['Type']['Text'] in reciver_details:
            response['Customer'][item['Type']['Text']] = item['ValueDetection']['Text']
    return response


def extract_text_from_image(image):
    client = boto3.client(
        'textract',         
        region_name=AWS_REGION,
        aws_access_key_id=AWS_ACCESS_KEY_ID,
        aws_secret_access_key=AWS_SECRET_ACCESS_KEY)

    return process_expense_analysis(image, client)

