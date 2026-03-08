ddl = """
CREATE TABLE IF NOT EXISTS feed_data (
    id         INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id    INTEGER NOT NULL REFERENCES users(id),
    meals      TEXT,
    energy     INTEGER NOT NULL,
    created_at DATETIME NOT NULL
);

CREATE UNIQUE INDEX IF NOT EXISTS idx_feed_user_date
ON feed_data (user_id, date(created_at));
"""