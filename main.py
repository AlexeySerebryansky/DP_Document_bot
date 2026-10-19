import asyncio
import os

from aiogram import Bot, Dispatcher
from dotenv import load_dotenv

from tg_bot.handlers import router
from checker.checker import AvailabilityChecker
from database.databases import init_db

load_dotenv()

CHECK_INTERVAL_MINUTES = int(
    os.getenv("CHECK_INTERVAL_MINUTES", "10")
)

CHECK_INTERVAL = CHECK_INTERVAL_MINUTES * 60


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
        await asyncio.gather(
            dp.start_polling(bot),
            check_loop(checker),
        )

    finally:
        try:
            checker.client.close()
        except Exception as exc:
            print(
                f"[CLIENT] CLOSE ERROR: {exc}",
                flush=True,
            )

        await bot.session.close()


async def check_loop(checker: AvailabilityChecker):
    while True:
        try:
            print("[CHECK] Opening GoLogin profile...", flush=True)

            await asyncio.to_thread(checker.client.open)

            print("[CHECK] Profile opened. Running check...", flush=True)

            await checker.check()

            print("[CHECK] Check completed successfully.", flush=True)

        except asyncio.CancelledError:
            raise

        except Exception as exc:
            print(f"[CHECK] ERROR: {exc}", flush=True)

        finally:
            try:
                await asyncio.to_thread(checker.client.close)
            except Exception as exc:
                print(
                    f"[CHECK] Failed to close client: {exc}",
                    flush=True,
                )

        print(
            f"[CHECK] Sleeping for {CHECK_INTERVAL_MINUTES} minutes...",
            flush=True,
        )

        await asyncio.sleep(CHECK_INTERVAL)


if __name__ == "__main__":
    print("Starting bot...")
    asyncio.run(main())
