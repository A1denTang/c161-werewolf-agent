"""Inference through the local llama.cpp server. No cloud account is needed."""

import json
import os
from urllib.request import ProxyHandler, build_opener, Request


MODEL = "c161-werewolf-qwen"


def turn_text(situation):
    lines = [f"You are {situation['your_seat']}.", "", "Your view from the game server:",
             situation["seat_observation"], "", "Statements delivered to you:"]
    for entry in situation["player_statements"]:
        audience = entry["to"] if isinstance(entry["to"], str) else ", ".join(entry["to"])
        lines.append(f"Day {entry['day']}, {entry['from']} to {audience}: {json.dumps(entry['claim'])}")
    if not situation["player_statements"]:
        lines.append("(none available)")
    if situation.get("table_note"):
        lines.extend(["", situation["table_note"]])
    if "menu" in situation:
        lines.extend(["", "Legal action IDs for this turn:"])
        lines.extend(f"{key} = {label}" for key, label in situation["menu"].items())
    else:
        lines.append("Available message audiences: " + ", ".join(situation["audiences"]))
    return "\n".join(lines)


class LocalModel:
    def __init__(self):
        port = int(os.environ.get("WEREWOLF_PORT", "18261"))
        if not 1 <= port <= 65535:
            raise ValueError("WEREWOLF_PORT must be a valid TCP port")
        self.url = f"http://127.0.0.1:{port}/v1/chat/completions"
        self.http = build_opener(ProxyHandler({}))

    def complete(self, instructions, situation, schema, *, timeout, max_tokens):
        request = Request(self.url, method="POST", headers={"Content-Type": "application/json"},
                          data=json.dumps({
                              "model": MODEL,
                              "messages": [
                                  {"role": "system", "content": instructions},
                                  {"role": "user", "content": turn_text(situation)},
                              ],
                              "temperature": 0, "seed": 161, "max_tokens": max_tokens,
                              "response_format": {"type": "json_schema", "json_schema": {
                                  "name": "werewolf_decision", "strict": True, "schema": schema,
                              }},
                          }).encode("utf-8"))
        with self.http.open(request, timeout=timeout) as response:
            payload = json.load(response)
        answer = json.loads(payload["choices"][0]["message"]["content"])
        if not isinstance(answer, dict):
            raise ValueError("Expected a JSON object from the model")
        return answer, payload.get("usage", {})
