from telethon import events, Button, custom
import re, os
from KazukoBot.events import register
from KazukoBot import telethn as tbot
from KazukoBot import telethn as tgbot
PHOTO = "https://telegra.ph/file/c93c5bbc5494c0188a541.jpg "
@register(pattern=("/alive"))
async def awake(event):
  Kazuko = event.sender.first_name
  Kazuko = "**♡ I,m Kazuko** \n\n"
  Kazuko += "**♡ I'm Working with awesome speed**\n\n"
  Kazuko += "**♡ Kazuko : first version**\n\n"
  Kazuko += "**♡ My Creator :** [heyaaman](t.me/heyaaman)\n\n"
  Kazuko += "**♡ Telethon Version : 1.23.0**\n\n"
  BUTTON = [[Button.url("Support", "https://t.me/KazukoSupportChat"), Button.url("Update", "https://t.me/phoenix_empire")]]
  await tbot.send_file(event.chat_id, PHOTO, caption=Kazuko,  buttons=BUTTON)
