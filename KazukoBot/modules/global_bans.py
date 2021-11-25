import html
import time
from datetime import datetime
from io import BytesIO

from telegram import ParseMode, Update
from telegram.error import BadRequest, TelegramError, Unauthorized
from telegram.ext import (
    CallbackContext,
    CommandHandler,
    Filters,
    MessageHandler,
    run_async,
)
from telegram.utils.helpers import mention_html

import KazukoBot.modules.sql.global_bans_sql as sql
from KazukoBot.modules.sql.users_sql import get_user_com_chats
from KazukoBot import (
    DEV_USERS,
    EVENT_LOGS,
    OWNER_ID,
    STRICT_GBAN,
    DRAGONS,
    SUPPORT_CHAT,
    SPAMWATCH_SUPPORT_CHAT,
    DEMONS,
    TIGERS,
    WOLVES,
    sw,
    dispatcher,
)
from KazukoBot.modules.helper_funcs.chat_status import (
    is_user_admin,
    support_plus,
    user_admin,
)
from KazukoBot.modules.helper_funcs.extraction import (
    extract_user,
    extract_user_and_text,
)
from KazukoBot.modules.helper_funcs.misc import send_to_list

GBAN_ENFORCE_GROUP = 6

GBAN_ERRORS = {
    "User is an administrator of the chat",
    "Chat not found",
    "Not enough rights to restrict/unrestrict chat member",
    "User_not_participant",
    "Peer_id_invalid",
    "Group chat was deactivated",
    "Need to be inviter of a user to kick it from a basic group",
    "Chat_admin_required",
    "Only the creator of a basic group can kick group administrators",
    "Channel_private",
    "Not in the chat",
    "Can't remove chat owner",
}

UNGBAN_ERRORS = {
    "User is an administrator of the chat",
    "Chat not found",
    "Not enough rights to restrict/unrestrict chat member",
    "User_not_participant",
    "Method is available for supergroup and channel chats only",
    "Not in the chat",
    "Channel_private",
    "Chat_admin_required",
    "Peer_id_invalid",
    "User not found",
}


@run_async
@support_plus
def gban(update, context):
    message = update.effective_message
    chat = update.effective_chat
    args = context.args
    user_id, reason = extract_user_and_text(message, args)

    if not user_id:
        message.reply_text("You don't seem to be referring to a user.")
        return

    if user_id == OWNER_ID:
        message.reply_text("Nice try -_- but I'm never gonna gban him.")
        return

    if int(user_id) in DEV_USERS:
        message.reply_text(
            "I spy, with my little eye... a sudo user war! Why are you guys turning on each other?"
        )
        return

    if int(user_id) in SUPPORT_USERS:
        message.reply_text(
            "OOOH someone's trying to gban a support user! *grabs popcorn*"
        )
        return

    if user_id in (777000, 1087968824):
        message.reply_text("How can i ban someone that i don't know who is it.")
        return

    if user_id == context.bot.id:
        message.reply_text("-_- So funny, lets gban myself why don't I? Nice try.")
        return

    if not reason:
        message.reply_text("Please Specified a reason. I won't allow a bare gban :)")
        return

    try:
        user_chat = context.bot.get_chat(user_id)
    except BadRequest as excp:
        message.reply_text(excp.message)
        return

    if user_chat.type != "private":
        message.reply_text("That's not a user!")
        return

    if user_chat.first_name == "":
        message.reply_text("This is a deleted account! no point to gban them...")
        return

    if sql.is_user_gbanned(user_id):
        if not reason:
            message.reply_text(
                "This user is already gbanned; I'd change the reason, but you haven't given me one..."
            )
            return

        old_reason = sql.update_gban_reason(
            user_id, user_chat.username or user_chat.first_name, reason
        )
        user_id, new_reason = extract_user_and_text(message, args)

        if old_reason:
            banner = update.effective_user
            bannerid = banner.id
            bannername = banner.first_name
            new_reason = (
                f"{new_reason} // GBanned by {bannername} banner id: {bannerid}"
            )

            context.bot.sendMessage(
                MESSAGE_DUMP,
                "<b>Global Ban Reason Update</b>"
                "\n<b>Sudo Admin:</b> {}"
                "\n<b>User:</b> {}"
                "\n<b>ID:</b> <code>{}</code>"
                "\n<b>Previous Reason:</b> {}"
                "\n<b>New Reason:</b> {}".format(
                    mention_html(banner.id, banner.first_name),
                    mention_html(
                        user_chat.id, user_chat.first_name or "Deleted Account"
                    ),
                    user_chat.id,
                    old_reason,
                    new_reason,
                ),
                parse_mode=ParseMode.HTML,
            )

            message.reply_text(
                "This user is already gbanned, for the following reason:\n"
                "<code>{}</code>\n"
                "I've gone and updated it with your new reason!".format(
                    html.escape(old_reason)
                ),
                parse_mode=ParseMode.HTML,
            )

        else:
            message.reply_text(
                "This user is already gbanned, but had no reason set; I've gone and updated it!"
            )

        return

    message.reply_text(
        f"<b>Beginning of Global Ban for</b> {mention_html(user_chat.id, user_chat.first_name)}"
        f"\n<b>With ID</b>: <code>{user_chat.id}</code>"
        f"\n<b>Reason</b>: <code>{reason or 'No reason given'}</code>",
        parse_mode=ParseMode.HTML,
    )

    banner = update.effective_user
    bannerid = banner.id
    bannername = banner.first_name
    reason = f"{reason} // GBanned by {bannername} banner id: {bannerid}"

    context.bot.sendMessage(
        MESSAGE_DUMP,
        "<b>New Global Ban</b>"
        "\n#GBAN"
        "\n<b>Status:</b> <code>Enforcing</code>"
        "\n<b>Sudo Admin:</b> {}"
        "\n<b>User:</b> {}"
        "\n<b>ID:</b> <code>{}</code>"
        "\n<b>Reason:</b> {}".format(
            mention_html(banner.id, banner.first_name),
            mention_html(user_chat.id, user_chat.first_name),
            user_chat.id,
            reason or "No reason given",
        ),
        parse_mode=ParseMode.HTML,
    )

    try:
        context.bot.kick_chat_member(chat.id, user_chat.id)
    except BadRequest:
        pass
    sql.gban_user(user_id, user_chat.username or user_chat.first_name, reason)


@run_async
@support_plus
def ungban(update: Update, context: CallbackContext):
    bot, args = context.bot, context.args
    message = update.effective_message
    user = update.effective_user
    chat = update.effective_chat
    log_message = ""

    user_id = extract_user(message, args)

    if not user_id:
        message.reply_text(
            "You don't seem to be referring to a user or the ID specified is incorrect..",
        )
        return

    user_chat = bot.get_chat(user_id)
    if user_chat.type != "private":
        message.reply_text("That's not a user!")
        return

    if not sql.is_user_gbanned(user_id):
        message.reply_text("This user is not gbanned!")
        return

    message.reply_text(f"I'll give {user_chat.first_name} a second chance, globally.")

    start_time = time.time()
    datetime_fmt = "%Y-%m-%dT%H:%M"
    current_time = datetime.utcnow().strftime(datetime_fmt)

    if chat.type != "private":
        chat_origin = f"<b>{html.escape(chat.title)} ({chat.id})</b>\n"
    else:
        chat_origin = f"<b>{chat.id}</b>\n"

    log_message = (
        f"#UNGBANNED\n"
        f"<b>Originated from:</b> <code>{chat_origin}</code>\n"
        f"<b>Admin:</b> {mention_html(user.id, user.first_name)}\n"
        f"<b>Unbanned User:</b> {mention_html(user_chat.id, user_chat.first_name)}\n"
        f"<b>Unbanned User ID:</b> <code>{user_chat.id}</code>\n"
        f"<b>Event Stamp:</b> <code>{current_time}</code>"
    )

    if EVENT_LOGS:
        try:
            log = bot.send_message(EVENT_LOGS, log_message, parse_mode=ParseMode.HTML)
        except BadRequest as excp:
            log = bot.send_message(
                EVENT_LOGS,
                log_message
                + "\n\nFormatting has been disabled due to an unexpected error.",
            )
    else:
        send_to_list(bot, DRAGONS + DEMONS, log_message, html=True)

    chats = get_user_com_chats(user_id)
    ungbanned_chats = 0

    for chat in chats:
        chat_id = int(chat)

        # Check if this group has disabled gbans
        if not sql.does_chat_gban(chat_id):
            continue

        try:
            member = bot.get_chat_member(chat_id, user_id)
            if member.status == "kicked":
                bot.unban_chat_member(chat_id, user_id)
                ungbanned_chats += 1

        except BadRequest as excp:
            if excp.message in UNGBAN_ERRORS:
                pass
            else:
                message.reply_text(f"Could not un-gban due to: {excp.message}")
                if EVENT_LOGS:
                    bot.send_message(
                        EVENT_LOGS,
                        f"Could not un-gban due to: {excp.message}",
                        parse_mode=ParseMode.HTML,
                    )
                else:
                    bot.send_message(
                        OWNER_ID, f"Could not un-gban due to: {excp.message}",
                    )
                return
        except TelegramError:
            pass

    sql.ungban_user(user_id)

    if EVENT_LOGS:
        log.edit_text(
            log_message + f"\n<b>Chats affected:</b> {ungbanned_chats}",
            parse_mode=ParseMode.HTML,
        )
    else:
        send_to_list(bot, DRAGONS + DEMONS, "un-gban complete!")

    end_time = time.time()
    ungban_time = round((end_time - start_time), 2)

    if ungban_time > 60:
        ungban_time = round((ungban_time / 60), 2)
        message.reply_text(f"Person has been un-gbanned. Took {ungban_time} min")
    else:
        message.reply_text(f"Person has been un-gbanned. Took {ungban_time} sec")


@run_async
@support_plus
def gbanlist(update: Update, context: CallbackContext):
    banned_users = sql.get_gban_list()

    if not banned_users:
        update.effective_message.reply_text(
            "There aren't any gbanned users! You're kinder than I expected...",
        )
        return

    banfile = "Screw these guys.\n"
    for user in banned_users:
        banfile += f"[x] {user['name']} - {user['user_id']}\n"
        if user["reason"]:
            banfile += f"Reason: {user['reason']}\n"

    with BytesIO(str.encode(banfile)) as output:
        output.name = "gbanlist.txt"
        update.effective_message.reply_document(
            document=output,
            filename="gbanlist.txt",
            caption="Here is the list of currently gbanned users.",
        )


def check_and_ban(update, user_id, should_message=True):

    if user_id in TIGERS or user_id in WOLVES:
        sw_ban = None
    else:
        try:
            sw_ban = sw.get_ban(int(user_id))
        except:
            sw_ban = None

    if sw_ban:
        update.effective_chat.kick_member(user_id)
        if should_message:
            update.effective_message.reply_text(
                f"<b>Alert</b>: this user is globally banned.\n"
                f"<code>*bans them from here*</code>.\n"
                f"<b>Appeal chat</b>: {SPAMWATCH_SUPPORT_CHAT}\n"
                f"<b>User ID</b>: <code>{sw_ban.id}</code>\n"
                f"<b>Ban Reason</b>: <code>{html.escape(sw_ban.reason)}</code>",
                parse_mode=ParseMode.HTML,
            )
        return

    if sql.is_user_gbanned(user_id):
        update.effective_chat.kick_member(user_id)
        if should_message:
            text = (
                f"<b>Alert</b>: this user is globally banned.\n"
                f"<code>*bans them from here*</code>.\n"
                f"<b>Appeal chat</b>: @{SUPPORT_CHAT}\n"
                f"<b>User ID</b>: <code>{user_id}</code>"
            )
            user = sql.get_gbanned_user(user_id)
            if user.reason:
                text += f"\n<b>Ban Reason:</b> <code>{html.escape(user.reason)}</code>"
            update.effective_message.reply_text(text, parse_mode=ParseMode.HTML)


@run_async
def enforce_gban(update: Update, context: CallbackContext):
    # Not using @restrict handler to avoid spamming - just ignore if cant gban.
    bot = context.bot
    try:
        restrict_permission = update.effective_chat.get_member(
            bot.id,
        ).can_restrict_members
    except Unauthorized:
        return
    if sql.does_chat_gban(update.effective_chat.id) and restrict_permission:
        user = update.effective_user
        chat = update.effective_chat
        msg = update.effective_message

        if user and not is_user_admin(chat, user.id):
            check_and_ban(update, user.id)
            return

        if msg.new_chat_members:
            new_members = update.effective_message.new_chat_members
            for mem in new_members:
                check_and_ban(update, mem.id)

        if msg.reply_to_message:
            user = msg.reply_to_message.from_user
            if user and not is_user_admin(chat, user.id):
                check_and_ban(update, user.id, should_message=False)


@run_async
@user_admin
def gbanstat(update, context):
    args = context.args
    if len(args) > 0:
        if args[0].lower() in ["on", "yes"]:
            sql.enable_gbans(update.effective_chat.id)
            update.effective_message.reply_text(
                "I've enabled Spam Sheild in this group. This will help protect you "
                "from spammers, unsavoury characters, and the biggest trolls."
            )
        elif args[0].lower() in ["off", "no"]:
            sql.disable_gbans(update.effective_chat.id)
            update.effective_message.reply_text(
                "I've disabled Spam sheild in this group. GBans wont affect your users "
                "anymore. You'll be less protected from any trolls and spammers "
                "though!"
            )
    else:
        update.effective_message.reply_text(
            "Give me some arguments to choose a setting! on/off, yes/no!\n\n"
            "Your current setting is: {}\n"
            "When True, any gbans that happen will also happen in your group. "
            "When False, they won't, leaving you at the possible mercy of "
            "spammers.".format(sql.does_chat_gban(update.effective_chat.id))
        )


def __stats__():
    return "× {} gbanned users.".format(sql.num_gbanned_users())


def __user_info__(user_id):
    is_gbanned = sql.is_user_gbanned(user_id)

    text = "<b>Globally banned</b>: {}"

    if int(user_id) in DEV_USERS + SUPPORT_USERS:
        return ""
    if is_gbanned:
        text = text.format("Yes")
        user = sql.get_gbanned_user(user_id)
        if user.reason:
            text += "\nReason: {}".format(html.escape(user.reason))
            text += "\n\nAppeal at @KazukoSupportChat if you think it's invalid."
    else:
        text = text.format("No")
    return text


def __migrate__(old_chat_id, new_chat_id):
    sql.migrate_chat(old_chat_id, new_chat_id)


def __chat_settings__(chat_id, user_id):
    return "This chat is enforcing *gbans*: `{}`.".format(sql.does_chat_gban(chat_id))


__help__ = f"""
*Admins only:*
 • `/antispam <on/off/yes/no>`*:* Will toggle our antispam tech or return your current settings.
Anti-Spam, used by bot devs to ban spammers across all groups. This helps protect \
you and your groups by removing spam flooders as quickly as possible.
*Note:* Users can appeal gbans or report spammers at @{SUPPORT_CHAT}
This also integrates @Spamwatch API to remove Spammers as much as possible from your chatroom!
*What is SpamWatch?*
SpamWatch maintains a large constantly updated ban-list of spambots, trolls, bitcoin spammers and unsavoury characters[.](https://telegra.ph/file/f584b643c6f4be0b1de53.jpg)
Constantly help banning spammers off from your group automatically So, you wont have to worry about spammers storming your group.
*Note:* Users can appeal spamwatch bans at @SpamwatchSupport
"""

GBAN_HANDLER = CommandHandler("gban", gban)
UNGBAN_HANDLER = CommandHandler("ungban", ungban)
GBAN_LIST = CommandHandler("gbanlist", gbanlist)

GBAN_STATUS = CommandHandler("antispam", gbanstat, filters=Filters.group)

GBAN_ENFORCER = MessageHandler(Filters.all & Filters.group, enforce_gban)

dispatcher.add_handler(GBAN_HANDLER)
dispatcher.add_handler(UNGBAN_HANDLER)
dispatcher.add_handler(GBAN_LIST)
dispatcher.add_handler(GBAN_STATUS)

__mod_name__ = "Anti-Spam"
__handlers__ = [GBAN_HANDLER, UNGBAN_HANDLER, GBAN_LIST, GBAN_STATUS]

if STRICT_GBAN:  # enforce GBANS if this is set
    dispatcher.add_handler(GBAN_ENFORCER, GBAN_ENFORCE_GROUP)
    __handlers__.append((GBAN_ENFORCER, GBAN_ENFORCE_GROUP))
