import json
import base64
import boto3
import cv2
import random
import time
from datetime import datetime
#sns_client = boto3.client('sns')
dynamodb_client = boto3.client('dynamodb')

def get_details(face_id):
	result = dynamodb_client.get_item(TableName= 'Visitors',  Key={'FaceId':{'S':str(face_id)}})

	if result['ResponseMetadata']['HTTPStatusCode'] == 200:
		if 'Item' in result.keys():
			phone = result['Item']['PhoneNumber']['S']
			return phone


def lambda_handler(event, context):
	matchedFace = 0
	unmatchedFace = 0

	for record in event['Records']:
		load = base64.b64decode(record['kinesis']['data'])
		print(load)
		load = json.loads(load)
		print(load)
		if(load['FaceSearchResponse'] != None):
			for face in load['FaceSearchResponse']:
				if(face['MatchedFaces'] != None and len(face['MatchedFaces'])> 0):
				    matchedFace += 1
				    face_id = face['MatchedFaces'][0]['Face']['FaceId']
				    print("matchedFace "+str(matchedFace)+" face id "+ face_id)
				    phone_num=get_details(face_id)
				    print(phone_num)
				    epoch = int(time.time())
				    OTP = ''
				    for _ in range(6):
				    	OTP += str(random.randint(0,9))
				    var = dynamodb_client.put_item(TableName = 'Passcodes', Item = { 'FaceId': {'S':str(face_id)}, 'pin': {'S':str(OTP)}, 'timeStamp': {'N':str(epoch)} })
				    
				    msg = 'This is your one time code: ' + OTP
				    sns_client = boto3.client('sns',aws_access_key_id="AKIAWABDYZXZYICTFKVD", aws_secret_access_key="NLkS+/IvNUK0l25uCwHWSKXVxZauZWFlvkm92JK2",region_name="us-west-2")
				    response=sns_client.publish(PhoneNumber=phone_num, Message=msg,)
				    response_x=sns_client.publish(PhoneNumber=phone_num,Message='https://smartdoor-rekognition.s3.amazonaws.com/visitor/visitor.html',)
				    print(msg)
				    print("message sent")
				    #print(message)
				    
				    
				    
				else:
				    kvs_client = boto3.client('kinesisvideo')
				    kvs_data_pt = kvs_client.get_data_endpoint(StreamARN='arn:aws:kinesisvideo:us-west-2:412391886323:stream/KVS1/1573767765155', APIName='GET_MEDIA')
				    print(kvs_data_pt)
				    end_pt = kvs_data_pt['DataEndpoint']
				    kvs_video_client = boto3.client('kinesis-video-media', endpoint_url=end_pt, region_name='us-west-2') # provide your region
				    record= event['Records'][0]
				    payload = base64.b64decode(record["kinesis"]["data"])			     # Decode Base64 encoded JSON data received from KDS
				    payload_obj=json.loads(payload)			      			     # JSON String to Object
				    frag_num = payload_obj["InputInformation"]["KinesisVideo"]["FragmentNumber"] # Get fragment number from data
				    kvs_stream = kvs_video_client.get_media(
				        StreamARN='arn:aws:kinesisvideo:us-west-2:412391886323:stream/KVS1/1573767765155', # kinesis stream arn
				        StartSelector={'StartSelectorType': 'FRAGMENT_NUMBER', 'AfterFragmentNumber': frag_num} # to keep getting latest available chunk on the stream
				        )
				    print(kvs_stream)
				    with open('/tmp/stream.mkv', 'wb') as f:
				    	streamBody = kvs_stream['Payload'].read(1024*2048) # reads min(16MB of payload, payload size) - can tweak this
				    	f.write(streamBody)
				    	# use openCV to get a frame
				    	cap = cv2.VideoCapture('/tmp/stream.mkv')
				    	ret, frame = cap.read()
				    	cv2.imwrite('/tmp/frame.jpg', frame)
				    	s3_client = boto3.client('s3')
				    	s3_client.upload_file('/tmp/frame.jpg', 'liverekognitionphoto', 'frame.jpg')
				    	cap.release()
				    	print('Image uploaded')
				    	unmatchedFace += 1
				    	s3Client=boto3.client('s3')
				    	object1=s3Client.generate_presigned_url('get_object',Params={'Bucket':'liverekognitionphoto','Key': 'frame.jpg'})
				    	sns_client = boto3.client('sns',aws_access_key_id="AKIAWABDYZXZYICTFKVD", aws_secret_access_key="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",region_name="us-east-1")
				    	response1=sns_client.publish(PhoneNumber= "+19293326898", Message='<a href={0}>link</a>'.format(object1))
				    	response2=sns_client.publish(PhoneNumber= "+19293326898",Message='https://smartdoor-rekognition.s3.amazonaws.com/owner/owner.html')
				    	print(response1)
				    	print(object1)
				    


	if(matchedFace > 0 or unmatchedFace > 0):
		message = str(matchedFace) + ' Known Person(s) found ' + str(unmatchedFace) + ' Unknown Person(s) on Video Feed'
		# sns_client = boto3.client('sns',aws_access_key_id="AKIAWABDYZXZYICTFKVD", aws_secret_access_key="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",region_name="us-east-1")
		# response = sns_client.publish(PhoneNumber = "+19293326898",Message=message)
		# print("message sent")
		print(message)