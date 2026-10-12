from database.database import get_connection


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

class AvailabilityRepository:

    @staticmethod
    def get_has_slots() -> bool:
        with get_connection() as connection:
            row = connection.execute(
                """
                SELECT has_slots
                FROM availability
                WHERE id = 1
                """
            ).fetchone()

        return bool(row["has_slots"])

    @staticmethod
    def set_has_slots(has_slots: bool) -> None:
        with get_connection() as connection:
            connection.execute(
                """
                UPDATE availability
                SET has_slots = ?,
                    updated_at = CURRENT_TIMESTAMP
                WHERE id = 1
                """,
                (int(has_slots),),
            )

            connection.commit()