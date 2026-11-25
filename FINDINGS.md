# Findings log

Every finding with the evidence behind it. Severity: **high** means wrong results or money, **med** means a broken contract or misleading behaviour, **low** means polish. Each item lists the log file and test name that show it.

## Tasks API

| # | Sev | Finding | Evidence |
|---|---|---|---|
| T1 | high | Hitting `max_runtime_seconds` ends with status `completed` and no error. The agent's text says it finished "1 of 60". The docs say `failed` / `time_limit`. | `tasks_extra_budget_injection_timelimit.jsonl` `lim2.runtime_60s_ui_browsing` |
| T2 | high | `max_cost_usd` is overshot: $0.01 cap spent $0.0239 on balanced (+139%), $0.03 cap spent $0.0415 on advanced (+38%), fast +3%. The cap is checked after each model call. | same file, `lim2.budget_*`; `tasks_lifecycle_limits.jsonl` `lim.budget_0.02` |
| T3 | high | `verification.passed` only checks the schema. It was `true` for a wrong answer (moss-fast, poetry multi-hop) and for an empty phone on an impossible goal. | `tasks_accuracy.json` |
| T4 | high | A start page that failed to load (httpbin 400) still produced `completed` with `passed: true`. The agent took the answer from the base64 in the URL and never said the page failed. | `tasks_extra_budget_injection_timelimit.jsonl` `inject.*`, screenshots in `logs/tasks/task_d2dca78a...` |
| T5 | med | The 20-queued cap never triggers, because tasks go to `running` at once. 24 back-to-back creates were all accepted, so nothing limits concurrent running tasks or spend rate. | `tasks_extra_queue.jsonl` |
| T6 | med | `start_url` accepts `localhost`, `169.254.169.254` and `10.0.0.1`. Each was cancelled before its first step, so reachability was not tested. | `tasks_validation.jsonl` `val.start_url_*` |
| T7 | med | BYOK is documented for tasks but rejected with `provider_key_not_supported`. | `tasks_validation.jsonl` `val.byok_on_moss_model` |
| T8 | low | Undocumented but live: `GET /v1/tasks` (cursor paging, `total`, status filter); fields `webhook`, `live_url`, `video_available`, `trace_available`, `zero_data_retention`; models `moss-fast-beta`, `moss-balanced-handoff`. | `list_probe.jsonl`, first create response |
| T9 | low | Unknown query params (`?order=asc`) are ignored, while unknown body fields return 400. | `list_probe.jsonl` |
| T10 | low | moss-advanced costs about the same as balanced ($0.054 to $0.073 vs $0.054 to $0.075 per task), with identical accuracy here. | `tasks_accuracy.json` |
| T11 | low | `max_runtime_seconds: 90.5` is accepted. | `tasks_validation.jsonl` |

Positives:
- Validation caught 29 of 30 bad inputs with clear messages.
- Idempotency works: replay header, 422 on reuse, keys are case sensitive.
- Cancel takes about 10 s.
- Files: 409 before finish, path traversal blocked.
- 17 of 18 answerable goals correct.
- 1,000 of 1,000 CSV rows correct in 45 s for $0.011 (`books_csv_verification.json`).
- Prompt injection resisted on all tiers (`tasks_extra_injection2.jsonl` plus screenshot).

## Inference API

| # | Sev | Finding | Evidence |
|---|---|---|---|
| I1 | high | The reply cache is on by default and ignores `temperature` and `user`. A random-number prompt at temperature 1.0 returns the same number, and different `user` values share one reply. | `cache_probe.jsonl` |
| I2 | med | Cache hits report a different `completion_tokens` for identical text (7 vs 1, 53 vs 60, 62 vs 57). | `cache_probe.jsonl`, `inference_caching_functional_streaming.jsonl` |
| I3 | med | `"model": 123` returns 200 and runs fastlane. | `inference_burst_errors.jsonl` `err.model_wrong_type` |
| I4 | med | A body over 4 MB gets a TCP reset, not the documented JSON 413. | `inference_burst_errors.jsonl` `err.body_over_4mb` |
| I5 | med | `seed`, `frequency_penalty` and `logit_bias` are accepted on fastlane and DeepSeek although the docs say they're refused. | `token_overhead.jsonl` |
| I6 | low | Fastlane bills about 65 hidden prompt tokens per request, even with `X-Moss-System-Prompt: off` (94 vs 28 on luna). | `token_overhead.jsonl` |
| I7 | low | 33 indexes return 403 "outside this project" instead of the max-32 error. | `err.33_indexes` |
| I8 | low | GET on a POST route returns an empty-body 404, not a JSON 405. | `err.wrong_method_get_chat` |
| I9 | low | `content: null` returns a raw dump of 19 pydantic errors. | `err.content_null` |
| I10 | low | Kimi K3 output is priced at $19.20 per million tokens, likely a decimal slip. | Models page |

Positives:
- The stock OpenAI SDK works on both endpoints.
- Fastlane's p50 time to first token is 155 ms (`model_matrix.json`).
- Prefix cache: 4,800 of 4,814 tokens cached.
- Errors tell you the fix.
- Rate limiting is as documented, with `Retry-After`.

## Round 2: model and agent behaviour, API details

### Inference (`inference_ai.py`, `inference_followup.py`, `empty_reply_probe.py`, `api_probe.py`)

| # | Sev | Finding | Evidence |
|---|---|---|---|
| I11 | high | Haiku returns 200 with `finish_reason: content_filter`, empty content and 0 output tokens on a harmless random-word prompt, at 10k, 25k and 40k words. The prompt tokens are still billed. | `empty_reply_probe.jsonl` |
| I12 | med | The context-limit pre-check undercounts. An 83,213-token prompt went through to Haiku although the documented Moss-key limit is 64,000. | `empty_reply_probe.jsonl`, `inference_followup.jsonl` |
| I13 | med | Named `tool_choice` is not honoured on Haiku: forced to call `get_time`, it called both tools. It is honoured on fastlane and luna. | `inference_ai_*.jsonl` `tools.named.*` |
| I14 | med | Haiku with `tool_choice: "none"` returns empty content (1 token, `finish: stop`). | `inference_followup.jsonl` `haiku.tool_choice_none` |
| I15 | med | Invalid tool definitions are accepted: a name with spaces and `!`, and parameter type `nope`, return 200. | `tools.invalid_tool_schema` |
| I16 | med | The hidden fastlane prompt still applies with `X-Moss-System-Prompt: off` and leaks on request. It tells the model to never name or confirm its base model or maker, and adds today's date. This is the ~65 billed tokens in I6. | `leak.system_prompt_off` |
| I17 | low | `logprobs: true` returns 200 with no logprobs (silently ignored). `n: 2` is rejected cleanly. | `media.logprobs`, `media.n_2` |
| I18 | low | Fastlane's image error is a raw engine message: "At most 0 image(s) may be provided". Vendor models read the image correctly. | `media.image.*` |
| I19 | low | On reasoning models `max_tokens` includes hidden reasoning tokens, so small values give empty or wrong answers (luna: 14 to 20 of 20 tokens were reasoning). This should be documented. | `empty_reply_probe.jsonl` |
| I20 | low | Searching Logs by your own `X-Request-Id` spins forever. Moss request IDs work. The ID is not echoed in response headers either. | portal, `api_probe.jsonl` |
| I21 | low | CORS allows any origin to send `Authorization`, so a browser page can call the API with a project key. The docs should say keys are server-only. (The portal itself uses a short-lived session key, which is the right pattern.) | `cors.preflight_any_origin` |
| I22 | low | No gzip on responses. | `http.gzip` |

Positives:
- On 15 arithmetic and logic questions, fastlane scored 14/15 (3/3 on reruns of its miss) and luna, haiku, gemini flash-lite and deepseek flash scored 15/15.
- Strict nested JSON schema: 5/5 exact on all five models.
- Fastlane long context: needle found at 40k, 120k and 165k tokens and at 10, 50, 90 and 95% depth. 165k takes 17.8 s.
- Context limits return precise errors ("about 322634 prompt tokens. The limit is 262144").
- Tool calling on fastlane and luna is correct for required, none, named, parallel (4 calls) and `parallel_tool_calls: false`. Streamed tool-call arguments rebuild into valid JSON on all three models.
- Fastlane is fully deterministic at temperature 0 (1 distinct output in 5); deepseek 2; luna 5, since temperature doesn't apply.
- Header retrieval takes 10.8 ms, adds about 325 prompt tokens, and the answers cite indexed facts. The `moss_search` tool works but made 6 searches and used 3,164 input tokens, about 7x the header path, for the same question.
- A stream dropped by the client stops billing: 32 output tokens billed out of a requested 1,500-word story.

### Round 3 inference (`inference_more.py`, `context_estimate_probe.py`)

| # | Sev | Finding | Evidence |
|---|---|---|---|
| I23 | high | **Fastlane's usable context is about 175k tokens, not the advertised 262,144.** The pre-check estimates about 1.5 tokens per word for every model. A prompt that is really 176k tokens is rejected as "about 264,097 prompt tokens", while 174k really fits (174,087 reported). The same estimate undercounts for Haiku, which is how I12 happened. | `context_estimate_probe.jsonl` |
| I24 | low | Tool-result prompt injection was resisted by fastlane, luna, haiku and deepseek, with no `send_email` calls in 14 tries. DeepSeek quoted the account number back to the user while flagging the attack (my detector counted that as a hijack; it isn't one). | `inference_more_*injection*.jsonl` |

Positives:
- With retrieval on, both models said "not in the documents" for facts missing from the index and answered in-index questions from it. (The luna "BAD" rows in the summary are my checker missing the curly apostrophe in "don’t"; it's fixed in the script.)
- Prompt tokens match between streamed and non-streamed calls on fastlane, luna and haiku. Responses streaming reports usage in `response.completed`.
- Under 8 concurrent streams, fastlane's time to first token goes from 0.10 s to 0.26 s p50, with no errors.
- The tokens-per-minute limit works: after one 170k prompt, the next three got 429 `rate_limit_exceeded` with `Retry-After: 21`.

### Tasks (`tasks_ai.py`)

| # | Sev | Finding | Evidence |
|---|---|---|---|
| T12 | med | The agent logs in with credentials it guesses from the URL. Given `httpbin.org/basic-auth/agentuser/s3cret` and no instruction to log in, it authenticated and returned the protected JSON. Agents shouldn't try credentials they weren't given. | `tasks_ai_agent_api.jsonl` `auth.basic_auth_wall` |
| T13 | low | `effort` barely changes anything: low took 4 steps, $0.0070 and 22 s; high took 7 steps, $0.0084 and 45 s, for the same correct answer. | `effort.*` |
| T14 | low | `webhook` appears in every task object, but sending it on create returns "Unknown field webhook". | `api.webhook_field` |
| T15 | low | Tasks start within 0.1 s of creation (p50 and p90 0.0 s across 64 tasks), which is why the queued-task cap never applies (T5). 60 back-to-back GETs: all 200, no limit. | `api.queue_wait_all_tasks`, `api.poll_60_rapid` |

Positives:
- **No made-up answers.** For a book that doesn't exist it checked all 1,000 books and said so, with and without a schema. For an ISBN not on the page it said "Not shown".
- Full-page extraction (20 rows × title, price, rating) was 20/20 exact on fast ($0.0075) and balanced ($0.087).
- No start URL works through web search (Eiffel Tower → 1889, $0.006).
- File deliverables work: `outputs/page1.json` matched the ground truth.
- moss-fast got the multi-hop question right 3/3.
- Vendor and open models work as task models (luna $0.005, haiku $0.006, deepseek $0.008).
- Cancel right after create gives `cancelled` in 3 s with only the one-minute browser minimum billed.

### Round 3 tasks (`tasks_more.py`)

| # | Sev | Finding | Evidence |
|---|---|---|---|
| T16 | med | **No way to pass secrets.** A password given in the goal is stored in plain text in the task object, returned by `GET /v1/tasks` to anyone holding the project key, and shown in the portal. The agent didn't echo it in its output. A `secrets` field that is redacted after use would fix this. | `tasks_more.jsonl` `secrets.login_with_password` |
| T17 | low | The agent runs arbitrary code in its sandbox: asked to, it reported Python 3.12.3 on `Linux-7.0.0-1017-gcp`. I didn't probe further (env vars, metadata). Together with T6, the sandbox's network and credentials deserve a look. | `sandbox.runtime_info` |
| T18 | low | The undocumented `moss-fast-beta` cost $0.022 on the multi-hop goal, about 3x moss-fast. `moss-balanced-handoff` cost $0.0053, cheaper than moss-fast. Both were correct, but nothing says what they are. | `model.*` |

Positives:
- **It obeys "do not" instructions.** Told to fill a form without submitting, it filled it and stopped; the final screenshot shows the unsent form.
- It handled infinite scroll (100 of 100 quotes), delayed JavaScript rendering, and reading a PDF.
- It found the cheapest of 1,000 books correctly in 54 s for $0.011.
- It logged in with credentials it was given.

## Portal

| # | Sev | Finding |
|---|---|---|
| P1 | med | Numbers disagree: spend is $0.94 on Analytics vs $0.99 on Usage, requests are 205 on Logs vs 257 on Analytics, and "Inference tokens" is 1.4M in the chart vs 14.6K in the table. |
| P2 | med | Logs & Traces and Analytics show a blank panel for 8 to 10 s with no loader. |
| P3 | low | The balance only appears under Settings → Billing. |
| P4 | low | Agent model calls are mixed into Logs with no link to their task. |
| P5 | low | No live view while a task runs, although the API has `live_url`. The steps counter showed 0 at 6.8k tokens. |
| P6 | low | Home says "Get your project key" after a key exists. |
