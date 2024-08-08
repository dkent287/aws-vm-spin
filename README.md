aws-vm-spin

This is a solution for spinning up resources on AWS to train a machine learning model, downloading the results and then termimating the various services needed to train the model.

The AWS services include EC2, S3, Lambda, EventBridge, Secrets Manager, IAM and SNS.

The Lamda function is mainly responsible for checking whether the model builiding process has been completed and and performing some of the service shut-down work.  The Lambda function requires a Lambda layer which is built from a Docker container.

Instructions on use to follow.