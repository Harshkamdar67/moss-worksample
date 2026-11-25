| test | expected | observed | pass |
|---|---|---|---|
| val.missing_goal | 400 | 400 invalid_request_error: goal must be text of 1 to 20000 characters | yes |
| val.empty_goal | 400 | 400 invalid_request_error: goal must be text of 1 to 20000 characters | yes |
| val.whitespace_goal | 400 | 400 invalid_request_error: goal must be text of 1 to 20000 characters | yes |
| val.goal_20001_chars | 400 | 400 invalid_request_error: goal must be text of 1 to 20000 characters | yes |
| val.missing_environment | 400 | 400 invalid_request_error: environment must be {"type": "browser"}; v0 runs browser tasks only | yes |
| val.env_type_desktop | 400 | 400 invalid_request_error: environment must be {"type": "browser"}; v0 runs browser tasks only | yes |
| val.start_url_ftp | 400 | 400 invalid_request_error: environment.start_url must be an http or https URL, or a host such as example.com | yes |
| val.start_url_javascript | 400 | 400 invalid_request_error: environment.start_url must be an http or https URL, or a host such as example.com | yes |
| val.start_url_file | 400 | 400 invalid_request_error: environment.start_url must be an http or https URL, or a host such as example.com | yes |
| val.start_url_not_a_url | 400 | 400 invalid_request_error: environment.start_url must be an http or https URL, or a host such as example.com | yes |
| val.runtime_59 | 400 | 400 invalid_request_error: limits.max_runtime_seconds must be a number from 60 to 7200 | yes |
| val.runtime_7201 | 400 | 400 invalid_request_error: limits.max_runtime_seconds must be a number from 60 to 7200 | yes |
| val.runtime_float | 400 | ACCEPTED (202) -> spent money; cancelled (200 running) | NO |
| val.cost_0.001 | 400 | 400 invalid_request_error: limits.max_cost_usd must be a number from 0.01 to 50 | yes |
| val.cost_51 | 400 | 400 invalid_request_error: limits.max_cost_usd must be a number from 0.01 to 50 | yes |
| val.cost_negative | 400 | 400 invalid_request_error: limits.max_cost_usd must be a number from 0.01 to 50 | yes |
| val.cost_string | 400 | 400 invalid_request_error: limits.max_cost_usd must be a number from 0.01 to 50 | yes |
| val.unknown_limit_key | 400 | 400 invalid_request_error: limits takes max_runtime_seconds and max_cost_usd | yes |
| val.unknown_top_field | 400 | 400 invalid_request_error: Unknown field priority | yes |
| val.bad_model | 400 | 400 model_not_found: model must be a Moss tier or a Moss catalog model that tasks serve: moss-advanced, moss-balanced, moss-balanced-handoff, moss-fast, moss-fas | yes |
| val.bad_effort | 400 | 400 invalid_request_error: effort must be low, medium or high | yes |
| val.schema_not_object | 400 | 400 invalid_request_error: output_schema must describe one JSON object: its "type" must be "object". For a list, put it in a property, such as {"type": "object", "prop | yes |
| val.schema_invalid | 400 | 400 invalid_request_error: output_schema.properties.a.type must be one of object, array, string, boolean, null, integer, number, or a list of them | yes |
| val.schema_20kb | 400 | 400 invalid_request_error: output_schema must be a JSON Schema object under 20000 bytes | yes |
| val.metadata_4kb | 400 | 400 invalid_request_error: metadata must be an object under 4000 bytes | yes |
| val.metadata_not_object | 400 | 400 invalid_request_error: metadata must be an object under 4000 bytes | yes |
| val.idempotency_key_too_long | 400 | 400 invalid_request_error: Idempotency-Key must be 1 to 255 visible ASCII characters | yes |
| val.idempotency_key_non_ascii | 400 | EXC UnicodeEncodeError('ascii', 'клюé', 0, 4, 'ordinal not in range(128)') | NO |
| val.byok_on_moss_model | 400 | 400 provider_key_not_supported: Tasks on this server do not take X-Moss-Provider-Key. Create the task without it | yes |
| val.body_over_256k | 413 | 413 invalid_request_error: The request body is larger than 262144 bytes | yes |
| val.start_url_localhost | 400 (internal address) | ACCEPTED 202, cancelled immediately (running) | n/a |
| val.start_url_metadata_ip | 400 (internal address) | ACCEPTED 202, cancelled immediately (running) | n/a |
| val.start_url_private_ip | 400 (internal address) | ACCEPTED 202, cancelled immediately (running) | n/a |