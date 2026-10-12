import asyncio
import os

from aiogram import Bot, Dispatcher
from dotenv import load_dotenv

from tg_bot.handlers import router
from checker.checker import AvailabilityChecker
from database.database import init_db


load_dotenv()


CHECK_INTERVAL = 15 * 60


async def main():
    bot_token = os.getenv("BOT_TOKEN")

    if not bot_token:
        raise RuntimeError(
            "BOT_TOKEN is not set"
        )

    init_db()

    bot = Bot(token=bot_token)

    dp = Dispatcher()

    dp.include_router(router)

    checker = AvailabilityChecker(bot)

    try:
        checker.client.open()

        await asyncio.gather(
            dp.start_polling(bot),
            check_loop(checker),
        )

    finally:
        checker.client.close()

        await bot.session.close()


async def check_loop(
    checker: AvailabilityChecker,
):
    while True:
        try:
            await checker.check()

        except Exception as exc:
            print(
                f"[CHECK] ERROR: {exc}",
                flush=True,
            )

        await asyncio.sleep(CHECK_INTERVAL)


if __name__ == "__main__":
    asyncio.run(main())