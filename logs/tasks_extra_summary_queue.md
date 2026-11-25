| test | expected | observed | pass |
|---|---|---|---|
| queue.cap_20 | 429 too_many_queued_tasks around #21 | accepted=24 first_429_at=None | NO |
| queue.cancel_cleanup | all cancelled, ~$0 | statuses={'completed': 21, 'cancelled': 3} total_cost=0.1003 | yes |