import json
import os
import random
import threading
from datetime import time, timedelta, timezone
from http.server import BaseHTTPRequestHandler, HTTPServer

from sqlalchemy import create_engine, text
from telegram import InlineKeyboardButton, InlineKeyboardMarkup, Update
from telegram.ext import Application, CallbackQueryHandler, CommandHandler, ContextTypes

TOKEN = os.environ["BOT_TOKEN"]
PROXY = os.getenv("TG_PROXY")

DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///wordbot.db")
if DATABASE_URL.startswith("postgresql://"):
    DATABASE_URL = DATABASE_URL.replace("postgresql://", "postgresql+psycopg://", 1)
engine = create_engine(DATABASE_URL, pool_pre_ping=True)

BEIJING = timezone(timedelta(hours=8))
PUSH_TIME = time(hour=8, minute=0, tzinfo=BEIJING)   # 每天北京时间 8:00 推送

with open("words.json", encoding="utf-8") as f:
    WORDS = json.load(f)


def init_db():
    with engine.begin() as conn:
        conn.execute(text("""
            CREATE TABLE IF NOT EXISTS subscribers (
                chat_id BIGINT PRIMARY KEY
            )
        """))


def format_word(w: dict) -> str:
    return f"📖 {w['word']}\n释义：{w['meaning']}\n例句：{w['example']}"


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    name = update.effective_user.first_name
    await update.message.reply_text(
        f"你好 {name}！我是每日一词机器人。\n"
        "/word 随机一个单词\n"
        "/quiz 做一道测验\n"
        "/subscribe 订阅每天早上 8 点的单词推送\n"
        "/unsubscribe 取消订阅"
    )


async def word(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(format_word(random.choice(WORDS)))


async def quiz(update: Update, context: ContextTypes.DEFAULT_TYPE):
    options = random.sample(range(len(WORDS)), 4)
    answer = random.choice(options)
    buttons = [
        [InlineKeyboardButton(WORDS[i]["meaning"], callback_data=f"quiz:{i}:{answer}")]
        for i in options
    ]
    await update.message.reply_text(
        f"❓ {WORDS[answer]['word']} 是什么意思？",
        reply_markup=InlineKeyboardMarkup(buttons),
    )


async def quiz_answer(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    _, picked, answer = query.data.split(":")
    picked, answer = int(picked), int(answer)
    if picked == answer:
        result = "✅ 答对了！"
    else:
        result = f"❌ 答错了，你选的是“{WORDS[picked]['meaning']}”"
    await query.edit_message_text(f"{result}\n\n{format_word(WORDS[answer])}")


async def subscribe(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat_id = update.effective_chat.id
    with engine.begin() as conn:
        exists = conn.execute(
            text("SELECT 1 FROM subscribers WHERE chat_id = :id"), {"id": chat_id}
        ).fetchone()
        if exists is None:
            conn.execute(text("INSERT INTO subscribers (chat_id) VALUES (:id)"), {"id": chat_id})
    await update.message.reply_text("订阅成功！每天早上 8 点给你发一个单词 ☀️")


async def unsubscribe(update: Update, context: ContextTypes.DEFAULT_TYPE):
    with engine.begin() as conn:
        conn.execute(
            text("DELETE FROM subscribers WHERE chat_id = :id"), {"id": update.effective_chat.id}
        )
    await update.message.reply_text("已取消订阅，想回来随时发 /subscribe")


async def send_daily(context: ContextTypes.DEFAULT_TYPE):
    """定时任务：给所有订阅者发今日单词。"""
    w = random.choice(WORDS)
    with engine.begin() as conn:
        rows = conn.execute(text("SELECT chat_id FROM subscribers")).fetchall()
    for row in rows:
        try:
            await context.bot.send_message(row.chat_id, "☀️ 今日单词\n\n" + format_word(w))
        except Exception as e:
            print(f"发给 {row.chat_id} 失败：{e}")


async def push_now(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """测试用：立刻触发一次推送。"""
    await send_daily(context)


class HealthHandler(BaseHTTPRequestHandler):
    def do_GET(self):
        self.send_response(200)
        self.end_headers()
        self.wfile.write(b"ok")

    def log_message(self, *args):
        pass   # 不打印每次访问的日志，免得刷屏


def start_health_server():
    port = int(os.getenv("PORT", "8080"))
    server = HTTPServer(("0.0.0.0", port), HealthHandler)
    threading.Thread(target=server.serve_forever, daemon=True).start()
    print(f"健康检查网页已启动，端口 {port}")


def main():
    init_db()
    start_health_server()

    builder = Application.builder().token(TOKEN)
    if PROXY:
        builder = builder.proxy(PROXY).get_updates_proxy(PROXY)
    app = builder.build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("word", word))
    app.add_handler(CommandHandler("quiz", quiz))
    app.add_handler(CommandHandler("subscribe", subscribe))
    app.add_handler(CommandHandler("unsubscribe", unsubscribe))
    app.add_handler(CommandHandler("pushnow", push_now))
    app.add_handler(CallbackQueryHandler(quiz_answer, pattern="^quiz:"))

    app.job_queue.run_daily(send_daily, time=PUSH_TIME)

    print("机器人启动了，按 Ctrl+C 停止")
    app.run_polling()


if __name__ == "__main__":
    main()