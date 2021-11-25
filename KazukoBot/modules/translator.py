import json
import os

import requests
from gpytranslate import SyncTranslator
from telegram import (
    ParseMode,
    Update,
    ChatAction,
    InlineKeyboardButton,
    InlineKeyboardMarkup,
)
from telegram.ext import CallbackContext, run_async

from KazukoBot import dispatcher
from KazukoBot.modules.disable import DisableAbleCommandHandler
from KazukoBot.modules.helper_funcs.alternate import typing_action, send_action

trans = SyncTranslator()


@typing_action
def translate(update: Update, context: CallbackContext) -> None:
    bot = context.bot
    message = update.effective_message
    reply_msg = message.reply_to_message
    to_translate = []
    if not reply_msg:
        message.reply_text("Reply to a message to translate it!")
        return
    if reply_msg.caption:
        to_translate = reply_msg.caption
    elif reply_msg.text:
        to_translate = reply_msg.text
    try:
        args = message.text.split()[1].lower()
        if "//" in args:
            source = args.split("//")[0]
            dest = args.split("//")[1]
        else:
            source = trans.detect(to_translate)
            dest = args
    except IndexError:
        source = trans.detect(to_translate)
        dest = "en"
    translation = trans(to_translate, sourcelang=source, targetlang=dest)
    reply = (
        f"<b>Translated from {source} to {dest}</b>:\n"
        f"<code>{translation.text}</code>"
    )

    message.reply_text(reply, parse_mode=ParseMode.HTML)


@typing_action
def languages(update: Update, context: CallbackContext) -> None:
    update.effective_message.reply_text(
        "Click on the button below to see the list of supported language codes for Kazuko.",
        reply_markup=InlineKeyboardMarkup(
            [
                [
                    InlineKeyboardButton(
                        text="Language codes",
                        url="https://telegra.ph/Lang-Codes-03-19-3",
                    ),
                ],
            ],
            disable_web_page_preview=True,
        ),
    )


# Open API key
API_KEY = "6ae0c3a0-afdc-4532-a810-82ded0054236"
URL = "http://services.gingersoftware.com/Ginger/correct/json/GingerTheText"


@typing_action
def spellcheck(update, _):
    if update.effective_message.reply_to_message:
        msg = update.effective_message.reply_to_message

        params = dict(lang="US", clientVersion="2.0", apiKey=API_KEY, text=msg.text)

        res = requests.get(URL, params=params)
        changes = json.loads(res.text).get("LightGingerTheTextResult")
        curr_string = ""
        prev_end = 0

        for change in changes:
            start = change.get("From")
            end = change.get("To") + 1
            suggestions = change.get("Suggestions")
            if suggestions:
                sugg_str = suggestions[0].get("Text")  # should look at this list more
                curr_string += msg.text[prev_end:start] + sugg_str
                prev_end = end

        curr_string += msg.text[prev_end:]
        update.effective_message.reply_text(curr_string)
    else:
        update.effective_message.reply_text(
            "Reply to some message to get grammar corrected text!"
        )


__help__ = """
 /tr or /tl: To translate to your language, by default language is set to english,\
use `/tr <lang code>` for some other language!
 /langs: List of all language code to translates!
 /splcheck: As a reply to get grammar corrected text of gibberish message. 
"""

__mod_name__ = "Translate"

dispatcher.add_handler(
    DisableAbleCommandHandler(["tr", "tl"], translate, pass_args=True, run_async=True)
)
dispatcher.add_handler(
    DisableAbleCommandHandler(["langs", "lang"], languages, run_async=True)
)
dispatcher.add_handler(
    DisableAbleCommandHandler("splcheck", spellcheck, run_async=True)
)
