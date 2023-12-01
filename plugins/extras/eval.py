"""Evaluate Python Code inside Telegram
Syntax: .eval PythonCode"""

import asyncio
import io
import json
import os
import sys
import traceback

from pyrogram import Client, filters

from info import ADMINS
from plugins.helpers.terminal import Terminal


@Client.on_message(filters.command("eval") & filters.user(ADMINS))
async def eval(client, message):
    status_message = await message.reply_text("Processing ...")
    cmd = message.text.split(" ", maxsplit=1)[1]
    if len(cmd) == 1:
        await message.reply_text("No command to execute was given.")
        return

    reply_to_ = message
    if message.reply_to_message:
        reply_to_ = message.reply_to_message

    old_stderr = sys.stderr
    old_stdout = sys.stdout
    redirected_output = sys.stdout = io.StringIO()
    redirected_error = sys.stderr = io.StringIO()
    stdout, stderr, exc = None, None, None

    try:
        value = await aexec(cmd, client, message)
    except Exception:
        exc = traceback.format_exc().strip()

    stdout = redirected_output.getvalue().strip()
    stderr = redirected_error.getvalue().strip()
    sys.stdout = old_stdout
    sys.stderr = old_stderr
    output = exc or stderr or stdout or value

    if output is None:
        output = "😴"
    elif output == "":
        output = '""'
    elif isinstance(output, (dict, list)):
        try:
            output = json.dumps(output, indent=4, ensure_ascii=False)
        except Exception:
            pass

    final_output = "<b>EVAL</b>: "
    final_output += f"<code>{cmd}</code>\n\n"
    final_output += "<b>OUTPUT</b>:\n"
    final_output += f"<code>{output}</code> \n"

    if len(final_output) > 4096:
        with io.BytesIO(str.encode(final_output)) as out_file:
            out_file.name = "eval.text"
            await reply_to_.reply_document(
                document=out_file,
                caption=cmd[: 4096 // 4 - 1],
                disable_notification=True,
                quote=True,
            )
    else:
        await reply_to_.reply_text(final_output, quote=True)
    await status_message.delete()


async def aexec(code, client, message):
	p = lambda _x: print(_x)
    reply = message.reply_to_message
    r = reply
    exec(
        "async def __aexec(client, message, r, reply, p): "
        + "".join(f"\n {l_}" for l_ in code.split("\n"))
    )
    return await locals()["__aexec"](client, message, r, reply, p)

    
    
    
@Client.on_message(filters.command("term") & filters.user(ADMINS))
async def teml(bot, update):
    cmd = update.text.split(" ", 1)
    if len(cmd) == 1:
        await update.reply_text("No command to execute was given.")
        return
    cmd = cmd[1]
    try:
        t_obj = await Terminal.execute(cmd)
    except Exception as t_e:
        await update.reply(f"**ERROR:** `{t_e}`")
        return
    try:
        uid = os.geteuid()
    except ImportError:
        uid = 1
    output = f"`MilfLover:~#` `{cmd}`\n" if uid == 0 else f"`MilfLover:~$` `{cmd}`\n"
    count = 0
    k = None
    while not t_obj.finished:
        count += 1
        await asyncio.sleep(0.5)
        if count >= 5:
            count = 0
            out_data = f"{output}`{t_obj.read_line}`"
            try:
                if not k:
                    k = await update.reply(out_data)
                else:
                    await k.edit(out_data)
            except BaseException:
                pass
    out_data = f"`{output}{t_obj.get_output}`"
    if len(out_data) > 4096:
        if k:
            await k.delete()
        with open("terminal.txt", "w+") as ef:
            ef.write(out_data)
            ef.close()
        await update.reply_document("terminal.txt", caption=cmd)
        os.remove("terminal.txt")
        return
    send = k.edit if k else update.reply
    await send(out_data)
 