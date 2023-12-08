import os
import random

import requests
from pyrogram import Client, filters
from pyrogram.types import InlineKeyboardButton as IKB
from pyrogram.types import InlineKeyboardMarkup as IKM

from plugins.helpers import nsfw_var as useless


@Client.on_message(filters.command("ne"))
async def neko(client, message):
    "Search images from nekos"
    reply = message.reply_to_message
    reply_id = reply.id if reply else None
    catevent = await message.reply_text("`Processing Nekos...`")
    choose = message.text.split(" ", 1)
    if len(choose) == 1:
        await catevent.edit(
            f"**Give Some Tags to Search Pervert!! Choose from here:**\n\n{useless.nsfw(useless.nekos())}"
        )
        return
    choose = choose[1]
    if choose not in useless.nekos():
        return await catevent.edit(
            f"**Wrong catagory!! Choose from here:**\n\n{useless.nsfw(useless.nekos())}"
        )
    link = useless.nekos(choose)
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


# This list is for waifu.im
ISFW = [
    "maid",
    "marin-kitagawa",
    "mori-calliope",
    "oppai",
    "raiden-shogun",
    "selfies",
    "uniform",
    "waifu",
]

INSFW = [
    "ass",
    "ecchi",
    "ero",
    "hentai",
    "milf",
    "oral",
    "paizuri",
]

waifu_help = "**🔞 NSFW** :  "
for i in INSFW:
    waifu_help += f"`{i.lower()}`   "
waifu_help += "\n\n**😇 SFW** :  "
for m in ISFW:
    waifu_help += f"`{m.lower()}`   "


@Client.on_message(filters.command("wi"))
async def waifu(client, message):
    "Search images from waifu.im"
    reply = message.reply_to_message
    reply_id = reply.id if reply else None
    target = message.text.split(None, 1)
    choose = None
    url_ = "https://api.waifu.im"
    if len(target) == 1:
        url = f"{url_}/search"
    elif len(target) > 1:
        choose = target[1]
    if choose in ISFW:
        url = f"{url_}/search/?included_tags={choose}&is_nsfw=null"
    elif choose in INSFW:
        url = f"{url_}/search/?included_tags={choose}"
    if choose not in waifu_help:
        return await message.reply_text(
            f"**Wrong Category!! Choose from below**\n\n{waifu_help}"
        )
    catevent = await message.reply_text("`Processing...`")
    resp = requests.get(url).json()
    link = resp["images"][0]["url"]
    source = resp["images"][0]["source"]
    if not source:
        source = "https://cat-bounce.com/"
    btn = IKM([[IKB("💦 Source", url=f"{source}")]])
    try:
        if link.endswith(".gif"):
            await client.send_animation(
                chat_id=message.chat.id,
                animation=link,
                caption=choose,
                reply_markup=btn,
                reply_to_message_id=reply_id,
            )
        else:
            await client.send_photo(
                chat_id=message.chat.id,
                photo=link,
                caption=choose,
                reply_markup=btn,
                reply_to_message_id=reply_id,
            )
    except Exception as e:
        await message.reply_text(e)
    await catevent.delete()


@Client.on_message(filters.command("jav"))
async def jav(client, message):
    "Search random jav images"
    reply = message.reply_to_message
    reply_id = reply.id if reply else None
    catevent = await message.reply_text("`Processing...`")
    link = useless.nekos("jav")
    await catevent.delete()
    try:
        if link.endswith(".gif"):
            await client.send_animation(
                chat_id=message.chat.id, animation=link, reply_to_message_id=reply_id
            )
        else:
            await client.send_photo(
                chat_id=message.chat.id, photo=link, reply_to_message_id=reply_id
            )
    except Exception as e:
        await message.reply_text(e)


@Client.on_message(filters.command("pgif"))
async def pgif(client, message):
    "Search random purn gifs"
    reply = message.reply_to_message
    reply_id = reply.id if reply else None
    catevent = await message.reply_text("`Processing...`")
    rep = requests.get("https://scathach.redsplit.org/v3/nsfw/gif").json()
    link = rep.get("url")
    await catevent.delete()
    try:
        if link.endswith(".gif"):
            await client.send_animation(
                chat_id=message.chat.id, animation=link, reply_to_message_id=reply_id
            )
        else:
            await client.send_photo(
                chat_id=message.chat.id, photo=link, reply_to_message_id=reply_id
            )
    except Exception as e:
        await message.reply_text(e)


@Client.on_message(filters.command("ahe"))
async def ahegao(client, message):
    "Search random ahegao images"
    reply = message.reply_to_message
    reply_id = reply.id if reply else None
    catevent = await message.reply_text("`Processing...`")
    rep = requests.get("https://scathach.redsplit.org/v3/nsfw/ahegao").json()
    link = rep.get("url")
    await catevent.delete()
    try:
        if link.endswith(".gif"):
            await client.send_animation(
                chat_id=message.chat.id, animation=link, reply_to_message_id=reply_id
            )
        else:
            await client.send_photo(
                chat_id=message.chat.id, photo=link, reply_to_message_id=reply_id
            )
    except Exception as e:
        await message.reply_text(e)
