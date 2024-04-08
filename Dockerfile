FROM python:3.12-slim

RUN apt-get -y update


RUN mkdir app/

COPY requirements.txt app/requirements.txt

RUN pip install -r app/requirements.txt

COPY /src/ app/src/
COPY /loggs/ app/loggs/

WORKDIR app

CMD python3 src/gradio_app.py
