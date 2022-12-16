from pyrogram import Client, filters
import config

bot = Client(
    name=config.name,
    api_id=config.api_id,
    api_hash=config.api_hash)


@bot.on_message(filters.private, filters.command('start'))
async def test_bot(client, message):
    print(message)


bot.run()
