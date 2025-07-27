import asyncio
import io
import os
import sys
import traceback
import textwrap
import logging
from pprint import pformat  # For pretty-printing
from pyrogram import Client, filters
from info import ADMINS
from plugins.helpers.util import json_parser

MAX_MESSAGE_LENGTH = 4096
EVAL_TIMEOUT = 60  # Timeout in seconds
eval_history = []

logging.basicConfig(filename="eval_logs.txt", level=logging.INFO)


@Client.on_message(filters.command("eval") & filters.user(ADMINS))
async def eval_command(client, message):
    status_message = await message.reply_text("`Processing ...`")
    cmd = message.text.split(" ", maxsplit=1)[1]

    reply_to_ = message
    if message.reply_to_message:
        reply_to_ = message.reply_to_message

    old_stderr = sys.stderr
    old_stdout = sys.stdout
    redirected_output = sys.stdout = io.StringIO()
    redirected_error = sys.stderr = io.StringIO()
    stdout, stderr, exc, result = None, None, None, None

    try:
        # Run the user-provided code and capture the result of the last expression
        execution_result = await aexec(cmd, client, message)
        result = execution_result["return_value"]
        printed_output = execution_result["printed_output"]
    except Exception as e:
        exc = traceback.format_exc()
        error_type = e.__class__.__name__
        error_message = str(e)
        evaluation = (
            f"❌ **Error**: `{error_type}`\n"
            f"**Message**: `{error_message}`\n"
            f"**Traceback**:\n<code>{exc}</code>"
        )
    else:
        stdout = redirected_output.getvalue()
        stderr = redirected_error.getvalue()
        formatted_result = json_parser(result, indent=4) if result is not None else None
        formatted_printed = json_parser(printed_output.strip(), indent=4) if printed_output.strip() else None
        if stderr:
            evaluation = f"⚠️ **Stderr**:\n<code>{stderr}</code>"
        elif stdout:
            evaluation = f"<code>{stdout}</code>"
        elif printed_output:
            evaluation = f"<code>{formatted_printed}</code>"    
        elif result is not None:
            evaluation = f"<code>{formatted_result}</code>"    
        else:
            evaluation = "✅ **Success**"
    finally:
        sys.stdout = old_stdout
        sys.stderr = old_stderr

    final_output = "<b>EVAL</b>: "
    final_output += f"<code>{cmd}</code>\n\n"
    final_output += "<b>OUTPUT</b>:\n"
    final_output += f"{evaluation.strip()} \n"

    # Maintain a history of eval commands (max 25 entries)
    eval_history.append(cmd)
    if len(eval_history) > 25:
        eval_history.pop(0)

    if len(final_output) > MAX_MESSAGE_LENGTH:
        with io.BytesIO(str.encode(final_output)) as out_file:
            out_file.name = "eval.txt"
            await reply_to_.reply_document(
                document=out_file,
                caption=cmd[: MAX_MESSAGE_LENGTH // 4 - 1],
                disable_notification=True,
                quote=True,
            )
            os.remove("eval.txt")
    else:
        await reply_to_.reply_text(final_output, quote=True)
    await status_message.delete()


async def aexec(code, client, message):
    indent = "    "
    print_output = io.StringIO()

    # Strip input and split into lines
    lines = [line.strip() for line in code.strip().split("\n") if line.strip()]
    
    # Generate function header
    header = (
        "async def __aexec(client, message, print_output):\n"
        f"{indent}import os\n"
        f"{indent}import requests\n"
        f"{indent}from pprint import pformat\n"
        f"{indent}neo = message\n"
        f"{indent}e = message = event = neo\n"
        f"{indent}r = reply = message.reply_to_message\n"
        f"{indent}chat = message.chat.id\n"
        f"{indent}c = client\n"
        f"{indent}to_photo = message.reply_photo\n"
        f"{indent}to_video = message.reply_video\n"
        f"{indent}def p(*args, **kwargs):\n"
        f"{indent*2}import builtins\n"
        f"{indent*2}sep = kwargs.get('sep', ' ')\n"
        f"{indent*2}end = kwargs.get('end', '\\n')\n"
        f"{indent*2}output = sep.join(pformat(arg) for arg in args) + end\n"
        f"{indent*2}print_output.write(output)\n"
        f"{indent*2}builtins.print(*args, **kwargs)\n"
        f"{indent}print = p\n"
        f"{indent}_result = None\n"
    )

    # Handle return line
    if lines and lines[-1].startswith("return "):
        # Convert 'return x' => '_result = x'
        return_expr = lines[-1][len("return "):]
        body = "\n".join(f"{indent}{line}" for line in lines[:-1])
        body += f"\n{indent}_result = {return_expr}"
    else:
        # Default: execute all lines and capture result of last line
        body = "\n".join(f"{indent}{line}" for line in lines[:-1]) if len(lines) > 1 else ""
        if lines:
            body += f"\n{indent}_result = {lines[-1]}"

    # Add return line to return both values
    return_line = f"\n{indent}return _result, print_output.getvalue()\n"

    full_code = header + body + return_line

    # Compile and execute the function definition
    exec(full_code)
    result, printed_output = await locals()["__aexec"](client, message, print_output)

    return {
        "return_value": result,
        "printed_output": printed_output
    }



# Add a command to view history
@Client.on_message(filters.command("ehis") & filters.user(ADMINS))
async def show_history(_, message):
    # Add numbering to each command and wrap in <code> tags
    formatted_history = "\n".join(f"<b>{i + 1}.</b> <code>{cmd}</code>" for i, cmd in enumerate(reversed(eval_history)))

    # Check if the message exceeds Telegram's character limit
    if len(formatted_history) > MAX_MESSAGE_LENGTH:
        # Send as a text file
        with io.BytesIO(str.encode(formatted_history)) as out_file:
            out_file.name = "eval_history.txt"
            await message.reply_document(
                document=out_file,
                caption="__Limit exceeded, so sending as file__",
                quote=True,
            )
            os.remove("eval_history.txt")
    else:
        # Send as a regular message
        await message.reply_text(f"<b>EVAL HISTORY:</b>\n{formatted_history}", quote=True)