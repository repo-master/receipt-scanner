import os
from dotenv import load_dotenv
import boto3
import cv2
import numpy as np

load_dotenv()

AWS_REGION = os.getenv('AWS_REGION')
AWS_ACCESS_KEY_ID=os.getenv('AWS_ACCESS_KEY_ID')
AWS_SECRET_ACCESS_KEY=os.getenv('AWS_SECRET_ACCESS_KEY')



def extract_text_from_image(image):
    # with open(image_name, 'rb') as image:
    #     imageBytes = image.read()


    _, encoded_image = cv2.imencode('.jpg', image)

    # Convert the encoded image data to a bytearray
    imageBytes = np.array(encoded_image).tobytes()

    print(type(imageBytes))

    textract = boto3.client(
        'textract',         
        region_name=AWS_REGION,
        aws_access_key_id=AWS_ACCESS_KEY_ID,
        aws_secret_access_key=AWS_SECRET_ACCESS_KEY)

    # Call Amazon Textract
    response = textract.detect_document_text(Document={'Bytes': imageBytes})
    height, width, _ = image.shape

    # Print detected text
    extracted_text = []
    for item in response["Blocks"]:
        if item["BlockType"] == "LINE":
            dict_ = {
                    "Confidence": item["Confidence"],
                    "Text": item['Text'],
                    "Width": item["Geometry"]["BoundingBox"]['Width']*width,
                    "Height": item["Geometry"]["BoundingBox"]['Height']*height,
                    "x":  item["Geometry"]["BoundingBox"]['Top']*height,
                    "y": item["Geometry"]["BoundingBox"]['Left']*width
                    }
            extracted_text.append(dict_)

    return extracted_text

