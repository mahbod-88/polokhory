import logging
import re
from telegram import Update, ReplyKeyboardMarkup
from telegram.ext import (
    Application,
    CommandHandler,
    MessageHandler,
    filters,
    CallbackContext,
    ConversationHandler
)

# تنظیمات لاگ‌گیری
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)

# وضعیت‌های مکالمه
SELECTING, GET_PHONE = range(2)

# تنظیمات ربات
TOKEN = "8024922621:AAGpURQA6TE6PMngEg0DbpWpJYKUgn2d8GQ"  # از @BotFather دریافت کنید
ADMIN_CHAT_ID = 7188976639  # آی‌دی عددی ادمین

# دیکشنری ذخیره سفارشات
orders = {}

# منوی غذاها
menu = [
    ["کباب", "چلو مرغ"],
    ["لازانیا", "ساندویچ"],
    ["سالاد", "نوشابه"],
    ["/done", "/cancel"]
]
reply_markup = ReplyKeyboardMarkup(menu, resize_keyboard=True)

async def start(update: Update, context: CallbackContext) -> int:
    """شروع ربات"""
    await update.message.reply_text(
        "به ربات سفارش غذا خوش آمدید!\n"
        "لطفاً از منوی زیر غذاهای مورد نظر را انتخاب کنید:",
        reply_markup=reply_markup
    )
    return SELECTING

async def help_command(update: Update, context: CallbackContext) -> None:
    """نمایش راهنما"""
    await update.message.reply_text(
        "راهنمای ربات:\n"
        "- از منو غذا انتخاب کنید\n"
        "- برای تکمیل سفارش /done را بزنید\n"
        "- برای لغو سفارش /cancel را انتخاب کنید"
    )

async def select_food(update: Update, context: CallbackContext) -> int:
    """ثبت انتخاب غذا"""
    user_id = update.message.from_user.id
    food = update.message.text
    
    if food in ["کباب", "چلو مرغ", "لازانیا", "ساندویچ", "سالاد", "نوشابه"]:
        if user_id not in orders:
            orders[user_id] = {}
        
        orders[user_id][food] = orders[user_id].get(food, 0) + 1
        await update.message.reply_text(
            f"✅ {food} به سبد خرید اضافه شد (تعداد: {orders[user_id][food]})\n"
            "برای افزودن غذای دیگر از منو انتخاب کنید یا /done را بزنید"
        )
    else:
        await update.message.reply_text("لطفاً از گزینه‌های منو انتخاب کنید.")
    
    return SELECTING

async def done(update: Update, context: CallbackContext) -> int:
    """تکمیل سفارش و درخواست شماره تماس"""
    user_id = update.message.from_user.id
    
    if user_id in orders and orders[user_id]:
        order_summary = "\n".join(
            [f"• {food}: {count} عدد" for food, count in orders[user_id].items()]
        )
        await update.message.reply_text(
            f"📝 سفارش شما:\n{order_summary}\n\n"
            "لطفاً شماره تماس خود را وارد کنید:",
            reply_markup=ReplyKeyboardMarkup([["/cancel"]], resize_keyboard=True)
        )
        return GET_PHONE
    else:
        await update.message.reply_text(
            "سبد خرید شما خالی است! لطفاً از منو انتخاب کنید.",
            reply_markup=reply_markup
        )
        return SELECTING

async def get_phone(update: Update, context: CallbackContext) -> int:
    """دریافت و ثبت شماره تماس"""
    user_id = update.message.from_user.id
    phone = update.message.text.strip()
    
    if re.match(r'^(\+98|0)?9\d{9}$', phone):
        phone = re.sub(r'^\+98', '0', phone)
        phone = re.sub(r'^0098', '0', phone)
        
        order_summary = "\n".join(
            [f"• {food}: {count} عدد" for food, count in orders[user_id].items()]
        )
        
        try:
            # ارسال سفارش به ادمین
            await context.bot.send_message(
                chat_id=ADMIN_CHAT_ID,
                text=f"📦 سفارش جدید:\n{order_summary}\n\n"
                     f"👤 کاربر: {update.message.from_user.full_name}\n"
                     f"📞 تلفن: {phone}\n"
                     f"🆔 آی‌دی: {user_id}"
            )
            
            await update.message.reply_text(
                "✅ سفارش شما با موفقیت ثبت شد!\n"
                "به زودی با شما تماس گرفته خواهد شد.",
                reply_markup=reply_markup
            )
            
            del orders[user_id]
            return SELECTING
        except Exception as e:
            logging.error(f"خطا در ارسال پیام به ادمین: {e}")
            await update.message.reply_text(
                "⚠️ مشکلی در ثبت سفارش پیش آمد. لطفاً دوباره تلاش کنید.",
                reply_markup=reply_markup
            )
            return SELECTING
    else:
        await update.message.reply_text(
            "⚠️ شماره تلفن نامعتبر!\n"
            "لطفاً شماره خود را به صورت صحیح وارد کنید:\n"
            "مثال: 09123456789 یا +989123456789",
            reply_markup=ReplyKeyboardMarkup([["/cancel"]], resize_keyboard=True)
        )
        return GET_PHONE

async def cancel(update: Update, context: CallbackContext) -> int:
    """لغو سفارش"""
    user_id = update.message.from_user.id
    
    if user_id in orders:
        del orders[user_id]
    
    await update.message.reply_text(
        "❌ سفارش شما لغو شد.\n"
        "هر زمان که خواستید می‌توانید دوباره سفارش دهید.",
        reply_markup=reply_markup
    )
    return SELECTING

async def unknown(update: Update, context: CallbackContext) -> int:
    """پاسخ به دستورات ناشناخته"""
    await update.message.reply_text(
        "⚠️ دستور نامعتبر!\n"
        "لطفاً از منو یا دستورات معتبر استفاده کنید.",
        reply_markup=reply_markup
    )
    return SELECTING

def main() -> None:
    """اجرای اصلی ربات"""
    application = Application.builder().token(TOKEN).build()
    
    # تنظیم هندلرهای مکالمه
    conv_handler = ConversationHandler(
        entry_points=[CommandHandler('start', start)],
        states={
            SELECTING: [
                MessageHandler(filters.Regex("^(کباب|چلو مرغ|لازانیا|ساندویچ|سالاد|نوشابه)$"), select_food),
                CommandHandler('done', done),
                CommandHandler('help', help_command),
                CommandHandler('cancel', cancel),
            ],
            GET_PHONE: [
                MessageHandler(filters.TEXT & ~filters.COMMAND, get_phone),
                CommandHandler('cancel', cancel),
            ],
        },
        fallbacks=[
            CommandHandler('cancel', cancel),
            MessageHandler(filters.TEXT, unknown),
        ],
    )
    
    application.add_handler(conv_handler)
    
    # اجرای ربات
    application.run_polling()

if __name__ == '__main__':
    main()