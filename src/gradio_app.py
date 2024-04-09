import gradio as gr
from openai import OpenAI
from loguru import logger
from datetime import datetime
from minio_connection import save_log
from pydantic_settings import BaseSettings
from pydantic import Field, HttpUrl

current_time = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")

# define path log file
file_name = f"loggs/app-loging-{current_time}.log"

# Configure the logger
logger.add(file_name, format="{time} {level} {message}", level="INFO")


# configure env variables
class Settings(BaseSettings):
    url: HttpUrl = Field(alias="MODEL_URL")
    model: str = Field(alias="MODEL_NAME")
    api_key: str = Field(alias="API_KEY")
    host: str = Field(alias="HOST")
    port: int = Field(alias="PORT")


settings = Settings()

# define bool flag for comment upvote and downvote
COMMENT_FLAG: bool = False

client = OpenAI(base_url=str(settings.url), api_key=settings.api_key)


def predict(message: str, history: list[tuple[str, str]]):
    """
    This function is used to predict the next message from the user conversation history

    :param message:
    :param history:
    :return:
    """
    global COMMENT_FLAG

    messages = []

    for user_message, assistant_message in history:
        messages.append({"role": "user", "content": user_message})
        messages.append({"role": "assistant", "content": assistant_message})

    messages.append({"role": "user", "content": message})

    response = client.chat.completions.create(
        model=settings.model, messages=messages, stream=True
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

    COMMENT_FLAG = True

    # save log into minio storage
    save_log(file_name)


def upvote():
    """
    This function is used to upvote the assistant response in to log file
    :return:
    """
    global COMMENT_FLAG

    if COMMENT_FLAG:
        logger.info("Upvoted!")
        save_log(file_name)
        COMMENT_FLAG = False


def downvote():
    """
    This function is used to downvote the assistant response in to log file
    :return:
    """
    global COMMENT_FLAG

    if COMMENT_FLAG:
        logger.info("Downvoted!")
        save_log(file_name)
        COMMENT_FLAG = False


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


with gr.Blocks(theme=gr.themes.Soft(), js=js, css=css, fill_height=True) as demo:

    gr.ChatInterface(
        predict,
        fill_height=True,
        examples=[
            "What is the capital of France?",
            "Who was the first person on the moon?",
        ],
    )

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
