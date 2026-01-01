from sentence_transformers import SentenceTransformer
from sklearn.metrics.pairwise import cosine_similarity
import sqlite3
from datetime import datetime

DB_FILE = "matchmaking.db"
conn = sqlite3.connect(DB_FILE)
model = SentenceTransformer('all-MiniLM-L6-v2')


def match_score(text1, text2):
    """Return similarity score as percentage (0-100) between two texts."""
    if not text1:
        text1 = ""
    if not text2:
        text2 = ""
    emb1 = model.encode([text1])
    emb2 = model.encode([text2])
    score = cosine_similarity(emb1, emb2)[0][0]
    return round(score * 100, 3)


def ensure_matches_table(conn):
    cur = conn.cursor()
    cur.execute("""
        CREATE TABLE IF NOT EXISTS matches (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            candidate_id INTEGER NOT NULL,
            score REAL NOT NULL,
            created_at TEXT NOT NULL
        )
    """)
    conn.commit()


def fetch_users(conn):
    cur = conn.cursor()
    cur.execute("SELECT id, name, gender, interested_in, looking_for, about_me FROM users")
    cols = [d[0] for d in cur.description]
    rows = cur.fetchall()
    users = [dict(zip(cols, r)) for r in rows]
    return users


def compute_and_store_matches(min_score=0.0):
    conn = sqlite3.connect(DB_FILE)
    ensure_matches_table(conn)

    # optional: clear previous matches
    conn.execute("DELETE FROM matches")
    conn.commit()

    users = fetch_users(conn)
    id_to_user = {u['id']: u for u in users}

    inserted = 0
    for u in users:
        # Find candidates whose gender matches this user's `interested_in`
        candidates = [c for c in users if c['gender'] == u['interested_in'] and c['id'] != u['id']]

        for c in candidates:
            # Compare this user's `looking_for` with candidate's `about_me`
            score = match_score(u.get('looking_for', ''), c.get('about_me', ''))
            if score >= min_score:
                conn.execute(
                    "INSERT INTO matches (user_id, candidate_id, score, created_at) VALUES (?, ?, ?, ?)",
                    (u['id'], c['id'], score, datetime.utcnow().isoformat())
                )
                inserted += 1

    conn.commit()
    conn.close()
    print(f"Inserted {inserted} match rows into 'matches' table.")


if __name__ == '__main__':
    compute_and_store_matches()
