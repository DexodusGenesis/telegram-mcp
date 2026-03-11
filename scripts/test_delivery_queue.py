#!/usr/bin/env python3
"""
Test the human-clock delivery queue logic **without a Telegram account**.

Run from telegram-mcp directory (needs deps: use uv):
  cd telegram-mcp && uv run python scripts/test_delivery_queue.py

Tests:
- submit_telegram_reply with mode=immediate → message in active queue
- submit_telegram_reply with mode=scheduled → message in delayed heap + JSON persistence
- Persistence: save and load delayed_queue.json

Does NOT start the Telegram client or the delivery worker (no network).
"""

import asyncio
import json
import os
import sys
import tempfile

# Run from telegram-mcp root
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Use a temp file for delayed queue so we don't touch the real one
TEST_QUEUE_JSON = None
_original_delayed_store_path = None


def _patched_store_path():
    return TEST_QUEUE_JSON or _original_delayed_store_path()


async def test_immediate_enqueue():
    """submit_telegram_reply with mode=immediate should put one message in active_queue."""
    import main as m
    m._active_queue = asyncio.Queue()
    m._delayed_heap.clear()
    plan = {
        "mode": "immediate",
        "delay_seconds": None,
        "oof_message": None,
        "user_tz": "UTC",
        "batch_key": "telegram:test-session",
    }
    out = await m.submit_telegram_reply(
        chat_id=12345,
        message="Hello (test)",
        delivery_plan=plan,
        session_id="test-session",
        original_user_messages=["user said hi"],
        reply_to_message_id=None,
        agent_id=None,
    )
    assert "immediate" in out or "Queued" in out, out
    assert m._active_queue.qsize() >= 1, "expected at least one message in active queue"
    msg = await m._active_queue.get()
    assert msg.llm_reply == "Hello (test)"
    assert msg.chat_id == 12345
    print("  OK: immediate → active queue")


async def test_scheduled_enqueue_and_persist():
    """submit_telegram_reply with mode=scheduled should put in delayed heap and persist."""
    import main as m
    m._active_queue = asyncio.Queue()
    m._delayed_heap.clear()
    plan = {
        "mode": "scheduled",
        "delay_seconds": 300,
        "oof_message": None,
        "user_tz": "Europe/Paris",
        "batch_key": "telegram:test-session-2",
    }
    out = await m.submit_telegram_reply(
        chat_id=67890,
        message="Scheduled reply (test)",
        delivery_plan=plan,
        session_id="test-session-2",
        original_user_messages=["night message"],
        reply_to_message_id=None,
        agent_id=None,
    )
    assert "scheduled" in out or "Queued" in out or "eta" in out.lower(), out
    assert len(m._delayed_heap) >= 1, "expected at least one item in delayed heap"
    # Persistence: file should exist and contain the item
    path = m._delayed_store_path()
    assert os.path.isfile(path), f"expected persistence file {path}"
    with open(path, "r", encoding="utf-8") as f:
        data = json.load(f)
    assert isinstance(data, list) and len(data) >= 1
    assert data[0].get("llm_reply") == "Scheduled reply (test)"
    assert data[0].get("chat_id") == 67890
    print("  OK: scheduled → delayed heap + persistence")


async def test_persistence_load():
    """_load_delayed_queue and _restore_delayed_heap should restore items."""
    import main as m
    path = m._delayed_store_path()
    # Write a known payload
    payload = [
        {
            "chat_id": 111,
            "session_id": "restore-session",
            "llm_reply": "Restored message",
            "user_tz": "UTC",
            "batch_key": "telegram:restore-session",
            "created_at": "2025-03-10T12:00:00+00:00",
            "planned_eta_utc": "2025-03-11T07:00:00+00:00",
            "original_user_messages": [],
            "reply_to_message_id": None,
            "agent_id": None,
        }
    ]
    m._save_delayed_queue(payload)
    loaded = m._load_delayed_queue()
    assert len(loaded) == 1 and loaded[0]["llm_reply"] == "Restored message"
    m._delayed_heap.clear()
    m._restore_delayed_heap()
    assert len(m._delayed_heap) == 1
    _, _, qm = m._delayed_heap[0]
    assert qm.llm_reply == "Restored message" and qm.chat_id == 111
    print("  OK: persistence load + restore heap")


def run_tests():
    global TEST_QUEUE_JSON, _original_delayed_store_path
    import main as m
    _original_delayed_store_path = m._delayed_store_path
    fd, TEST_QUEUE_JSON = tempfile.mkstemp(suffix=".json", prefix="delayed_queue_test_")
    os.close(fd)
    try:
        m._delayed_store_path = _patched_store_path
        asyncio.run(test_immediate_enqueue())
        asyncio.run(test_scheduled_enqueue_and_persist())
        asyncio.run(test_persistence_load())
    finally:
        if TEST_QUEUE_JSON and os.path.isfile(TEST_QUEUE_JSON):
            try:
                os.remove(TEST_QUEUE_JSON)
            except OSError:
                pass
        m._delayed_store_path = _original_delayed_store_path


if __name__ == "__main__":
    print("Testing delivery queue (no Telegram connection)...\n")
    run_tests()
    print("\nAll delivery queue tests passed.")
