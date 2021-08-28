FROM python:latest


ADD ./requirements.txt .
RUN pip install -r requirements.txt
RUN mkdir src
WORKDIR src
