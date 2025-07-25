import pymongo
from info import DATABASE_URI, DATABASE_NAME, SECONDDB_URI

# Initialize connections
primary_db = pymongo.MongoClient(DATABASE_URI)[DATABASE_NAME]
secondary_db = pymongo.MongoClient(SECONDDB_URI)[DATABASE_NAME]

# Collections
captions_col = primary_db['captions']
captions_col_secondary = secondary_db['captions']

def get_caption_template():
    """Fetch template from primary DB, fallback to secondary"""
    template = captions_col.find_one({"type": "global"})
    if not template:
        template = captions_col_secondary.find_one({"type": "global"})
    return template.get("text") if template else None

def set_caption_template(template_text: str):
    """Update template in both databases"""
    captions_col.update_one(
        {"type": "global"},
        {"$set": {"text": template_text}},
        upsert=True
    )
    captions_col_secondary.update_one(
        {"type": "global"},
        {"$set": {"text": template_text}},
        upsert=True
    )