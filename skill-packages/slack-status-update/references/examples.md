# Example Patterns

## New status post

```json
{
  "action": "post_message",
  "channel": "C123456",
  "text": "Investigating elevated checkout errors. Rollback is in progress. Next update in 15 minutes."
}
```

## Threaded follow-up

```json
{
  "action": "post_message",
  "channel": "C123456",
  "thread_ts": "1712345678.900000",
  "text": "Mitigation is holding. Error rate is trending down. We are confirming customer recovery."
}
```

## Update the lead message

```json
{
  "action": "update_message",
  "channel": "C123456",
  "ts": "1712345678.900000",
  "text": "Resolved. Traffic is stable after rollback. Follow-up review will be posted by 17:00 UTC."
}
```
