# Geoservices for AWS

Amazon CDK configurations for deploying Princeton University Library geoservices.

## First-time setup

* Install language dependencies with asdf or according to versions listed in [.tool-versions](/.tool-verions)

* Install aws-cdk client
  ```
  brew install aws-cdk
  ```

* Install pipenv
  ```
  pip install --user pipenv
  ```

* Install the required python dependencies
  ```
  pipenv sync
  ```

* Activate your virtualenv
  ```
  pipenv shell
  ```

* Update your `.aws/config` to include:
  ```
  [geoservices-deploy]
  region = us-east-1
  ```

* Update your `.aws/credentials` to include credentials from LastPass -> Shared-ITIMS-Passwords\Figgy -> TiTilerAWS like
  ```
  [geoservices-deploy]
  aws_access_key_id = [username]
  aws_secret_access_key = [password]
  ```

* Copy `.env.example` to `.env` and update the account number using the note from that LastPass entry.


## Every time setup

```
pipenv sync
pipenv shell
```

## Check that changes are valid

```
cdk synth
```

## Deploy Geodata

1. Deploy the staging stack
  ```
  cdk --profile geoservices-deploy deploy geodata-staging
  ```

1. Deploy the production stack
  ```
  cdk --profile geoservices-deploy deploy geodata-production
  ```

To add additional dependencies, for example other CDK libraries, just add
them with the `pipenv install` command.

## Useful commands

Read the [CDK documentation](https://docs.aws.amazon.com/cdk/latest/guide/cli.html)

 * `cdk deploy`      deploy this stack to your default AWS account/region
 * `cdk destroy`     delete this stack from your default AWS account/region
 * `cdk diff`        compare deployed stack with current state
 * `cdk docs`        open CDK documentation
 * `cdk ls`          list all stacks in the app
 * `cdk synth`       emits the synthesized CloudFormation template
