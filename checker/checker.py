from aiogram import Bot

from client.client import GoLoginClient
from database.repository import (
    AvailabilityRepository,
    UserRepository,
)


class AvailabilityChecker:

    def __init__(self, bot: Bot):
        self.bot = bot

        self.client = GoLoginClient()

        self.user_repository = UserRepository()
        self.availability_repository = AvailabilityRepository()

    async def check(self) -> None:
        days = self.client.check_days()

        has_slots = bool(days)

        previous_state = (
            self.availability_repository.get_has_slots()
        )

        print(
            f"[CHECK] previous={previous_state}, "
            f"current={has_slots}, "
            f"days={len(days)}",
            flush=True,
        )

        self.availability_repository.set_has_slots(
            has_slots
        )

        # Мест нет
        if not has_slots:
            return

        if previous_state:
            return

        print(
            "[CHECK] 🚨 Slots appeared!",
            flush=True,
        )

        await self._notify_users(days)

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