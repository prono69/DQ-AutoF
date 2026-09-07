import asyncio
import logging
from struct import pack
import re
import base64
from pyrogram.file_id import FileId
from pymongo.errors import DuplicateKeyError
from umongo import Instance, Document, fields
from motor.motor_asyncio import AsyncIOMotorClient
from marshmallow.exceptions import ValidationError
from info import DATABASE_URI, DATABASE_NAME, COLLECTION_NAME, USE_CAPTION_FILTER, MAX_B_TN, SECONDDB_URI
from utils import get_settings, save_group_settings
from sample_info import tempDict

logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)

# some basic variables needed
saveMedia = None

# primary db
client = AsyncIOMotorClient(DATABASE_URI)
db = client[DATABASE_NAME]
instance = Instance.from_db(db)


@instance.register
class Media(Document):
    file_id = fields.StrField(attribute='_id')
    file_ref = fields.StrField(allow_none=True)
    file_name = fields.StrField(required=True)
    file_size = fields.IntField(required=True)
    file_type = fields.StrField(allow_none=True)
    mime_type = fields.StrField(allow_none=True)
    caption = fields.StrField(allow_none=True)

    class Meta:
        indexes = ('$file_name', )
        collection_name = COLLECTION_NAME


# secondary db
client2 = AsyncIOMotorClient(SECONDDB_URI)
db2 = client2[DATABASE_NAME]
instance2 = Instance.from_db(db2)


@instance2.register
class Media2(Document):
    file_id = fields.StrField(attribute='_id')
    file_ref = fields.StrField(allow_none=True)
    file_name = fields.StrField(required=True)
    file_size = fields.IntField(required=True)
    file_type = fields.StrField(allow_none=True)
    mime_type = fields.StrField(allow_none=True)
    caption = fields.StrField(allow_none=True)

    class Meta:
        indexes = ('$file_name', )
        collection_name = COLLECTION_NAME


async def choose_mediaDB():
    """Choose which database to use based on tempDict['indexDB']."""
    global saveMedia
    if tempDict['indexDB'] == DATABASE_URI:
        logger.info("Using first db (Media)")
        saveMedia = Media
    else:
        logger.info("Using second db (Media2)")
        saveMedia = Media2


async def save_file(media):
    """Save file in database"""

    # TODO: Find better way to get same file_id for same media to avoid duplicates
    file_id, file_ref = unpack_new_file_id(media.file_id)
    file_name = re.sub(r"(_|\-|\.|\+)", " ", str(media.file_name))

    # BUG FIX: check against whichever DB is actually active (saveMedia),
    # not always the primary Media collection. Previously a file already
    # present in Media2 would pass this check when Media2 was active.
    if await saveMedia.count_documents({'file_id': file_id}, limit=1):
        logger.warning(f'{getattr(media, "file_name", "NO_FILE")} is already saved in the active DB !')
        return False, 0

    try:
        file = saveMedia(
            file_id=file_id,
            file_ref=file_ref,
            file_name=file_name,
            file_size=media.file_size,
            file_type=media.file_type,
            mime_type=media.mime_type,
            caption=media.caption.html if media.caption else None,
        )
    except ValidationError:
        logger.exception('Error occurred while saving file in database')
        return False, 2

    try:
        await file.commit()
    except DuplicateKeyError:
        logger.warning(f'{getattr(media, "file_name", "NO_FILE")} is already saved in database')
        return False, 0

    logger.info(f'{getattr(media, "file_name", "NO_FILE")} is saved to database')
    return True, 1


def _build_regex(query: str):
    """
    Shared regex-building logic used by both get_search_results and
    get_bad_files. Returns a compiled regex, or None if the pattern
    fails to compile.
    """
    query = query.strip()
    if not query:
        raw_pattern = '.'
    elif ' ' not in query:
        raw_pattern = r'(\b|[\.\+\-_])' + re.escape(query) + r'(\b|[\.\+\-_])'
    else:
        raw_pattern = re.escape(query).replace(r'\ ', r'.*[\s\.\+\-_()]')

    try:
        return re.compile(raw_pattern, flags=re.IGNORECASE)
    except re.error:
        logger.exception(f'Failed to compile search regex for query: {query!r}')
        return None


def _build_filter(query: str, file_type=None):
    """Build the mongo filter dict for a given query/file_type, or None on bad regex."""
    regex = _build_regex(query)
    if regex is None:
        return None

    if USE_CAPTION_FILTER:
        filter_ = {'$or': [{'file_name': regex}, {'caption': regex}]}
    else:
        filter_ = {'file_name': regex}

    if file_type:
        filter_['file_type'] = file_type

    return filter_


async def _resolve_max_results(chat_id, default_max_results):
    """Look up the per-chat max_results setting, falling back sensibly."""
    settings = await get_settings(int(chat_id))
    try:
        use_max_btn = settings['max_btn']
    except KeyError:
        await save_group_settings(int(chat_id), 'max_btn', False)
        settings = await get_settings(int(chat_id))
        use_max_btn = settings['max_btn']

    return 10 if use_max_btn else int(MAX_B_TN)


async def get_search_results(chat_id, query, file_type=None, max_results=10, offset=0, filter=False):
    """For given query return (results, next_offset, total_results)"""
    if chat_id is not None:
        max_results = await _resolve_max_results(chat_id, max_results)

    # BUG FIX: offset can arrive as a string (e.g. from callback data);
    # cursor.skip() requires an int or it raises TypeError.
    offset = int(offset)

    filter_ = _build_filter(query, file_type)
    if filter_ is None:
        return [], '', 0

    # OPTIMIZATION: run both count_documents calls concurrently instead of
    # sequentially awaiting them one after another.
    media_count, media2_count = await asyncio.gather(
        Media.count_documents(filter_),
        Media2.count_documents(filter_),
    )
    total_results = media_count + media2_count

    # verifies max_results is an even number or not
    if max_results % 2 != 0:  # if max_results is odd, add 1 to make it even
        logger.info(f"Since max_results is an odd number ({max_results}), bot will use {max_results + 1} as max_results to make it even.")
        max_results += 1

    cursor = Media.find(filter_)
    cursor2 = Media2.find(filter_)
    # Sort by recent
    cursor.sort('$natural', -1)
    cursor2.sort('$natural', -1)
    # Slice files according to offset and max results
    cursor2.skip(offset).limit(max_results)
    # Get list of files
    fileList2 = await cursor2.to_list(length=max_results)

    if len(fileList2) < max_results:
        next_offset = offset + len(fileList2)
        media2_total = await Media2.count_documents(filter_)
        cursorSkipper = next_offset - media2_total
        cursor.skip(cursorSkipper if cursorSkipper >= 0 else 0).limit(max_results - len(fileList2))
        fileList1 = await cursor.to_list(length=(max_results - len(fileList2)))
        files = fileList2 + fileList1
        next_offset = next_offset + len(fileList1)
    else:
        files = fileList2
        next_offset = offset + max_results

    if next_offset >= total_results:
        next_offset = ''

    return files, next_offset, total_results


async def get_bad_files(query, file_type=None, filter=False):
    """For given query return (results, total_results)"""
    filter_ = _build_filter(query, file_type)
    if filter_ is None:
        return [], 0

    cursor = Media.find(filter_).sort('$natural', -1)
    cursor2 = Media2.find(filter_).sort('$natural', -1)

    # OPTIMIZATION: fetch counts concurrently, then fetch the two file lists
    # concurrently, instead of four sequential round trips.
    media_count, media2_count = await asyncio.gather(
        Media.count_documents(filter_),
        Media2.count_documents(filter_),
    )
    fileList2, fileList1 = await asyncio.gather(
        cursor2.to_list(length=media2_count),
        cursor.to_list(length=media_count),
    )

    files = fileList2 + fileList1
    total_results = len(files)

    return files, total_results


async def get_file_details(query):
    filter_ = {'file_id': query}
    filedetails = await Media.find(filter_).to_list(length=1)
    if not filedetails:
        filedetails = await Media2.find(filter_).to_list(length=1)
    return filedetails


def encode_file_id(s: bytes) -> str:
    r = b""
    n = 0

    for i in s + bytes([22]) + bytes([4]):
        if i == 0:
            n += 1
        else:
            if n:
                r += b"\x00" + bytes([n])
                n = 0

            r += bytes([i])

    return base64.urlsafe_b64encode(r).decode().rstrip("=")


def encode_file_ref(file_ref: bytes) -> str:
    return base64.urlsafe_b64encode(file_ref).decode().rstrip("=")


def unpack_new_file_id(new_file_id):
    """Return file_id, file_ref"""
    decoded = FileId.decode(new_file_id)
    file_id = encode_file_id(
        pack(
            "<iiqq",
            int(decoded.file_type),
            decoded.dc_id,
            decoded.media_id,
            decoded.access_hash
        )
    )
    file_ref = encode_file_ref(decoded.file_reference)
    return file_id, file_ref