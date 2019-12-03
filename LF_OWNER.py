import json
import boto3
import time
from random import randint
from boto3.dynamodb.conditions import Key

def lambda_handler(event, context):
    
    name=event["name"]
    ph_no="+1" + event["phno"]
    
    client = boto3.client('rekognition') 
    response = client.index_faces(CollectionId = 'MyCollection',
                                Image={'S3Object':{'Bucket':'liverekognitionphoto','Name':'frame.jpg'}},
                                DetectionAttributes=(),
                                ExternalImageId='frame.jpg')
    
    #return response
    faceID=response['FaceRecords'][0]['Face']['FaceId']
    
    dynamodb_resource = boto3.client('dynamodb')
    
    status1=dynamodb_resource.put_item(
        TableName='Visitors',
        Item= {
            "FaceId":{"S":faceID},
            "Name":{"S":name},
            "PhoneNumber":{"S":ph_no}
        }
    )
    OTP=str(GenerateOTP())
    status2=dynamodb_resource.put_item(
        TableName='Passcodes',
        Item= {
            "FaceId":{"S":faceID},
            "timeStamp":{"N":str(int(time.time()))},
            "pin":{"S":OTP}
        }
    )
    
    msg = 'This is your one time code: ' + OTP
    sns_client = boto3.client('sns',aws_access_key_id="AKIAWABDYZXZYICTFKVD", aws_secret_access_key="NLkS+/IvNUK0l25uCwHWSKXVxZauZWFlvkm92JK2",region_name="us-west-2")
    response=sns_client.publish(PhoneNumber=ph_no, Message=msg,)
    
    return{
      "status1":status1,
      "status2":status2
    }
    

def GenerateOTP():
    OTP=randint(100000,999999)
    isUnique=False
    passcodesTable = boto3.resource('dynamodb').Table('Passcodes').scan()["Items"]
    passcodes =[]
    for item in passcodesTable:
        passcodes.append(item["pin"])
    passcodes= set(passcodes)
    while(OTP in passcodes):
        OTP=randint(100000,999999)
            
    return OTP
