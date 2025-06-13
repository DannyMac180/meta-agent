Below is a no-nonsense, copy-paste-ready playbook for wiring **OpenRouter** into any Python project.
It starts with the absolute minimum (three lines of code) and ends with tips for streaming, error handling, and popular frameworks. Follow the sections in order and you’ll have a working integration in minutes.

---

## 1. Why use OpenRouter?

* One endpoint unlocks **hundreds of LLMs** (OpenAI, Anthropic, Mistral, Cohere, etc.). ([openrouter.ai][1])
* It speaks the same request/response schema as the OpenAI Chat API, so existing code usually needs only a new `base_url` and key. ([openrouter.ai][2])
* Built-in model fall-backs and edge routing keep latency low and uptime high. ([openrouter.ai][2], [openrouter.ai][1])

---

## 2. Grab an API key

1. Log in at **openrouter.ai → API Keys → “Create key.”**
2. Optionally set a credit limit per key (useful for staging/production separation). ([openrouter.ai][3])
3. Keep the key in an environment variable, e.g.:

```bash
export OPENROUTER_API_KEY="sk-or-…"
```

Storing secrets in env-vars (not code) is the officially recommended practice. ([openrouter.ai][3])

---

## 3. Install the only dependency you need

```bash
pip install --upgrade openai   # Official OpenAI SDK, fully compatible
```

No special OpenRouter SDK is required. ([openrouter.ai][2])

---

## 4. Three-line minimal client

```python
from openai import OpenAI
import os

client = OpenAI(
    base_url="https://openrouter.ai/api/v1",
    api_key=os.getenv("OPENROUTER_API_KEY"),
)

response = client.chat.completions.create(
    model="openai/gpt-4o",          # pick any model you like
    messages=[{"role": "user", "content": "Hello, world!"}],
)
print(response.choices[0].message.content)
```

This is the exact snippet from the Quick-start docs with only the variable names changed. ([openrouter.ai][2])

> **Heads-up:** adding optional headers `HTTP-Referer` and `X-Title` lets your app appear on OpenRouter public leaderboards, but they’re not required. ([openrouter.ai][2])

---

## 5. Streaming tokens in real time (for chat UIs)

```python
import json, requests, os

url = "https://openrouter.ai/api/v1/chat/completions"
headers = {
    "Authorization": f"Bearer {os.getenv('OPENROUTER_API_KEY')}",
    "Content-Type": "application/json",
}
payload = {
    "model": "anthropic/claude-3.7-sonnet",
    "messages": [{"role": "user", "content": "Stream this response"}],
    "stream": True,
}

with requests.post(url, headers=headers, json=payload, stream=True) as r:
    for chunk in r.iter_lines():
        if chunk and chunk != b'data: [DONE]':
            data = json.loads(chunk.lstrip(b'data: '))
            delta = data["choices"][0]["delta"].get("content", "")
            print(delta, end="", flush=True)
```

Set `"stream": True` and parse the Server-Sent Events (SSE) you receive. ([openrouter.ai][4])

---

## 6. Know the limits & common errors

| Concern            | What to expect                                                              | Docs                 |
| ------------------ | --------------------------------------------------------------------------- | -------------------- |
| **Free models**    | 20 req/min; 50 req/day unless you buy ≥10 credits (then 1 000/day).         | ([openrouter.ai][5]) |
| **Status codes**   | 400 bad params, 401 bad key, 429 rate-limited, 502 provider down, etc.      | ([openrouter.ai][6]) |
| **Retry strategy** | Exponential back-off on 429/502 is recommended; models may be “warming up.” | ([openrouter.ai][6]) |

---

## 7. Popular framework adapters (optional but handy)

| Framework       | One-liner to switch to OpenRouter                                                                     | Docs                                  |
| --------------- | ----------------------------------------------------------------------------------------------------- | ------------------------------------- |
| **LangChain**   | `ChatOpenAI(base_url="https://openrouter.ai/api/v1", openai_api_key=os.getenv("OPENROUTER_API_KEY"))` | ([openrouter.ai][7], [medium.com][8]) |
| **LiteLLM**     | Works out of the box—just set `api_base`.                                                             | ([github.com][9])                     |
| **Instructor**  | `client = instructor.from_openai(OpenAI(base_url="https://openrouter.ai/api/v1", api_key=…))`         | ([python.useinstructor.com][10])      |
| **Pydantic-AI** | `OpenAIModel("anthropic/claude-3.7-sonnet", base_url="…", api_key="…")`                               | ([openrouter.ai][7])                  |

These adapters keep type safety, tool-calling, or automatic retries while routing requests through OpenRouter.

---

## 8. One-file chatbot template (copy off the shelf)

```python
#!/usr/bin/env python3
"""
chatbot.py – minimal REPL chat with any OpenRouter model
"""
from openai import OpenAI
import os, sys

client = OpenAI(
    base_url="https://openrouter.ai/api/v1",
    api_key=os.getenv("OPENROUTER_API_KEY"),
)

history = []

print("⇢ Type 'exit' to quit.")
while True:
    user = input("you: ")
    if user.lower() in {"exit", "quit"}:
        sys.exit()
    history.append({"role": "user", "content": user})

    resp = client.chat.completions.create(
        model="mistralai/mistral-small-7b-v0.2",
        messages=history,
    )
    bot = resp.choices[0].message.content
    history.append({"role": "assistant", "content": bot})
    print("bot:", bot.strip())
```

Based on the public chatbot tutorial published 2 June 2025. ([teguhteja.id][11])

---

## 9. Best-practice checklist

* **Store keys in env-vars** or a secrets manager—never commit to Git. ([openrouter.ai][3])
* **Choose models intentionally**: call `GET /models` to list options or browse [https://openrouter.ai/models](https://openrouter.ai/models). ([openrouter.ai][2], [openrouter.ai][12])
* **Batch small prompts** or enable prompt caching (see feature docs) to trim bills. ([openrouter.ai][13])
* **Add fall-back logic**: if a provider returns 502, retry with another model slug; OpenRouter’s global routing already helps here. ([openrouter.ai][6])
* **Monitor usage** via the dashboard or `GET /credits` endpoint for spend tracking. ([openrouter.ai][2])

---

### That’s it!

With the three-line client you’re already live on OpenRouter, and the extra sections show how to scale to streaming, frameworks, and production error handling. Happy building!

[1]: https://openrouter.ai/?utm_source=chatgpt.com "OpenRouter"
[2]: https://openrouter.ai/docs/quickstart "OpenRouter Quickstart Guide | Developer Documentation | OpenRouter | Documentation"
[3]: https://openrouter.ai/docs/api-reference/authentication "API Authentication | OpenRouter OAuth and API Keys | OpenRouter | Documentation"
[4]: https://openrouter.ai/docs/api-reference/streaming "API Streaming | Real-time Model Responses in OpenRouter | OpenRouter | Documentation"
[5]: https://openrouter.ai/docs/api-reference/limits?utm_source=chatgpt.com "API Rate Limits | Configure Usage Limits in OpenRouter"
[6]: https://openrouter.ai/docs/api-reference/errors?utm_source=chatgpt.com "API Error Handling | OpenRouter Error Documentation"
[7]: https://openrouter.ai/docs/community/frameworks "Integration Frameworks | OpenRouter SDK and Library Support | OpenRouter | Documentation"
[8]: https://medium.com/%40tedisaacs/from-openai-to-opensource-in-2-lines-of-code-b4b8d2cf2541 "Connect to OpenRouter from Python - Easily! | by Theo McCabe | Apr, 2024 | Medium | Medium"
[9]: https://github.com/OpenRouterTeam/openrouter-examples-python "GitHub - OpenRouterTeam/openrouter-examples-python: Examples of calling OpenRouter models from Python code"
[10]: https://python.useinstructor.com/integrations/openrouter/ "Structured outputs with OpenRouter, a complete guide with instructor - Instructor"
[11]: https://teguhteja.id/build-openrouter-python-chatbot-tutorial/ "OpenRouter Python Chatbot : Amazing! Build Your 1st Apps"
[12]: https://openrouter.ai/models?utm_source=chatgpt.com "Models - OpenRouter"
[13]: https://openrouter.ai/docs/features/prompt-caching?utm_source=chatgpt.com "Prompt Caching | Reduce AI Model Costs with OpenRouter"
