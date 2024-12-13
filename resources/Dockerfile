ARG PYTHON_VERSION=3.13

FROM --platform=linux/amd64 public.ecr.aws/lambda/python:${PYTHON_VERSION}

WORKDIR /tmp

RUN python -m pip install pip -U

ENV PACKAGES_DIR=/var/lang/lib/python3.13/site-packages

# Install system dependencies to compile (numexpr) then
# Reduce package size and remove useless files
RUN dnf install -y gcc-c++ && \
    python -m pip install "titiler.application==0.19.2" "mangum>=0.10.0" --no-binary pydantic, urllib3 && \
    dnf remove -y gcc-c++ && \
    dnf clean all && \
    cd $PACKAGES_DIR && find . -type f -name '*.pyc' | while read f; do n=$(echo $f | sed 's/__pycache__\///' | sed 's/.cpython-[0-9]*//'); cp $f $n; done && \
    cd $PACKAGES_DIR && find . -type d -a -name '__pycache__' -print0 | xargs -0 rm -rf && \
    cd $PACKAGES_DIR && find . -type f -a -name '*.py' -print0 | xargs -0 rm -f && \
    find $PACKAGES_DIR -type d -a -name 'tests' -print0 | xargs -0 rm -rf && \
    rm -rdf $PACKAGES_DIR/numpy/doc/ $PACKAGES_DIR/boto3* $PACKAGES_DIR/botocore* && \
    rm -rdf $PACKAGES_DIR/bin $PACKAGES_DIR/geos_license $PACKAGES_DIR/Misc

WORKDIR ${LAMBDA_TASK_ROOT}

COPY handler.py ${LAMBDA_TASK_ROOT}
COPY middleware.py ${LAMBDA_TASK_ROOT}

CMD [ "handler.handler" ]
