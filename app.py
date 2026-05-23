from flask import Flask, request, jsonify, render_template
from flask_cors import CORS
import os
import mysql.connector

app = Flask(__name__)
CORS(app)

def get_db():
    return mysql.connector.connect(
        host=os.getenv("DB_HOST"),
        user=os.getenv("DB_USER"),
        password=os.getenv("DB_PASSWORD"),
        database=os.getenv("DB_NAME"),
        charset="utf8mb4"
    )

#логика
def check_word(secret, guess):
    result = ["gray"] * len(guess)
    secret_list = list(secret)

    # green
    for i in range(len(guess)):
        if guess[i] == secret[i]:
            result[i] = "green"
            secret_list[i] = None

    # yellow
    for i in range(len(guess)):
        if result[i] == "gray" and guess[i] in secret_list:
            result[i] = "yellow"
            secret_list[secret_list.index(guess[i])] = None

    return result

#случайное слово
def get_random_word(length):
    db = get_db()
    cursor = db.cursor()

    query = """
    SELECT word, theme FROM words
    WHERE useful = 1 AND CHAR_LENGTH(word) = %s
    ORDER BY RAND()
    LIMIT 1
    """

    cursor.execute(query, (length,))
    result = cursor.fetchone()

    cursor.close()
    db.close()

    return result[0] if result else None

#загаданное слово
result = get_random_word(5)

SECRET = result[0]
THEME = result[1]
print("SECRET:", SECRET)

@app.route("/")
def home():
    return render_template("index.html")

@app.route("/guess", methods=["POST"])
def guess():
    data = request.get_json(force=True)

    if not data or "word" not in data:
        return jsonify({"error": "Нет поля word"}), 400

    word = data["word"]

    db = get_db()
    cursor = db.cursor()

    try:
        #проверки
        cursor.execute("SELECT * FROM words WHERE word = %s", (word,))
        if not cursor.fetchone():
            return jsonify({"error": "Слова не существует"}), 400

        if len(word) != len(SECRET):
            return jsonify({"error": "Неверная длина слова"}), 400

        result = check_word(SECRET, word)
        print(" word - ", word, " ",result)
        return jsonify(result)

    finally:
        cursor.close()
        db.close()

@app.route("/start", methods=["GET"])
def start():

    global SECRET, THEME

    result = get_random_word(5)

    SECRET = result[0]
    THEME = result[1]

    print("SECRET:", SECRET)
    print("THEME:", THEME)

    return jsonify({
        "message": "Новая игра начата",
        "theme": THEME
    })

@app.route("/secret")
def secret():
    return jsonify({"word": SECRET})

if __name__ == "__main__":
    app.run()
