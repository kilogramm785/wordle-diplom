from flask import Flask, request, jsonify, render_template
from flask_cors import CORS
import os
import mysql.connector

app = Flask(__name__)
CORS(app)

CURRENT_LENGTH = 5  # по умолчанию 5 букв
SECRET = None

def get_db():
    return mysql.connector.connect(
        host=os.getenv("DB_HOST"),
        user=os.getenv("DB_USER"),
        password=os.getenv("DB_PASSWORD"),
        database=os.getenv("DB_NAME"),
        charset="utf8mb4"
    )

def check_word(secret, guess):
    result = ["gray"] * len(guess)
    secret_list = list(secret)

    for i in range(len(guess)):
        if guess[i] == secret[i]:
            result[i] = "green"
            secret_list[i] = None

    for i in range(len(guess)):
        if result[i] == "gray" and guess[i] in secret_list:
            result[i] = "yellow"
            secret_list[secret_list.index(guess[i])] = None

    return result

def get_random_word(length):
    db = get_db()
    cursor = db.cursor()
    query = """
    SELECT word FROM words 
    WHERE useful = 1 AND CHAR_LENGTH(word) = %s 
    ORDER BY RAND() LIMIT 1
    """
    cursor.execute(query, (length,))
    result = cursor.fetchone()
    cursor.close()
    db.close()
    return result[0] if result else None

def init_secret():
    global SECRET
    SECRET = get_random_word(CURRENT_LENGTH)

init_secret()  # при запуске

@app.route("/")
def home():
    return render_template("index.html", length=5)

@app.route("/4")
def mode4():
    global CURRENT_LENGTH
    CURRENT_LENGTH = 4
    init_secret()
    return render_template("index.html", length=4)

@app.route("/6")
def mode6():
    global CURRENT_LENGTH
    CURRENT_LENGTH = 6
    init_secret()
    return render_template("index.html", length=6)

@app.route("/guess", methods=["POST"])
def guess():
    data = request.get_json(force=True)
    word = data.get("word", "").strip().lower()

    if len(word) != CURRENT_LENGTH:
        return jsonify({"error": f"Слово должно состоять из {CURRENT_LENGTH} букв"}), 400

    db = get_db()
    cursor = db.cursor()
    try:
        cursor.execute("SELECT * FROM words WHERE word = %s", (word,))
        if not cursor.fetchone():
            return jsonify({"error": "Слова не существует"}), 400

        result = check_word(SECRET, word)
        return jsonify(result)
    finally:
        cursor.close()
        db.close()

@app.route("/start", methods=["GET"])
def start():
    global SECRET
    SECRET = get_random_word(CURRENT_LENGTH)
    return jsonify({"message": "Новая игра"})

@app.route("/theme")
def get_theme():
    db = get_db()
    cursor = db.cursor(dictionary=True)
    try:
        cursor.execute("SELECT theme FROM words WHERE word = %s", (SECRET,))
        result = cursor.fetchone()
        return jsonify({"theme": result['theme'] if result and result['theme'] else "Без темы"})
    finally:
        cursor.close()
        db.close()

@app.route("/secret")
def secret():
    return jsonify({"word": SECRET})

@app.route("/suggest", methods=["POST"])
def suggest_word():
    data = request.get_json(force=True)
    word = data.get("word", "").strip().lower()
    
    if len(word) < 3 or len(word) > 10:
        return jsonify({"error": "Неверная длина слова"}), 400

    db = get_db()
    cursor = db.cursor()
    try:
        cursor.execute("""
            INSERT INTO suggested_words (word, status, created_at) 
            VALUES (%s, 'pending', NOW())
        """, (word,))
        db.commit()
        return jsonify({"message": "Слово отправлено на рассмотрение"}), 201
    except mysql.connector.errors.IntegrityError:
        return jsonify({"error": "Такое слово уже есть"}), 409
    finally:
        cursor.close()
        db.close()

if __name__ == "__main__":
    app.run(debug=True)
