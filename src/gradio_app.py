import gradio as gr
from openai import OpenAI
from loguru import logger
from datetime import datetime
from minio_connection import save_log
from pydantic_settings import BaseSettings
from pydantic import Field, HttpUrl

# get the current time for the log file
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
    stop_words: list[str] = Field(default=["<|im_start|>"], alias="STOP_WORDS")


# read the settings from the .env file
settings = Settings()

# define bool flag for comment upvote and downvote
COMMENT_FLAG: bool = False

# create an instance of the OpenAI class
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

    # combine the user message and assistant message in the appropriate format for chat completion
    for user_message, assistant_message in history:
        messages.append({"role": "user", "content": user_message})
        messages.append({"role": "assistant", "content": assistant_message})

    # add the current user message to the messages list
    messages.append({"role": "user", "content": message})

    # call the openai chat completion API
    response = client.chat.completions.create(
        model=settings.model, messages=messages, stream=True, stop=settings.stop_words
    )

    # log the model name and user message
    logger.info("=====================================")
    logger.info(f"Model name: {settings.model}")
    logger.info(f"User message: {messages}")

    # extract the assistant response from the response object and show to the user
    text = ""
    for chunk in response:
        content = chunk.choices[0].delta.content
        if content:
            text += content
            yield text

    # log the assistant response
    dict_output = dict(response=text)
    logger.info(f"Assistant response: {dict_output}")

    # set the comment flag to True for upvote and downvote
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
        # log the upvote
        logger.info("Upvoted!")

        # save log into minio storage
        save_log(file_name)

        # set the comment flag to False after upvote (does not duplicate the upvote in the log file)
        COMMENT_FLAG = False


def downvote():
    """
    This function is used to downvote the assistant response in to log file
    :return:
    """
    global COMMENT_FLAG

    if COMMENT_FLAG:
        # log the downvote
        logger.info("Downvoted!")

        # save log into minio storage
        save_log(file_name)

        # set the comment flag to False after downvote (does not duplicate the downvote in the log file)
        COMMENT_FLAG = False


# define the custom css and js for the gradio interface
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

# create the gradio interface
with gr.Blocks(theme=gr.themes.Soft(), js=js, css=css, fill_height=True) as demo:

    # create the chat interface
    gr.ChatInterface(
        predict,
        fill_height=True,
        examples=[
            "What is the capital of France?",
            "Who was the first person on the moon?",
        ],
    )

    # create the upvote and downvote buttons
    with gr.Row() as button_row:
        upvote_btn = gr.Button(value="👍  Upvote", interactive=True)
        downvote_btn = gr.Button(value="👎  Downvote", interactive=True)

    # set the upvote and downvote button actions
    upvote_btn.click(
        upvote,
    )
    downvote_btn.click(
        downvote,
    )

if __name__ == "__main__":
    # log the server is running
    logger.info(f"Server is running on {settings.host}:{settings.port}")
    logger.info(f"stop words: {settings.stop_words}")

    # run the gradio interface
    demo.launch(server_name=settings.host, server_port=settings.port)
