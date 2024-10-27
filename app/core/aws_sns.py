import boto3
import json

from django.conf import settings

sns_client = boto3.client(
    "sns",
    region_name=settings.AWS_REGION_NAME,
    aws_access_key_id=settings.AWS_ACCESS_KEY_ID,
    aws_secret_access_key=settings.AWS_SECRET_ACCESS_KEY
)


def create_endpoint(device_token):
    platform_arn = settings.AWS_SNS_PLATFORM_APPLICATION_ARN
    response = sns_client.create_platform_endpoint(
        PlatformApplicationArn=platform_arn,
        Token=device_token,
    )
    return response["EndpointArn"]


def send_push_notification(endpoint_arn, message):
    response = sns_client.publish(
        TargetArn=endpoint_arn,
        MessageStructure='json',
        Message=json.dumps({
            'default': message,
            'GCM': json.dumps({"notification": {"body": message}}),
            'APNS': json.dumps({"aps": {"alert": message}}),
        })
    )
    return response
