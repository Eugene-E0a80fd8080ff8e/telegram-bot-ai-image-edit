import sqlite3
import os

class Database:
    def __init__(self, db_path='telegram_bot.db'):
        self.db_path = db_path
        self.connection = None
        self.cursor = None
        self.connect()
        self.setup_migrations()

    def connect(self):
        self.connection = sqlite3.connect(self.db_path)
        self.cursor = self.connection.cursor()

    def close(self):
        if self.cursor:
            self.cursor.close()
        if self.connection:
            self.connection.close()

    def setup_migrations(self):
        # Create migrations table if not exists
        self.cursor.execute('''
            CREATE TABLE IF NOT EXISTS migrations (
                id INTEGER PRIMARY KEY,
                version INTEGER UNIQUE,
                applied_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        self.connection.commit()

        # Get current version
        self.cursor.execute('SELECT MAX(version) FROM migrations')
        current_version = self.cursor.fetchone()[0] or 0

        # Define migrations
        migrations = [
            (1, '''
                CREATE TABLE IF NOT EXISTS messages (
                    id INTEGER PRIMARY KEY,
                    user_id TEXT,
                    chat_id TEXT,
                    message_id TEXT,
                    media_group_id TEXT,
                    message_text TEXT,
                    photo_id TEXT,
                    photo BLOB,
                    timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                );
            '''),
            (2, '''
                ALTER TABLE messages ADD COLUMN message_json TEXT;
            '''),
            (3, '''
                BEGIN;
                CREATE TABLE messages_new (
                    id INTEGER PRIMARY KEY,
                    user_id TEXT,
                    chat_id TEXT,
                    message_id TEXT,
                    media_group_id TEXT,
                    message_text TEXT,
                    photo_id TEXT,
                    timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    message_json TEXT
                );
                INSERT INTO messages_new (id, user_id, chat_id, message_id, media_group_id, message_text, photo_id, timestamp, message_json)
                SELECT id, user_id, chat_id, message_id, media_group_id, message_text, photo_id, timestamp, message_json FROM messages;
                DROP TABLE messages;
                ALTER TABLE messages_new RENAME TO messages;
                COMMIT;
            '''),
            (4, '''
                CREATE TABLE photos (
                    photo_id TEXT PRIMARY KEY,
                    photo_blob BLOB,
                    media_group_id TEXT
                );
                CREATE INDEX idx_photos_photo_id ON photos (photo_id);
                CREATE INDEX idx_photos_media_group_id ON photos (media_group_id);
            '''),
        ]

        # Apply pending migrations
        for version, sql in migrations:
            if version > current_version:
                self.cursor.executescript(sql)
                self.cursor.execute('INSERT INTO migrations (version) VALUES (?)', (version,))
                self.connection.commit()
                print(f"Applied migration version {version}")

    def execute_query(self, query, params=()):
        self.cursor.execute(query, params)
        self.connection.commit()

    def fetch_all(self, query, params=()):
        self.cursor.execute(query, params)
        return self.cursor.fetchall()

    def fetch_one(self, query, params=()):
        self.cursor.execute(query, params)
        return self.cursor.fetchone()

    def add_message(self, user_id, chat_id, message_id, media_group_id=None, message_text=None, photo_id=None, message_json=None):
        query = """
        INSERT INTO messages (user_id, chat_id, message_id, media_group_id, message_text, photo_id, message_json)
        VALUES (?, ?, ?, ?, ?, ?, ?)
        """
        params = (user_id, chat_id, message_id, media_group_id, message_text, photo_id, message_json)
        self.execute_query(query, params)
    def add_photo(self, photo_id, photo_blob, media_group_id=None):
        query = """
        INSERT INTO photos (photo_id, photo_blob, media_group_id)
        VALUES (?, ?, ?)
        """
        params = (photo_id, photo_blob, media_group_id)
        self.execute_query(query, params)

    def get_photo_by_id(self, photo_id):
        query = "SELECT photo_blob FROM photos WHERE photo_id = ?"
        res = self.fetch_one(query, (photo_id,))
        return res[0]

    def get_photo_by_media_group_id(self, media_group_id):
        query = "SELECT photo_id, photo_blob FROM photos WHERE media_group_id = ?"
        res = self.fetch_all(query, (media_group_id,))
        return [x[1] for x in res]

    def check_photo_by_id(self, photo_id):
        query = "SELECT 1 FROM photos WHERE photo_id = ? LIMIT 1"
        result = self.fetch_one(query, (photo_id,))
        return result is not None