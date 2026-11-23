# Telegram Calendar Assistant – Demo (n8n)

> **Personal project / demo, not a client project.**
> Sanitized copy of a privately operated n8n workflow. All test data is synthetic. The workflow in this repository is **inactive** and was **not executed** as part of the demo.
> Deutsche Fassung: [README.md](README.md)

## What the workflow does

You write to the Telegram bot in plain language (German, Russian or English). A language model (OpenAI, `gpt-5.4-mini`) recognises the intent; the rest runs rule-based in n8n.

0. **Check the sender:** `IF — Allowed Sender?` lets through only messages from the configured Telegram user ID; all others are silently ignored (E1).
1. **Recognise the intent:** `AI — Detect Intent` returns structured data: intent (`create_calendar_event`, `read_calendar`, `update_calendar_event`, `general_chat`), title, times, language of the message.
2. **Create an event:** A code node computes start and end (end as given by the model, otherwise start + 60 minutes); without a recognisable start nothing is created. Google Calendar creates the event; reply in the chat, e.g. "✓ Added: Besprechung Muster AG, 24.11.2026 10:00".
3. **Show events:** Google Calendar reads the period. Without events the bot replies "No events in the requested period."; otherwise the events are collected and summarised by the model in the language of the message.
4. **Change an event:** The events of the next 30 days are read. A code node finds the event by its title (substring, case-insensitive) and computes the new time from the event it found: the model only supplies what the user said (new date, new time, new duration); anything missing is taken from the event itself. Only with **exactly one** match and a recognised new time is the event changed through the Google Calendar API ("✓ Updated: …"). Otherwise the bot replies and changes nothing: not found, several matches, new time not recognised, all-day event.
5. **General chat:** Everything else is answered by an AI agent with conversation memory (no calendar access).

**No approval step.** Unlike the [inbox triage demo](https://github.com/OlegRegina/n8n-ai-inbox-triage-demo), there is no confirmation before creating or changing an event: the user's request is the approval, and the assistant never plans anything on its own. See E1 for the consequence.

Flow and node overview: [docs/architecture.md](docs/architecture.md) (German).

## Contents

| Path | Content |
|---|---|
| [`workflows/telegram-calendar-assistant.json`](workflows/telegram-calendar-assistant.json) | Workflow "Telegram Calendar Assistant (Demo)" (27 nodes, 28 connections) |
| [`docs/setup.md`](docs/setup.md) | Setup: credentials, import, test (German) |
| [`docs/architecture.md`](docs/architecture.md) | Flow and mapping of all nodes (German) |
| [`docs/test-plan.md`](docs/test-plan.md) | Test cases with status (German) |
| [`docs/datenschutz.md`](docs/datenschutz.md) | Data flows and privacy notes (German) |
| [`test-data/`](test-data/) | Synthetic test messages |
| [`tests/logic-harness/`](tests/logic-harness/) | Repeatable logic test (33 scenarios, isolated n8n, Docker) |
| [`evidence/`](evidence/) | Validation report, import test, logic test, log of the live tests |
| [`scripts/`](scripts/) | Sanitizing (`sanitize.py`) and validation (`validate.py`) of the export |
| [`SECURITY.md`](SECURITY.md) | What was removed, risks, reporting problems (German) |

## Import in brief

1. Import `workflows/telegram-calendar-assistant.json` into n8n ("Import from File").
2. Connect credentials: Telegram, Google Calendar (OAuth2), OpenAI.
3. **Enter your own Telegram user ID** in `IF — Allowed Sender?` (placeholder `REPLACE_WITH_TELEGRAM_USER_ID`); without it the bot answers nobody.
4. Check the calendar: the value `primary` is the main calendar of the connected account.
5. For tests, use a **separate test calendar** and a **separate bot**, and read E2.

Details: [docs/setup.md](docs/setup.md). The workflow has exactly one placeholder (the user ID).

## Status & limits

### State of verification (23 Nov 2026)

| Area | Status | Evidence |
|---|---|---|
| Sanitizing of the export: allowed keys, pattern scan, structure, only approved changes | PASS according to the automatic report; date, number of files checked and result are in the report header. Valid only for the file state at that time | [`evidence/validation-report.txt`](evidence/validation-report.txt), [`evidence/validation-notes.md`](evidence/validation-notes.md) |
| Local import into n8n 2.43.7 (isolated, no network): structure, node parameters and connections unchanged | PASS | [`evidence/import-test.md`](evidence/import-test.md) |
| Logic test with sample data (33 scenarios: sender filter, create, show, change; real execution of the nodes in isolated n8n 2.43.7) | PASS, 33 of 33. Shows the logic of filter, time calculation, search and reply texts, and that start and end of the Google requests are valid (end after start, time zone); **not** Google, Telegram or the model | [`evidence/logic-test.md`](evidence/logic-test.md), [`tests/logic-harness/`](tests/logic-harness/) |
| Live tests in the author's private system (23 Nov 2026) | DOCUMENTED, partial: create without a duration, showing events with and without results and "several matches" passed with this version; change and "not found" passed with the previous version; other cases open. No public evidence | [`evidence/live-test.md`](evidence/live-test.md), [`docs/test-plan.md`](docs/test-plan.md) |
| Test cases M01–M15 in this demo (with your own setup) | NOT TESTED | [`docs/test-plan.md`](docs/test-plan.md) |
| Function of the Telegram, Google Calendar and OpenAI integrations from this repository | NOT TESTED | – |

> **Local import ≠ functional test of the integrations.** The logic test replaces calendar, model and Telegram with fixed sample data.

### Known limits E1–E8

Compared with the original private workflow, these parts were changed: the sender filter (new), creating (E4), showing without events (E6), the "change event" branch (E5) and retries (E7); the reasons are in [`evidence/live-test.md`](evidence/live-test.md). The other limits remain.

**E1 – sender filter by Telegram user ID only.** The Telegram trigger itself accepts messages from **anyone** who finds the bot. `IF — Allowed Sender?` lets only the configured user ID through and silently ignores all others; as long as the placeholder is not replaced, the bot answers nobody. The check relies on the sender ID that Telegram puts in the message. In the logic test the filter rejects foreign and missing senders (F2, F3); in the private system the bot worked for the author's own account after the filter was introduced; rejection of a foreign account was not verified live (M15). Whoever may enter the user ID can read, create and change events.

**E2 – no approval step.** Creating and changing run without confirmation. If the model misunderstands (wrong day, wrong title), it takes effect in the calendar immediately; the chat reply names title and time so that it gets noticed.

**E3 – free chat branch.** The "general_chat" branch is an AI agent **without a system prompt** (only the message and the per-chat conversation memory). It has no tools and no calendar access, but answers arbitrary questions at the expense of the OpenAI account.

**E4 – creating: assumptions.** `Prepare — Event Times` takes the end from the model; if it is missing, empty or not after the start, start + 60 minutes applies; without a recognisable start nothing is created. Title and date are still determined by the model. There is no conflict check against existing events and no protection against duplicate events (the same message twice creates two events). A previous version passed an empty end to Google and failed with HTTP 400 (confirmed live, 23 Nov 2026, 16:03); with this version the case passed (16:12).

**E5 – changing: scope.** Only the next 30 days from today are searched, by a substring of the title. With several matches the bot changes nothing and asks; only if the model supplies the previous start time is the match narrowed down by it. Only start and end are changed, not the title; relative statements ("one hour later") are not computed ("new time not recognised"); all-day events are not moved. Previous versions failed with HTTP 400 when moving an event; the presumed cause was that the model determined date and end itself (not conclusively confirmed). This version computes both from the event it found.

**E6 – showing: data volume.** For the summary, the **complete record of every event** is sent to OpenAI, including attendees, description, location and links, not only title and time (see [privacy](docs/datenschutz.md)). A period without events no longer stays without a reply ("No events in the requested period."); the previous version stayed silent (confirmed live, 16:05), this one replies (16:12).

**E7 – errors without a reply.** Reading (showing, searching) and changing are retried up to three times at 2-second intervals; creating is not, because a retry could create duplicate events. If an error persists there is no reply in the chat. This is deliberate: there is no error message to the user of its own, because the reference to the private error workflow was removed and an error output would suppress its alert. You can connect your own error workflow in the workflow settings.

**E8 – fixed settings.** The time zone `Europe/Zurich` is hard-coded in the prompts and in the change request. Reply texts exist in German, Russian and English (other languages: English). The output "Calender" of the node `Route — User Intent` has a typo and a leading `=`; it stays unchanged because connections reference nodes and outputs by name.

### Further limits

- Intent recognition is probabilistic; misclassifications are possible.
- With several matches of the same title, the reply lists the events in the order Google returns them (not necessarily by time).
- The conversation memory of the chat branch is a simple window memory per chat; it is not deleted.
- The workflow writes no logs of its own; n8n stores execution data according to the instance settings.

### Not verified

- Execution and activation of the workflow from this repository.
- Opening in the editor, connecting credentials.
- Registration of the Telegram webhook and reachability of the n8n instance (`WEBHOOK_URL`).
- Model behaviour under deliberate prompt injection (e.g. instructions in an event title) and with languages other than German, Russian, English.
- n8n versions other than 2.43.7 and the platform `linux/amd64`.

## Privacy

The workflow processes messages and calendar data and sends parts of them to providers outside Switzerland (OpenAI, Google, Telegram). Overview of the data flows and notes: [docs/datenschutz.md](docs/datenschutz.md). No legal advice, no compliance claim.

## Security

What was removed from the export, risks from untrusted content and how to report problems: [SECURITY.md](SECURITY.md).

## License

MIT – see [LICENSE](LICENSE). Own development, created with the support of AI assistants.
