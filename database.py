import os

import psycopg
from dotenv import load_dotenv


load_dotenv()


def get_connection():
    return psycopg.connect(
        host=os.getenv("DB_HOST"),
        port=os.getenv("DB_PORT"),
        dbname=os.getenv("DB_NAME"),
        user=os.getenv("DB_USER"),
        password=os.getenv("DB_PASSWORD"),
    )


def get_or_create_user(vk_id):
    with get_connection() as conn:
        with conn.cursor() as cursor:
            cursor.execute(
                """
                INSERT INTO users (vk_id)
                VALUES (%s)
                ON CONFLICT (vk_id)
                DO UPDATE SET vk_id = EXCLUDED.vk_id
                RETURNING id
                """,
                (vk_id,),
            )

            return cursor.fetchone()[0]


def add_note(vk_id, text):
    user_id = get_or_create_user(vk_id)

    with get_connection() as conn:
        with conn.cursor() as cursor:
            # Находим следующий номер заметки у этого пользователя
            cursor.execute(
                """
                SELECT COALESCE(MAX(note_number), 0) + 1
                FROM notes
                WHERE user_id = %s
                """,
                (user_id,),
            )

            note_number = cursor.fetchone()[0]

            cursor.execute(
                """
                INSERT INTO notes (user_id, note_number, text)
                VALUES (%s, %s, %s)
                RETURNING note_number
                """,
                (user_id, note_number, text),
            )

            return cursor.fetchone()[0]


def get_notes(vk_id):
    with get_connection() as conn:
        with conn.cursor() as cursor:
            cursor.execute(
                """
                SELECT notes.note_number, notes.text, notes.created_at
                FROM notes
                JOIN users ON users.id = notes.user_id
                WHERE users.vk_id = %s
                ORDER BY notes.note_number
                """,
                (vk_id,),
            )

            return cursor.fetchall()


def delete_note(vk_id, note_number):
    with get_connection() as conn:
        with conn.cursor() as cursor:
            cursor.execute(
                """
                DELETE FROM notes
                WHERE note_number = %s
                  AND user_id = (
                      SELECT id
                      FROM users
                      WHERE vk_id = %s
                  )
                RETURNING note_number
                """,
                (note_number, vk_id),
            )

            result = cursor.fetchone()

            return result is not None


def edit_note(vk_id, note_number, new_text):
    with get_connection() as conn:
        with conn.cursor() as cursor:
            cursor.execute(
                """
                UPDATE notes
                SET text = %s
                WHERE note_number = %s
                  AND user_id = (
                      SELECT id
                      FROM users
                      WHERE vk_id = %s
                  )
                RETURNING note_number
                """,
                (new_text, note_number, vk_id),
            )

            result = cursor.fetchone()

            return result is not None


def search_notes(vk_id, search_text):
    with get_connection() as conn:
        with conn.cursor() as cursor:
            cursor.execute(
                """
                SELECT notes.note_number, notes.text, notes.created_at
                FROM notes
                JOIN users ON users.id = notes.user_id
                WHERE users.vk_id = %s
                  AND notes.text ILIKE %s
                ORDER BY notes.note_number
                """,
                (vk_id, f"%{search_text}%"),
            )

            return cursor.fetchall()