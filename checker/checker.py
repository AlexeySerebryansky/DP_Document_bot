from aiogram import Bot

from client.client import GoLoginClient
from database.repository import (
    UserRepository,
    CheckHistoryRepository
)


class AvailabilityChecker:

    def __init__(self, bot: Bot):
        self.bot = bot
        self.client = GoLoginClient()

        self.user_repository = UserRepository()
        self.history_repository = CheckHistoryRepository()

    async def check(self) -> None:
        try:
            days = self.client.check_days()

            has_slots = bool(days)

            self.history_repository.add(
                result="slots_found" if has_slots else "no_slots",
                days_count=len(days),
                status_code=200,
            )

            print(
                f"[CHECK] result="
                f"{'slots_found' if has_slots else 'no_slots'}, "
                f"days={len(days)}",
                flush=True,
            )

            if has_slots:
                await self._notify_users(days)

        except Exception as exc:
            self.history_repository.add(
                result="error",
            )

            print(
                f"[CHECK] Error: {exc}",
                flush=True,
            )


    async def _notify_users(self, days: list[dict]) -> None:
        users = self.user_repository.get_active_users()

        if not users:
            print(
                "[CHECK] No active users",
                flush=True,
            )
            return

        text = self._build_message(days)

        for chat_id in users:
            try:
                await self.bot.send_message(
                    chat_id=chat_id,
                    text=text,
                )

                print(
                    f"[TG] Notification sent to {chat_id}",
                    flush=True,
                )

            except Exception as exc:
                print(
                    f"[TG] Failed to notify {chat_id}: {exc}",
                    flush=True,
                )

    @staticmethod
    def _build_message(days: list[dict]) -> str:
        lines = [
            "🚨 З'явилися вільні місця!",
            "",
            f"доступніх дат: {len(days)}",
            "",
        ]

        for day in days:
            date = day.get("date")
            allowed = day.get("allowedJobCount")

            lines.append(
                f"📅 {date} — місць: {allowed}"
            )

        return "\n".join(lines)