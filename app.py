from flask import Flask, request, jsonify, render_template
from flask_cors import CORS
import mysql.connector

app = Flask(__name__)
CORS(app)

db = mysql.connector.connect(
    host="localhost",
    user="root",
    password="1234",
    database="mydb",
    charset="utf8mb4"
)

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

def get_random_word(length):
    cursor = db.cursor()
    query = """
    SELECT word FROM words
    WHERE useful = 1 AND CHAR_LENGTH(word) = %s
    ORDER BY RAND()
    LIMIT 1
    """
    cursor.execute(query, (length,))
    result = cursor.fetchone()
    return result[0] if result else None

# изменить потом глобальное слово
SECRET = get_random_word(5)
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

    cursor = db.cursor()

    # проверка существования слова
    cursor.execute("SELECT * FROM words WHERE word = %s", (word,))
    if not cursor.fetchone():
        return jsonify({"error": "Слова не существует"}), 400

    if len(word) != len(SECRET):
        return jsonify({"error": "Неверная длина слова"}), 400

    result = check_word(SECRET, word)

    return jsonify(result)

@app.route("/start", methods=["GET"])
def start():
    global SECRET
    SECRET = get_random_word(5)
    return jsonify({"message": "Новая игра начата"})

# Запуск
if __name__ == "__main__":
    app.run()
