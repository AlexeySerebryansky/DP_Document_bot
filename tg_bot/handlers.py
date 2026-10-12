from aiogram import Router
from aiogram.filters import CommandStart
from aiogram.types import Message

from database.repository import UserRepository


router = Router()

user_repository = UserRepository()


@router.message(CommandStart())
async def start_handler(message: Message):
    user_repository.add_user(message.chat.id)

    await message.answer(
        "✅ Ви підписалися на повідомлення.\n\n"
        "я сповіщю вас, коли з'являться вільні місця."
    )