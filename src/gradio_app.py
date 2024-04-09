import gradio as gr

from openai import OpenAI
import os

from loguru import logger
from datetime import datetime
from minio_connection import save_log
from pydantic_settings import BaseSettings
from pydantic import Field, HttpUrl
# Configure the logger
current_time = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")

file_name = f"loggs/app-loging-{current_time}.log"

logger.add(file_name, format="{time} {level} {message}", level="INFO")


# configure env variables
class Settings(BaseSettings):
    model_url: HttpUrl = Field(alias="MODEL_URL")
    model: str = Field(alias="MODEL_NAME")
    api_key: str = Field(alias="API_KEY")
    host: str = Field(alias="HOST")
    port: int = Field(alias="PORT")

# MODEL_URL = os.getenv("MODEL_URL", "http://0.0.0.0:9091/v1")
# MODEL_NAME = os.getenv("MODEL_NAME", "/models/mistral-7b-v0.1.Q2_K.gguf")
# API_KEY = os.getenv("API_KEY", "key")
#
# HOST = os.getenv("HOST", "0.0.0.0")
# PORT = os.getenv("PORT", 9008)
# PORT = int(PORT)

settings = Settings()

COMMENT_FLAG = False

client = OpenAI(
    base_url=str(settings.model_url),
    api_key=settings.api_key
)


def predict(message, history):
    messages = []

    for user_message, assistant_message in history:
        messages.append({"role": "user", "content": user_message})
        messages.append({"role": "assistant", "content": assistant_message})

    messages.append({"role": "user", "content": message})

    response = client.chat.completions.create(
        model=settings.model,
        messages=messages,
        stream=True
    )
    logger.info("=====================================")
    logger.info(f"Model name: {settings.model}")
    logger.info(f"User message: {messages}")

    text = ""
    for chunk in response:
        content = chunk.choices[0].delta.content
        if content:
            text += content
            yield text

    dict_output = dict(response=text)
    logger.info(f"Assistant response: {dict_output}")

    global COMMENT_FLAG
    COMMENT_FLAG = True

    # save log into minio storage
    save_log(file_name)


js = """function () {
  gradioURL = window.location.href
  if (!gradioURL.endsWith('?__theme=dark')) {
    window.location.replace(gradioURL + '?__theme=dark');
  }
}"""

css = """
footer {
    visibility: hidden;
}
full-height {
    height: 100%;
}
"""


def upvote():
    global COMMENT_FLAG

    if COMMENT_FLAG:
        logger.info("Upvoted!")
        COMMENT_FLAG = False


def downvote():
    global COMMENT_FLAG

    if COMMENT_FLAG:
        logger.info("Downvoted!")
        COMMENT_FLAG = False


with gr.Blocks(theme=gr.themes.Soft(), js=js, css=css, fill_height=True) as demo:

    gr.ChatInterface(predict, fill_height=True,
                     examples=["What is the capital of France?", "Who was the first person on the moon?"])

    with gr.Row() as button_row:
        upvote_btn = gr.Button(value="👍  Upvote", interactive=True)
        downvote_btn = gr.Button(value="👎  Downvote", interactive=True)

    upvote_btn.click(
        upvote,
    )
    downvote_btn.click(
        downvote,
    )

if __name__ == "__main__":
    logger.info(f"Server is running on {settings.host}:{settings.port}")

    demo.launch(server_name=settings.host, server_port=settings.port)
