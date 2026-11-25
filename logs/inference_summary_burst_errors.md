| test | expected | observed | pass |
|---|---|---|---|
| err.no_auth | 401 | 401 in 0.13s code=authentication_error | yes |
| err.bad_key | 401 | 401 in 0.75s code=authentication_error | yes |
| err.key_only_no_project | 401 w/ helpful msg | 401 in 0.04s code=authentication_error | yes |
| err.swapped_id_key | 401 | 401 in 0.32s code=authentication_error | yes |
| err.unknown_model | 400 model_not_found | 400 in 0.04s code=model_not_found | yes |
| err.vendor_native_no_byok | 400 missing_provider_key | 400 in 0.04s code=missing_provider_key | yes |
| err.bad_byok_key | 401 upstream_error | 401 in 0.63s code=upstream_error | yes |
| err.responses_unknown_field | 400 | 400 in 0.04s code=unsupported_parameter | yes |
| err.responses_previous_id | 400 | 400 in 0.04s code=unsupported_parameter | yes |
| err.unsupported_seed | 400 unsupported_parameter | 200 in 0.04s code=None | NO |
| err.openai_stop | 400 unsupported_parameter | 400 in 0.04s code=unsupported_parameter | yes |
| err.anthropic_temperature | 400 unsupported_parameter | 400 in 0.04s code=unsupported_parameter | yes |
| err.empty_messages | 400 | 400 in 0.05s code=invalid_request_error | yes |
| err.missing_messages | 400 | 400 in 0.04s code=invalid_request_error | yes |
| err.bad_role | 400 | 400 in 0.04s code=invalid_request_error | yes |
| err.temperature_out_of_range | 400 | 400 in 0.04s code=invalid_request_error | yes |
| err.negative_max_tokens | 400 | 400 in 0.05s code=invalid_request_error | yes |
| err.max_tokens_1 | 200, finish_reason=length | 200 in 0.08s code=None finish=length usage={'prompt_tokens': 92, 'completion_tokens': 1, 'total_tokens': 93, 'prompt_tokens_details': {'cached_tokens': 0, 'cache_write_tokens': 0}, 'completion_tokens_details': {'reasonin | yes |
| err.malformed_json | 400 | 400 in 0.04s code=invalid_request_error | yes |
| err.unknown_index | 403 permission_error | 403 in 0.85s code=permission_error | yes |
| err.33_indexes | 400 (max 32) | 403 in 0.39s code=permission_error | NO |
| err.wrong_method_get_chat | 405 | 404 in 0.03s code=None | NO |
| err.unknown_route | 404 | 404 in 0.03s code=None | yes |
| err.prompt_injection_in_model | 400 not 500 | 400 in 0.04s code=model_not_found | yes |
| err.model_wrong_type | 400 not 500 | 200 in 0.04s code=None | NO |
| err.content_null | 400 not 500 | 400 in 0.04s code=invalid_request_error | yes |
| err.unicode_heavy | 200 | 200 in 0.04s code=None | yes |
| err.body_over_4mb | 413 | EXC in 0.12s connection error: ReadError('[WinError 10053] An established connection was aborted by the software in your host machine') bytes=4400000 | NO |
| err.body_just_under_4mb | 400 context_length_exceeded | 400 in 0.96s code=context_length_exceeded bytes=3980000 | yes |
| err.context_length_300k_tokens | 400 context_length_exceeded | 400 in 0.45s code=context_length_exceeded bytes=1200000 | yes |
| burst.25x_moss/fastlane-1 | some 429 with Retry-After beyond burst 10 | mixed in 0.31s codes={200: 9, 429: 16} p50=0.31s max=0.40s 429_headers={'content-type': 'application/json', 'retry-after': '1', 'x-moss-box': 'g2a0e48', 'x-moss-request-id': '888c4185076e4e049c42eea65f58e829', 'x-ratelim | n/a |