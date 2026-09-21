import logging
from uuid import uuid4
from pyrogram import Client
from pyrogram.errors.exceptions.bad_request_400 import QueryIdInvalid
from pyrogram.types import (
    InlineKeyboardButton,
    InlineKeyboardMarkup,
    InlineQueryResultCachedDocument,
    InlineQuery
)
from database.ia_filterdb import get_search_results
from database.connections_mdb import active_connection
from utils import is_subscribed, get_size, temp
import info

logger = logging.getLogger(__name__)

# Determine cache strategy
CACHE_TIME = 0 if (info.AUTH_USERS or info.AUTH_CHANNEL) else info.CACHE_TIME


async def is_user_allowed(query: InlineQuery) -> bool:
    """Check if the querying user is authorized or banned."""
    if not query.from_user:
        return False

    user_id = query.from_user.id

    if info.AUTH_USERS:
        return user_id in info.AUTH_USERS

    return user_id not in temp.BANNED_USERS


def format_caption(file, title: str, size: str) -> str:
    """Format caption safely using CUSTOM_FILE_CAPTION fallback."""
    raw_caption = getattr(file, "caption", "") or ""

    if info.CUSTOM_FILE_CAPTION:
        try:
            return info.CUSTOM_FILE_CAPTION.format(
                file_name=title or "",
                file_size=size or "",
                file_caption=raw_caption
            )
        except Exception as err:
            logger.error("Caption formatting error: %s", err)

    return raw_caption or title or "Unnamed File"


def build_reply_markup(query: str) -> InlineKeyboardMarkup:
    """Construct inline keyboard for query results."""
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("Search again", switch_inline_query_current_chat=query)]
    ])


@Client.on_inline_query()
async def inline_search_handler(bot: Client, query: InlineQuery):
    """Show search results for given inline query."""
    if not await is_user_allowed(query):
        await query.answer(
            results=[],
            cache_time=0,
            switch_pm_text="Unauthorized access",
            switch_pm_parameter="unauthorized"
        )
        return

    if info.AUTH_CHANNEL and not await is_subscribed(bot, query):
        await query.answer(
            results=[],
            cache_time=0,
            switch_pm_text="Subscribe to channel to use the bot",
            switch_pm_parameter="subscribe"
        )
        return

    # Parse file type filters (e.g. "Movie Name | video")
    raw_query = query.query.strip()
    if "|" in raw_query:
        search_str, file_type = [part.strip() for part in raw_query.split("|", maxsplit=1)]
        file_type = file_type.lower()
    else:
        search_str = raw_query
        file_type = None

    offset = int(query.offset or 0)
    chat_id = await active_connection(str(query.from_user.id))

    files, next_offset, total = await get_search_results(
        chat_id=chat_id,
        query=search_str,
        file_type=file_type,
        max_results=10,
        offset=offset
    )

    reply_markup = build_reply_markup(search_str)
    results = []

    for file in files:
        title = getattr(file, "file_name", "Unknown")
        file_size_str = get_size(file.file_size)
        f_caption = format_caption(file, title, file_size_str)

        results.append(
            InlineQueryResultCachedDocument(
                id=uuid4().hex,  # Unique ID for Telegram client caching
                title=title,
                document_file_id=file.file_id,
                caption=f_caption,
                description=f"Size: {file_size_str}\nType: {getattr(file, 'file_type', 'N/A')}",
                reply_markup=reply_markup
            )
        )

    if results:
        # Dynamic switch button title text formatting
        if search_str:
            switch_text = f"📁 Results - {total} for {search_str}"
        else:
            switch_text = f"📁 Total Files - {total}"

        try:
            await query.answer(
                results=results,
                is_personal=True,
                cache_time=CACHE_TIME,
                switch_pm_text=switch_text[:64],  # Prevent Telegram API 64-char overflow
                switch_pm_parameter="start",
                next_offset=str(next_offset) if next_offset else ""
            )
        except QueryIdInvalid:
            pass  # Query expired before response reached Telegram
        except Exception as e:
            logger.exception("Failed to answer inline query: %s", e)

    else:
        # No results state string formatting
        if search_str:
            switch_text = f'❌ No results for "{search_str}"'
        else:
            switch_text = f'❌ No files available'

        await query.answer(
            results=[],
            is_personal=True,
            cache_time=CACHE_TIME,
            switch_pm_text=switch_text[:64],
            switch_pm_parameter="okay"
        )
