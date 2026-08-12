# PW Extractor

PW Extractor is a dashboard app for students of [Physics Wallah (PW)](https://www.pw.live/) to access, view, and download course resources such as notes, DPPs, quizzes, and announcements from their enrolled PW batches and subjects.

## Features

- **Batch content tree** — loads your purchased batches, subjects and topics in parallel.
- **Bulk downloads** — multi-select subjects and content types, download everything in parallel.
- **Content types:**
  - Notes (PDF)
  - DPP — Daily practice problems (PDF)
  - DPP Quiz with solutions (self-contained HTML, question + solution images embedded)
  - Announcements with attachments
  - Lectures (listing only)
  - Videos (MP4) — downloads lecture videos from your enrolled batches. DASH segments are fetched directly and, for DRM-protected lectures, decrypted with `mp4decrypt` (Bento4) and merged with `ffmpeg`.
- **Announcement notifications** — watch for new announcements and push to Discord, Telegram, or Email.
- **Two interfaces** — Streamlit web app and a CLI.

## Quick Start

1. Clone the repository:

   ```
   git clone https://github.com/viraj-sh/pw-extractor.git
   cd pw-extractor
   ```

2. Create and activate a Python virtual environment:

   ```
   python -m venv venv
   ```

   ```
   # On Windows:
   venv\Scripts\activate
   ```

   ```
   # On Mac/Linux:
   source venv/bin/activate
   ```

3. Install dependencies:

   ```
   pip install -r requirements.txt
   ```

4. Install the external binaries used for video downloads (videos only):

   ```
   # ffmpeg — https://ffmpeg.org/download.html
   # mp4decrypt (Bento4) — https://www.bento4.com/downloads/  (needed for DRM-protected lectures)
   ```

5. Run the app:

   ```
   streamlit run streamlit.py
   ```

   The app opens at `http://localhost:8501`.

### How to get your PW session token

1. Visit https://www.pw.live/ and log in (or use a tab where you are already logged in).
2. Open browser developer tools (F12), go to the **Network** tab, and refresh the page.
3. Filter by `token`, click the `verify-token` request, and look at the `Authorization` request header.
4. Copy the value after `Bearer ` — this is your access token.

The token can be:
- pasted in the app's login screen (saved to `data/token.txt`), or
- set as the `ACCESS_TOKEN` environment variable, or
- placed in `data/token.txt` for the CLI.

`data/` is git-ignored and never committed.

## Web App Usage

- **Login** — paste an existing token, or log in with phone + OTP.
- **Download tab** — pick a batch (sidebar), choose subjects and content types, then **Scan & preview** to see what will be downloaded, and **Download** to fetch everything in parallel with a live progress bar. Results can be exported as a ZIP. Selecting **Videos** queues each lecture video as a job (needs `ffmpeg` and `mp4decrypt` on PATH).
- **Browse tab** — drill into a batch → subject → topic and open/download notes, DPPs, attempted quizzes with solutions, announcements, and lecture info individually. The **Lectures** tab also shows a **Download MP4** button per lecture.

## CLI Usage

```
# List batches, subjects and topics
python main.py --list

# Download everything (all batches, all subjects, all types)
python main.py --workers 8 --zip

# Limit to a batch, some subjects, and specific content types
python main.py --batch "Shreshth GATE" --subjects Maths Physics --types Notes DPP Quiz

# Download announcements only
python main.py --types Announcements
```

Options: `--out DIR`, `--batch KEYWORDS`, `--subjects KEYWORDS`, `--types TYPE...`, `--workers N`, `--zip`, `--list`.

## Announcement Notifications

Fetch new announcements and push them to your channels:

```
python -m core.notify
```

Configuration is read from a `.env` file (see below) or environment variables. Known announcement IDs are tracked in `data/known_announcements.json` so the same announcement is only pushed once.

| Variable | Purpose |
| --- | --- |
| `DISCORD_WEBHOOK_URL` | Discord webhook URL for announcements |
| `TELEGRAM_BOT_TOKEN` | Telegram bot token |
| `TELEGRAM_CHAT_ID` | Telegram chat/channel ID |
| `SMTP_HOST` | SMTP server (e.g. `smtp.gmail.com`) |
| `SMTP_PORT` | SMTP port (default `587`) |
| `SMTP_USERNAME` / `SMTP_PASSWORD` | SMTP login |
| `EMAIL_FROM` | From address (defaults to `SMTP_USERNAME`) |
| `EMAIL_TO` | Comma-separated recipient addresses |
| `ACCESS_TOKEN` | PW access token (alternative to `data/token.txt`) |

Example `.env`:

```
TELEGRAM_BOT_TOKEN=123456:ABC...
TELEGRAM_CHAT_ID=-1001234567890
DISCORD_WEBHOOK_URL=https://discord.com/api/webhooks/...
EMAIL_TO=me@example.com
SMTP_HOST=smtp.gmail.com
SMTP_USERNAME=me@gmail.com
SMTP_PASSWORD=app-password
```

## Project Layout

```
core/            # API + download logic
  content.py     # batches, subjects, topics, notes, DPP, lectures, announcements, quiz
  downloader.py  # job builder, parallel downloads, ZIP export
  video.py       # DASH manifest parsing + Widevine DRM video downloads
  quiz.py        # builds self-contained quiz HTML
  utils.py       # session, retries, auth helpers
  generate_token.py  # OTP login
  announcer.py   # announcement fetching
  dashboard.py   # dashboard/performance stats
  notify.py      # announcement notification runner
notification/    # Discord / Telegram / Email senders
main.py          # CLI entry point
streamlit.py     # web app
```

## Purpose

This app is designed to help PW students manage and access their enrolled study resources — notes, DPPs, quizzes, announcements and lecture videos — more efficiently. Video downloads use your own valid session token against the batches you are enrolled in; DRM-protected streams are decrypted locally on your machine. Usage is limited to your own legitimately enrolled courses on pw.live.

## Disclaimer

This project is only for legitimate users of [pw.live](https://www.pw.live/). Unauthorized or unintended use is not supported. Piracy or commercial misuse is not tolerated.
