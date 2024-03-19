import os
from aws_cdk import (
    Stack,
    BundlingOptions,
    DockerImage,
    Duration,
    Fn,
    CfnOutput,
    aws_certificatemanager as certificatemanager,
    aws_cloudfront as cloudfront,
    aws_cloudfront_origins as cloudfront_origins,
    aws_iam as iam,
    aws_s3 as s3,
    aws_wafv2 as waf,
    aws_lambda,
    aws_events,
    aws_events_targets
)

from constructs import Construct

class TitilerServiceStack(Stack):
    def __init__(self, scope: Construct, construct_id: str, stage: str, **kwargs) -> None:
        super().__init__(scope, construct_id, **kwargs)

        # Environment Variables
        env = {
            "CPL_VSIL_CURL_ALLOWED_EXTENSIONS": ".tif,.TIF,.tiff",
            "GDAL_CACHEMAX": "800",  # 800 mb
            "GDAL_DISABLE_READDIR_ON_OPEN": "EMPTY_DIR",
            "GDAL_HTTP_MERGE_CONSECUTIVE_RANGES": "YES",
            "GDAL_HTTP_MULTIPLEX": "YES",
            "GDAL_HTTP_VERSION": "2",
            "PYTHONWARNINGS": "ignore",
            "VSI_CACHE": "TRUE",
            "VSI_CACHE_SIZE": "5000000",  # 5 MB (per file-handle)
            "RIO_TILER_MAX_THREADS": "1" # turn off rio-tiler threading, better for lamda
        }

        # Lambda Function Definition
        lambda_function = aws_lambda.Function(
            self,
            f"titiler-{stage}-TitilerFuntion",
            runtime=aws_lambda.Runtime.PYTHON_3_8,
            code=aws_lambda.Code.from_asset(
                path=os.path.abspath("./"),
                bundling=BundlingOptions(
                    image=DockerImage.from_build(
                        path = os.path.abspath("./"), file="resources/Dockerfile",
                        platform = "linux/amd64"
                    ),
                    command=["bash", "-c", "cp -R /var/task/. /asset-output/."],
                ),
            ),
            handler="handler.handler",
            memory_size=3008,
            timeout=Duration.seconds(600),
            environment=env,
        )

        # S3 Permissions
        permission = iam.PolicyStatement(
            actions=["s3:GetObject"],
            resources=[
                f"arn:aws:s3:::figgy-geo-{stage}/*",
                "arn:aws:s3:::*/*"
            ],
        )
        lambda_function.add_to_role_policy(permission)

        # Add function url to primary lambda
        # Use instead of API gateway to bypass 30 second gateway timeout limit
        lambda_url = lambda_function.add_function_url(
            auth_type=aws_lambda.FunctionUrlAuthType.NONE
        )
        function_url = Fn.select(2, Fn.split('/', lambda_url.url))

        # Certificate
        if stage == "staging":
            custom_domain = "map-tiles-staging.princeton.edu"
        else:
            custom_domain = "map-tiles.princeton.edu"

        certificate = certificatemanager.Certificate(self, f"titiler-{stage}-Certificate",
            domain_name=custom_domain,
            validation=certificatemanager.CertificateValidation.from_dns()
        )

        # Cloudfront
        cache_policy = cloudfront.CachePolicy(self, f"titiler-{stage}-CachePolicy",
            cache_policy_name=f"titiler-{stage}-CachePolicy",
            comment="Cache policy for TiTiler",
            default_ttl=Duration.days(365),
            max_ttl=Duration.days(365),
            min_ttl=Duration.days(365),
            query_string_behavior=cloudfront.CacheQueryStringBehavior.all(),
            enable_accept_encoding_gzip=True,
            enable_accept_encoding_brotli=True
        )
        response_headers_policy = cloudfront.ResponseHeadersPolicy(self, f"titiler-{stage}-ResponseHeadersPolicy",
            response_headers_policy_name=f"titiler-{stage}-ResponseHeadersPolicy",
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
        distribution = cloudfront.Distribution(self, f"titiler-{stage}-DistPolicy",
            certificate=certificate,
            domain_names=[custom_domain],
            default_behavior=cloudfront.BehaviorOptions(
                origin=cloudfront_origins.HttpOrigin(function_url),
                cache_policy=cache_policy,
                allowed_methods=cloudfront.AllowedMethods.ALLOW_GET_HEAD_OPTIONS,
                response_headers_policy=response_headers_policy,
                viewer_protocol_policy=cloudfront.ViewerProtocolPolicy.REDIRECT_TO_HTTPS,
                origin_request_policy=cloudfront.OriginRequestPolicy.CORS_S3_ORIGIN
            )
        )

        # Add base url env var so TiTiler generates correct tile URLs.
        # Used in HostMiddleware.
        lambda_function.add_environment("TITILER_BASE_URL", custom_domain)

        # Add env var to set the correct s3 bucket
        lambda_function.add_environment("TITILER_S3_BUCKET", f"figgy-geo-{stage}")

        CfnOutput(self, "Function URL", value=function_url)
        CfnOutput(self, "Cloudfront Endpoint", value=distribution.domain_name)

        # Lambda warmer
        eventRule = aws_events.Rule(
          self,
          f"titiler-{stage}-warmer",
          schedule=aws_events.Schedule.cron(minute="0/15")
        )
        eventRule.add_target(aws_events_targets.LambdaFunction(lambda_function))
