| test | expected | observed | pass |
|---|---|---|---|
| responses.basic | 200 + text | 200 in 0.10s text='The capital of Australia is Canberra.' | yes |
| responses.default_model | 200, model=moss/fastlane-1 | 200 in 0.03s model=moss/fastlane-1 | yes |
| chat.basic | 200 + usage | 200 in 0.03s text='The capital of Australia is Canberra.' usage={'prompt_tokens': 0, 'completion_tokens': 9, 'total_tokens': 9, 'prompt_tokens_details': {'cached_tokens': 0, 'cache_write_tokens': 0}, 'completion_tokens_d | yes |
| chat.alias_moss | 200 (deprecated alias) | 200 in 0.03s model=moss/fastlane-1 | yes |
| chat.json_schema | valid JSON matching schema | 200 in 0.03s parsed={'city': 'Tokyo', 'country': 'Japan', 'population_millions': 14.026217413088585} | yes |
| chat.tool_call | tool_calls get_weather(Paris) | 200 in 0.23s tool_calls=[{'id': 'chatcmpl-tool-99891c9d1792a781', 'type': 'function', 'function': {'name': 'get_weather', 'arguments': '{"city": "Paris"}'}}] | yes |
| chat.tool_loop_round2 | answer uses tool result (14C, rain) | 200 in 0.35s text="It's raining in Paris right now, with a temperature of 14°C (about 57°F). You might want to grab an | yes |
| chat.multiturn | says Zorblat | 200 in 0.11s text='Zorblat' | yes |
| chat.system_prompt_off | 200 | 200 in 0.17s text='I am Moss fastlane-1, an AI model served by Moss.' | yes |
| chat.index_retrieval | 200 + X-Moss-Retrieve-Ms header | 200 in 0.59s text="The stored agent memory does not contain any information about what the stored agent memory says, as it only includes s | yes |
| openai_sdk.chat | works unmodified | 200 in 0.93s text='The capital of Australia is Canberra.' | yes |
| openai_sdk.responses | works unmodified | 200 in 0.19s output_text='The capital of Australia is Canberra.' | yes |
| cache.reply_cache_hit | 2nd identical call faster, prompt_tokens=0 | 200 in 0.03s 1st=0.46s usage1={'prompt_tokens': 126, 'completion_tokens': 62, 'total_tokens': 188, 'prompt_tokens_details': {'cached_tokens': 0, 'cache_write_tokens': 0}, 'completion_tokens_details': {'reasoning_tokens': | yes |
| cache.reply_cache_off | full cost again | 200 in 0.62s usage={'prompt_tokens': 126, 'completion_tokens': 69, 'total_tokens': 195, 'prompt_tokens_details': {'cached_tokens': 0, 'cache_write_tokens': 0}, 'completion_tokens_details': {'reasoning_tokens': 0}} | yes |
| cache.prefix_0 | cached_tokens>0 on calls 2,3 | 200 in 0.39s prompt=4814 cached=0 | n/a |
| cache.prefix_1 | cached_tokens>0 on calls 2,3 | 200 in 0.39s prompt=4814 cached=4800 | yes |
| cache.prefix_2 | cached_tokens>0 on calls 2,3 | 200 in 0.32s prompt=4814 cached=4800 | yes |
| stream.chat_fastlane | TTFT, [DONE], usage chunk | 200 in 0.55s ttft=0.15502500000002328 chunks=24 usage={'prompt_tokens': 99, 'completion_tokens': 70, 'total_tokens': 169, 'prompt_tokens_details': {'cached_tokens': 0, 'cache_write_tokens': 0}, 'completion_tokens_details | yes |
| stream.responses | delta events + response.completed | 200 in 0.32s ttft=0.14942750000045635 events={'response.created': 1, 'response.in_progress': 1, 'response.output_item.added': 1, 'response.content_part.added': 1, 'response.output_text.delta': 11, 'response.output_text.d | yes |