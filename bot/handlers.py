from telegram import InlineKeyboardButton, InlineKeyboardMarkup, Update
from telegram.ext import ContextTypes, CallbackQueryHandler
from config import FSUB_IDS  # Your channel IDs list

FSUB_CHANNEL_ID = FSUB_IDS[0]  # -1002661417456
FSUB_CHANNEL_LINK = "https://t.me/+qXNXNu_LytJiMzU0"

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    chat_id = update.effective_chat.id

    # Send force-subscription message with buttons
    keyboard = [
        [InlineKeyboardButton("Join Now", url=FSUB_CHANNEL_LINK)],
        [InlineKeyboardButton("Joined", callback_data="check_sub")]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)

    await context.bot.send_message(
        chat_id=chat_id,
        text="To access this bot, please join our channel first.",
        reply_markup=reply_markup
    )

async def check_sub_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    user_id = query.from_user.id

    # Check if user is member of the force sub channel
    try:
        member = await context.bot.get_chat_member(FSUB_CHANNEL_ID, user_id)
        status = member.status
        if status in ["member", "creator", "administrator"]:
            await query.answer("Welcome! You have access to the bot now.")
            # Here you can send the welcome message or proceed with bot features
            await query.edit_message_text("Thanks for joining! You now have access to the bot.")
        else:
            await query.answer("Please join the channel first to access the bot.", show_alert=True)
    except Exception as e:
        # Likely user is not member
        await query.answer("Please join the channel first to access the bot.", show_alert=True)
