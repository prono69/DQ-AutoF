import os
import random

import requests
from pyrogram import Client, filters

from plugins.helpers.nsfw_var import nsfw as useless


@Client.on_message(filters.command("ne"))
async def neko(client, message):
    "Search images from nekos"
    reply_to = message.reply_to_message
    reply = message.reply_to_message
    reply_id = reply.message_id if reply else None
    choose = message.text.split(" ", 1)[1]
    catevent = await message.reply_text("`Processing Nekos...`")
    if choose not in useless.nekos():
        return await catevent.edit(
            f"**Wrong catagory!! Choose from here:**\n\n{useless.nsfw(useless.nekos())}"
        )
    link = useless.nekos(choose)
    caption = choose
    await catevent.delete()
    try:
        if link.endswith(".gif"):
            await client.send_animation(
                chat_id=message.chat.id,
                animation=link,
                caption=choose,
                reply_to_message_id=reply_id,
            )
        else:
            await client.send_photo(
                chat_id=message.chat.id,
                photo=link,
                caption=choose,
                reply_to_message_id=reply_id,
            )
    except Exception as e:
        await message.reply_text(e)
