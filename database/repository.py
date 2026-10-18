from database.databases import get_connection


class UserRepository:

    @staticmethod
    def add_user(chat_id: int) -> None:
        with get_connection() as connection:
            connection.execute(
                """
                INSERT INTO users (chat_id)
                VALUES (?)
                ON CONFLICT(chat_id)
                DO UPDATE SET is_active = 1
                """,
                (chat_id,),
            )

            connection.commit()

    @staticmethod
    def deactivate_user(chat_id: int) -> None:
        with get_connection() as connection:
            connection.execute(
                """
                UPDATE users
                SET is_active = 0
                WHERE chat_id = ?
                """,
                (chat_id,),
            )

            connection.commit()

    @staticmethod
    def get_active_users() -> list[int]:
        with get_connection() as connection:
            rows = connection.execute(
                """
                SELECT chat_id
                FROM users
                WHERE is_active = 1
                """
            ).fetchall()

        return [row["chat_id"] for row in rows]

class CheckHistoryRepository:

    @staticmethod
    def add(
        *,
        result: str,
        days_count: int | None = None,
        status_code: int | None = None,
    ) -> None:
        with get_connection() as connection:
            connection.execute(
                """
                INSERT INTO check_events (
                    result,
                    days_count,
                    status_code
                )
                VALUES (?, ?, ?)
                """,
                (result, days_count, status_code),
            )

