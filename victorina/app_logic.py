import sqlite3
import os
from typing import List, Tuple


def _conn(db_path: str):
    return sqlite3.connect(db_path)


def ensure_db(db_path: str):
    # Создаем директорию для БД если её нет
    db_dir = os.path.dirname(db_path)
    if db_dir and not os.path.exists(db_dir):
        os.makedirs(db_dir)

    conn = _conn(db_path)
    cur = conn.cursor()
    cur.execute("CREATE TABLE IF NOT EXISTS quizzes (id INTEGER PRIMARY KEY AUTOINCREMENT, title TEXT UNIQUE);")
    cur.execute(
        "CREATE TABLE IF NOT EXISTS questions (id INTEGER PRIMARY KEY AUTOINCREMENT, quiz_id INTEGER, text TEXT, difficulty TEXT, correct_answer TEXT, wrong1 TEXT, wrong2 TEXT, wrong3 TEXT);")
    cur.execute(
        "CREATE TABLE IF NOT EXISTS records (id INTEGER PRIMARY KEY AUTOINCREMENT, player_name TEXT, score INT, quiz_title TEXT);")
    conn.commit();
    conn.close()


def seed_quizzes(db_path: str, titles: List[str]):
    conn = _conn(db_path);
    cur = conn.cursor()
    cur.execute("SELECT COUNT(*) FROM quizzes;")
    if cur.fetchone()[0] == 0:
        cur.executemany("INSERT INTO quizzes (title) VALUES (?);", [(t,) for t in titles])
        conn.commit()
    conn.close()


def seed_questions(db_path: str, rows: List[Tuple[int, str, str, str, str, str, str]]):
    if not rows: return
    conn = _conn(db_path)
    # Проверяем, есть ли уже вопросы
    cur = conn.cursor()
    cur.execute("SELECT COUNT(*) FROM questions;")
    if cur.fetchone()[0] == 0:
        conn.executemany(
            "INSERT INTO questions (quiz_id, text, difficulty, correct_answer, wrong1, wrong2, wrong3) VALUES (?, ?, ?, ?, ?, ?, ?);",
            rows)
        conn.commit()
    conn.close()


def get_quizzes(db_path: str):
    conn = _conn(db_path);
    rows = conn.execute("SELECT id, title FROM quizzes ORDER BY id;").fetchall();
    conn.close();
    return rows


def get_questions(db_path: str, quiz_id: int, limit: int):
    import random
    conn = _conn(db_path)
    q = conn.execute(
        "SELECT id, quiz_id, text, difficulty, correct_answer, wrong1, wrong2, wrong3 FROM questions WHERE quiz_id=?;",
        (quiz_id,)).fetchall()
    conn.close();
    random.shuffle(q);
    return q[:limit]


def save_record(db_path: str, name, score, quiz_title):
    conn = _conn(db_path)
    conn.execute("INSERT INTO records (player_name, score, quiz_title) VALUES (?, ?, ?);", (name, score, quiz_title))
    conn.commit();
    conn.close()


def get_records(db_path: str):
    conn = _conn(db_path)
    rows = conn.execute("SELECT player_name, score, quiz_title FROM records ORDER BY score DESC LIMIT 100;").fetchall()
    conn.close();
    return rows


def base_points_for(diff: str):
    d = (diff or '').lower()
    if d == 'easy': return 10
    if d == 'medium': return 20
    if d == 'hard': return 30
    return 10