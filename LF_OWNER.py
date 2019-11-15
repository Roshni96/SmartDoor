import json
from boto3 import resource
from boto3.dynamodb.conditions import Key

def lambda_handler(event, context):
    
    dynamodb_resource = resource('dynamodb')
    tablePasscodes = dynamodb_resource.Table('Visitors')
    