import asyncio
import logging
import re
import base64
from struct import pack

from pyrogram.file_id import FileId
from pymongo.errors import DuplicateKeyError
from umongo import Instance, Document, fields
from motor.motor_asyncio import AsyncIOMotorClient
from marshmallow.exceptions import ValidationError

from info import (
    DATABASE_URI,
    DATABASE_NAME,
    COLLECTION_NAME,
    USE_CAPTION_FILTER,
    MAX_B_TN,
    SECONDDB_URI,
)
from utils import get_settings, save_group_settings
from sample_info import tempDict

logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)

saveMedia = None

# Primary DB setup
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
        indexes = ('$file_name',)
        collection_name = COLLECTION_NAME


# Secondary DB setup
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
        indexes = ('$file_name',)
        collection_name = COLLECTION_NAME


async def choose_mediaDB():
    """Choose active target DB model based on tempDict."""
    global saveMedia
    if tempDict.get('indexDB') == DATABASE_URI:
        logger.info("Using first DB (Media)")
        saveMedia = Media
    else:
        logger.info("Using second DB (Media2)")
        saveMedia = Media2


async def save_file(media):
    """Save file in the active target database."""
    file_id, file_ref = unpack_new_file_id(media.file_id)
    file_name = re.sub(r"[_.\-+]", " ", str(getattr(media, "file_name", "")))

    if await saveMedia.count_documents({'file_id': file_id}, limit=1):
        logger.warning(f"{file_name or 'NO_FILE'} is already saved in active DB!")
        return False, 0

    try:
        file = saveMedia(
            file_id=file_id,
            file_ref=file_ref,
            file_name=file_name,
            file_size=media.file_size,
            file_type=getattr(media, "file_type", None),
            mime_type=getattr(media, "mime_type", None),
            caption=media.caption.html if getattr(media, "caption", None) else None,
        )
    except ValidationError:
        logger.exception("Validation error while preparing file document")
        return False, 2

    try:
        await file.commit()
    except DuplicateKeyError:
        logger.warning(f"{file_name or 'NO_FILE'} is already saved in database")
        return False, 0

    logger.info(f"{file_name or 'NO_FILE'} is saved to database")
    return True, 1


def _build_regex(query: str):
    """Build compiled regex for search."""
    query = query.strip()
    if not query:
        # Match everything if query is empty
        return re.compile(r'.', flags=re.IGNORECASE)

    if ' ' not in query:
        raw_pattern = r'(\b|[\.\+\-_])' + re.escape(query) + r'(\b|[\.\+\-_])'
    else:
        tokens = [re.escape(term) for term in query.split() if term]
        raw_pattern = r'.*[\s\.\+\-_()]'.join(tokens)

    try:
        return re.compile(raw_pattern, flags=re.IGNORECASE)
    except re.error:
        logger.exception(f"Failed to compile search regex for query: {query!r}")
        return None


def _build_filter(query: str, file_type=None):
    """Build the mongo filter dict for query and optional file_type."""
    filter_ = {}
    query_str = query.strip() if query else ""

    if query_str:
        # Only apply name/caption filter if query contains text
        regex = _build_regex(query_str)
        if regex is None:
            return None
        if USE_CAPTION_FILTER:
            filter_['$or'] = [{'file_name': regex}, {'caption': regex}]
        else:
            filter_['file_name'] = regex
            
    # If query_str is empty (""), filter_ remains empty ({}), 
    # which tells MongoDB to retrieve ALL documents by default.

    if file_type:
        filter_['file_type'] = file_type

    return filter_



async def _resolve_max_results(chat_id: int, default_max_results: int) -> int:
    """Fetch per-chat button layout limits securely."""
    try:
        settings = await get_settings(chat_id)
        use_max_btn = settings.get('max_btn', False)
    except Exception:
        await save_group_settings(chat_id, 'max_btn', False)
        use_max_btn = False

    return 10 if use_max_btn else int(MAX_B_TN)


async def get_search_results(chat_id, query, file_type=None, max_results=10, offset=0, filter=False):
    """Paginate and merge search results across dual Mongo collections."""
    if chat_id is not None:
        max_results = await _resolve_max_results(int(chat_id), max_results)

    offset = int(offset)

    filter_ = _build_filter(query, file_type)
    if filter_ is None:
        return [], '', 0

    # Count documents across both databases concurrently
    media2_count, media_count = await asyncio.gather(
        Media2.count_documents(filter_),
        Media.count_documents(filter_)
    )
    total_results = media_count + media2_count

    if total_results == 0:
        return [], '', 0

    # Ensure max_results is even for 2-column inline button grids
    if max_results % 2 != 0:
        max_results += 1

    files = []

    # Case 1: Offset lies within Media2
    if offset < media2_count:
        cursor2 = Media2.find(filter_).sort('$natural', -1).skip(offset).limit(max_results)
        fileList2 = await cursor2.to_list(length=max_results)
        files.extend(fileList2)

        # Fill remaining slots from Media if needed
        needed = max_results - len(fileList2)
        if needed > 0 and media_count > 0:
            cursor1 = Media.find(filter_).sort('$natural', -1).limit(needed)
            fileList1 = await cursor1.to_list(length=needed)
            files.extend(fileList1)

    # Case 2: Offset has exceeded Media2, query Media directly
    else:
        media_offset = offset - media2_count
        cursor1 = Media.find(filter_).sort('$natural', -1).skip(media_offset).limit(max_results)
        files = await cursor1.to_list(length=max_results)

    next_offset = offset + len(files)
    if next_offset >= total_results or not files:
        next_offset_str = ''
    else:
        next_offset_str = str(next_offset)

    return files, next_offset_str, total_results


async def get_bad_files(query, file_type=None, filter=False):
    """Fetch total files matching filter across both collections."""
    filter_ = _build_filter(query, file_type)
    if filter_ is None:
        return [], 0

    # Fetch records concurrently
    fileList2, fileList1 = await asyncio.gather(
        Media2.find(filter_).sort('$natural', -1).to_list(length=None),
        Media.find(filter_).sort('$natural', -1).to_list(length=None)
    )

    files = fileList2 + fileList1
    return files, len(files)


async def get_file_details(query):
    """Get single document details by file_id."""
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
    """Unpack raw Pyrogram FileId structure."""
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
