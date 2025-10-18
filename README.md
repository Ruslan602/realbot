# RealMadrid Auto News Bot (Uzbek translation)

**What it does**
- Collects Real Madrid news from RSS feeds (and best-effort scraping of Marca/Goal/AS)
- Translates titles and summaries into Uzbek
- Posts formatted messages to your Telegram channel
- Avoids reposting the same article via SQLite DB
- Configurable polling interval (default 15 minutes)

**Important security note**
- Do NOT commit or share your `config.env` with the real TELEGRAM_BOT_TOKEN.
- Keep the token private. Add the bot as an admin to your channel.

## Prepare & Run (VPS)
1. Copy files to your server. Install Python 3.11+
2. Create virtual env and install deps:
   ```bash
   python3 -m venv venv
   source venv/bin/activate
   pip install -r requirements.txt
   ```
3. Edit `config.env` and set `TELEGRAM_BOT_TOKEN` and optionally tweak `RSS_SOURCES` or `POLL_INTERVAL_SECONDS`.
4. Add your bot to the Telegram channel and grant admin rights (post messages).
5. Run:
   ```bash
   python bot.py
   ```

## Run with Docker
```bash
docker build -t realbot .
docker run -d --env-file=config.env realbot
```

## Notes on scraping & APIs
- This project uses simple scraping for match/results when APIs are not used. Scraping is fragile.
- For reliable match scores and fixtures, integrate a football data API (API-Football, Sofascore, etc.) — those often require an API key.

## Customization ideas
- Add filters (e.g., only transfer news)
- Add rate-limiting and backoff for failed network requests
- Use official APIs for fixtures/results for better reliability
