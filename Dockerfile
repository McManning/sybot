FROM python:3.7-alpine

LABEL maintainer="Chase McManning <cmcmanning@gmail.com>"

WORKDIR /sybot

COPY ./requirements.txt /sybot/requirements.txt

# build-deps are packages required for building zeroc-ice
RUN apk add --no-cache \
    libstdc++ \
    python-dev \
    openssl-dev \
    bzip2-dev \
    libjpeg-turbo-dev \
    make \
    gcc \
    g++ \
    && pip install --no-cache-dir -r requirements.txt

# build-deps are packages required for building zeroc-ice
# RUN apk add --no-cache --virtual .build-deps \
#     python-dev \
#     openssl-dev \
#     bzip2-dev \
#     make \
#     gcc \
#     g++ \
#     && pip install --no-cache-dir -r requirements.txt \
#     && apk del .build-deps \
#     && apk add --no-cache \
#     openssl \
#     libstdc++

# Issue with the above: the wrong openssl build is installed
# versus the one that zeroc-ice is compiled against.
# openssl-dev !== openssl. Might be able to move openssl-dev
# outside of .build-deps and keep it + its other depends,
# but for now we'll just maintain all the build deps and
# slice things down when we need to.

COPY . /sybot

EXPOSE 5000
CMD ["python", "entry.py"]
