FROM --platform=$BUILDPLATFORM amazonlinux:latest

RUN yum update -y 
RUN yum install -y gcc-c++ pkgconfig python3-devel redhat-rpm-config python3-pip

RUN mkdir -p /app
ADD . /app
WORKDIR /app

RUN pip3 install -r requirements.txt

CMD ./transform.sh
