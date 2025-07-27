import asyncio
from pyrogram import Client, filters, enums 
from plugins.helpers.admin_check import admin_check


@Client.on_message(filters.command("purge") & (filters.group | filters.channel | filters.private))                   
async def purge(client, message):
    if message.chat.type not in (
        enums.ChatType.SUPERGROUP,
        enums.ChatType.CHANNEL,
        enums.ChatType.PRIVATE,
    ):
        return

    is_admin = True if message.chat.type == enums.ChatType.PRIVATE else await admin_check(message)
    if not is_admin:
        return

    if not message.reply_to_message:
        await message.reply_text("Reply to a message to start purging.", quote=True)
        return

    status_message = await message.reply_text("Purging...", quote=True)
    await message.delete()
    message_ids = []
    count_del_etion_s = 0

    for a_s_message_id in range(message.reply_to_message.id, message.id):
        message_ids.append(a_s_message_id)
        if len(message_ids) == 100:  # Fix: this was a string earlier
            await client.delete_messages(
                chat_id=message.chat.id,
                message_ids=message_ids,
                revoke=True
            )
            count_del_etion_s += len(message_ids)
            message_ids = []

    if message_ids:
        await client.delete_messages(
            chat_id=message.chat.id,
            message_ids=message_ids,
            revoke=True
        )
        count_del_etion_s += len(message_ids)

    await status_message.edit_text(f"Deleted {count_del_etion_s} messages 🧹")
    await asyncio.sleep(5)
    await status_message.delete()