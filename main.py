import os
import logging
from telegram import (
    Update,
    InlineKeyboardButton,
    InlineKeyboardMarkup,
)
from telegram.ext import (
    ApplicationBuilder,
    CommandHandler,
    MessageHandler,
    CallbackQueryHandler,
    ContextTypes,
    filters,
)
import pandas as pd

BOT_TOKEN = "8594466501:AAGf8OYkw8AS8xmHoqSgI_uvamBodJiNAGw"

# Paths
ESIC_FOLDER = "data/esic"
OT_FILE = "data/ot.xlsx"
SUN_FILE = "data/sunday.xlsx"

# Logging
logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    level=logging.INFO
)
logger = logging.getLogger(__name__)

user_state = {}  # Tracks which option the user selected


# ---------------------- START / MENU ----------------------
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    keyboard = [
        [InlineKeyboardButton("📄 Get my ESIC Card", callback_data="esic")],
        [InlineKeyboardButton("⏱ Know my OT Dates", callback_data="ot")],
        [InlineKeyboardButton("🌞 Know my Sunday Work Dates", callback_data="sun")],
    ]
    await update.message.reply_text(
        "Hello! Please choose an option:",
        reply_markup=InlineKeyboardMarkup(keyboard)
    )


# ---------------------- HANDLE BUTTONS ----------------------
async def button_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    user_id = query.from_user.id

    choice = query.data
    user_state[user_id] = choice

    await query.message.reply_text("Please enter your TR Number:")


# ---------------------- HANDLE TR INPUT ----------------------
async def text_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.message.from_user.id
    tr_no = update.message.text.strip()

    if user_id not in user_state:
        await update.message.reply_text("Please type /start to use the menu.")
        return

    choice = user_state[user_id]

    # ---------------------- ESIC CARD ----------------------
    if choice == "esic":
        file_path = os.path.join(ESIC_FOLDER, f"{tr_no}.pdf")

        if os.path.exists(file_path):
            await update.message.reply_document(open(file_path, "rb"))
        else:
            await update.message.reply_text("❌ No ESIC card found for this TR Number.")

    # ---------------------- OT DATES ----------------------
    elif choice == "ot":
        if not os.path.exists(OT_FILE):
            await update.message.reply_text("OT file missing on server.")
            return

        df = pd.read_excel(OT_FILE)
        if "TR No" not in df.columns:
            await update.message.reply_text("OT Excel format incorrect.")
            return

        result = df[df["TR No"].astype(str) == tr_no]

        if result.empty:
            await update.message.reply_text("❌ No OT records found.")
        else:
            dates = "\n".join(str(x) for x in result["OT Date"].tolist())
            await update.message.reply_text(f"⏱ *Your OT Dates:*\n{dates}", parse_mode="Markdown")

    # ---------------------- SUNDAY DATES ----------------------
    elif choice == "sun":
        if not os.path.exists(SUN_FILE):
            await update.message.reply_text("Sunday file missing on server.")
            return

        df = pd.read_excel(SUN_FILE)
        if "TR No" not in df.columns:
            await update.message.reply_text("Sunday Excel format incorrect.")
            return

        result = df[df["TR No"].astype(str) == tr_no]

        if result.empty:
            await update.message.reply_text("❌ No Sunday work records found.")
        else:
            dates = "\n".join(str(x) for x in result["Sunday Date"].tolist())
            await update.message.reply_text(f"🌞 *Your Sunday Work Dates:*\n{dates}", parse_mode="Markdown")

    # Reset state
    del user_state[user_id]


# ---------------------- MAIN FUNCTION ----------------------
def main():
    app = ApplicationBuilder().token(BOT_TOKEN).build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(CallbackQueryHandler(button_handler))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, text_handler))

    print("Bot is running on Render...")
    app.run_polling()


if __name__ == "__main__":
    main()
