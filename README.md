# chatbot-evaluation

```
docker run --rm -it -p 9095:8000 -v /home/models:/models -e MODEL=/models/Mistral-7b-v0.9-Q3_K_M.gguf -e API_KEY=one -e CHAT_FORMAT=chatml -e SYSTEM_PROMPT_FILE=/home/models/system_prompt.json ghcr.io/abetlen/llama-cpp-python
```