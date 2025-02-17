import json
import sys
from openai import OpenAI

def load_config(config_path="system_files/config.json"):
    """Loads configuration from a JSON file."""
    try:
        with open(config_path, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception as e:
        print(f"Error loading config file: {e}")
        sys.exit(1)

# Load config
config = load_config()

# Load system prompt
try:
    with open(config["system_prompt"], "r", encoding="utf-8") as f:
        SYSTEM_PROMPT = f.read().strip()
except Exception as e:
    print(f"Error loading system prompt file: {e}")
    sys.exit(1)


JSON_SCHEMA = config["json_schema"]

# Initialize LM Studio client
client = OpenAI(base_url="http://127.0.0.1:1234/v1", api_key="lm-studio")

# Global parameters
MODEL = "llama-3.1-8b-lexi-uncensored-v2"
CHAT_HISTORY_LIMIT = 3072
MAX_RESPONSE_TOKENS = 512
TEMPERATURE = 0.8 #higher value means more creativity
TOP_P = 0.7 #Higher value means more freedom

def truncate_chat_history(messages, max_tokens=CHAT_HISTORY_LIMIT):
    """Truncates the chat history to stay within the token limit."""
    total_tokens = sum(len(msg["content"].split()) for msg in messages)
    while total_tokens > max_tokens:
        removed_message = messages.pop(1)
        total_tokens -= len(removed_message["content"].split())
    return messages

def chat(user_input, messages=None):
    """Handles interaction with the LLM and returns reply + prompt."""
    if messages is None:
        messages = [{"role": "system", "content": SYSTEM_PROMPT}]
    
    messages.append({"role": "user", "content": user_input})
    messages = truncate_chat_history(messages)
    
    try:
        response = client.chat.completions.create(
            model=MODEL,
            messages=messages,
            max_tokens=MAX_RESPONSE_TOKENS,
            temperature=TEMPERATURE,
            top_p=TOP_P,
            stream=False,
            response_format={
                "type": "json_schema",
                "json_schema": JSON_SCHEMA,
            },
        )
        
        # Extract the content from the response
        content = response.choices[0].message.content
        
        # Parse the content as JSON to get the reply and prompt
        content_json = json.loads(content)
        reply = content_json.get("Reply", "[No reply provided]")
        prompt = content_json.get("Prompt", "[No prompt provided]")
        
        # Append the assistant's reply and prompt to the chat history
        messages.append({"role": "assistant", "content": reply})
        messages.append({"role": "assistant", "content": f"Prompt: {prompt}"})
        
        return reply, prompt, messages
    except Exception as e:
        print(f"Error: {str(e)}")
        return "[Error in processing]", "[No prompt]", messages