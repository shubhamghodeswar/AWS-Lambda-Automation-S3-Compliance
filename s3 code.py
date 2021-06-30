import json
import boto3
import botocore

def lambda_handler(event, context):
    # TODO implement
    tagKey = ''
    tagValue = ''
    bucketList = []
    client = boto3.client('s3')
    response = client.list_buckets()['Buckets']
    print (response)
    for bucket in response:
        
        try:
            responsetag = client.get_bucket_tagging(
                Bucket = bucket['Name']  
            )
            for r in responsetag['TagSet']:
                if(r['Key'] == 'approved_by' and r['Value'] == 'wba-cso'):
                    tagKey = r['Key']
                    tagValue = r['Value']
        except client.exceptions.ClientError as e:
            print("Error occured")
        
        
        if(tagKey == 'approved_by' and tagValue == 'wba-cso'):
            #do nothing
            print("S3 is good")
        else:
            try:
                access = client.get_public_access_block(Bucket=bucket['Name'])
                print(bucket['Name'])
                print (access)
            except client.exceptions.ClientError as e:
                if e.response['Error']['Code'] == 'NoSuchPublicAccessBlockConfiguration':
                    print(bucket['Name'])
                    print('\t Publicly Accessbile')
                    bucketList.append(bucket['Name'])
                
                # ====== Removing public access if the S3 bucket is public
                
                response = client.put_public_access_block(
                    Bucket=bucket['Name'],
                    PublicAccessBlockConfiguration={
                        'BlockPublicAcls': True,
                        'IgnorePublicAcls': True,
                        'BlockPublicPolicy': True,
                        'RestrictPublicBuckets': True
                    },
                )
                
                # ================= #
                
            else:
                print("uneected error: %s" % (e.response))
                
        # ======= Checking for S3 encryption and applying encryption if disabled ====== #
            try:
                enc = client.get_bucket_encryption(Bucket=bucket['Name'])
                rules = enc['ServerSideEncryptionConfiguration']['Rules']
                print('Bucket: %s, Encryption: %s' % (bucket['Name'], rules))
            except client.exceptions.ClientError as e:
                if e.response['Error']['Code'] == 'ServerSideEncryptionConfigurationNotFoundError':
                    bucketList.append(bucket['Name'])
                    #print('Bucket: %s, no server-side encryption' % (bucket['Name']))
                
                    responseenc = client.put_bucket_encryption(
                        Bucket=bucket['Name'],
                        ServerSideEncryptionConfiguration={
                            'Rules': [
                                {
                                    'ApplyServerSideEncryptionByDefault': {
                                        'SSEAlgorithm': 'AES256',
                                    },
                                },
                            ]
                        },
                    )
                
            else:
                print("Bucket: %s, unexpected error: %s" % (bucket['Name'], e))
                
        # ========= End of checking and applying S3 encryption ========= #
            
        
        
    
    send_s3_mail(bucketList)
        

def send_s3_mail(buckets):
    if(buckets == []):
        bucketStr = 'All buckets are encrypted'
    else:
        bucketStr = '\n'.join(map(str, buckets))
        bucketStr = '\n' + bucketStr + ' \n \n buckets have public access'
    ses_client = boto3.client('ses')
    ses_client.send_email(
        Source = 'partha.abdas@gmail.com',
        Destination = {
            'ToAddresses': ['shubhshubh2480@gmail.com']
        },
        Message = {
            'Subject': {
                'Data': 'S3 Encryption Notification',
                'Charset': 'utf-8'
            },
            'Body': {
                'Text': {
                    'Data': bucketStr
                }
            }
        }
    )