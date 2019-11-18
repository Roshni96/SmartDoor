import json
import boto3
import time
from random import randint
from boto3.dynamodb.conditions import Key

def lambda_handler(event, context):
    
    name=event["name"]
    ph_no="+1" + event["phno"]
    S3Object=event["S3Object"].split('/')[-1]
    
    faceID = index_face('MyCollection', 'liverekognitionphoto', S3Object)

    dynamodb_resource = boto3.client('dynamodb')
    
    status1=dynamodb_resource.put_item(
        TableName='Visitors',
        Item= {
            "FaceId":{"S":response['FaceRecords']['Face']['FaceId']},
            "Name":{"S":name},
            "PhoneNumber":{"S":ph_no}
        }
    )
    
    status2=dynamodb_resource.put_item(
        TableName='Passcodes',
        Item= {
            "FaceId":{"S":faceID},
            "timeStamp":{"N":str(int(time.time()))},
            "pin":{"S":str(GenerateOTP())}
        }
    )
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


def index_face(collection_id, bucket_name, bucket_file_name):
    
        print("Indexing[" + bucket_name + ":" + bucket_file_name + "] into collection[" + collection_id + "]")
        client = boto3.client('rekognition') 
        response = client.index_faces(CollectionId = collection_id,
                                    Image={'S3Object':{'Bucket':bucket_name,'Name':bucket_file_name}},
                                    DetectionAttributes=(),
                                    ExternalImageId=bucket_file_name)

        if len(response['FaceRecords']) > 0:
            return response['FaceRecords'][0]['Face']['FaceId']
        else:
            print("No Faces Found in image")
            return None