import os
from aws_cdk import (
    Stack,
    aws_certificatemanager as certificatemanager,
    aws_cloudfront as cloudfront,
    aws_cloudfront_origins as origins,
    aws_iam as iam,
    aws_s3 as s3,
    aws_wafv2 as waf
)
from constructs import Construct
from helpers.ip_list import IpList

class GeodataStack(Stack):
    def __init__(self, scope: Construct, construct_id: str, stage: str, **kwargs) -> None:
        super().__init__(scope, construct_id, **kwargs)

        ## geo storage bucket
        bucket_name = f"figgy-geo-{stage}"
        bucket_arn = f"arn:aws:s3:::figgy-geo-{stage}"
        bucket = s3.Bucket.from_bucket_arn(self, bucket_name, bucket_arn)

        ## cloudfront

        # certificate
        if stage == "staging":
            custom_public_domain = "geodata-staging.lib.princeton.edu"
            public_cert_arn = f"arn:aws:acm:us-east-1:{self.account}:certificate/fa154918-05c2-4fa9-b5f1-0efad11ae1c2"
            custom_restricted_domain = "geodata-restricted-staging.lib.princeton.edu"
            restricted_cert_arn = f"arn:aws:acm:us-east-1:{self.account}:certificate/32ff0b31-d108-4bb5-841e-b272aa4ebbce"
        else:
            custom_public_domain = "geodata.lib.princeton.edu"
            public_cert_arn = f"arn:aws:acm:us-east-1:{self.account}:certificate/33374ebc-6185-4ff6-b32c-f406d6234178"
            custom_restricted_domain = "geodata-restricted.lib.princeton.edu"
            restricted_cert_arn = f"arn:aws:acm:us-east-1:{self.account}:certificate/0526ff5f-4a4d-4a94-8913-6155d75016b3"

        public_certificate = certificatemanager.Certificate.from_certificate_arn(self,
            f"geodata-{stage}-certificate",
            public_cert_arn
        )

        restricted_certificate = certificatemanager.Certificate.from_certificate_arn(self,
            f"geodata-restricted-{stage}-certificate",
            restricted_cert_arn
        )

        # IP Set
        ipset_ip4 = waf.CfnIPSet(self, f"geodata-{stage}-ip4-ipset",
            addresses=IpList().ip4(),
            ip_address_version="IPV4",
            scope="CLOUDFRONT",
            description="On Campus and VPN IP4 Addresses",
            name=f"geodata-{stage}-ip4-ipset",
        )

        ipset_ip6 = waf.CfnIPSet(self, f"geodata-{stage}-ip6-ipset",
            addresses=IpList().ip6(),
            ip_address_version="IPV6",
            scope="CLOUDFRONT",
            description="On Campus and VPN IP6 Addresses",
            name=f"geodata-{stage}-ip6-ipset",
        )

        # Web Application Firewall
        ruleIPMatch = waf.CfnWebACL.RuleProperty(
            name     = 'IPMatch',
            priority =  0,
            action   = waf.CfnWebACL.RuleActionProperty(
                allow=waf.CfnWebACL.AllowActionProperty(), block=None
            ),
            statement = waf.CfnWebACL.StatementProperty(
                or_statement = waf.CfnWebACL.OrStatementProperty(
                    statements = [
                        waf.CfnWebACL.StatementProperty(
                            ip_set_reference_statement = waf.CfnWebACL.IPSetReferenceStatementProperty(
                                arn=ipset_ip4.attr_arn
                            )
                        ),
                        waf.CfnWebACL.StatementProperty(
                            ip_set_reference_statement = waf.CfnWebACL.IPSetReferenceStatementProperty(
                                arn=ipset_ip6.attr_arn
                            )
                        )
                    ]
                )
            ),
            visibility_config = waf.CfnWebACL.VisibilityConfigProperty(
                cloud_watch_metrics_enabled = True,
                metric_name                 = 'IPMatch',
                sampled_requests_enabled    = True
            )
        )

        firewall = waf.CfnWebACL(self, f"geodata-{stage}-waf",
            scope = "CLOUDFRONT",
            description = f"Firewall for restricted geodata content in {stage}",
            name = f"geodata-{stage}-waf",
            default_action=waf.CfnWebACL.DefaultActionProperty(block=waf.CfnWebACL.BlockActionProperty(), allow=None),
            rules=[ruleIPMatch],
            visibility_config = waf.CfnWebACL.VisibilityConfigProperty(
                cloud_watch_metrics_enabled = True,
                metric_name                 = 'geodatawaf',
                sampled_requests_enabled    = True
            )
        )

        response_headers_policy = cloudfront.ResponseHeadersPolicy(self, f"geodata-{stage}-ResponseHeadersPolicy",
            response_headers_policy_name=f"geodata-{stage}-ResponseHeadersPolicy",
            comment="Custom response policy with cache-control max-age set to match TTL",
            cors_behavior=cloudfront.ResponseHeadersCorsBehavior(
                access_control_allow_credentials=False,
                access_control_allow_headers=["*"],
                access_control_allow_methods=["ALL"],
                access_control_allow_origins=["*"],
                access_control_expose_headers=["*"],
                origin_override=True
            ),
            custom_headers_behavior=cloudfront.ResponseCustomHeadersBehavior(
                custom_headers=[cloudfront.ResponseCustomHeader(header="Cache-Control", value="public, max-age= 31536000", override=True)]
            )
        )

        public_distribution = cloudfront.Distribution(self, f"geodata-public-{stage}-distribution",
            certificate=public_certificate,
            domain_names=[custom_public_domain],
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
            certificate=restricted_certificate,
            domain_names=[custom_restricted_domain],
            web_acl_id = firewall.attr_arn,
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
