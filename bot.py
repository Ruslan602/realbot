import asyncio, os, logging, feedparser, aiohttp, aiosqlite
from aiogram import Bot
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from dotenv import load_dotenv
from translator import translate_to_uz
from match_fetcher import fetch_realmadrid_latest_matches, fetch_from_site
from urllib.parse import urlparse

load_dotenv('config.env')

BOT_TOKEN = os.getenv('TELEGRAM_BOT_TOKEN')
CHANNEL_ID = os.getenv('CHANNEL_ID')
RSS_SOURCES = os.getenv('RSS_SOURCES', '').split(',')
POLL_INTERVAL = int(os.getenv('POLL_INTERVAL_SECONDS', '900'))
DB_PATH = os.getenv('DB_PATH', 'realbot.db')

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger('realbot')

if not BOT_TOKEN or 'YOUR_BOT_TOKEN' in BOT_TOKEN:
    logger.warning('Bot token not set in config.env. Please add TELEGRAM_BOT_TOKEN before running.')
if not CHANNEL_ID:
    logger.error('CHANNEL_ID is not set. Set CHANNEL_ID in config.env and add bot as admin to the channel.')
    raise SystemExit(1)

bot = Bot(token=BOT_TOKEN, parse_mode='HTML')

async def init_db():
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute('''
            CREATE TABLE IF NOT EXISTS posted (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                guid TEXT UNIQUE,
                title TEXT,
                source TEXT,
                published TEXT
            )
        ''')
        await db.commit()

async def already_posted(guid: str) -> bool:
    async with aiosqlite.connect(DB_PATH) as db:
        cur = await db.execute('SELECT 1 FROM posted WHERE guid = ?', (guid,))
        row = await cur.fetchone()
        await cur.close()
        return row is not None

async def mark_posted(guid: str, title: str, source: str, published: str = ''):
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute('INSERT OR IGNORE INTO posted (guid, title, source, published) VALUES (?, ?, ?, ?)', (guid, title, source, published))
        await db.commit()

async def fetch_rss(url: str):
    # use aiohttp to fetch feed then feedparser to parse bytes
    try:
        async with aiohttp.ClientSession() as session:
            async with session.get(url, timeout=20) as resp:
                content = await resp.read()
                return feedparser.parse(content)
    except Exception as e:
        logger.exception('RSS fetch failed %s: %s', url, e)
        return None

def build_message(title: str, summary: str, link: str, source_name: str) -> str:
    title_uz = translate_to_uz(title)
    summary_uz = translate_to_uz(summary)
    short_summary = (summary_uz[:800] + '...') if len(summary_uz) > 800 else summary_uz
    msg = f"⚽️ <b>{title_uz}</b>\n\n{short_summary}\n\n🔗 <a href='{link}'>Manba: {source_name}</a>\n\n#RealMadrid #HalaMadrid"
    return msg

async def post_to_channel(title: str, summary: str, link: str, source_name: str, guid: str):
    if await already_posted(guid):
        return False
    text = build_message(title, summary, link, source_name)
    kb = InlineKeyboardMarkup(inline_keyboard=[[InlineKeyboardButton(text='Manbaga o‘tish', url=link)]])
    try:
        await bot.send_message(CHANNEL_ID, text, reply_markup=kb, disable_web_page_preview=False)
        await mark_posted(guid, title, source_name)
        logger.info('Posted: %s', title)
        await asyncio.sleep(1.0)
        return True
    except Exception as e:
        logger.exception('Failed to send message: %s', e)
        return False

async def process_rss_source(url: str):
    parsed = await fetch_rss(url)
    if not parsed or not parsed.entries:
        return
    # iterate oldest first
    for entry in sorted(parsed.entries, key=lambda e: e.get('published_parsed') or 0):
        guid = entry.get('id') or entry.get('link') or entry.get('title')
        title = entry.get('title', '')[:400]
        summary = entry.get('summary', '') or entry.get('description', '')
        link = entry.get('link', '')
        source_name = urlparse(url).netloc
        await post_to_channel(title, summary, link, source_name, guid)

async def process_scrape_sources():
    # pull some items from realmadrid news page
    try:
        rm_items = fetch_realmadrid_latest_matches()
        for it in rm_items:
            guid = it.get('link') or it.get('title')
            await post_to_channel(it.get('title',''), it.get('summary',''), it.get('link',''), 'realmadrid.com', guid)
    except Exception as e:
        logger.exception('Error processing realmadrid scrape: %s', e)
    # generic scraping for Marca/Goal/AS - best effort
    from os import getenv
    rss_sources = os.getenv('RSS_SOURCES','').split(',')
    for src in rss_sources:
        src = src.strip()
        if not src:
            continue
        if 'realmadrid.com' in src:
            continue
        try:
            items = fetch_from_site(src)
            for it in items:
                guid = it.get('link') or it.get('title')
                await post_to_channel(it.get('title',''), it.get('summary',''), it.get('link',''), src, guid)
        except Exception as e:
            logger.exception('Error scraping %s: %s', src, e)

async def main_loop():
    await init_db()
    while True:
        logger.info('Checking RSS sources...')
        # process RSS sources (official feeds)
        rss_sources = os.getenv('RSS_SOURCES','').split(',')
        for src in rss_sources:
            src = src.strip()
            if not src:
                continue
            await process_rss_source(src)
        # also do scrape-based results & match pulls
        logger.info('Checking scraped sources (site scraping)...')
        await asyncio.get_event_loop().run_in_executor(None, process_scrape_sources)
        logger.info('Sleeping for %s seconds', POLL_INTERVAL)
        await asyncio.sleep(POLL_INTERVAL)

if __name__ == '__main__':
    try:
        asyncio.run(main_loop())
    except KeyboardInterrupt:
        logger.info('Stopped by user')

async def send_live_updates():
    """Jonli o‘yin holatini chiqarish va gol aniqlansa “GOAL!” deb yozish"""
    live, goal_detected = await get_live_match()

    if live:
        text = (
            f"🏆 {live['competition']}\n"
            f"⚽️ {live['home']} 🆚 {live['away']}\n"
            f"📊 Hisob: {live['score']}\n\n"
            f"#RealMadrid #Live #HalaMadrid"
        )
        await bot.send_message(CHANNEL_ID, text)

        # Agar gol bo‘lgan bo‘lsa, “GOAL!” postini yuborish
        if goal_detected:
            await bot.send_message(
                CHANNEL_ID,
                "⚽️ <b>GOAL!</b> Real Madrid gol urdi! 🔥🔥 #RealMadrid #GOAL"
            )
