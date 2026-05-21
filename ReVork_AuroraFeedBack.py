# -*- coding: utf-8 -*-
# AuroraFeedBack RU+ — версия с ссылкой на профиль и цветными кнопками (через emoji)

__version__ = (1, 2, 1)

from aiogram.types import Message as AiogramMessage
from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup
from html import escape

from .. import loader, utils
from ..inline.types import InlineCall


@loader.tds
class AuroraFeedBackMod(loader.Module):
    "Фидбэк‑бот с улучшенными кнопками"

    strings = {
        "name": "AuroraFeedback",
        "waiting_answer": "<tg-emoji emoji-id=5296482716567495148>⌛️</tg-emoji> Напишите ответ пользователю",
        "flink": "Вот ссылка на моего feedback бота",
        "owner_answer": "<tg-emoji emoji-id=5296258510684712098>💬</tg-emoji> Ответ владельца",
        "successfully_send": "<tg-emoji emoji-id=5409029658794537988>✅</tg-emoji> Сообщение отправлено",
        "banned": "<tg-emoji emoji-id=5339428493992162714>🚫</tg-emoji> Вы были заблокированы в фидбеке",
        "user_unbanned": "🔓 Пользователь {user_id} разбанен",
        "user_not_banned": "❌ Пользователь {user_id} не был в бане",
        "invalid_user_id": "❌ Укажи корректный ID пользователя"
    }
    strings_ru = {
        "waiting_answer": "<tg-emoji emoji-id=5296482716567495148>⌛️</tg-emoji> Напишите ответ пользователю",
        "flink": "Вот ссылка на моего feedback бота",
        "owner_answer": "<tg-emoji emoji-id=5296258510684712098>💬</tg-emoji> Ответ владельца",
        "successfully_send": "<tg-emoji emoji-id=5409029658794537988>✅</tg-emoji> Сообщение отправлено",
        "banned": "<tg-emoji emoji-id=5339428493992162714>🚫</tg-emoji> Вы были заблокированы в фидбеке",
        "user_unbanned": "🔓 Пользователь {user_id} разбанен",
        "user_not_banned": "❌ Пользователь {user_id} не был в бане",
        "invalid_user_id": "❌ Укажи корректный ID пользователя"
    }

    def __init__(self):
        self.config = loader.ModuleConfig(
            loader.ConfigValue(
                "mode",
                True,
                lambda: "Включить / выключить feedback бота",
                validator=loader.validators.Boolean(),
            )
        )

    async def on_dlmod(self, client, db):
        self.db.set("AuroraFeedBackMod", "ban_list", [])

    async def client_ready(self, client, db):
        self._ban_list = self.db.get("AuroraFeedBackMod", "ban_list")
        self.tg_id = (await client.get_me()).id
        self.db.set("AuroraFeedBackMod", "state", "done")

    @loader.command()
    async def flink(self, message):
        "Получить ссылку на бота"
        slinkbot = f"{self.strings['flink']}: https://t.me/{self.inline.bot_username}?start=AuroraFeedBack"
        await utils.answer(message, slinkbot)

    @loader.command()
    async def unbanfeedback(self, message):
        "🔓 Разбанить пользователя в фидбеке. Использование: .unbanfeedback <user_id>"
        args = utils.get_args_raw(message).strip()
        
        if not args:
            return await utils.answer(message, self.strings["invalid_user_id"])
        
        try:
            user_id = int(args)
        except ValueError:
            return await utils.answer(message, self.strings["invalid_user_id"])
        
        if user_id in self._ban_list:
            self._ban_list.remove(user_id)
            self.db.set("AuroraFeedBackMod", "ban_list", self._ban_list)
            await utils.answer(message, self.strings["user_unbanned"].format(user_id=user_id))
        else:
            await utils.answer(message, self.strings["user_not_banned"].format(user_id=user_id))

    async def aiogram_watcher(self, message: AiogramMessage):

        if not self.config["mode"]:
            return

        if message.from_user.id in self.db.get("AuroraFeedBackMod", "ban_list"):
            await message.answer(self.strings["banned"])
            return

        if message.text == "/start AuroraFeedBack":
            if message.from_user.id == self.tg_id:
                return
            else:
                await message.answer("<tg-emoji emoji-id=5355277430120523169>👋</tg-emoji> Добро пожаловать! Напишите сообщение владельцу.")
                return

        # Ответ владельца
        if message.from_user.id == self.tg_id:
            state = self.db.get("AuroraFeedBackMod", "state")

            if state.startswith("waiting_"):
                to_id = int(state.split("_")[1])
                to_delete = self.db.get("AuroraFeedbackMod", "to_delete")

                await message.send_copy(to_id)

                await self.inline.bot.delete_message(
                    message.chat.id,
                    to_delete
                )

                await self.inline.bot.send_message(
                    self.tg_id,
                    self.strings["successfully_send"]
                )

                self.db.set("AuroraFeedBackMod", "state", "done")
                self.db.set("AuroraFeedbackMod", "to_delete", None)
                return

        user_id = message.from_user.id
        first_name = escape(message.from_user.first_name)

        custom_text = (
            f"📩 Новое сообщение от {first_name}:\n"
            f"UserID: <a href='tg://user?id={user_id}'>{user_id}</a>"
        )

        buttons = []

        if user_id != self.tg_id:
            buttons.append(
                [InlineKeyboardButton(text="Ответить", callback_data=f"reply_{user_id}", style="success")]
            )

        buttons.append(
            [InlineKeyboardButton(text="Забанить", callback_data=f"ban_{user_id}", style="danger")]
        )

        buttons.append(
            [InlineKeyboardButton(text="Удалить", callback_data="MessageDelete",)]
        )

        buttons.append(
            [InlineKeyboardButton(text="Открыть профиль", url=f"tg://user?id={user_id}", style="primary")]
        )

        reply_markup = InlineKeyboardMarkup(inline_keyboard=buttons)

        await message.send_copy(self.tg_id, reply_markup=reply_markup)

        await self.inline.bot.send_message(
            user_id, "✅ Сообщение отправлено владельцу"
        )

    async def feedback_callback_handler(self, call: InlineCall):

        if call.data == "MessageDelete":
            await self.inline.bot.delete_message(
                call.message.chat.id, call.message.message_id
            )
            return

        if call.data.startswith("ban_"):
            user_id = int(call.data.split("_")[1])

            if user_id not in self._ban_list:
                self._ban_list.append(user_id)

            self.db.set("AuroraFeedBackMod", "ban_list", self._ban_list)

            reply_markup = InlineKeyboardMarkup(
                inline_keyboard=[
                    [InlineKeyboardButton(text="🔓 Разбанить", callback_data=f"unban_{user_id}")]
                ]
            )

            await self.inline.bot.send_message(
                self.tg_id,
                f"🔴 Пользователь {user_id} забанен",
                reply_markup=reply_markup,
            )
            return

        if call.data.startswith("unban_"):
            user_id = int(call.data.split("_")[1])

            if user_id in self._ban_list:
                self._ban_list.remove(user_id)

            self.db.set("AuroraFeedBackMod", "ban_list", self._ban_list)

            reply_markup = InlineKeyboardMarkup(
                inline_keyboard=[
                    [InlineKeyboardButton(text="🔴 Забанить", callback_data=f"ban_{user_id}")]
                ]
            )

            await self.inline.bot.send_message(
                self.tg_id,
                f"🟢 Пользователь {user_id} разбанен",
                reply_markup=reply_markup,
            )
            return

        if call.data.startswith("reply_"):
            user_id = int(call.data.split("_")[1])

            self.db.set(
                "AuroraFeedBackMod",
                "state",
                f"waiting_{user_id}",
            )

            reply_markup = InlineKeyboardMarkup(
                inline_keyboard=[
                    [InlineKeyboardButton(text="❌ Отмена", callback_data="cancel_reply")]
                ]
            )

            wait_answer = await self.inline.bot.send_message(
                    self.tg_id,
                    self.strings["waiting_answer"],
                    reply_markup=reply_markup,
                )
            
            self.db.set("AuroraFeedbackMod", "to_delete", wait_answer.message_id)
            return

        if call.data == "cancel_reply":
            self.db.set("AuroraFeedBackMod", "state", "done")

            await self.inline.bot.delete_message(
                call.message.chat.id,
                call.message.message_id
            )
