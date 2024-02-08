import asyncio
import os
import re
import subprocess
from datetime import datetime

from apscheduler.schedulers.background import BackgroundScheduler
from pyrogram import Client, filters
from pyrogram.enums import ParseMode
from pyrogram.errors import BadRequest
from pyrogram.errors import FloodWait
from pyrogram.types import Message

import config

app = Client(
    name=config.name,
    api_id=config.api_id,
    api_hash=config.api_hash,
    proxy=config.proxy if config.use_proxy else None)


@app.on_message((filters.private | filters.group) & filters.text)
async def welcome(client, message: Message):
    if message.text is None:
        return

    if config.auto_seen:
        await read_history(message)
    if message.text.startswith('ping'):
        await message.reply_text('pong')
    if message.text.startswith('txt'):
        await send_txt(message)
    if message.text.startswith('seen'):
        await set_auto_seen(message)
    if message.text.startswith('cmd'):
        await execute(message)
    if message.text.startswith('dl'):
        await download_link(message)


async def read_history(message: Message):
    await app.read_chat_history(chat_id=message.chat.id)
    await app.mark_chat_unread(chat_id=message.chat.id)
    # await message.reply_chat_action(ChatAction.TYPING)


async def send_txt(message: Message):
    query = message.text.split('\n')
    if len(query) < 3:
        await message.reply_text(text='**txt\n<file name>\n<content>**', parse_mode=ParseMode.MARKDOWN)
        return
    name = query[1]
    content = query[2:]
    await send_txt_file(message, name, content)


async def send_txt_file(message: Message, name: str, content: [str]):
    doc = f'{name}.txt'
    with open(file=doc, mode='w') as file:
        file.writelines(content)
    await message.reply_document(document=doc)
    os.remove(doc)


async def set_auto_seen(message: Message):
    if not message.from_user.is_self:
        return
    config.auto_seen = False if message.text.endswith('off') else True


async def execute(message: Message):
    if not message.from_user.is_self:
        return
    cmd = message.text.split()[1:]
    output = ''
    try:
        temp = subprocess.Popen(args=cmd, stdout=subprocess.PIPE)
        output = str(temp.communicate()[0])
        output = output.replace(r'\n', '\n').replace(r'\r', '\r').strip()
        await message.reply_text(output, parse_mode=ParseMode.MARKDOWN)

    except BadRequest:
        if output != '':
            await send_txt_file(message, 'output', output.split('\n'))
    except Exception as e:
        await message.reply_text(str(e.args))


async def download_link(message: Message):
    query = re.split('\n|\\s+', message.text)
    if len(query) < 2:
        await message.reply_text(text='**dl <url>**', parse_mode=ParseMode.MARKDOWN)
        return
    url = query[1]
    name = url.split('/')[-1]
    msg = await message.reply_text('Downloading..')
    try:
        subprocess.call(['curl', '--max-filesize', '2147483648', '-o', name, url])
        await msg.edit('Uploading..')
        if name.endswith('.mp4') or name.endswith('.mkv'):
            await message.reply_video(name)
        elif name.endswith('.mp3'):
            await message.reply_audio(name)
        else:
            await message.reply_document(name)
        await msg.delete()
    except Exception:
        await msg.edit('Bad URL')
    finally:
        os.remove(name)


async def update_bio_job():
    try:
        current_time = datetime.now().strftime("%H:%M:%S")
        await app.update_profile(current_time)
    except FloodWait as e:
        await asyncio.sleep(60)


def update_bio_job_runner():
    asyncio.run(update_bio_job())


scheduler = BackgroundScheduler()
scheduler.add_job(update_bio_job_runner, 'interval', minutes=1)
await scheduler.start()

app.run()
