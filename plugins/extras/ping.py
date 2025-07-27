# Credits by @neomatrix90

import time
from datetime import datetime as dt
from random import choice

import requests
from pyrogram import Client, filters
from pyrogram.types import (
    InlineQuery,
    InlineQueryResultArticle,
    InlineQueryResultPhoto,
    InputTextMessageContent,
    Message,
)

from info import ADMINS
from plugins import StartTime
from utils import get_readable_time

PING_DISABLE_NONPREM = {}
ANIME_WAIFU_IS_RANDOM = {}


def waifu_hentai():
    LIST_SFW_JPG = ["waifu", "blowjob", "neko"]
    waifu_link = "https"
    waifu_api = "api.waifu.pics"
    waifu_types = "nsfw"
    waifu_category = choice(LIST_SFW_JPG)
    waifu_param = f"{waifu_link}://{waifu_api}/{waifu_types}/{waifu_category}"
    response = requests.get(waifu_param).json()
    return response["url"]


def waifu_random():
    LIST_SFW_JPG = ["neko", "waifu", "megumin", "shinobu"]
    waifu_link = "https"
    waifu_api = "api.waifu.pics"
    waifu_types = "sfw"
    waifu_category = choice(LIST_SFW_JPG)
    waifu_param = f"{waifu_link}://{waifu_api}/{waifu_types}/{waifu_category}"
    response = requests.get(waifu_param).json()
    return response["url"]


def get_caption(
    client, duration: float, server_status: str, uptime: str, is_premium: bool
) -> str:
    """Generate the caption for the ping response."""
    if is_premium:
        return f"**Pong !!** `{duration}ms`\n**Server:** {server_status}\n**Uptime** - `{uptime}`\n"
    return (
        f"🏓 **Pɪɴɢᴇʀ :** `{duration}ms`\n"
        f"👨‍💻 **Sᴇʀᴠᴇʀ:** `{server_status}`\n"
        f"⌛ **Uᴘᴛɪᴍᴇ :** `{uptime}`\n"
        f"🤴 **Oᴡɴᴇʀ :** {client.me.mention}"
    )


async def send_ping_response(
    client,
    message: Message,
    duration: float,
    server_status: str,
    uptime: str,
    is_premium: bool,
    photo=None,
):
    """Send the ping response with optional photo."""
    caption = get_caption(client, duration, server_status, uptime, is_premium)
    if photo:
        await message.reply_photo(photo, caption=caption)
    else:
        await message.reply_text(caption)


@Client.on_message(
    filters.command("pingset") & filters.user(ADMINS) & ~filters.forwarded
)
async def pingsetsetting(client, message: Message):
    global PING_DISABLE_NONPREM, ANIME_WAIFU_IS_RANDOM
    args = message.text.lower().split()[1:]
    chat = message.chat

    if chat.type != "private" and args:
        if args[0] == "waifu":
            ANIME_WAIFU_IS_RANDOM[message.from_user.id] = {
                "waifu": True,
                "hentai": False,
            }
            await message.reply_text(f"__Turned on ping {args[0]}__")
        elif args[0] == "hentai":
            ANIME_WAIFU_IS_RANDOM[message.from_user.id] = {
                "waifu": False,
                "hentai": True,
            }
            await message.reply_text(f"__Turned on ping {args[0]}__")
        elif args[0] in ("no", "off", "false"):
            PING_DISABLE_NONPREM[message.from_user.id] = False
            ANIME_WAIFU_IS_RANDOM[message.from_user.id] = {
                "waifu": False,
                "hentai": False,
            }
            await message.reply_text("__Turned off picture ping__")
    else:
        ping_mode = (
            "On"
            if PING_DISABLE_NONPREM.get(message.from_user.id)
            else "Anime" if ANIME_WAIFU_IS_RANDOM.get(message.from_user.id) else "Off"
        )
        await message.reply_text(f"**Ping Mode:** `{ping_mode}`")


@Client.on_message(filters.command("ping") & ~filters.forwarded)
async def custom_ping_handler(client, message: Message):
    uptime = get_readable_time((time.time() - StartTime))
    start = dt.now()
    lol = await message.reply_text("**__Pong!!__**")
    # await asyncio.sleep(1.5)
    duration_ = (dt.now() - start).microseconds / 1000
    duration = round(duration_)

    is_premium = client.me.is_premium
    is_anime = ANIME_WAIFU_IS_RANDOM.get(message.from_user.id)
    server_status = "Sexy Maid Online"

    if PING_DISABLE_NONPREM.get(message.from_user.id):
        await lol.edit_text(
            get_caption(client, duration, server_status, uptime, is_premium)
        )
        return

    if is_anime:
        photo = (
            waifu_random()
            if is_anime.get("anime")
            else waifu_hentai() if is_anime.get("hentai") else None
        )
        if photo:
            await send_ping_response(
                client, message, duration, server_status, uptime, is_premium, photo
            )
            await lol.delete()
            return

    await send_ping_response(
        client, message, duration, server_status, uptime, is_premium
    )
    await lol.delete()


# Inline query handler for @bot ping
@Client.on_inline_query(filters.regex("^ping$"))
async def ping_inline_query(client, inline_query: InlineQuery):
    # Record the start time
    start = dt.now()

    uptime = get_readable_time((time.time() - StartTime))
    is_premium = client.me.is_premium
    is_anime = ANIME_WAIFU_IS_RANDOM.get(inline_query.from_user.id)
    server_status = "Sexy Maid Online"

    # Prepare the response message
    response_message = get_caption(
        client, 0, server_status, uptime, is_premium
    )  # Temporarily set latency to 0

    # Check if the user has anime/hentai preferences
    if is_anime:
        photo_url = (
            waifu_random()
            if is_anime.get("anime")
            else waifu_hentai() if is_anime.get("hentai") else None
        )
        if photo_url:
            # Record the end time
            end = dt.now()
            duration_ = (end - start).microseconds / 1000
            duration = round(duration_)

            # Update the response message with the correct latency
            response_message = get_caption(
                client, duration, server_status, uptime, is_premium
            )

            # Send photo response
            result = InlineQueryResultPhoto(
                photo_url=photo_url,
                thumb_url=photo_url,
                caption=response_message,
                title="Ping",
                description="Click to check bot's ping and status with a photo",
            )
            await inline_query.answer([result], cache_time=1)
            return

    # Record the end time for text response
    end = dt.now()
    duration_ = (end - start).microseconds / 1000
    duration = round(duration_)

    # Update the response message with the correct latency
    response_message = get_caption(
        client, duration, server_status, uptime, is_premium)

    # Default text response
    result = InlineQueryResultArticle(
        title="Ping",
        input_message_content=InputTextMessageContent(response_message),
        description="Click to check bot's ping and status",
    )
    await inline_query.answer([result], cache_time=1)
