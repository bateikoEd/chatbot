FROM python:3.12-slim

RUN apt-get -y update && apt-get install -y fortunes

RUN pip install fschat[model_worker,webui]

RUN mkdir app/

WORKDIR app/loggs

CMD python3 -m fastchat.serve.gradio_web_server --controller-url "" --share --register-api-endpoint-file api_endpoints.json

