import asyncio
import logging
import os
from io import BytesIO

from pyrogram import Client, filters

from info import ADMINS

MAX_MESSAGE_LENGTH = 4096
COMMAND_TIMEOUT = 60  # Timeout in seconds
COMMAND_ALIASES = {
    "update": "git pull",
    "restart": "systemctl restart mybot.service",
}
command_history = []

logging.basicConfig(filename="bash_logs.txt", level=logging.INFO)


@Client.on_message(filters.command("bash") & filters.user(ADMINS))
async def execution(_, message):
    status_message = await message.reply("`Processing ...`")
    cmd = message.text.split(" ", maxsplit=1)[1]

    # Replace command with alias if it exists
    cmd = COMMAND_ALIASES.get(cmd, cmd)

    reply_to_ = message
    if message.reply_to_message:
        reply_to_ = message.reply_to_message

    try:
        # Log the command
        logging.info(f"Command executed by {message.from_user.id}: {cmd}")

        # Run the command with a timeout
        process = await asyncio.create_subprocess_shell(
            cmd, stdout=asyncio.subprocess.PIPE, stderr=asyncio.subprocess.PIPE
        )
        try:
            stdout, stderr = await asyncio.wait_for(
                process.communicate(), timeout=COMMAND_TIMEOUT
            )
        except asyncio.TimeoutError:
            await process.kill()  # Kill the process if it times out
            await status_message.edit(
                "❌ **Timeout**: The command took too long to execute."
            )
            return

        e = stderr.decode().strip() if stderr else "😂"
        o = stdout.decode().strip() if stdout else "😐"

        OUTPUT = ""
        OUTPUT += f"<b>QUERY:</b>\n<u>Command:</u>\n<code>{cmd}</code> \n"
        OUTPUT += f"<u>PID</u>: <code>{process.pid}</code>\n\n"
        OUTPUT += f"<b>stderr</b>: \n<code>{e}</code>\n\n"
        OUTPUT += f"<b>stdout</b>: \n<code>{o}</code>"

        if len(OUTPUT) > MAX_MESSAGE_LENGTH:
            with BytesIO(str.encode(OUTPUT)) as out_file:
                out_file.name = "exec.txt"
                await reply_to_.reply_document(
                    document=out_file,
                    caption=cmd[: MAX_MESSAGE_LENGTH // 4 - 1],
                    disable_notification=True,
                    quote=True,
                )
                os.remove("exec.txt")
        else:
            await reply_to_.reply(OUTPUT, quote=True)

        # Add command to history
        command_history.append(cmd)
        if len(command_history) > 25:  # Keep only the last 10 commands
            command_history.pop(0)

    except Exception as ex:
        await reply_to_.reply(f"❌ **Error**: {str(ex)}", quote=True)
    finally:
        await status_message.delete()


@Client.on_message(filters.command("bhis") & filters.user(ADMINS))
async def show_history(_, message):
    # Add numbering to each command and wrap in <code> tags
    formatted_history = "\n".join(
        f"<b>{i + 1}.</b> <code>{cmd}</code>"
        for i, cmd in enumerate(reversed(command_history))
    )

    # Check if the message exceeds Telegram's character limit
    if len(formatted_history) > MAX_MESSAGE_LENGTH:
        # Send as a text file
        with BytesIO(str.encode(formatted_history)) as out_file:
            out_file.name = "command_history.txt"
            await message.reply_document(
                document=out_file,
                caption="__Limit exceeded, so sending as file__",
                quote=True,
            )
    else:
        # Send as a regular message
        await message.reply_text(
            f"<b>Command History:</b>\n{formatted_history}", quote=True
        )
