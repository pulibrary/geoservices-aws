ARG PYTHON_VERSION=3.13

FROM --platform=linux/amd64 public.ecr.aws/lambda/python:${PYTHON_VERSION}

WORKDIR /tmp

RUN python -m pip install pip -U

ENV PACKAGES_DIR=/var/lang/lib/python3.13/site-packages

# Install system dependencies to compile (numexpr)
RUN dnf install -y gcc-c++ && \
    python -m pip install "titiler.application==0.19.2" "mangum>=0.10.0" --no-binary pydantic, urllib3 && \
    dnf remove -y gcc-c++ && \
    dnf clean all

WORKDIR ${LAMBDA_TASK_ROOT}

COPY handler.py ${LAMBDA_TASK_ROOT}
COPY middleware.py ${LAMBDA_TASK_ROOT}

CMD [ "handler.handler" ]
