# Numerai Signals

## Outline

This document covers:
- purpose
- prerequisites
- installation
- build
- ETLs
- docker files for contenarization
- cdk scripts for architecture definition and cloud deployment
- CI/CD pipeline

## Purpose

In a nutshell, this project aims at providing data for our Numerai Signals models:
- starting with extracting/loading yahoo financial data
- then transforming it using technical analysis library
- ultimately publishing it to make it available for our models

## Prerequisite

Before participating to this project, you need to have installed in your development environment:
- python/pipenv
- docker
- aws cli
- aws cdk

Please check related document that is available online. Also note you need access to AWS prod/dev accounts. Reach out to chauvary.hugo@proton.me if you don't.

## Installation

You can fin required python dependencies in `requirements.txt`. Suggested installation steps:

###
```bash
# create virtual environment
pipenv shell

# install required packages into virtual environment
# make sure it is activated beforehand!
pip install -r requirements.txt
```

## Build (Optional)

Although python code does not need to be compiled, we provide test coverage and other steps in a `Makefile` similar format. You may use the following command to 'compile' your python application:

- clean (repository)
- install (dependencies)
- test (application)
- black check (format code)
- copy (`src` to docker stacks)

```bash
# build app
make all

# code test coverage
coverage run -m pytest -v && coverage report -m
```

## ETLs

### Load

Here we load data from yahoo finance API. We curl the API, parse the response in a suitable format and upload it into our data lake.

```bash
usage: load.py [-h] --start START --end END [--ntickers NTICKERS]
               [--ticker TICKER]

optional arguments:
  -h, --help           show this help message and exit
  --start START        start date format YYMMDD
  --end END            start date format YYMMDD
  --ntickers NTICKERS  Limit to the first n tickers
  --ticker TICKER      Load a given ticker

python src/numerai_signals/load.py\
    --start 221014\
    --end 221022\
    --ticker 000060.KS
```

### Transform

Here we create features by combining the technical analysis library and data shifting, that can be used in regression and classification algorithms.

The objective is to avoid the usage of time-series algorithms (ARIMAs, TBATS, etc.) because they require multistep autocorrelation. (which is absent 95% of the time on financial datasets)

```bash
usage: transform.py [-h] --cmd {all,momentum,other,trend,volatility,volume}
                    [--reload] [--lags LAGS]

optional arguments:
  -h, --help            show this help message and exit
  --cmd {all,momentum,other,trend,volatility,volume}
                        please choose from: all, momentum, other,
                        trend,volatility, volume
  --reload              whether to reload data or not
  --lags LAGS           How many lags you want to apply

python src/numerai_signals/transform.py\
    --cmd volume\
    --lags 5\
    --reload
```

This will return a dataframe with the volume indicators, each shifted 5 times
and cleaned for NAs', i.e. the dataset will have lost 5 days of data at the beginning Furthermore, downcasting is performed on all floats to reduce the total memory
used by the program.



## Docker

We automate complete pipeline by deploying containers in AWS, our cloud provider.

### Ubuntu

You can use ubuntu image to test app in linux environment (as we deploy linux images to AWS)

```bash
docker build \
    -t signals_ubuntu\
    -f Dockerfile_ubuntu .

docker run\
    -v /Users/hugo/Documents/workspace:/home\
    -it signals_ubuntu\
    bash
```

### Load/Transform

```bash
docker build \
    -t signals_load/transform\
    -f Dockerfile_load/transform .

docker run -t signals_load/transform
```

## Infrastructure

Stack is made of following components:
- EventBridge rules to trigger Fargate tasks
- FargateTasks to deploy image repo
- S3 bucket to store files
- Glue to crawl S3 bucket and create database/tables
- Athena to access those tables
- CloudWatch log groups to persists logs
- CloudWatch alarms to trigger SNS topics

![Infrastructure](doc/Signals_stack.png)

We use AWS CDK to automate releases. See `lib/signals-stack.ts`.

## CI/CD

We enable CI/CD by creating a stack for our Pipeline. We use AWS CDK coupled with an EventBridge standard event to automate pipeline self mutation before stack release. See`lib/signals-pipeline-stack.ts` and `lib/signals-pipeline-stage.ts`.

There are two AWS accounts for this project:
- 227502685550/jh_numerai: production
- 615955932111/jh_numerai_dev: dev

Deployment approach followed by devs is summarized in picture below.

![Infrastructure](doc/AWS_stack.png)

### How to deploy to live

```bash
./deploy.sh
```

### How to deploy to dev

```bash
cdk deploy
```