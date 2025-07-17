import os
import logging
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import (
    Application,
    CommandHandler,
    MessageHandler,
    CallbackQueryHandler,
    ConversationHandler,
    ContextTypes,
    filters,
)


from image_generator import create_image, FONTS, COLOR_PALETTES, hex_to_Rgb
from dotenv import load_dotenv

load_dotenv()

TOKEN=os.getenv("TELEGRAM_BOT_TOKEN")

logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s", level=logging.INFO
)
logger = logging.getLogger(__name__)


GET_TEXT, GET_FONT, GET_PALLETE, GET_CUSTOM_COLOR_1, GET_CUSTOM_COLOR_2, GET_V_ALIGN, GET_H_ALIGN = range(7) 


def build_keyboard(items, colums=2): 

    buttons = []
    for item in items:
        buttons.append(InlineKeyboardButton(text=item, callback_data=item))
    
    if colums == 1:
        return InlineKeyboardMarkup.from_column(buttons)
    
    keyboard = [buttons[i:i + colums] for i in range(0, len(buttons), colums)]
    return InlineKeyboardMarkup(keyboard)


async def start_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None: 

    await update.message.reply_text(
        "👋 Hello! I'm your Image Quote Bot.\n\n"
        "I can create beautiful gradient images with your text on them. "
        "Send /create to get started!"
    )

async def create_flow_start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:

    context.user_data.clear()
    await update.message.reply_text("ok lets create an image! First, send me the text you want to put on it.") 
    return GET_TEXT

async def recieved_text(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int: 

    context.user_data['the_text'] = update.message.text
    logger.info(f"User text: {context.user_data['the_text']}")
    
    keyboard = build_keyboard(list(FONTS.keys()))
    await update.message.reply_text("Great! Now, choose a font for your text:", reply_markup=keyboard)
    return GET_FONT



async def received_font(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:

    query = update.callback_query
    await query.answer()
    context.user_data['font'] = query.data
    logger.info(f"User font: {context.user_data['font']}")

    pallete_keys = list(COLOR_PALETTES.keys()) 
    keyboard = build_keyboard(pallete_keys + ["Custom Colors..."])
    await query.edit_message_text("Awesome. Now pick a color pallete:", reply_markup=keyboard)
    return GET_PALLETE

async def recieved_pallete(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int: 

    query = update.callback_query
    await query.answer()
    choice = query.data

    if choice == "Custom Colors...":
        await query.edit_message_text("Okay, send me the first hex color code for the gradients top (e.g., #1A2B3C).")
        return GET_CUSTOM_COLOR_1
    else:
        context.user_data['pallete'] = choice 
        logger.info(f"User pallete: {context.user_data['pallete']}")
        
        keyboard = build_keyboard(["Top", "Center", "Bottom"], colums=3)
        await query.edit_message_text("Next, choose the vertical text alignment:", reply_markup=keyboard)
        return GET_V_ALIGN


async def received_custom_color_1(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:

    color = update.message.text
    if not hex_to_Rgb(color):
        await update.message.reply_text("That doesnt look like a valid hex code. Please try again (e.g., #FF5733).") 
        return GET_CUSTOM_COLOR_1
    
    context.user_data['custom_color1'] = color
    await update.message.reply_text("Got it. Now send me the second hex color code for the gradient's bottom.")
    return GET_CUSTOM_COLOR_2


async def received_custom_color_2(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:

    color = update.message.text
    if not hex_to_Rgb(color):
        await update.message.reply_text("That doesn't look like a valid hex code. try again (e.g., #C70039).")
        return GET_CUSTOM_COLOR_2
    
    context.user_data['custom_color2'] = color
    context.user_data['pallete'] = "Custom"

    logger.info(f"User custom colors: {context.user_data.get('custom_color1')}, {context.user_data.get('custom_color2')}")

    keyboard = build_keyboard(["Top", "Center", "Bottom"], colums=3)
    await update.message.reply_text("Perfect! Now choose the vertical text alignment:", reply_markup=keyboard)
    return GET_V_ALIGN


async def received_v_align(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:

    query = update.callback_query
    await query.answer()
    choice = query.data.lower()
    
    context.user_data['v_align'] = choice
    logger.info(f"v align: {choice}") 

    keyboard = build_keyboard(["Left", "Center", "Right"], colums=3)
    await query.edit_message_text("And now the horizontal alignment:", reply_markup=keyboard)
    return GET_H_ALIGN


async def received_h_align_and_generate(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    query = update.callback_query
    await query.answer()
    choice = query.data.lower()
    
    context.user_data['h_align'] = choice
    logger.info(f"h align: {choice}")
    
    await query.edit_message_text("Generating your image, pls wait a moment...") 

    filename = create_image(
        text=context.user_data['the_text'],
        font_choice=context.user_data['font'],
        pallete_choice=context.user_data.get('pallete'), 
        v_align=context.user_data['v_align'],
        h_align=context.user_data['h_align'],
        custom_color1=context.user_data.get('custom_color1'),
        custom_color2=context.user_data.get('custom_color2')
    )

    if filename.startswith("Error:"):
        await context.bot.send_message(chat_id=update.effective_chat.id, text=f"Oops! Something went wrong.\n\n{filename}")
    else:
        try:
            await context.bot.send_photo(
                chat_id=update.effective_chat.id,
                photo=open(filename, 'rb'),
                caption="Heres your image! \n\nSend /create to make another one."
            )
        finally:
            if os.path.exists(filename):
                os.remove(filename)

    context.user_data.clear()
    return ConversationHandler.END


async def cancel(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:

    await update.message.reply_text("Action cancelled. Send /create anytime to start over.")
    return ConversationHandler.END


def main() -> None:

    application = Application.builder().token(TOKEN).build()

    conv_handler = ConversationHandler(
        entry_points=[CommandHandler("create", create_flow_start)],
        states={
            GET_TEXT: [MessageHandler(filters.TEXT & ~filters.COMMAND, recieved_text)], 
            GET_FONT: [CallbackQueryHandler(received_font)],
            GET_PALLETE: [CallbackQueryHandler(recieved_pallete)], 
            GET_CUSTOM_COLOR_1: [MessageHandler(filters.TEXT & ~filters.COMMAND, received_custom_color_1)],
            GET_CUSTOM_COLOR_2: [MessageHandler(filters.TEXT & ~filters.COMMAND, received_custom_color_2)],
            GET_V_ALIGN: [CallbackQueryHandler(received_v_align)],
            GET_H_ALIGN: [CallbackQueryHandler(received_h_align_and_generate)],
        },
        fallbacks=[CommandHandler("cancel", cancel)],
    )

    application.add_handler(CommandHandler("start", start_command))
    application.add_handler(conv_handler)

    print("Bot is running...")
    application.run_polling()

if __name__ == "__main__":
    main()