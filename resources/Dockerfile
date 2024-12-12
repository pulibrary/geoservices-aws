ARG PYTHON_VERSION=3.11

FROM --platform=linux/amd64 public.ecr.aws/lambda/python:${PYTHON_VERSION}

WORKDIR /tmp

# Install system dependencies to compile (numexpr)
RUN yum install -y gcc-c++

RUN python -m pip install pip -U
RUN python -m pip install "titiler.application==0.19.2" "mangum>=0.10.0" --no-binary pydantic, urllib3

# Remove system dependencies
RUN yum remove -y gcc-c++

WORKDIR ${LAMBDA_TASK_ROOT}

COPY handler.py ${LAMBDA_TASK_ROOT}
COPY middleware.py ${LAMBDA_TASK_ROOT}

CMD [ "handler.handler" ]
