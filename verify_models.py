#!/usr/bin/env python3
"""
Verify that the models listed in .tellrc are reachable and responsive.
Exits with code 0 if all configured models pass a quick ping test.
"""
import json
import os
import sys
import urllib.request

def load_config():
    config_path = os.path.expanduser(".tellrc")
    if not os.path.exists(config_path):
        print(f"ERROR: {config_path} not found")
        sys.exit(1)
    with open(config_path) as f:
        return json.load(f)

def ping_openrouter(model, api_key):
    url = "https://openrouter.ai/api/v1/chat/completions"
    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json",
    }
    data = json.dumps({
        "model": model,
        "messages": [{"role": "user", "content": "hi"}],
        "max_tokens": 1,
        "temperature": 0,
    }).encode("utf-8")
    req = urllib.request.Request(url, data=data, headers=headers, method="POST")
    try:
        with urllib.request.urlopen(req, timeout=10) as resp:
            resp_data = json.load(resp)
            if "choices" in resp_data and len(resp_data["choices"]) > 0:
                return True
    except Exception as e:
        print(f"  OpenRouter model {model} failed: {e}")
    return False

def ping_nvidia(model, api_key):
    url = "https://api.nvcf.nvidia.com/v2/chat/completions"
    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json",
    }
    data = json.dumps({
        "model": model,
        "messages": [{"role": "user", "content": "hi"}],
        "max_tokens": 1,
        "temperature": 0,
    }).encode("utf-8")
    req = urllib.request.Request(url, data=data, headers=headers, method="POST")
    try:
        with urllib.request.urlopen(req, timeout=10) as resp:
            resp_data = json.load(resp)
            if "choices" in resp_data and len(resp_data["choices"]) > 0:
                return True
    except Exception as e:
        print(f"  NVIDIA model {model} failed: {e}")
    return False

def main():
    config = load_config()
    providers = config.get("providers", [])
    models_cfg = config.get("models", {})
    ok = True

    api_keys = {
        "openrouter": os.environ.get("OPENROUTER_API_KEY"),
        "nvidia": os.environ.get("NVIDIA_API_KEY"),
    }
    print(f"DEBUG: openrouter key: {api_keys['openrouter'][:10]}...", file=sys.stderr)
    print(f"DEBUG: nvidia key: {api_keys['nvidia'][:10]}...", file=sys.stderr)

    for prov in providers:
        if prov not in models_cfg:
            print(f"WARNING: No models configured for provider {prov}")
            continue
        model_list = models_cfg[prov].get("query", [])
        if not model_list:
            print(f"WARNING: No query models listed for provider {prov}")
            continue
        print(f"\nChecking provider '{prov}' ({len(model_list)} models):")
        api_key = api_keys.get(prov)
        if not api_key:
            print(f"  ERROR: Missing API key for {prov}")
            ok = False
            continue
        for model in model_list:
            print(f"  - {model}", end=" ")
            if prov == "openrouter":
                result = ping_openrouter(model, api_key)
            elif prov == "nvidia":
                result = ping_nvidia(model, api_key)
            else:
                print(f"Unknown provider {prov}")
                result = False
            if result:
                print("[OK]")
            else:
                print("[FAIL]")
                ok = False

    if ok:
        print("\nAll models are reachable and responsive.")
    else:
        print("\nSome models failed checks. Please review your .tellrc and API keys.")
        sys.exit(1)

if __name__ == "__main__":
    main()