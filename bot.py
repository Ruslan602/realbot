import asyncio
import feedparser
import html
import os
from aiogram import Bot
from aiogram.types import ParseMode
from deep_translator import GoogleTranslator
from dotenv import load_dotenv

# 🔧 Config faylni o‘qish
load_dotenv("config.env")

BOT_TOKEN = os.getenv("8323122825:AAGEiIlsvikLyLY8XsH_oVz54bEi5xxklp0")
CHANNEL_ID = os.getenv("-1001798081251")
UPDATE_INTERVAL = int(os.getenv("UPDATE_INTERVAL", 900))  # 15 daqiqa = 900 soniya

# 🌐 Yangilik manbalari
FEEDS = [
    "https://www.realmadrid.com/en/rss",  # Real Madrid rasmiy
    "https://www.marca.com/en/rss/futbol/real-madrid.xml",
    "https://www.goal.com/feeds/en/news/9/rss",  # Goal.com
    "https://as.com/rss/futbol/real_madrid.xml"
]

bot = Bot(token=BOT_TOKEN, parse_mode=ParseMode.HTML)
translator = GoogleTranslator(source="auto", target="uz")

# 🧠 Yangiliklarni qayta ishlash
def pick_emoji(title: str) -> str:
    """Yangilik turiga qarab emoji tanlaydi"""
    t = title.lower()
    if "goal" in t or "gol" in t:
        return "⚽️"
    elif "injury" in t or "jarohat" in t:
        return "🚑"
    elif "transfer" in t or "sotib" in t or "sotildi" in t:
        return "💰"
    elif "match" in t or "game" in t or "o‘yin" in t:
        return "🏟"
    else:
        return "📰"


async def format_post(news):
    """Chiroyli formatda post tayyorlash"""
    title = html.escape(news.get("title", "Real Madrid yangilik"))
    summary = html.escape(news.get("summary", ""))

    # tarjima qilish
    try:
        title = translator.translate(title)
        summary = translator.translate(summary)
    except Exception:
        pass

    emoji = pick_emoji(title)

    formatted = (
        f"{emoji} <b>{title}</b>\n\n"
        f"{summary}\n\n"
        f"#RealMadrid #HalaMadrid #Yangilik #Futbol"
    )

    return formatted


async def send_news_to_channel(bot, channel_id, news):
    message_text = await format_post(news)

    if news.get("image"):
        try:
            await bot.send_photo(chat_id=channel_id, photo=news["image"], caption=message_text)
        except Exception:
            await bot.send_message(chat_id=channel_id, text=message_text)
    else:
        await bot.send_message(chat_id=channel_id, text=message_text)


# 📰 RSS manbadan yangiliklarni olish
async def fetch_news():
    news_list = []

    for url in FEEDS:
        feed = feedparser.parse(url)
        for entry in feed.entries[:3]:  # har manbadan faqat so‘nggi 3ta
            news_item = {
                "title": entry.title,
                "summary": entry.get("summary", ""),
                "link": entry.link,
                "image": None,
            }

            # Rasmni topish (agar mavjud bo‘lsa)
            if "media_content" in entry:
                media = entry.media_content
                if isinstance(media, list) and len(media) > 0:
                    news_item["image"] = media[0].get("url")
            elif "links" in entry:
                for l in entry.links:
                    if "image" in l.type:
                        news_item["image"] = l.href
                        break

            news_list.append(news_item)

    return news_list


# 🕒 Asosiy ishchi sikl
async def main():
    print("✅ Real Madrid yangiliklar boti ishga tushdi!")

    sent_titles = set()

    while True:
        news_list = await fetch_news()

        for news in news_list:
            title = news["title"]
            if title not in sent_titles:
                await send_news_to_channel(bot, CHANNEL_ID, news)
                sent_titles.add(title)

        await asyncio.sleep(UPDATE_INTERVAL)  # keyingi tekshiruvgacha kutish


if __name__ == "__main__":
    asyncio.run(main())

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
