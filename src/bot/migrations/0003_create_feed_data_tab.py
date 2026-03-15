ddl = """
CREATE TABLE IF NOT EXISTS feed_data (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER NOT NULL REFERENCES users(id),
    energy INTEGER NOT NULL,
    protein INTEGER NOT NULL,
    fats INTEGER NOT NULL,
    carbohydrates INTEGER NOT NULL,
    fiber INTEGER NOT NULL,
    created_at DATETIME NOT NULL
)
"""