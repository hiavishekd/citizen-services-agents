"""Optional chat app for Citizen Services Agents.

A small Gradio front end for the Neuro SAN server that scripts/run.sh starts on port 8080. It keeps the conversation
(chat_context) and the session state (sly_data) for each browser session and sends them back with every message, so
multi-turn chats work. It holds no API key: only the server talks to the model.
"""
import json
import os
from typing import Any
from typing import Dict
from typing import Tuple

import gradio as gr
import requests

SERVER_URL = os.environ.get("NEURO_SAN_URL", "http://localhost:8080")
NETWORKS = ["scheme_navigator", "health_triage", "fraud_shield", "governance_dashboard"]
BANNER = "**Prototype. Uses demo data. Not official advice.**"
TIMEOUT_SECONDS = 240

NOT_RUNNING = ("I could not reach the Neuro SAN server. Start it in another terminal with ./scripts/run.sh, "
               "wait a few seconds, and try again.")
TIMED_OUT = "The server took too long to answer. Please try again."
SERVER_ERROR = "The server returned an error. Check the terminal running ./scripts/run.sh, then try again."
EMPTY_REPLY = "I did not get a reply. Please try again."


def new_session() -> Dict[str, Any]:
    """A fresh conversation: no chat history and no stored session data."""
    return {"chat_context": {}, "sly_data": {}}


def parse_stream(text: str) -> list:
    """The server streams concatenated JSON objects; return them as a list."""
    decoder = json.JSONDecoder()
    objects, i = [], 0
    while i < len(text):
        while i < len(text) and text[i].isspace():
            i += 1
        if i >= len(text):
            break
        obj, i = decoder.raw_decode(text, i)
        objects.append(obj)
    return objects


def send_message(session: Dict[str, Any], network: str, text: str) -> Tuple[str, Dict[str, Any]]:
    """Send one message to a network. Returns (reply text, updated session). Never raises for server problems."""
    payload: Dict[str, Any] = {"user_message": {"text": text}}
    if session.get("chat_context"):
        payload["chat_context"] = session["chat_context"]
    if session.get("sly_data"):
        payload["sly_data"] = session["sly_data"]
    url = f"{SERVER_URL}/api/v1/citizen_services/{network}/streaming_chat"
    try:
        response = requests.post(url, json=payload, timeout=TIMEOUT_SECONDS)
        response.raise_for_status()
        messages = parse_stream(response.text)
    except requests.exceptions.ConnectionError:
        return NOT_RUNNING, session
    except requests.exceptions.Timeout:
        return TIMED_OUT, session
    except (requests.exceptions.RequestException, ValueError):
        return SERVER_ERROR, session

    reply = ""
    updated = {"chat_context": dict(session.get("chat_context") or {}), "sly_data": dict(session.get("sly_data") or {})}
    for item in messages:
        body = item.get("response", item.get("result", {}).get("response", {}))
        if not isinstance(body, dict):
            continue
        if body.get("text"):
            reply = body["text"]
        if body.get("chat_context"):
            updated["chat_context"] = body["chat_context"]
        if body.get("sly_data"):
            updated["sly_data"].update(body["sly_data"])
    return (reply.strip() or EMPTY_REPLY), updated


def build_app() -> gr.Blocks:
    with gr.Blocks(title="Citizen Services Agents") as demo:
        gr.Markdown("# Citizen Services Agents")
        gr.Markdown(BANNER)
        network = gr.Dropdown(NETWORKS, value=NETWORKS[0], label="Network")
        chat = gr.Chatbot(label="Chat", height=420)
        box = gr.Textbox(placeholder="Type a message and press Enter", label="Message")
        clear = gr.Button("Start a new conversation")
        session = gr.State(new_session())

        def on_message(message, history, selected, state):
            if not message or not message.strip():
                return "", history, state
            reply, state = send_message(state, selected, message.strip())
            history = (history or []) + [{"role": "user", "content": message},
                                         {"role": "assistant", "content": reply}]
            return "", history, state

        def reset(_selected=None):
            return [], new_session(), ""

        box.submit(on_message, [box, chat, network, session], [box, chat, session])
        network.change(reset, [network], [chat, session, box])  # changing the network resets the conversation
        clear.click(reset, [network], [chat, session, box])
    return demo


if __name__ == "__main__":
    build_app().launch(server_name="127.0.0.1", server_port=7860)
