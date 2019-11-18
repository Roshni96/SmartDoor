import json
from boto3 import resource
from boto3.dynamodb.conditions import Key

def lambda_handler(event, context):
    
    accessCode = event["accessCode"]
    message = "Access Denied"
    
    dynamodb_resource = resource('dynamodb')
    tablePasscodes = dynamodb_resource.Table('Passcodes')
    response=tablePasscodes.scan(FilterExpression=Key('pin').eq(accessCode))
    
    if response["Count"] > 0:
        tableVisitor = dynamodb_resource.Table('Visitors')
        #remove the entry for OTP
        faceID=response["Items"][0]["FaceId"]
        tablePasscodes.delete_item(
            Key={
                'FaceId':faceID
            }
        )
        #Fetch the visitor
        response=tableVisitor.scan(FilterExpression=Key('FaceId').eq(faceID))
        message = "Access Granted to " + response["Items"][0]["Name"]
        
    return{
        'statusCode': 200,
        'message': message
    }
    