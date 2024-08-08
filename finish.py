import boto3
import os
import pandas as pd
from datetime import datetime
from botocore.exceptions import ClientError

# parmeters
region = 'us-west-2'
lambda_function_name = 'StopEC2InstanceFunction'

# load finish_key
finish_key = pd.read_csv('finish_key.csv')
bucket_name, key_name, secret_name = finish_key['0'].tolist()

### Step 1: Download and Delete Files from S3 Bucket

# create a directory for the results; change to that directory
currentDateAndTime = str(datetime.now())[:-7]
folder_name = 'results - ' + currentDateAndTime
folder_name = folder_name.replace(':', '-')
cwd = os.getcwd()
results_wd = cwd + '\ '
results_wd = results_wd[:-1] + folder_name
os.mkdir(results_wd)
os.chdir(results_wd)

# list the files
def list_files(bucket_name):
    s3_client = boto3.client('s3')
    try:
        # List objects in the specified S3 bucket
        response = s3_client.list_objects_v2(Bucket=bucket_name)
        if 'Contents' in response:
            return [obj['Key'] for obj in response['Contents']]
        else:
            return []
    except ClientError as e:
        print(f"An error occurred: {e}")
        return []

all_files = list_files(bucket_name)

# download the files
def download_file(bucket_name, file_key, local_dir):   
    s3_client = boto3.client('s3')
    try:
        filename = local_dir + '\ '
        filename = filename[:-1] + file_key
        s3_client.download_file(bucket_name, file_key, filename)
    except:
        pass

for file_key in all_files:
    download_file(bucket_name, file_key, results_wd)

# delete the files
def delete_files(bucket_name, files_to_delete):
    s3_client = boto3.client('s3')
    delete_request = {'Objects': [{'Key': file} for file in files_to_delete]}
    try:
        # Delete the specified files
        response = s3_client.delete_objects(Bucket=bucket_name, Delete=delete_request)
        
        # Check for errors
        if 'Errors' in response:
            print("Errors occurred:")
            for error in response['Errors']:
                print(f" - {error['Key']}: {error['Message']}")
    except ClientError as e:
        print(f"An error occurred: {e}")
        
delete_files(bucket_name, all_files)
    
### Step 2: Delete S3 Bucket
try:    
    s3 = boto3.resource('s3')
    bucket = s3.Bucket(bucket_name)
    bucket.delete()
except:
    pass

### Step3: Delete Keypairs
try:
    client = boto3.client('ec2', region_name=region)
    response = client.describe_key_pairs(KeyNames=['dtk-vm-spin-keypair-3936678'])
    key_pair_id = response["KeyPairs"][0]["KeyPairId"]
    response = client.delete_key_pair(KeyName=key_name, KeyPairId=key_pair_id)
except:
    pass

### Step 4: Delete Secret
try:
    secrets_client = boto3.client('secretsmanager', region_name=region)  # Replace with your region
    get_secret_value_response = secrets_client.get_secret_value(SecretId=secret_name)
    Secret_Id = get_secret_value_response['ARN']
    response = secrets_client.delete_secret(SecretId=Secret_Id)
except:
    pass

### Step 5: Delete Lambda Function
try:
    lambda_client = boto3.client('lambda', region_name=region)
    response = lambda_client.delete_function(FunctionName=lambda_function_name)
except:
    pass

### Step 6: Delete Lanbda IAM role
try:
    iam = boto3.client('iam', region_name=region)
    response = iam.detach_role_policy(RoleName='LambdaEC2FileCheckRole', PolicyArn='arn:aws:iam::aws:policy/AmazonEC2FullAccess')
    response = iam.detach_role_policy(RoleName='LambdaEC2FileCheckRole', PolicyArn='arn:aws:iam::aws:policy/AmazonS3FullAccess')
    response = iam.detach_role_policy(RoleName='LambdaEC2FileCheckRole', PolicyArn='arn:aws:iam::aws:policy/CloudWatchFullAccess')
    response = iam.detach_role_policy(RoleName='LambdaEC2FileCheckRole', PolicyArn='arn:aws:iam::aws:policy/AmazonSNSFullAccess')
    response = iam.detach_role_policy(RoleName='LambdaEC2FileCheckRole', PolicyArn='arn:aws:iam::aws:policy/SecretsManagerReadWrite')
    response = iam.detach_role_policy(RoleName='LambdaEC2FileCheckRole', PolicyArn='arn:aws:iam::aws:policy/AmazonEventBridgeFullAccess')
    response = iam.delete_role(RoleName='LambdaEC2FileCheckRole')
except:
    pass


























# Configuration parameters
instance_id = 'your-instance-id'
region = 'us-west-2'
key_name = 'your-key-pair-name'
key_path = 'path-to-your-private-key.pem'
file1 = '/path/to/remote/file1'
file2 = '/path/to/remote/file2'
local_file1 = 'local_file1'
local_file2 = 'local_file2'

# Initialize boto3 clients
ec2 = boto3.client('ec2', region_name=region)

# Start EC2 instance
def start_instance(instance_id):
    ec2.start_instances(InstanceIds=[instance_id])
    print(f'Instance {instance_id} started')

# Wait for instance to be running and get its public DNS
def wait_for_instance(instance_id):
    waiter = ec2.get_waiter('instance_running')
    waiter.wait(InstanceIds=[instance_id])
    ec2_resource = boto3.resource('ec2', region_name=region)
    instance = ec2_resource.Instance(instance_id)
    instance.load()
    return instance.public_dns_name

# Download files from EC2 instance
def download_files(public_dns, key_path, files):
    ssh = paramiko.SSHClient()
    ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    ssh.connect(public_dns, username='ec2-user', key_filename=key_path)
    sftp = ssh.open_sftp()
    for remote_file, local_file in files.items():
        sftp.get(remote_file, local_file)
        print(f'Downloaded {remote_file} to {local_file}')
    sftp.close()
    ssh.close()

# Terminate EC2 instance
def terminate_instance(instance_id):
    ec2.terminate_instances(InstanceIds=[instance_id])
    print(f'Instance {instance_id} terminated')

# Main execution flow
start_instance(instance_id)
public_dns = wait_for_instance(instance_id)

# Download specified files
download_files(public_dns, key_path, {file1: local_file1, file2: local_file2})

# Terminate the instance
terminate_instance(instance_id)

print("All is done.")
