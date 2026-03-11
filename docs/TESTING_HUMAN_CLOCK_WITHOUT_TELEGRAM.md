# Testing the human-clock delivery without a Telegram account

If you don't have a Telegram account (e.g. the previous one was banned), you can still test the new delivery pipeline in two ways.

## 1. AI-service: time router and timezone (no Telegram, no heavy deps)

From **AI-service** directory:

```bash
cd AI-service
python3 scripts/test_human_clock_delivery.py
```

This script is **self-contained** (only stdlib + `zoneinfo`). It tests:

- `effective_timezone` from `lead_info` (timezone, country, fallback to UTC)
- `time_router_compute_delivery_plan`: day (07:00–21:59 local) → immediate; night → scheduled with next 7am + jitter
- Meet channel always gets immediate; Telegram uses circadian routing

No Telegram, no LangGraph, no API keys required.

## 2. telegram-mcp: queue, persistence, and submit_telegram_reply (no Telegram connection)

From **telegram-mcp** directory (install deps first, e.g. with uv):

```bash
cd telegram-mcp
uv run python scripts/test_delivery_queue.py
```

This script tests:

- `submit_telegram_reply` with `mode=immediate` → message lands in the active queue
- `submit_telegram_reply` with `mode=scheduled` → message lands in the delayed heap and is persisted to `delayed_queue.json` (test uses a temp file)
- Persistence: save and load of the delayed queue, and restore into the heap

It **does not** start the Telegram client or the delivery worker, so no connection to Telegram is needed. It only checks that enqueue and persistence behave correctly.

## 3. Optional: dry-run the full stack with a mock client

To run telegram-mcp end-to-end without sending anything to Telegram, you would need to:

- Run telegram-mcp in HTTP mode **without** calling `client.start()` (e.g. add a `TELEGRAM_DRY_RUN=1` that skips connection and makes the delivery worker no-op), or
- Mock the Telethon `client` so `get_entity`, `send_message`, `send_read_acknowledge`, and `SetTypingRequest` are no-ops that only log.

That would allow the AI-service cron to call `submit_telegram_reply` via MCP and see messages flow through the queue and (in dry-run) get “sent” only in logs. Implementing that is optional; the two scripts above are enough to validate the logic without any Telegram account.
