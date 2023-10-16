from aws_cdk import (
    Stack,
    aws_iam as iam,
    aws_s3 as s3
)
from constructs import Construct

class GeoservicesStack(Stack):
    def __init__(self, scope: Construct, construct_id: str, stage: str, **kwargs) -> None:
        super().__init__(scope, construct_id, **kwargs)

        bucket_name = f"figgy-geo-{stage}"
        bucket_arn = f"arn:aws:s3:::figgy-geo-{stage}"
        bucket = s3.Bucket.from_bucket_arn(self, bucket_name, bucket_arn)

        ## These must be set manually on bucket permissions page, unless creating
        ## a new managed bucket. Settings here for reference
        # public_access = s3.BlockPublicAccess(block_public_policy=False,
        #                                     block_public_acls=False,
        #                                     ignore_public_acls=False,
        #                                     restrict_public_buckets=False)

        permission = iam.PolicyStatement.from_json({
            "Sid": "AllowCloudFrontServicePrincipal",
            "Effect": "Allow",
            "Principal": {
                "Service": "cloudfront.amazonaws.com"
            },
            "Action": "s3:GetObject",
            "Resource": f"arn:aws:s3:::figgy-geo-{stage}/*",
            "Condition": {
                "StringEquals": {
                    "AWS:SourceArn": "arn:aws:cloudfront::080265008837:distribution/E31CT4TYD6ODK"
                }
            }
        })

        s3.CfnBucketPolicy(self, 'bucketpolicy',
            bucket=bucket.bucket_name,
            policy_document=iam.PolicyDocument(statements=[permission])
        )
