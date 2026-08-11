# SS permanent chat/data preservation contract

## Non-negotiable rule

**SS must never delete, clean, prune, rotate, truncate, overwrite, or migrate away existing chats or generated user content unless the user explicitly requests that specific deletion.**

This applies to:
- SS Second Brain updates
- Provider Console updates
- version changes
- migrations
- refactors
- reinstallations
- model/provider changes
- database/schema changes

## Where chats are stored

The application stores persistent chat snapshots outside the Git repository:

- Windows default: `%LOCALAPPDATA%\\SS\\chats`
- Other systems: `$XDG_DATA_HOME/SS/chats` or `~/.local/share/SS/chats`

Each chat is stored as an individual JSON file containing its messages, provider, model and timestamps.

## Cloud mirror

Set the environment variable `SS_CHAT_CLOUD_ROOT` to a **locally synchronized cloud folder**. Examples include a folder synchronized by OneDrive, Google Drive for desktop, Dropbox, or another user-controlled sync service.

SS writes the same chat snapshot to both locations. The cloud mirror is therefore independent of the Git repository and can survive code replacement.

Example Windows launcher configuration:

```bat
set SS_CHAT_CLOUD_ROOT=C:\Users\YOURNAME\Google Drive\SS\chats
```

Use the actual synchronized folder on the machine; SS does not assume a provider-specific cloud path.

## Updates

An SS update replaces application code only. It must not remove the external `%LOCALAPPDATA%\\SS\\chats` directory.

Before any future migration that changes the data format, the migration must create a backup copy first and be reversible. No destructive migration is permitted.

## Existing browser-only chats

Older versions of the console kept some conversation history in browser `localStorage`. Those conversations cannot be recovered by the server unless the browser still contains them and the user exports/migrates them. New v0.8.2 conversations are server-persisted when a chat ID is supplied.

## GitHub is code storage, not the chat archive

The SS Git repository stores source/configuration/documentation. It is **not** used as the primary chat database. This prevents code updates from accidentally modifying chat history and avoids placing potentially sensitive conversation content into Git history.
