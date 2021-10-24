from KazukoBot.modules.disable import DisableAbleCommandHandler, DisableAbleMessageHandler
from telegram.ext import CommandHandler, MessageHandler, CallbackQueryHandler, InlineQueryHandler
from telegram.ext.filters import BaseFilter
from KazukoBot import dispatcher as d, log
from KazukoBot import Optional, Union, List


    def inlinequery(self, pattern: Optional[str] = None, run_async: bool = True, pass_user_data: bool = True, pass_chat_data: bool = True, chat_types: List[str] = None):
        def _inlinequery(func):
            self._dispatcher.add_handler(InlineQueryHandler(pattern=pattern, callback=func, run_async=run_async, pass_user_data=pass_user_data, pass_chat_data=pass_chat_data, chat_types=chat_types))
            log.debug(f'[KIGINLINE] Loaded inlinequery handler with pattern {pattern} for function {func.__name__} | PASSES USER DATA: {pass_user_data} | PASSES CHAT DATA: {pass_chat_data} | CHAT TYPES: {chat_types}')
            return func
        return _inlinequery
