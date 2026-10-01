"""Native Anthropic Messages and OpenAI-compatible adapters for Caro."""

import json
import re
from urllib import request

ANTHROPIC_BASE_URL = "https://api.anthropic.com/v1"
ANTHROPIC_MODEL = "claude-haiku-4-5-20251001"


def choose_move(board, candidates, api_key: str, base_url: str, model: str, provider: str = "openai") -> tuple[int, int]:
    allowed = {(row, col) for row, col, _ in candidates}
    board_text = "\n".join(f"{i:02d} " + " ".join(row) for i, row in enumerate(board))
    prompt = (
        "You are O in a 15x15 Gomoku/Caro game. X is the human. Exactly five "
        "consecutive marks in any straight direction wins, even with both ends blocked. Six or more do not win. Choose exactly one "
        "move from the minimax-approved candidates. Board columns are 0-14. "
        "Return only JSON like {\"row\":7,\"col\":8}.\n"
        f"Candidates: {[(r, c) for r, c, _ in candidates]}\nBoard:\n{board_text}"
    )
    system = "You are a tactical Caro player. Return only a JSON move."
    headers = {"Content-Type": "application/json"}
    if provider == "anthropic":
        # Keep Anthropic credentials bound to the official API destination.
        if base_url.rstrip("/") != ANTHROPIC_BASE_URL:
            raise ValueError("Endpoint Anthropic không hợp lệ.")
        if not api_key:
            raise ValueError("Chưa nhập Anthropic API key.")
        endpoint = ANTHROPIC_BASE_URL + "/messages"
        headers.update({"x-api-key": api_key, "anthropic-version": "2023-06-01"})
        payload = {
            "model": model, "max_tokens": 256, "system": system,
            "messages": [{"role": "user", "content": prompt}],
        }
    elif provider == "openai":
        endpoint = base_url.rstrip("/") + "/chat/completions"
        headers["Authorization"] = f"Bearer {api_key}"
        payload = {
            "model": model, "max_tokens": 256, "temperature": 0.3,
            "messages": [{"role": "system", "content": system}, {"role": "user", "content": prompt}],
        }
    else:
        raise ValueError("Nhà cung cấp LLM không hợp lệ.")
    req = request.Request(endpoint, data=json.dumps(payload).encode("utf-8"), headers=headers, method="POST")
    with request.urlopen(req, timeout=12) as response:
        data = json.load(response)
    if provider == "anthropic":
        if data.get("stop_reason") in {"max_tokens", "refusal"}:
            raise ValueError("Claude chưa trả về nước đi hoàn chỉnh.")
        content = "".join(block.get("text", "") for block in data["content"] if block.get("type") == "text")
    else:
        content = data["choices"][0]["message"]["content"]
    match = re.search(r"\{[^{}]*\}", content)
    if not match:
        raise ValueError("LLM không trả về tọa độ JSON.")
    move = json.loads(match.group())
    position = (move.get("row"), move.get("col"))
    if any(type(n) is not int for n in position) or position not in allowed:
        raise ValueError("LLM chọn nước đi ngoài danh sách hợp lệ.")
    return position
