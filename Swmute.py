# Deletes messages from certain users
# Copyright © 2022 https://t.me/nalinor
# Modified by @SwillWay — added mute reason

# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.

# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.

# You should have received a copy of the GNU General Public License
# along with this program.  If not, see <http://www.gnu.org/licenses/>.

# meta editor: @Nik4mnost
# scope: hikka_only
# scope: hikka_min 1.2.10

import logging
import re
import time
from typing import Any, List, Optional, Dict

from telethon import TelegramClient
from telethon.hints import Entity
from telethon.tl.custom import Message
from telethon.tl.functions.channels import JoinChannelRequest
from telethon.utils import get_peer_id

from .. import loader, security, utils

logger = logging.getLogger(__name__)

USER_ID_RE = re.compile(r"^(-100)?\d+$")


# pylint: disable=invalid-name
def s2time(string) -> int:
    """Parse time from text `string`"""
    r = {}  # results

    for time_type in ["mon", "w", "d", "h", "m", "s"]:
        try:
            r[time_type] = int(re.search(rf"(\d+)\s*{time_type}", string)[1])
        except TypeError:
            r[time_type] = 0

    return (
        r["mon"] * 86400 * 30
        + r["w"] * 86400 * 7
        + r["d"] * 86400
        + r["h"] * 3600
        + r["m"] * 60
        + r["s"]
    )


# pylint: disable=consider-using-f-string
def get_link(user: Entity) -> str:
    """Return permanent link to `user`"""
    return "<a href='tg://user?id={id}'>{name}</a>".format(
        id=user.id,
        name=utils.escape_html(
            user.first_name if hasattr(user, "first_name") else user.title
        ),
    )


def plural_number(n: int) -> str:
    """Pluralize number `n`"""
    return (
        "one"
        if n % 10 == 1 and n % 100 != 11
        else "few"
        if 2 <= n % 10 <= 4 and (n % 100 < 10 or n % 100 >= 20)
        else "many"
    )


# noinspection PyCallingNonCallable,PyAttributeOutsideInit
# pylint: disable=not-callable,attribute-defined-outside-init,invalid-name
@loader.tds
class SwmuteMod(loader.Module):
    """Deletes messages from certain users"""

    strings = {
        "name": "Swmute",
        "author": "@nalinormods",
        "not_group": "🚫 <b>This command is for groups only</b>",
        "muted": "🔇 <b>Swmuted {user} for {time}</b>\n📝 <b>Reason:</b> {reason}",
        "muted_forever": "🔇 <b>Swmuted {user} indefinitely</b>\n📝 <b>Reason:</b> {reason}",
        "unmuted": "🔉 <b>Removed swmute from {user}</b>",
        "not_muted": "🚫 <b>This user wasn't muted</b>",
        "invalid_user": "🚫 <b>Provided username/id {entity} is invalid</b>",
        "no_mute_target": "🧐 <b>Whom should I mute?</b>",
        "no_unmute_target": "🧐 <b>Whom should I unmute?</b>",
        "no_reason": "📝 <b>No reason provided</b>",
        "mutes_empty": "😔 <b>There's no mutes in this group</b>",
        "muted_users": "📃 <b>Swmuted users at the moment:</b>\n{names}",
        "cleared": "🧹 <b>Cleared mutes in this chat</b>",
        "cleared_all": "🧹 <b>Cleared all mutes</b>",
        "reason_updated": "📝 <b>Reason for {user} updated to:</b> {reason}",
        "deleted_with_reason": "🗑️ <b>Deleted message from {user}</b>\n📝 <b>Reason:</b> {reason}",
        "s_one": "second",
        "s_few": "seconds",
        "s_many": "seconds",
        "m_one": "minute",
        "m_few": "minutes",
        "m_many": "minutes",
        "h_one": "hour",
        "h_few": "hours",
        "h_many": "hours",
        "d_one": "day",
        "d_few": "days",
        "d_many": "days",
    }

    strings_ru = {
        "_cls_doc": "Удаляет сообщения от выбранных пользователей",
        "_cmd_doc_swmute": "<reply/username/id> <время> <причина> — Добавить пользователя в список swmute",
        "_cmd_doc_swunmute": "<reply/username/id> — Удалить пользователя из списка swmute",
        "_cmd_doc_swmutelist": "Получить пользователей в списке swmute",
        "_cmd_doc_swmuteclear": "<all> — Удалить всех пользователей из списка swmute в этом/всех чатах",
        "_cmd_doc_swmutereason": "<reply/username/id> <причина> — Изменить причину мута",
        "not_group": "🚫 <b>Эта команда предназначена только для групп</b>",
        "muted": "🔇 <b>{user} добавлен в список swmute на {time}</b>\n📝 <b>Причина:</b> {reason}",
        "muted_forever": "🔇 <b>{user} добавлен в список swmute навсегда</b>\n📝 <b>Причина:</b> {reason}",
        "unmuted": "🔉 <b>{user} удалён из списка swmute</b>",
        "not_muted": "🚫 <b>Этот пользователь не был в муте</b>",
        "invalid_user": "🚫 <b>Предоставленный юзернейм/айди {entity} некорректный</b>",
        "no_mute_target": "🧐 <b>Кого я должен замутить?</b>",
        "no_unmute_target": "🧐 <b>Кого я должен размутить?</b>",
        "no_reason": "📝 <b>Причина не указана</b>",
        "mutes_empty": "😔 <b>В этой группе никто не в муте</b>",
        "muted_users": "📃 <b>Пользователи в списке swmute:</b>\n{names}",
        "cleared": "🧹 <b>Муты в этой группе очищены</b>",
        "cleared_all": "🧹 <b>Все муты очищены</b>",
        "reason_updated": "📝 <b>Причина для {user} изменена на:</b> {reason}",
        "deleted_with_reason": "🗑️ <b>Удалено сообщение от {user}</b>\n📝 <b>Причина:</b> {reason}",
        "s_one": "секунда",
        "s_few": "секунды",
        "s_many": "секунд",
        "m_one": "минута",
        "m_few": "минуты",
        "m_many": "минут",
        "h_one": "час",
        "h_few": "часа",
        "h_many": "часов",
        "d_one": "день",
        "d_few": "дня",
        "d_many": "дней",
    }

    async def client_ready(self, client: TelegramClient, db):
        """client_ready hook"""
        self.client = client
        self.db = db

        try:
            await client(JoinChannelRequest(channel=self.strings("author")))
        except Exception:
            pass

        self.cleanup()

    def get(self, key: str, default: Any = None):
        """Get value from database"""
        return self.db.get(self.strings("name"), key, default)

    def set(self, key: str, value: Any):
        """Set value in database"""
        return self.db.set(self.strings("name"), key, value)

    def format_time(self, seconds: int, max_words: int = None) -> str:
        """Format time to human-readable variant"""
        words = []
        time_dict = {
            "d": seconds // 86400,
            "h": seconds % 86400 // 3600,
            "m": seconds % 3600 // 60,
            "s": seconds % 60,
        }

        for time_type, count in time_dict.items():
            if max_words and len(words) >= max_words:
                break

            if count != 0:
                words.append(
                    f"{count} {self.strings(time_type + '_' + plural_number(count))}"
                )

        return " ".join(words)

    def mute(self, chat_id: int, user_id: int, until_time: int = 0, reason: str = None):
        """Add user to mute list with reason"""
        chat_id = str(chat_id)
        user_id = str(user_id)

        mutes = self.get("mutes", {})
        mutes.setdefault(chat_id, {})
        mutes[chat_id][user_id] = {
            "until": until_time,
            "reason": reason or self.strings("no_reason")
        }
        self.set("mutes", mutes)

        logger.debug("Muted user %s in chat %s with reason: %s", user_id, chat_id, reason)

    def unmute(self, chat_id: int, user_id: int):
        """Remove user from mute list"""
        chat_id = str(chat_id)
        user_id = str(user_id)

        mutes = self.get("mutes", {})
        if chat_id in mutes and user_id in mutes[chat_id]:
            mutes[chat_id].pop(user_id)
        self.set("mutes", mutes)

        logger.debug("Unmuted user %s in chat %s", user_id, chat_id)

    def get_mutes(self, chat_id: int) -> List[int]:
        """Get current mutes for specified chat"""
        mutes_list = []
        for user_id, mute_data in self.get("mutes", {}).get(str(chat_id), {}).items():
            # Check for old int format safely
            until = mute_data if isinstance(mute_data, int) else mute_data.get("until", 0)
            if until > time.time() or until == 0:
                mutes_list.append(int(user_id))
        return mutes_list

    def get_mute_data(self, chat_id: int, user_id: int) -> Optional[Dict]:
        """Get mute data (until_time, reason) for user"""
        data = self.get("mutes", {}).get(str(chat_id), {}).get(str(user_id))
        # Handle legacy int storage
        if isinstance(data, int):
            return {"until": data, "reason": self.strings("no_reason")}
        return data

    def get_mute_reason(self, chat_id: int, user_id: int) -> str:
        """Get mute reason for user"""
        mute_data = self.get_mute_data(chat_id, user_id)
        return mute_data.get("reason", self.strings("no_reason")) if mute_data else None

    def get_mute_time(self, chat_id: int, user_id: int) -> int:
        """Get mute expiration timestamp"""
        mute_data = self.get_mute_data(chat_id, user_id)
        return mute_data.get("until", 0) if mute_data else 0

    def update_mute_reason(self, chat_id: int, user_id: int, reason: str):
        """Update mute reason for user"""
        chat_id = str(chat_id)
        user_id = str(user_id)

        mutes = self.get("mutes", {})
        if chat_id in mutes and user_id in mutes[chat_id]:
            mute_data = mutes[chat_id][user_id]
            # Convert to dict if it's legacy data
            if isinstance(mute_data, int):
                mutes[chat_id][user_id] = {"until": mute_data, "reason": reason}
            else:
                mutes[chat_id][user_id]["reason"] = reason
            
            self.set("mutes", mutes)
            logger.debug("Updated reason for user %s in chat %s: %s", user_id, chat_id, reason)
            return True
        return False

    def cleanup(self):
        """Cleanup expired mutes and migrate old format data"""
        mutes = {}

        for chat_id, chat_mutes in self.get("mutes", {}).items():
            new_chat_mutes = {}
            for user_id, mute_data in chat_mutes.items():
                # Handle old format where mute_data was just an int
                if isinstance(mute_data, int):
                    mute_data = {
                        "until": mute_data,
                        "reason": self.strings("no_reason")
                    }

                until = mute_data.get("until", 0)
                if until == 0 or until > time.time():
                    new_chat_mutes[user_id] = mute_data
                    
            if new_chat_mutes:
                mutes[chat_id] = new_chat_mutes

        self.set("mutes", mutes)

    def clear_mutes(self, chat_id: int = None):
        """Clear all mutes for given or all chats"""
        if chat_id:
            mutes = self.get("mutes", {})
            mutes.pop(str(chat_id), None)
            self.set("mutes", mutes)
        else:
            self.set("mutes", {})

    async def swmutecmd(self, message: Message):
        """<reply/username/id> <time> <reason> — Add user to swmute list"""
        if not message.is_group:
            return await utils.answer(message, self.strings("not_group"))

        args = utils.get_args(message)
        reply = await message.get_reply_message()

        if reply and reply.sender_id:
            user_id = reply.sender_id
            user = await self.client.get_entity(reply.sender_id)
            string_time = args[0] if args else None
            reason = " ".join(args[1:]) if len(args) > 1 else None
        elif args:
            try:
                user = await self.client.get_entity(
                    int(args[0]) if USER_ID_RE.match(args[0]) else args[0]
                )
                user_id = get_peer_id(user)
            except ValueError:
                return await utils.answer(message, self.strings("no_mute_target"))
            string_time = args[1] if len(args) > 1 else None
            reason = " ".join(args[2:]) if len(args) > 2 else None
        else:
            return await utils.answer(message, self.strings("no_mute_target"))

        if string_time and string_time != "0":
            if mute_seconds := s2time(string_time):
                self.mute(
                    message.chat_id,
                    user_id,
                    int(time.time() + mute_seconds),
                    reason
                )
                return await utils.answer(
                    message,
                    self.strings("muted").format(
                        time=self.format_time(mute_seconds),
                        user=get_link(user),
                        reason=reason or self.strings("no_reason")
                    ),
                )

        self.mute(message.chat_id, user_id, 0, reason)
        await utils.answer(
            message,
            self.strings("muted_forever").format(
                user=get_link(user),
                reason=reason or self.strings("no_reason")
            )
        )

    async def swunmutecmd(self, message: Message):
        """<reply/username/id> — Remove swmute from user"""
        if not message.is_group:
            return await utils.answer(message, self.strings("not_group"))

        args = utils.get_args(message)
        reply = await message.get_reply_message()

        if reply and reply.sender_id:
            user_id = reply.sender_id
            user = await self.client.get_entity(reply.sender_id)
        elif args:
            try:
                user = await self.client.get_entity(
                    int(args[0]) if USER_ID_RE.match(args[0]) else args[0]
                )
                user_id = get_peer_id(user)
            except ValueError:
                return await utils.answer(message, self.strings("no_unmute_target"))
        else:
            return await utils.answer(message, self.strings("no_unmute_target"))

        if self.get_mute_data(message.chat_id, user_id) is None:
            return await utils.answer(message, self.strings("not_muted"))

        self.unmute(message.chat_id, user_id)
        await utils.answer(message, self.strings("unmuted").format(user=get_link(user)))

    async def swmutereasoncmd(self, message: Message):
        """<reply/username/id> <reason> — Change mute reason"""
        if not message.is_group:
            return await utils.answer(message, self.strings("not_group"))

        args = utils.get_args(message)
        reply = await message.get_reply_message()

        if reply and reply.sender_id:
            user_id = reply.sender_id
            user = await self.client.get_entity(reply.sender_id)
            reason = " ".join(args) if args else None
        elif args:
            try:
                user = await self.client.get_entity(
                    int(args[0]) if USER_ID_RE.match(args[0]) else args[0]
                )
                user_id = get_peer_id(user)
                reason = " ".join(args[1:]) if len(args) > 1 else None
            except ValueError:
                return await utils.answer(message, self.strings("invalid_user").format(entity=args[0]))
        else:
            return await utils.answer(message, self.strings("no_mute_target"))

        if not reason:
            return await utils.answer(message, "📝 <b>Укажи новую причину!</b>")

        if self.update_mute_reason(message.chat_id, user_id, reason):
            await utils.answer(
                message,
                self.strings("reason_updated").format(
                    user=get_link(user),
                    reason=reason
                )
            )
        else:
            await utils.answer(message, self.strings("not_muted"))

    async def swmutelistcmd(self, message: Message):
        """Get list of swmuted users"""
        if not message.is_group:
            return await utils.answer(message, self.strings("not_group"))

        mutes = self.get_mutes(message.chat_id)
        if not mutes:
            return await utils.answer(message, self.strings("mutes_empty"))

        self.cleanup()

        muted_users = []
        for mute_id in mutes:
            text = "• "

            try:
                text += (
                    f"<i>{get_link(await self.client.get_entity(mute_id))}</i> "
                    f"(<code>{mute_id}</code>)"
                )
            except ValueError:
                text += f"<code>{mute_id}</code>"

            # Добавляем причину
            reason = self.get_mute_reason(message.chat_id, mute_id)
            if reason:
                text += f"\n  📝 <i>{reason}</i>"

            # Добавляем время
            if until_ts := self.get_mute_time(message.chat_id, mute_id):
                time_formatted = self.format_time(
                    int(until_ts - time.time()),
                    max_words=2,
                )
                text += f"\n  ⏳ <b>({time_formatted} left)</b>"

            muted_users.append(text)

        await utils.answer(
            message, self.strings("muted_users").format(names="\n".join(muted_users))
        )

    async def swmuteclearcmd(self, message: Message):
        """<all> — Clear all swmutes in this chat/in all chats"""
        if "all" in utils.get_args_raw(
            message
        ) and await self.allmodules.check_security(
            message, security.OWNER | security.SUDO
        ):
            self.clear_mutes()
            await utils.answer(message, self.strings("cleared_all"))
        else:
            self.clear_mutes(message.chat_id)
            await utils.answer(message, self.strings("cleared"))

    async def watcher(self, message: Message):
        """Handles incoming messages"""
        if (
            isinstance(message, Message)
            and not message.out
            and message.is_group
            and message.sender_id in self.get_mutes(message.chat_id)
        ):
            await message.delete()
            reason = self.get_mute_reason(message.chat_id, message.sender_id)
            logger.debug(
                "Deleted message from user %s in chat %s. Reason: %s",
                message.sender_id,
                message.chat_id,
                reason
            )

