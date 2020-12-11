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
client = boto3.client('lex-runtime')   

    
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
    
    
def check_labels(labels, queries):
    label_list = []
    for label in labels:
        for query in queries:
            if query.lower() in label.lower():
                label_list.append(label)
    return label_list


def search_picture(label_list):
    response = es.search(index="photos", body={
        "query": {
            "match_all" : {}
        }
    }, size=100)
    response = response['hits']['hits']
    index_list = []
    for i in range(len(response)):
        labels = response[i]['_source']['labels']
        for label in label_list:
            if label in labels:
                index_list.append(response[i]["_source"]["objectKey"])
    
    return index_list
    

def get_qurey(event, context):
    messages = event['query']
    lex_response = client.post_text(
                botName='photo_album',
                botAlias='test',
                userId='search_lambda',
                inputText=event['query']
            )
    #print('lex: ', lex_response)
    
    if lex_response['slots']['slotTwo'] == None :
        query = lex_response['slots']['slotOne']
    else:
        query = [lex_response['slots']['slotOne'], lex_response['slots']['slotTwo']]
    print('query: ', query)
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
    queries = get_qurey(event, context)
    label = check_labels(label_list, queries)
    if label:
        index_list = search_picture(label)
        print(index_list)
        move_to_album(index_list)
        return "success"
    else: 
        return "no label"