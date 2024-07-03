import os
import asyncio
from dotenv import load_dotenv
from drive import DriveHandler
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ApplicationBuilder, ContextTypes, CommandHandler, CallbackQueryHandler
from telegram.error import TimedOut

# Entry Point
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE ):
    if not update.effective_message.chat_id == OWNER:
        await update.effective_chat.send_message("I'm sorry this bot is not built for you.")
    else:
        keyboard = [
        [InlineKeyboardButton("Get Lyrical Video.", callback_data='lyrics')],
        [InlineKeyboardButton("Get Shorts for Anime Edits.", callback_data='anime')],
        [InlineKeyboardButton("Get Shorts for Luxury life.", callback_data='luxury')]
    ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        msg = "Welcome to Your bot.\nThe Bot has all these options, Please choose one of them."
        await update.effective_chat.send_message(msg, reply_markup=reply_markup)

# A function to send lyrical videos
async def send_video(context: ContextTypes.DEFAULT_TYPE, channel: str):
    folder_id = os.getenv(channel)
    file = DRIVE.pick_one(folder_id)

    if file.get("mimeType").startswith("video/"):
        video_link = DRIVE.get_download_link(file.get("id"))
        reply_markup = InlineKeyboardMarkup([[InlineKeyboardButton("Delete?", callback_data=f"del-{file.get('id')}")]])

        max_retries = 3
        for attempt in range(max_retries):
            try:
                await context.bot.send_video(OWNER, video_link, caption="This is A Lyrical Video", reply_markup=reply_markup)
                break  # If successful, break out of the retry loop
            except TimedOut:
                if attempt < max_retries - 1:  # If it's not the last attempt
                    await asyncio.sleep(2 ** attempt)  # Exponential backoff
                else:
                    raise

# Define a callback handler to process button presses
async def button(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    query = update.callback_query

    # Handle different callback data
    if query.data == 'lyrics':
        await send_video(context, "LYRICS_FOLDER")
        await query.delete_message()
    elif query.data == 'anime':
        await send_video(context, "ANIME")
        await query.delete_message()
    elif query.data == 'luxury':
        await send_video(context, "LUXURY")
        await query.delete_message()
    elif query.data.startswith("del-"):
        file_id = query.data.split("del-")[-1]
        DRIVE.delete_one(file_id)
        await query.delete_message()

if __name__ == '__main__':

    # Load Environment Variables
    load_dotenv()
    TOKEN = os.getenv("TOKEN")
    OWNER = int(os.getenv("OWNER"))
    DRIVE = DriveHandler("creds.json", os.getenv("PARENT_FOLDER"))

    #create the Bot
    application = ApplicationBuilder().token(TOKEN).build()

    # Add Handlers
    start_handler = CommandHandler('start', start)
    application.add_handler(start_handler)
    application.add_handler(CallbackQueryHandler(button))

    # Start Polling
    application.run_polling()
