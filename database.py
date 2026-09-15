import sqlite3
from pathlib import Path

DB_PATH = Path("data/bookmarks.db")


class Database:

    def __init__(self):
        DB_PATH.parent.mkdir(exist_ok=True)
        self.conn = sqlite3.connect(DB_PATH)
        self.create_tables()

    def create_tables(self):
        self.conn.execute("""
        CREATE TABLE IF NOT EXISTS groups(
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            parent_id INTEGER
        )
        """)

        self.conn.execute("""
        CREATE TABLE IF NOT EXISTS bookmarks(
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            title TEXT NOT NULL,
            pdf_path TEXT NOT NULL,
            page INTEGER NOT NULL,
            group_id INTEGER
        )
        """)
        self.conn.commit()

    # -------------------------
    # GROUPS
    # -------------------------

    def add_group(self, name, parent_id=None):
        self.conn.execute(
            """
            INSERT INTO groups(name, parent_id)
            VALUES(?,?)
            """,
            (name, parent_id)
        )
        self.conn.commit()

    def get_groups(self):
        return self.conn.execute(
            """
            SELECT id, name, parent_id
            FROM groups
            ORDER BY name
            """
        ).fetchall()

    def rename_group(self, group_id, new_name):
        self.conn.execute(
            """
            UPDATE groups
            SET name=?
            WHERE id=?
            """,
            (new_name, group_id)
        )
        self.conn.commit()

    def delete_group(self, group_id):
        self.conn.execute(
            """
            DELETE FROM groups
            WHERE id=?
            """,
            (group_id,)
        )
        self.conn.commit()

    # -------------------------
    # BOOKMARKS
    # -------------------------

    def add_bookmark(self, title, pdf_path, page, group_id):
        self.conn.execute(
            """
            INSERT INTO bookmarks(title, pdf_path, page, group_id)
            VALUES(?,?,?,?)
            """,
            (title, pdf_path, page, group_id)
        )
        self.conn.commit()

    def get_bookmarks(self):
        return self.conn.execute(
            """
            SELECT id, title, pdf_path, page, group_id
            FROM bookmarks
            ORDER BY title
            """
        ).fetchall()

    def get_bookmark(self, bookmark_id):
        return self.conn.execute(
            """
            SELECT id, title, pdf_path, page, group_id
            FROM bookmarks
            WHERE id=?
            """,
            (bookmark_id,)
        ).fetchone()

    def rename_bookmark(self, bookmark_id, new_title):
        self.conn.execute(
            """
            UPDATE bookmarks
            SET title=?
            WHERE id=?
            """,
            (new_title, bookmark_id)
        )
        self.conn.commit()

    def delete_bookmark(self, bookmark_id):
        self.conn.execute(
            """
            DELETE FROM bookmarks
            WHERE id=?
            """,
            (bookmark_id,)
        )
        self.conn.commit()
