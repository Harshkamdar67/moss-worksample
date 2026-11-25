# Moss Inference: work sample

**Repo:** https://github.com/Harshkamdar67/moss-worksample
The repo has my scripts, raw logs and task outputs. `FINDINGS.md` lists the evidence for every point below. I made about 500 Inference calls and ran 89 browser tasks. I checked answers against data I scraped myself. Total cost: about $2.30.

## Tasks API

**Biggest issues**
1. **A task that runs out of time reports success.** It ends as `completed` with no error, even though the agent wrote "1 of 60" done. The docs say it should be `failed`. A client that trusts `status` will ship half-done work.
2. **The budget cap leaks.** A $0.01 cap spent $0.024 on balanced (+139%). Advanced went 38% over. The cap is only checked between model calls, and the API accepts caps smaller than one call.
3. **"Verified" doesn't mean correct.** `verification.passed` was `true` for a wrong answer and for an empty one. It was also `true` when the start page never loaded: the agent read the answer out of the URL and said nothing.
4. **Credentials and network access are loose.**
   - The agent logged in with credentials it found in a URL. Nobody asked it to.
   - Passwords in the goal are stored in plain text and show up in `GET /v1/tasks`.
   - `localhost` and `169.254.169.254` are accepted as start URLs.
   - The sandbox runs any code.
5. **Nothing caps concurrent tasks.** Tasks start in 0.1 s, so the 20-task queue limit never kicks in.

**Smaller:**
- `effort` and the advanced tier barely change results.
- BYOK is documented but rejected.
- The list route, `webhook` and two models aren't documented.

**Liked:**
- 40 of 41 scored goals were correct, and it never made up an answer on bait questions.
- It scraped 1,000 books into a CSV in 45 s for $0.011, with every row right.
- It obeyed "do not submit" and ignored prompt injection.
- Validation errors are excellent.

## Inference API

**Biggest issues**
1. **The reply cache is on by default and ignores `temperature` and `user`.** Ask for a random number twice and you get the same one. Two different end users can get the same cached reply.
2. **The context check guesses about 1.5 tokens per word for every model.** Fastlane rejects a real 176k-token prompt as "about 264k", so its usable context is about 175k, not 262k. The same guess let an 83k-token prompt through to Haiku, past its 64k limit.
3. **Haiku fails silently.** On a harmless prompt it returns 200, `content_filter` and an empty reply, and you still pay for the prompt. It also ignores a named `tool_choice`.
4. **You pay for a hidden prompt even with `X-Moss-System-Prompt: off`.** It adds about 65 tokens to every call, and the model repeats it when asked.

**Smaller:**
- `"model": 123`, broken tool schemas and `seed` all return 200, and `logprobs` is silently dropped.
- A body over 4 MB gets a dropped connection, not a 413.
- CORS allows any origin.

**Liked:**
- The stock OpenAI SDK works as is.
- Fastlane answers in 155 ms, gives the same output at temperature 0, and found a fact buried at 165k tokens.
- It scored 14/15 on reasoning questions, and all five models I tried scored 5/5 on strict JSON.
- Tool calling works.
- Retrieval adds 11 ms and doesn't invent facts.
- A dropped stream stops billing.

## Portal

**Liked:** it takes one screen to go from sign-up to a first call. The Playground shows speed and tokens on every reply, and the task list shows spend against the cap as it runs.

**Didn't:**
- Spend, request and token counts differ between Analytics, Usage and Logs.
- Logs and Analytics stay blank for 8 to 10 s.
- The balance is buried in Settings.
- The agent's calls aren't linked to their task.

## What I'd fix first

1. Mark timed-out tasks `failed` or `partial`, and check the budget before each call.
2. Make verification check the answer, and add a "not found" result.
3. Skip the cache when `temperature > 0`, and key it on `user`.
4. Count context with each model's real tokenizer.
5. Add a redacted secrets field, block private IPs, and cap running tasks.
6. Feed every portal number from one ledger.
