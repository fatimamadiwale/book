from flask import Flask, render_template, request, redirect, url_for, session
import sqlite3
import os

app = Flask(__name__)
app.secret_key = "supersecretkey"

# ---------------------------
# DEFAULT BOOK DATASET
# ---------------------------
default_books = [
    {"title": "The Fault in Our Stars", "author": "John Green", "difficulty": 1, "genre": "romance"},
    {"title": "Me Before You", "author": "Jojo Moyes", "difficulty": 2, "genre": "romance"},
    {"title": "It Ends With Us", "author": "Colleen Hoover", "difficulty": 2, "genre": "romance"},
    {"title": "The Silent Patient", "author": "Alex Michaelides", "difficulty": 2, "genre": "thriller"},
    {"title": "Gone Girl", "author": "Gillian Flynn", "difficulty": 3, "genre": "thriller"},
    {"title": "Harry Potter", "author": "J.K. Rowling", "difficulty": 1, "genre": "fantasy"},
    {"title": "The Hobbit", "author": "J.R.R. Tolkien", "difficulty": 2, "genre": "fantasy"},
]

# ---------------------------
# DATABASE
# ---------------------------
DB_PATH = os.path.join(os.path.dirname(__file__), "database.db")

def get_db():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    conn = get_db()
    c = conn.cursor()
    c.execute("""
        CREATE TABLE IF NOT EXISTS books (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user TEXT NOT NULL,
            title TEXT NOT NULL,
            author TEXT NOT NULL
        )
    """)
    conn.commit()
    conn.close()

# ---------------------------
# ROUTES
# ---------------------------
@app.route("/")
def home():
    return render_template("home.html")

@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        username = request.form.get("username")
        if username:
            session["user"] = username
            return redirect(url_for("books"))
    return render_template("login.html")

@app.route("/logout")
def logout():
    session.clear()
    return redirect(url_for("login"))

@app.route("/register", methods=["GET", "POST"])
def register():
    if request.method == "POST":
        # For simplicity, just redirect to login
        return redirect(url_for("login"))
    return render_template("register.html")

@app.route("/books")
def books():
    if "user" not in session:
        return redirect(url_for("login"))

    conn = get_db()
    c = conn.cursor()
    c.execute("SELECT id, title, author FROM books WHERE user=?", (session["user"],))
    user_books = c.fetchall()
    conn.close()

    return render_template("books.html", books=default_books, user_books=user_books)

@app.route("/add_book", methods=["GET", "POST"])
def add_book():
    if "user" not in session:
        return redirect(url_for("login"))

    if request.method == "POST":
        title = request.form.get("title")
        author = request.form.get("author")
        if title and author:
            conn = get_db()
            c = conn.cursor()
            c.execute("INSERT INTO books (user, title, author) VALUES (?, ?, ?)",
                      (session["user"], title, author))
            conn.commit()
            conn.close()
            return redirect(url_for("books"))

    return render_template("add_book.html")

@app.route("/delete_book/<int:book_id>")
def delete_book(book_id):
    if "user" not in session:
        return redirect(url_for("login"))

    conn = get_db()
    c = conn.cursor()
    c.execute("DELETE FROM books WHERE id=? AND user=?", (book_id, session["user"]))
    conn.commit()
    conn.close()
    return redirect(url_for("books"))

# ---------------------------
# QUIZ ROUTES
# ---------------------------
@app.route("/quiz_profile", methods=["GET", "POST"])
def quiz_profile():
    recommendation = None
    level = None
    if request.method == "POST":
        difficulty_pref = int(request.form.get("difficulty_pref", 1))
        vocab_comfort = int(request.form.get("vocab_comfort", 1))
        score = difficulty_pref + vocab_comfort

        if score <= 2:
            level = "Beginner"
            recommendation = "The Fault in Our Stars"
        elif score <= 4:
            level = "Intermediate"
            recommendation = "Me Before You"
        else:
            level = "Advanced"
            recommendation = "Gone Girl"

    return render_template("quiz_profile.html", level=level, recommendation=recommendation)

@app.route("/quiz_feedback", methods=["GET", "POST"])
def quiz_feedback():
    new_level = None
    if request.method == "POST":
        book_difficulty = int(request.form.get("book_difficulty", 0))
        vocab_diff = int(request.form.get("vocab_diff", 0))
        finished = int(request.form.get("finished", 1))

        score = book_difficulty - vocab_diff + finished
        if score <= 0:
            new_level = "Beginner"
        elif score == 1:
            new_level = "Intermediate"
        else:
            new_level = "Advanced"

    return render_template("quiz_feedback.html", new_level=new_level)

# ---------------------------
# RUN SERVER
# ---------------------------
if __name__ == "__main__":
    init_db()
    app.run(debug=True)
    