import time

from pyrogram import Client, filters
from pyrogram.enums import ChatAction
from pyrogram.types import Message

import config

bot = Client(
    name=config.name,
    api_id=config.api_id,
    api_hash=config.api_hash)


@bot.on_message(filters.private)
async def always_typing(client, message: Message):
    while True:
        await message.reply_chat_action(ChatAction.TYPING)
        time.sleep(3)

bot.run()
