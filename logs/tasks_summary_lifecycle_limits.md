| test | expected | observed | pass |
|---|---|---|---|
| life.get_unknown_id | 404 | 404 not_found_error: No task with this id in this project | yes |
| life.get_malformed_id | 404/400 | 404 not_found_error: No task with this id in this project | yes |
| life.cancel_unknown_id | 404 | 404 not_found_error: No task with this id in this project | yes |
| life.list_tasks_route | undocumented: probe | 200 {'object': 'list', 'data': [{'id': 'task_d629d7225fa149cda03511be2ab9b261', 'object': 'task', 'status': 'running', 'title': 'Find Tipping the Velvet Price', 'go | n/a |
| life.idempotent_replay | same id + Idempotent-Replayed: true | 202/202 same_id=True replay_hdr=true | yes |
| life.idempotency_key_reused | 422 | 422 idempotency_key_reused: This Idempotency-Key was sent with another body. Send a new key for a new task | yes |
| life.idempotency_key_case | probe: new task? | 202 same_id=False | n/a |
| life.files_before_finish | 409 task_not_finished | 409 task_not_finished: The task's files are served once it has finished | yes |
| life.example_com_heading | completed, 'Example Domain' | completed out='Example Domain' cost={'model_usd': 0.004412, 'total_usd': 0.004745, 'browser_usd': 0.0003333333333333333, 'traffic_usd': None} steps=4 transitions=[(0.3, 'running'), (16.4, 'completed')] | yes |
| life.files_list | 200 list | 200 n=4 [{'path': 'screenshots/agent/ses_dee819f98ffewVeGrceHM9PaWn-1795589835403-000.png', 'bytes': 83263}, {'path': 'screenshots/runner/00001-step-2.png', 'bytes': 83263}, {'path': 'screenshots/runner/00002 | yes |
| life.file_download | 200 bytes | 200 83263 bytes image/png | yes |
| life.file_path_traversal | 404 | 404 '{"detail":"Not Found"}' | yes |
| life.cancel_finished | 409 or no-op 200 | 200 status=completed  | yes |
| life.cancel_running | cancel_requested then cancelled quickly | cancel->200 status=running cancel_requested=True; final=cancelled after 10.4s; cost={'model_usd': 0.00602, 'total_usd': 0.006353, 'browser_usd': 0.0003333333333333333, 'traffic_usd': None} | yes |
| lim.budget_0.02 | budget_exceeded | failed budget_exceeded: Spent $0.02 run_s=7.188865 cost={'model_usd': 0.023856, 'total_usd': 0.024189, 'browser_usd': 0.0003333333333333333, 'traffic_usd': None} steps=1 partial_result='None' OVERSPEND model_usd=0.023856 > cap 0.02 | NO |
| lim.runtime_60s | time_limit | completed None: None run_s=45.092731 cost={'model_usd': 0.010221, 'total_usd': 0.010554, 'browser_usd': 0.0003333333333333333, 'traffic_usd': None} steps=7 partial_result='Collected all 1,000 book titles and displayed prices across 50 catalogue pages, ' | NO |