import os
import asyncio
from dotenv import load_dotenv
from drive import DriveHandler
from aiogram.filters import Command
from aiogram import Bot, Dispatcher, types
from aiogram.exceptions import TelegramNetworkError
from aiogram.utils.keyboard import InlineKeyboardBuilder

# Load Environment Variables
load_dotenv()
TOKEN = os.getenv("TOKEN")
OWNER = int(os.getenv("OWNER"))
DRIVE = DriveHandler("creds.json", os.getenv("PARENT_FOLDER"))

# Create the Bot and Dispatcher
bot = Bot(TOKEN)
dp = Dispatcher()

# Entry Point
@dp.message(Command("start", ignore_case=True))
async def start(message: types.message.Message) -> None:
    if message.chat.id != OWNER:
        await message.answer("I'm sorry this bot is not built for you.")
    else:
        keyboard = InlineKeyboardBuilder()
        keyboard.button(text="Get Lyrical Video.", callback_data='lyrics')
        keyboard.button(text="Get Shorts for Anime Edits.", callback_data='anime')
        keyboard.button(text="Get Shorts for Luxury life.", callback_data='luxury')
        keyboard.adjust(1)
        msg = "Welcome to Your bot.\n\nThe Bot has all these options, Please choose one of them.\n"
        await message.answer(msg, reply_markup=keyboard.as_markup())

# A function to send lyrical videos
async def send_video(chat: str):
    folder_id = os.getenv(chat)
    file = DRIVE.pick_one(folder_id) or {}

    if file.get("mimeType").startswith("video/"):
        video_link = DRIVE.get_download_link(file.get("id"))
        keyboard = InlineKeyboardBuilder()
        keyboard.button(text="Delete?", callback_data=f"del-{file.get('id')}")

        max_retries = 3
        for attempt in range(max_retries):
            try:
                await bot.send_video(OWNER, video_link, caption="Here's what you asked for.", reply_markup=keyboard.as_markup())
                break  # If successful, break out of the retry loop
            except TelegramNetworkError:
                if attempt < max_retries - 1:  # If it's not the last attempt
                    await asyncio.sleep(2 ** attempt)  # Exponential backoff
                else:
                    raise

# Define a callback handler to process button presses
@dp.callback_query()
async def button(callback_query: types.CallbackQuery):
    if callback_query.data == 'lyrics':
        await send_video("LYRICS_FOLDER")
        await bot.delete_message(callback_query.message.chat.id, callback_query.message.message_id - 1)
        await callback_query.message.delete()
    elif callback_query.data == 'anime':
        await send_video("ANIME")
        await bot.delete_message(callback_query.message.chat.id, callback_query.message.message_id - 1)
        await callback_query.message.delete()
    elif callback_query.data == 'luxury':
        await send_video("LUXURY")
        await bot.delete_message(callback_query.message.chat.id, callback_query.message.message_id - 1)
        await callback_query.message.delete()
    elif callback_query.data.startswith("del-"):
        file_id = callback_query.data.split("del-")[-1]
        DRIVE.delete_one(file_id)
        await callback_query.message.delete()

async def start_polling() -> None:
    # The run events dispatching
    await dp.start_polling(bot, polling_timeout=5)

def run_bot():
    asyncio.run(start_polling())
