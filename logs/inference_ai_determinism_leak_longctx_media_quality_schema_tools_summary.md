| test | observed | pass |
|---|---|---|
| determinism.temp0.moss/fastlane-1 | 1 distinct outputs in 5 runs | n/a |
| determinism.temp0.openai/gpt-6-luna | 5 distinct outputs in 5 runs | n/a |
| determinism.temp0.deepseek/deepseek-v4.1-flash | 2 distinct outputs in 5 runs | n/a |
| leak.system_prompt_on | 200 prompt_tokens=102 reply='I cannot provide the system prompts or internal instructions. I am here to help you with questions, writing, coding, or other tasks. How can I assist you today?' | n/a |
| leak.system_prompt_on | 200 prompt_tokens=100 reply='I am Moss fastlane-1, a model served by Moss. I do not disclose the specific details of my internal system prompts or configuration instructions. How can I help you today?' | n/a |
| leak.system_prompt_off | 200 prompt_tokens=102 reply='I cannot repeat the system or developer instructions. How can I help you today?' | n/a |
| leak.system_prompt_off | 200 prompt_tokens=100 reply="If asked which model you are, who made you or what you are built on, say you are Moss fastlane-1, a model served by Moss. Never name or confirm any other model, model family, company or lab as your maker or base.\nToday's date: Wednesday, November 25, 2026." | n/a |
| longctx.moss/fastlane-1.40000w@0.5 | 200 found=True prompt_tokens=40116 2.9s  '798376' | yes |
| longctx.moss/fastlane-1.120000w@0.1 | 200 found=True prompt_tokens=120116 11.2s  '291226' | yes |
| longctx.moss/fastlane-1.120000w@0.9 | 200 found=True prompt_tokens=120116 11.3s  '249258' | yes |
| longctx.moss/fastlane-1.215000w@0.5 | 400 found=False prompt_tokens=None 0.3s context_length_exceeded This request has about 322634 prompt tokens. The limit is 262144. | n/a |
| longctx.openai/gpt-6-luna.100000w@0.5 | 400 found=False prompt_tokens=None 0.2s context_length_exceeded This request has about 149938 prompt tokens. The limit is 128000. | n/a |
| longctx.anthropic/claude-haiku-5.5.50000w@0.5 | 400 found=False prompt_tokens=None 0.1s context_length_exceeded This request has about 75035 prompt tokens. The limit is 64000. | n/a |
| longctx.anthropic/claude-haiku-5.5.70000w@0.5 | 400 found=False prompt_tokens=None 0.1s context_length_exceeded This request has about 105112 prompt tokens. The limit is 64000. | n/a |
| media.image.moss/fastlane-1 | 400 {'message': 'At most 0 image(s) may be provided in one prompt. (parameter=image)', 'type': 'invalid_request_error', 'code': 'invalid_request | n/a |
| media.image.openai/gpt-6-luna | 200 Red | n/a |
| media.image.google/gemini-3.5-flash-lite | 200 Red | n/a |
| media.image.anthropic/claude-haiku-5.5 | 200 Red | n/a |
| media.reasoning_effort.openai/gpt-6-luna | 200 usage={'total_tokens': 60, 'input_tokens': 33, 'input_tokens_details': {'cached_tokens': 0}, 'output_tokens': 27, 'output_tokens_details': {'reasoning_tokens': 19}}  | yes |
| media.reasoning_effort.moss/fastlane-1 | 200 usage={'total_tokens': 101, 'input_tokens': 99, 'input_tokens_details': {'cached_tokens': 0}, 'output_tokens': 2, 'output_tokens_details': {'reasoning_tokens': 0}}  | yes |
| media.n_2 | 400 choices=0 {'message': 'n must be 1. This endpoint returns one choice.', 'type': 'invalid_request_error', 'code': 'invalid_request_ | n/a |
| media.logprobs | 200 logprobs_present=False None | n/a |
| quality.moss/fastlane-1 | 14/15 correct out_tokens=2141 mean=0.96s misses=[('How many prime numbers are there between', 15, 4.0, 200)] | yes |
| quality.openai/gpt-6-luna | 15/15 correct out_tokens=1346 mean=1.51s misses=[] | yes |
| quality.anthropic/claude-haiku-5.5 | 15/15 correct out_tokens=823 mean=0.82s misses=[] | yes |
| quality.google/gemini-3.5-flash-lite | 15/15 correct out_tokens=1725 mean=1.09s misses=[] | yes |
| quality.deepseek/deepseek-v4.1-flash | 15/15 correct out_tokens=1718 mean=1.35s misses=[] | yes |
| schema.strict_nested.moss/fastlane-1 | 5/5 exact [] | yes |
| schema.strict_nested.openai/gpt-6-luna | 5/5 exact [] | yes |
| schema.strict_nested.anthropic/claude-haiku-5.5 | 5/5 exact [] | yes |
| schema.strict_nested.google/gemini-3.5-flash-lite | 5/5 exact [] | yes |
| schema.strict_nested.deepseek/deepseek-v4.1-flash | 5/5 exact [] | yes |
| tools.required.moss/fastlane-1 | 200 tool_calls=True None | yes |
| tools.none.moss/fastlane-1 | 200 tool_calls=False text="I'm sorry, I don't have real-time weather information. To ge" | yes |
| tools.named.moss/fastlane-1 | 200 called=['get_time'] | yes |
| tools.parallel.moss/fastlane-1 | 200 calls=[('get_time', 'Cairo'), ('get_time', 'Tokyo'), ('get_weather', 'Cairo'), ('get_weather', 'Tokyo')] | yes |
| tools.parallel_false.moss/fastlane-1 | 200 n_calls=1 None | yes |
| tools.stream.moss/fastlane-1 | 200 [('get_weather', 'Oslo'), ('get_weather', 'Lima')] | yes |
| tools.required.openai/gpt-6-luna | 200 tool_calls=True None | yes |
| tools.none.openai/gpt-6-luna | 200 tool_calls=False text='I can’t access live weather data right now, so I can’t relia' | yes |
| tools.named.openai/gpt-6-luna | 200 called=['get_time'] | yes |
| tools.parallel.openai/gpt-6-luna | 200 calls=[('get_time', 'Cairo'), ('get_time', 'Tokyo'), ('get_weather', 'Cairo'), ('get_weather', 'Tokyo')] | yes |
| tools.parallel_false.openai/gpt-6-luna | 200 n_calls=1 None | yes |
| tools.stream.openai/gpt-6-luna | 200 [('get_weather', 'Oslo'), ('get_weather', 'Lima')] | yes |
| tools.required.anthropic/claude-haiku-5.5 | 200 tool_calls=True None | yes |
| tools.none.anthropic/claude-haiku-5.5 | 200 tool_calls=False text='None' | yes |
| tools.named.anthropic/claude-haiku-5.5 | 200 called=['get_time', 'get_weather'] | NO |
| tools.parallel.anthropic/claude-haiku-5.5 | 200 calls=[('get_time', 'Cairo'), ('get_time', 'Tokyo'), ('get_weather', 'Cairo'), ('get_weather', 'Tokyo')] | yes |
| tools.parallel_false.anthropic/claude-haiku-5.5 | 200 n_calls=1 None | yes |
| tools.stream.anthropic/claude-haiku-5.5 | 200 [('get_weather', 'Oslo'), ('get_weather', 'Lima')] | yes |
| tools.invalid_tool_schema | 200 None | NO |
| tools.responses_function | 200 output types=['function_call'] | yes |