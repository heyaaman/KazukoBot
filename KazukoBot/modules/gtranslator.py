from telegram.ext import CallbackContext, CommandHandler, run_async
from telegram import ParseMode, Update


from gpytranslate import SyncTranslator
from KazukoBot.modules.helper_funcs.misc import delete

from KazukoBot import dispatcher
from KazukoBot.modules.disable import DisableAbleCommandHandler


trans = SyncTranslator()

@run_async
def translate(update: Update, context: CallbackContext) -> None:
    bot = context.bot
    message = update.effective_message
    reply_msg = message.reply_to_message
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
    translation = trans(to_translate,
                        sourcelang=source, targetlang=dest)
    reply = f"<b>Translated from {source} to {dest}</b>:\n" \
        f"<code>{translation.text}</code>"

    bot.send_message(text=reply, chat_id=message.chat.id, parse_mode=ParseMode.HTML)


__help__="""
 • `/tts `*:* to create a an audio type message.
 *Example:* 
 •`/tts hello `*:* Creates an audio of hello
Reply to messages or write messages from other languages for translating into the intended language.
 • `/tr or /tl `(language code) as reply to a long message
*Example:* 
 •` /tr en`*:* translates something to english
 • `/tr hi-en`*:* translates hindi to english
*Language codes*
‣ Click [Languages](https://cloud.google.com/translate/docs/languages) to see the list of supported language codes!
"""

TRANSLATE_HANDLER = DisableAbleCommandHandler(["tr", "tl"], translate)

dispatcher.add_handler(TRANSLATE_HANDLER)

__mod_name__ = "Translator"
__command_list__ = ["tr", "tl"]
__handlers__ = [TRANSLATE_HANDLER]
