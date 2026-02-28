import os
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ApplicationBuilder, CommandHandler, MessageHandler, ConversationHandler, ContextTypes, CallbackQueryHandler, filters

TOKEN = os.getenv("8653328794:AAHS3WVbjA8_eP7qq7Qdrop3RsdNKITc9PQ")
PASSWORD = "1234"
ADMIN_ID = 891530001

ASK_PASSWORD, LENGTH, WIDTH, HEIGHT = range(4)
authorized_users = set()

ratios = ["2:1","3:1","4:1","1:1","100:60","100:50","100:40","10:1","10:6","10:4"]
extra_options = ["0%","5%","10%"]

def final_buttons():
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("📸 Отправить фото", callback_data="photo")],
        [InlineKeyboardButton("🔄 Новый расчет", callback_data="restart")]
    ])

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data.clear()
    if update.effective_user.id in authorized_users:
        await update.message.reply_text("Введите длину в см:")
        return LENGTH
    await update.message.reply_text(
        "✨ Добро пожаловать в профессиональный калькулятор эпоксидной смолы RUKOSA.\n\n"
        "🍀 Этот инструмент поможет точно рассчитать количество смолы и отвердителя для вашего изделия.\n\n"
        "🔐 Введите пароль для доступа."
    )
    return ASK_PASSWORD

async def check_password(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.message.text == PASSWORD:
        authorized_users.add(update.effective_user.id)
        await update.message.reply_text("🔓 Доступ разрешен.\nВведите длину в см:")
        return LENGTH
    await update.message.reply_text("Неверный пароль.")
    return ASK_PASSWORD

async def get_length(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try:
        context.user_data["length"] = float(update.message.text)
        await update.message.reply_text("Введите ширину в см:")
        return WIDTH
    except:
        await update.message.reply_text("Введите число.")
        return LENGTH

async def get_width(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try:
        context.user_data["width"] = float(update.message.text)
        await update.message.reply_text("Введите толщину слоя в мм:")
        return HEIGHT
    except:
        await update.message.reply_text("Введите число.")
        return WIDTH

async def get_height(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try:
        context.user_data["height"] = float(update.message.text)
        keyboard = [[InlineKeyboardButton(r, callback_data=f"ratio:{r}")] for r in ratios]
        await update.message.reply_text("Выберите пропорцию:", reply_markup=InlineKeyboardMarkup(keyboard))
        return ConversationHandler.END
    except:
        await update.message.reply_text("Введите число.")
        return HEIGHT

async def handle_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    data = query.data

    if data.startswith("ratio:"):
        ratio = data.replace("ratio:", "")
        context.user_data["ratio"] = ratio
        keyboard = [[InlineKeyboardButton(f"+{e}", callback_data=f"extra:{e}")] for e in extra_options]
        await query.message.reply_text(f"Пропорция выбрана: {ratio}\nВыберите запас:", reply_markup=InlineKeyboardMarkup(keyboard))

    elif data.startswith("extra:"):
        extra = data.replace("extra:", "")
        ratio = context.user_data["ratio"]
        length = context.user_data["length"]
        width = context.user_data["width"]
        height_mm = context.user_data["height"]

        height_cm = height_mm / 10
        volume = (length * width * height_cm) / 1000

        if extra == "5%":
            volume *= 1.05
        elif extra == "10%":
            volume *= 1.10

        part_a, part_b = map(float, ratio.split(":"))
        total = part_a + part_b

        resin = round(volume * part_a / total, 3)
        hardener = round(volume * part_b / total, 3)
        volume = round(volume, 3)

        await query.message.reply_text(
            f"📐 Размер: {length} × {width} × {height_mm} мм\n\n"
            f"📦 Общий объем: {volume} л\n"
f"⚗ Пропорция: {ratio}\n"
            f"➕ Запас: {extra}\n\n"
            f"🧴 Смола: {resin} л\n"
            f"🧪 Отвердитель: {hardener} л\n\n"
            "✨ Расчет завершен.\n\n"
            "С заботой о вашем творчестве,\nRUKOSA",
            reply_markup=final_buttons()
        )

    elif data == "restart":
        await query.message.reply_text("/start")

    elif data == "photo":
        await query.message.reply_text("Отправьте фото готовой работы.")

async def handle_photo(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    await context.bot.forward_message(chat_id=ADMIN_ID, from_chat_id=update.message.chat_id, message_id=update.message.message_id)
    await context.bot.send_message(chat_id=ADMIN_ID, text=f"Новая работа\nИмя: {user.first_name}\nUsername: @{user.username}\nID: {user.id}")
    await update.message.reply_text("Фото получено. Спасибо!", reply_markup=final_buttons())

conv = ConversationHandler(
    entry_points=[CommandHandler("start", start)],
    states={
        ASK_PASSWORD: [MessageHandler(filters.TEXT & ~filters.COMMAND, check_password)],
        LENGTH: [MessageHandler(filters.TEXT & ~filters.COMMAND, get_length)],
        WIDTH: [MessageHandler(filters.TEXT & ~filters.COMMAND, get_width)],
        HEIGHT: [MessageHandler(filters.TEXT & ~filters.COMMAND, get_height)],
    },
    fallbacks=[],
)

app = ApplicationBuilder().token(TOKEN).build()
app.add_handler(conv)
app.add_handler(CallbackQueryHandler(handle_callback))
app.add_handler(MessageHandler(filters.PHOTO, handle_photo))

app.run_polling()
