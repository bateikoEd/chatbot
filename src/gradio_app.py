import gradio as gr

from openai import OpenAI
import os

from loguru import logger
from datetime import datetime

# Configure the logger
current_time = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
logger.add(f"loggs/app-loging-{current_time}.log", format="{time} {level} {message}", level="INFO")


MODEL_URL = os.getenv("MODEL_URL", "http://0.0.0.0:9091/v1")
MODEL_NAME = os.getenv("MODEL_NAME", "/models/mistral-7b-v0.1.Q2_K.gguf")
API_KEY = os.getenv("API_KEY", "key")

HOST = os.getenv("HOST", "0.0.0.0")
PORT = os.getenv("PORT", 9008)


client = OpenAI(
    base_url=MODEL_URL,
    api_key=API_KEY
)


def predict(message, history):
    messages = []

    for user_message, assistant_message in history:
        messages.append({"role": "user", "content": user_message})
        messages.append({"role": "assistant", "content": assistant_message})

    messages.append({"role": "user", "content": message})

    response = client.chat.completions.create(
        model=MODEL_NAME,
        messages=messages,
        stream=True
    )
    logger.info("=====================================")
    logger.info(f"Model name: {MODEL_NAME}")
    logger.info(f"User message: {messages}")

    text = ""
    for chunk in response:
        content = chunk.choices[0].delta.content
        if content:
            text += content
            yield text

    logger.info(f"Assistant response: {text}")


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


# Define the upvote and downvote functions
def upvote():
    # Add your upvote logic here
    logger.info("Upvoted!")


def downvote():
    # Add your downvote logic here
    logger.info("Downvoted!")


# upvote_button = gr.Interface(fn=upvote, inputs="button", outputs="text", description="Upvote")
# downvote_button = gr.Interface(fn=downvote, inputs="button", outputs="text", description="Downvote")

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
    demo.launch(server_name=HOST, server_port=PORT)
