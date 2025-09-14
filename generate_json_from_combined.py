#!/usr/bin/env python3
"""Run `prompt.txt` against each text file in `combined_text/` using the `llm` Python library.

Writes model output to `json/<input_basename>.json`.

Set MODEL constant below to choose the model.
"""
import os
from pathlib import Path
import json
import time

MODEL = "gemini-2.5-flash"  # change to desired model


def load_prompt(prompt_path: Path) -> str:
    return prompt_path.read_text(encoding="utf-8")


def call_model(llm_client, model: str, prompt: str) -> str:
    # This function assumes the llm library provides a simple sync API.
    # Adjust if your llm client API differs.
    resp = llm_client.create(model=model, input=prompt)
    # Try common response shapes
    if isinstance(resp, dict):
        # look for text in common keys
        for k in ("text", "output", "content", "response"):
            if k in resp:
                return resp[k]
        # if choices list
        if "choices" in resp and isinstance(resp["choices"], list) and resp["choices"]:
            c = resp["choices"][0]
            if isinstance(c, dict) and "text" in c:
                return c["text"]
            if isinstance(c, dict) and "message" in c:
                return c["message"].get("content") or json.dumps(c["message"])
        return json.dumps(resp)
    return str(resp)


def run_prompt_on_file(model, prompt_template: str, file_path: Path, out_dir: Path):
    """Read file_path, run the prompt with the model, and write output JSON to out_dir."""
    # Check if output file already exists
    out_path = out_dir / (file_path.stem + ".json")
    if out_path.exists():
        print(f"Skipping {file_path.name} - JSON already exists")
        return
    
    try:
        doc_text = file_path.read_text(encoding="utf-8")
    except Exception as e:
        print(f"Failed to read {file_path}: {e}")
        return

    full_prompt = prompt_template + "\n```" + doc_text + "\n```\n"

    try:
        response = model.prompt(full_prompt, json_object=True)
        out = response.text()
    except Exception as e:
        print(f"Model call failed for {file_path.name}: {e}")
        time.sleep(2)
        return

    try:
        out_path.write_text(out, encoding="utf-8")
        print(f"Successfully processed {file_path.name}")
    except Exception as e:
        print(f"Failed to write {out_path}: {e}")

    # polite pause to avoid rate limits
    time.sleep(2)


def main():
    base = Path(__file__).resolve().parent
    combined_dir = base / "combined_text"
    prompt_path = base / "prompt.txt"
    out_dir = base / "json"
    out_dir.mkdir(parents=True, exist_ok=True)

    if not prompt_path.exists():
        print("prompt.txt not found at", prompt_path)
        return

    import llm

    model = llm.get_model(MODEL)

    prompt_template = load_prompt(prompt_path)

    files = sorted(p for p in combined_dir.iterdir() if p.is_file() and p.suffix == ".txt")
    for f in files:
        print(f)
        run_prompt_on_file(model, prompt_template, f, out_dir)


if __name__ == "__main__":
    main()
