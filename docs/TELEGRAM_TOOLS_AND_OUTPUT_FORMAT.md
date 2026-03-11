# Telegram MCP Tools and Output Format

This document describes the Telegram MCP server tools and their **output format**: what each tool returns and how to interpret it.

---

## Overview

All tools are exposed as **MCP tools** and return a **string**. That string is either:

- **Plain text** (newline-separated lines or short messages)
- **JSON** (indented, for structured data)
- **Success/status messages** (short human-readable text)
- **Error messages** (with an error code; see [Error format](#error-format))

There are no binary or file streams in tool outputs.

---

## Input validation: `chat_id` and `user_id`

Tools that take `chat_id` or `user_id` accept:

| Format | Example | Notes |
|--------|---------|--------|
| **Integer ID** | `123456789`, `-1001234567890` | Direct Telegram ID |
| **String ID** | `"123456789"` | Same as integer, as string |
| **Username** | `"@username"`, `"username"` | Public username (users/channels); 5+ chars |

Invalid values produce a clear error message (e.g. "Invalid chat_id: ... Must be a valid integer ID, or a username string.").

---

## Error format

On failure, tools use a central formatter. You get:

- **User-facing message**: Short, safe text.
- **Error code**: `{PREFIX}-ERR-{NNN}` (e.g. `CHAT-ERR-042`, `MSG-ERR-117`).

Example:

```text
An error occurred (code: CHAT-ERR-042). Check mcp_errors.log for details.
```

Full stack traces and context are written to **`mcp_errors.log`** (JSON lines). The code helps correlate log entries with the tool call.

---

## Output format by category

### 1. Chat listing and info

| Tool | Output type | Format |
|------|-------------|--------|
| **get_chats(page, page_size)** | Plain text | One line per chat: `Chat ID: {id}, Title: {title}`. "Page out of range." if no page. |
| **list_chats(chat_type, limit)** | Plain text | One line per chat: `Chat ID: {id}, Title: {title}, Type: {User\|Group\|Channel\|...}, Username: @{username}, Unread: {n}\|No unread messages`. "No chats found matching the criteria." if empty. |
| **get_chat(chat_id)** | Plain text | Multiple lines: `ID:`, `Title:` or `Name:`, `Type:`, `Username:`, `Participants:`, `Unread Messages:`, `Last Message:`, `Message:`. |

**Example – get_chats:**

```text
Chat ID: 123, Title: My Group
Chat ID: 456, Title: Support Channel
```

**Example – list_chats:**

```text
Chat ID: 123, Title: My Group, Type: Supergroup, Username: @mygroup, No unread messages
Chat ID: 456, Name: John Doe, Type: User, Username: @johndoe, Unread: 2
```

---

### 2. Messages

| Tool | Output type | Format |
|------|-------------|--------|
| **get_messages(chat_id, page, page_size)** | Plain text | One line per message: `ID: {id} \| {sender} \| Date: {date} \| reply to {id} \| views:n \| forwards:n \| reactions:n \| Message: {text}`. "No messages found for this page." if empty. |
| **list_messages(chat_id, limit, search_query, from_date, to_date)** | Plain text | Same line format as `get_messages`. |
| **get_history(chat_id, limit)** | Plain text | Same line format as `get_messages`. |
| **get_message_context(chat_id, message_id, context_size)** | Plain text | First line: `Context for message {id} in chat {chat_id}:`. Then blocks: `ID: {id} \| {sender} \| {date} [THIS MESSAGE] \| reply to {id}\n  → Replied message: ...\n{text}\n`. |
| **get_pinned_messages(chat_id)** | Plain text | Same per-message line format. "No pinned messages found in this chat." if none. |

**Example – get_messages / get_history:**

```text
ID: 42 | Alice | Date: 2025-01-01 12:00:00+00:00 | Message: Hello
ID: 43 | Bob | Date: 2025-01-01 12:01:00+00:00 | reply to 42 | Message: Hi there
```

---

### 3. Sending and editing messages

| Tool | Output type | Format |
|------|-------------|--------|
| **send_message(chat_id, message)** | Status | `"Message sent successfully."` or error. |
| **reply_to_message(chat_id, message_id, text)** | Status | Success or error. |
| **edit_message(chat_id, message_id, new_text)** | Status | Success or error. |
| **delete_message(chat_id, message_id)** | Status | Success or error. |
| **forward_message(...)** | Status | Success or error. |
| **pin_message / unpin_message** | Status | Success or error. |
| **mark_as_read(chat_id)** | Status | Success or error. |

---

### 4. Inline buttons

| Tool | Output type | Format |
|------|-------------|--------|
| **list_inline_buttons(chat_id, message_id?, limit?)** | Plain text | First line: `Buttons for message {id} (date {date}):`. Then one line per button: `[index] text='...', callback=yes|no[, url=...]`. Or "No message with inline buttons found." / "Message X does not contain inline buttons." |
| **press_inline_button(chat_id, message_id?, button_text?, button_index?)** | Status | Success or error. |

**Example – list_inline_buttons:**

```text
Buttons for message 42 (date 2025-01-01 12:00:00+00:00):
[0] text='📋 View tasks', callback=yes
[1] text='ℹ️ Help', callback=yes
[2] text='🌐 Visit site', callback=no, url=https://example.org
```

---

### 5. Chats, groups, channels

| Tool | Output type | Format |
|------|-------------|--------|
| **create_group(title, user_ids)** | Status | `"Group created with ID: {id}"` or "Group created successfully. ..." or error. |
| **invite_to_group(group_id, user_ids)** | Status | `"Successfully invited {n} users to {title}"` or error. |
| **leave_chat(chat_id)** | Status | e.g. `"Left channel/supergroup {name} (ID: ...)."` or error. |
| **subscribe_public_channel(channel)** | Status | `"Subscribed to {title}."` or "Already subscribed to ..." or error. |
| **get_invite_link(chat_id)** | Plain text | Raw invite URL, e.g. `https://t.me/+AbCdEfGhIjKlMnOp`, or "Could not retrieve invite link...". |
| **join_chat_by_link(link)** | Status | e.g. "Successfully joined chat: {title}" or "You are already a member of this chat: ...". |
| **get_participants(chat_id)** | Plain text | One line per participant: `ID: {id}, Name: {first last}`. |
| **get_admins(chat_id)** | Plain text | One line per admin (same style). |
| **get_banned_users(chat_id)** | Plain text | One line per banned user. |

---

### 6. Forum topics (supergroups)

| Tool | Output type | Format |
|------|-------------|--------|
| **list_topics(chat_id, limit, offset_topic, search_query)** | Plain text | One line per topic: `Topic ID: {id} \| Title: {title} \| Messages: {n} \| Unread: {n} \| Closed: Yes \| Last Activity: {iso date}`. "No topics found..." / "The specified chat is not a supergroup." / "forum topics not enabled" when applicable. |

**Example:**

```text
Topic ID: 1 | Title: General | Messages: 100 | Unread: 2 | Last Activity: 2025-01-01T12:00:00+00:00
Topic ID: 2 | Title: Support | Messages: 50 | Closed: Yes
```

---

### 7. Contacts

| Tool | Output type | Format |
|------|-------------|--------|
| **list_contacts()** | Plain text | One line per contact: `ID: {id}, Name: {name}[, Username: @x][, Phone: x]`. "No contacts found." if empty. |
| **search_contacts(query)** | Plain text | Same line format. "No contacts found matching '{query}'." if empty. |
| **get_contact_ids()** | Plain text | `"Contact IDs: id1, id2, ..."` or "No contact IDs found." |
| **get_direct_chat_by_contact(contact_query)** | Plain text | One line per match: `Chat ID: {id}, Contact: {name}[, Username: @x][, Unread: n]`. Or "No contacts found..." / "Found contacts: ... but no direct chats...". |

---

### 8. User and profile

| Tool | Output type | Format |
|------|-------------|--------|
| **get_me()** | JSON | Object: `id`, `name`, `type` ("user"), optional `username`, `phone`. |
| **get_user_photos(user_id, limit)** | JSON | Array of photo IDs: `[id1, id2, ...]`. |
| **get_user_status(user_id)** | Plain text | Telethon status string (e.g. "UserStatusOnline", "UserStatusOffline"). |
| **update_profile(first_name, last_name, about)** | Status | Success or error. |
| **get_bot_info(bot_username)** | JSON | Full user/bot object (from Telethon `to_dict`) or fallback: `bot_info` with `id`, `username`, `first_name`, `last_name`, `is_bot`, `verified`, `about`. |

**Example – get_me:**

```json
{
  "id": 123456789,
  "name": "Your Name",
  "type": "user",
  "username": "your_username",
  "phone": "+1234567890"
}
```

---

### 9. Reactions

| Tool | Output type | Format |
|------|-------------|--------|
| **send_reaction(chat_id, message_id, emoji, big)** | Status | e.g. `"Reaction '👍' sent to message {id} in chat {chat_id}."` |
| **remove_reaction(chat_id, message_id)** | Status | e.g. `"Reaction removed from message {id} in chat {chat_id}."` |
| **get_message_reactions(chat_id, message_id, limit)** | JSON | `{ "message_id", "chat_id", "reactions": [ { "user_id", "emoji", "date" } ], "count" }`. Or "No reactions on message ..." if none. |

**Example – get_message_reactions:**

```json
{
  "message_id": 42,
  "chat_id": "123",
  "reactions": [
    { "user_id": 111, "emoji": "👍", "date": "2025-01-01T12:00:00+00:00" },
    { "user_id": 222, "emoji": "❤️", "date": "2025-01-01T12:01:00+00:00" }
  ],
  "count": 2
}
```

---

### 10. Polls

| Tool | Output type | Format |
|------|-------------|--------|
| **create_poll(chat_id, question, options, ...)** | Status | `"Poll created successfully in chat {chat_id}."` or validation/error message. |

---

### 11. Drafts

| Tool | Output type | Format |
|------|-------------|--------|
| **get_drafts()** | JSON | `{ "drafts": [ { "peer_id", "message", "date", "no_webpage", "reply_to_msg_id" } ], "count" }`. "No drafts found." if empty. |
| **save_draft(chat_id, message, ...)** | Status | e.g. "Draft saved to chat {chat_id}. ..." |
| **clear_draft(chat_id)** | Status | e.g. "Draft cleared from chat {chat_id}." |

---

### 12. Folders (chat filters)

| Tool | Output type | Format |
|------|-------------|--------|
| **list_folders()** | JSON | `{ "folders": [ { "id", "title", "emoticon", "contacts", "groups", "broadcasts", "bots", "exclude_*", "*_peers_count", ... } ], "count" }`. "No folders found. ..." if none. |
| **get_folder(folder_id)** | JSON | Folder details plus resolved `included_chats` / `excluded_chats` (id, name, type, username). Or "Folder with ID ... not found. ...". |

---

### 13. Admin and moderation

| Tool | Output type | Format |
|------|-------------|--------|
| **get_recent_actions(chat_id)** | JSON | Array of admin log event objects (from Telethon `to_dict`), with dates serialized via `json_serializer`. "No recent admin actions found." if empty. |
| **promote_admin / demote_admin / ban_user / unban_user** | Status | Success or error. |

---

### 14. Other tools

| Tool | Output type | Format |
|------|-------------|--------|
| **resolve_username(username)** | Plain text | Raw Telethon `ResolveUsernameRequest` result string (peers, users, etc.). |
| **mute_chat / unmute_chat / archive_chat / unarchive_chat** | Status | e.g. "Chat {chat_id} muted." |
| **get_privacy_settings()** | (varies) | Privacy settings structure. |
| **set_privacy_settings(...)** | Status | Success or error. |
| **block_user / unblock_user** | Status | e.g. "User {id} unblocked." |
| **add_contact / delete_contact** | Status | Success or error. |
| **get_media_info(chat_id, message_id)** | (varies) | Media info for the message. |
| **search_public_chats(query)** | (varies) | Search results. |
| **search_messages(chat_id, query, limit)** | (varies) | Message list (same line format as get_messages where applicable). |
| **get_sticker_sets()** | (varies) | Sticker set list. |
| **set_bot_commands(bot_username, commands)** | Status | Success or error (bot accounts only). |

---

## Summary of output types

| Type | When used | Example |
|------|------------|--------|
| **Line-based text** | Chat lists, message lists, participants, contacts, topics, buttons | `ID: 1, Name: X\nID: 2, Name: Y` |
| **JSON** | get_me, get_drafts, list_folders, get_folder, get_message_reactions, get_bot_info, get_recent_actions, get_user_photos | `{"id": 1, "name": "..."}` |
| **Single message** | Success/status, invite link, "No ... found" | `Message sent successfully.` |
| **Error** | Any failure | `An error occurred (code: CHAT-ERR-042). Check mcp_errors.log for details.` |

All tool results are **UTF-8 text**. Dates in JSON use ISO 8601 (e.g. `2025-01-01T12:00:00+00:00`). The server uses a custom `json_serializer` for non-standard types (e.g. `datetime`, `bytes`).

---

## Removed / unavailable tools

The following are **not** available in this server (as noted in the main README):

- **File/media tools** that need local paths: `send_file`, `download_media`, `set_profile_photo`, `edit_chat_photo`, `send_voice`, `send_sticker`, `upload_file`
- **GIF tools**: `get_gif_search`, `get_saved_gifs`, `send_gif`

Calling them will result in "tool not found" or similar from the MCP layer, not from this document’s output formats.

---

*Generated from the Telegram MCP server implementation in `main.py`.*
