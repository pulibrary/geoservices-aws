import os
from aws_cdk import (
    Stack,
    aws_certificatemanager as certificatemanager,
    aws_cloudfront as cloudfront,
    aws_cloudfront_origins as origins,
    aws_iam as iam,
    aws_s3 as s3
)
from constructs import Construct

class GeoservicesStack(Stack):
    def __init__(self, scope: Construct, construct_id: str, stage: str, **kwargs) -> None:
        super().__init__(scope, construct_id, **kwargs)

        # geo storage bucket
        bucket_name = f"figgy-geo-{stage}"
        bucket_arn = f"arn:aws:s3:::figgy-geo-{stage}"
        bucket = s3.Bucket.from_bucket_arn(self, bucket_name, bucket_arn)

        # certificate
        if stage == "staging":
            custom_public_domain = "geodata-staging.princeton.edu"
            custom_restricted_domain = "geodata-restricted-staging.library.princeton.edu"
        else:
            custom_public_domain = "geodata.princeton.edu"
            custom_restricted_domain = "geodata-restricted.library.princeton.edu"

        # public_certificate = certificatemanager.Certificate(self, f"geodata-{stage}-certificate",
        #     domain_name=custom_public_domain,
        #     validation=certificatemanager.CertificateValidation.from_dns()
        # )
        #
        # restricted_certificate = certificatemanager.Certificate(self, f"geodata-restricted-{stage}-certificate",
        #     domain_name=custom_restricted_domain,
        #     validation=certificatemanager.CertificateValidation.from_dns()
        # )
        #
        ## cloudfront

        # Use titiler policy
        response_headers_policy = cloudfront.ResponseHeadersPolicy.from_response_headers_policy_id(
                self,
                f"geodata-{stage}-responseheaderspolicy",
                response_headers_policy_id="36af6d78-3c4e-4e15-903f-73b542589a60")

        # response_headers_policy = cloudfront.ResponseHeadersPolicy(self, f"geodata-{stage}-responseheaderspolicy",
        #     response_headers_policy_name=f"geodata-{stage}-responseheaders",
        #     comment="custom response policy with cache-control max-age set to match ttl",
        #     cors_behavior=cloudfront.ResponseHeadersCorsBehavior(
        #         access_control_allow_credentials=False,
        #         access_control_allow_headers=["*"],
        #         access_control_allow_methods=["all"],
        #         access_control_allow_origins=["*"],
        #         access_control_expose_headers=["*"],
        #         origin_override=True
        #     ),
        #     custom_headers_behavior=cloudfront.ResponseCustomHeadersBehavior(
        #         custom_headers=[cloudfront.ResponseCustomHeader(header="cache-control",
        #                                                         value="public, max-age= 31536000",
        #                                                         override=True)]
        #     )
        # )

        public_distribution = cloudfront.Distribution(self, f"geodata-public-{stage}-distribution",
            # certificate=public_certificate,
            # domain_names=[custom_public_domain],
            default_behavior=cloudfront.BehaviorOptions(
                origin=origins.S3Origin(bucket),
                cache_policy=cloudfront.CachePolicy.CACHING_OPTIMIZED,
                allowed_methods=cloudfront.AllowedMethods.ALLOW_GET_HEAD_OPTIONS,
                response_headers_policy=response_headers_policy,
                viewer_protocol_policy=cloudfront.ViewerProtocolPolicy.REDIRECT_TO_HTTPS,
                origin_request_policy=cloudfront.OriginRequestPolicy.CORS_S3_ORIGIN
            )
        )

        restricted_distribution = cloudfront.Distribution(self, f"geodata-restricted-{stage}-distribution",
            # certificate=restricted_certificate,
            # domain_names=[custom_restricted_domain],
            default_behavior=cloudfront.BehaviorOptions(
                origin=origins.S3Origin(bucket),
                cache_policy=cloudfront.CachePolicy.CACHING_OPTIMIZED,
                allowed_methods=cloudfront.AllowedMethods.ALLOW_GET_HEAD_OPTIONS,
                response_headers_policy=response_headers_policy,
                viewer_protocol_policy=cloudfront.ViewerProtocolPolicy.REDIRECT_TO_HTTPS,
                origin_request_policy=cloudfront.OriginRequestPolicy.CORS_S3_ORIGIN
            )
        )

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
                    "AWS:SourceArn": f"arn:aws:cloudfront::{self.account}:distribution/{restricted_distribution.distribution_id}"
                }
            }
        })

        # Add bucket policy to allow restricted distribution access
        s3.CfnBucketPolicy(self, 'bucketpolicy',
            bucket=bucket.bucket_name,
            policy_document=iam.PolicyDocument(statements=[permission])
        )
