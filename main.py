import datetime
import requests
import asyncio
from telegram import Update
from telegram.ext import (
    ApplicationBuilder,
    CommandHandler,
    ContextTypes,
)

# === CẤU HÌNH ===
TOKEN = "7591249085:AAEobNqhBvkC-Qq9Lr5_w209tCpOwVziJd8"
API_URL = "https://sunwin-taixiu.onrender.com/taixiu"
ADMIN_ID = 7598401539  # Thay bằng Telegram ID của admin

# === DỮ LIỆU BỘ NHỚ ===
user_keys = {
    7598401539: datetime.datetime(2025, 9, 15)
}         # {user_id: datetime}
user_states = {}       # {user_id: bool}
key_store = {}         # {key: datetime}
used_keys = set()
last_id = None


def is_key_valid(user_id):
    now = datetime.datetime.now()
    if user_id in user_keys:
        return now <= user_keys[user_id]
    return False


# === LỆNH BẮT ĐẦU ===
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    msg = (
        "📋 Danh sách lệnh:\n"
        "/key <key>\n"
        "/checkkey\n"
        "/chaybot\n"
        "/tatbot\n"
        "/stop\n"
        "/taokey <key> đến <dd-mm-yyyy> (admin)\n"
        "/help"
    )
    await update.message.reply_text(msg)


# === LỆNH NHẬP KEY ===
async def key(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    if not context.args:
        return await update.message.reply_text("❌ Vui lòng nhập key. Ví dụ: /key abc123")
    input_key = context.args[0]

    if input_key in used_keys:
        return await update.message.reply_text("❌ Key đã được sử dụng!")

    if input_key in key_store:
        expire = key_store[input_key]
        user_keys[user_id] = expire
        used_keys.add(input_key)
        await update.message.reply_text(f"✅ Key hợp lệ! Hạn dùng đến: {expire.strftime('%d-%m-%Y')}")
    else:
        await update.message.reply_text("❌ Key không hợp lệ!")


# === LỆNH TẠO KEY (Admin) ===
async def taokey(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id != ADMIN_ID:
        return await update.message.reply_text("⛔ Bạn không có quyền sử dụng lệnh này.")

    try:
        parts = " ".join(context.args).split("đến")
        key = parts[0].strip()
        date_str = parts[1].strip()
        expire_date = datetime.datetime.strptime(date_str, "%d-%m-%Y")
        key_store[key] = expire_date
        used_keys.discard(key)
        await update.message.reply_text(f"✅ Đã tạo key: {key}, hạn dùng đến {date_str}")
    except:
        await update.message.reply_text("❌ Sai cú pháp!\n/taokey <key> đến <dd-mm-yyyy>")


# === LỆNH KIỂM TRA KEY ===
async def checkkey(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    if is_key_valid(user_id):
        expire = user_keys[user_id].strftime("%d-%m-%Y")
        await update.message.reply_text(f"✅ Key còn hạn đến: {expire}")
    else:
        await update.message.reply_text("❌ Bạn chưa nhập key hoặc key đã hết hạn!")


# === LỆNH CHẠY BOT ===
async def chaybot(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    if not is_key_valid(user_id):
        return await update.message.reply_text("🔒 Key của bạn không hợp lệ hoặc đã hết hạn.")
    user_states[user_id] = True
    await update.message.reply_text("🤖 Bot sẽ tự động gửi khi có phiên mới.")


# === LỆNH TẮT BOT ===
async def tatbot(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_states[update.effective_user.id] = False
    await update.message.reply_text("🛑 Đã tắt bot tự động.")


# === LỆNH STOP ===
async def stop(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("👋 Hẹn gặp lại!")


# === HÀM GỬI THÔNG TIN PHIÊN MỚI ===
async def notify_users(app):
    global last_id
    while True:
        try:
            res = requests.get(API_URL, timeout=5)
            data = res.json()

            id_phien = data.get("id_phien")
            if id_phien != last_id:
                last_id = id_phien
                ket_qua = data.get("ket_qua")
                pattern = data.get("pattern")
                du_doan = data.get("du_doan")

                msg = f"""🎮 PHIÊN MỚI ĐÃ BẮT ĐẦU!
🆔 PHIÊN HIỆN TẠI: {id_phien}
🎲 KẾT QUẢ: {ket_qua}

📊 CẦU HIỆN TẠI: {pattern}
🆔 PHIÊN TIẾP THEO: {id_phien + 1}

🤖 DỰ ĐOÁN: {du_doan}
📖 LÝ DO: (AI)"""

                for user_id, running in user_states.items():
                    if running and is_key_valid(user_id):
                        await app.bot.send_message(chat_id=user_id, text=msg)

        except Exception as e:
            print("❌ Lỗi khi gọi API:", e)

        await asyncio.sleep(3)  # Kiểm tra mỗi 3 giây


# === MAIN ===
async def main():
    app = ApplicationBuilder().token(TOKEN).build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("key", key))
    app.add_handler(CommandHandler("checkkey", checkkey))
    app.add_handler(CommandHandler("chaybot", chaybot))
    app.add_handler(CommandHandler("tatbot", tatbot))
    app.add_handler(CommandHandler("stop", stop))
    app.add_handler(CommandHandler("taokey", taokey))

    asyncio.create_task(notify_users(app))

    print("🤖 Bot đang chạy...")
    await app.run_polling()

import asyncio

if __name__ == "__main__":
    import nest_asyncio
    nest_asyncio.apply()  # Cho phép nested event loop (nếu chưa cài, pip install nest_asyncio)

    try:
        asyncio.run(main())
    except RuntimeError as e:
        if "already running" in str(e):
            loop = asyncio.get_event_loop()
            loop.create_task(main())
            loop.run_forever()
        else:
            raise
