import json
import boto3
from elasticsearch import Elasticsearch, RequestsHttpConnection
from aws_requests_auth.aws_auth import AWSRequestsAuth
from datetime import datetime

# new test2
def lambda_handler(event, context):
    s3 = boto3.client('s3')
    rekognition = boto3.client('rekognition')
    
    host = 'search-photos-fwtybnc24legngf7vwuoppmuqu.us-east-1.es.amazonaws.com'
    region = 'us-east-1'
    service = 'es'
    credentials = boto3.Session().get_credentials()
    awsauth = AWSRequestsAuth(
        aws_access_key=credentials.access_key,
        aws_secret_access_key=credentials.secret_key,
        aws_token=credentials.token,
        aws_host=host,
        aws_region=region,
        aws_service='es'
    )
    
    url = 'https://search-photos-fwtybnc24legngf7vwuoppmuqu.us-east-1.es.amazonaws.com/'
    es = Elasticsearch(url, connection_class=RequestsHttpConnection, http_auth=awsauth)
    print('connected to elasticsearch')
        
    for record in event['Records']:
        bucket = record['s3']['bucket']['name']
        photo = record['s3']['object']['key']
        print(bucket)
        print(photo)
        
        # get labels from rekognition
        response = rekognition.detect_labels(Image={
            'S3Object': {'Bucket': bucket, 'Name': photo}
        }, MaxLabels=10)
        
        labels = []
        for label in response['Labels']:
            labels.append(label['Name'])
        
        # insert to elasticsearch
        timestamp = datetime.now().strftime('%Y-%m-%dT%H:%M:%S')
        document = {
            "objectKey": photo,
            "bucket": bucket,
            "createdTimestamp": timestamp,
            "labels": labels
        }
        es.index(index="photos", doc_type="_doc", body=document)
        
        print(response)
        print(labels)
    
    return 'success!'
