import json
import boto3
from elasticsearch import Elasticsearch, RequestsHttpConnection
from aws_requests_auth.aws_auth import AWSRequestsAuth


host = 'search-photos-fwtybnc24legngf7vwuoppmuqu.us-east-1.es.amazonaws.com'
region = 'us-east-1'
service = 'es'
credentials = boto3.Session().get_credentials()
awsauth = AWSRequestsAuth(aws_access_key=credentials.access_key,
                             aws_secret_access_key=credentials.secret_key,
                             aws_region=region,
                             aws_service=service,
                             aws_token=credentials.token,
                             aws_host=host)

es = Elasticsearch(
    hosts=[{'host': host, 'port': 443}],
    http_auth=awsauth,
    use_ssl=True,
    verify_certs=True,
    connection_class=RequestsHttpConnection
     )

s3 = boto3.resource('s3')
    
    
def search_labels():
    response = es.search(index="photos", body={
        "query": {
            "match_all" : {}
        }
    }, size=100)
    response = response['hits']['hits']
    #print("response:", response)
    
    label_list = []
    for i in range(len(response)):
        labels = response[i]['_source']['labels']
        for label in labels:
            label_list.append(label)
    
    label_list = list(set(label_list))
    #print('labels:', label_list)
    return label_list
    
    
def check_labels(labels, query):
    for label in labels:
        if query.lower() in label.lower():
            return label
            break


def search_picture(label):
    response = es.search(index="photos", body={
        "query": {
            "match_all" : {}
        }
    }, size=100)
    response = response['hits']['hits']
    index_list = []
    for i in range(len(response)):
        labels = response[i]['_source']['labels']
        if label in labels:
            index_list.append(response[i]["_source"]["objectKey"])
    
    return index_list
    

def get_qurey(event, context):
    messages = event['query']
    messages = messages.split()
    query = messages[len(messages)-1].lower()
    return query
    

def move_to_album(key_list):
    bucket = s3.Bucket('hw3-display-album')
    bucket.objects.all().delete()
    extra_args = {
    'ACL': 'public-read'
    }
    for key in key_list:
        print(key)
        copy_source = {
        'Bucket': 'coms6998-b2',
        'Key': key
     }
        try:
            s3.meta.client.copy(copy_source, 'hw3-display-album', 'album/'+key, extra_args)
        except:
            continue


def lambda_handler(event, context):
    print("event: ", event)
    label_list = search_labels()
    query = get_qurey(event, context)
    label = check_labels(label_list, query)
    if label:
        index_list = search_picture(label)
        print(index_list)
        move_to_album(index_list)
        return "success"
    else: 
        return "no label"