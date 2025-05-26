from flask import Flask, request, jsonify
from flask_sqlalchemy import SQLAlchemy
from flask_cors import CORS
from werkzeug.security import generate_password_hash, check_password_hash
from datetime import datetime
import os
import psycopg2
from dotenv import load_dotenv

load_dotenv()

app = Flask(__name__)
CORS(app)

# === Database Configuration ===
if os.getenv("DATABASE_URL"):
    app.config["SQLALCHEMY_DATABASE_URI"] = os.getenv("DATABASE_URL")
else:
    DB_NAME = os.getenv("DB_NAME")
    DB_USER = os.getenv("DB_USER")
    DB_PASSWORD = os.getenv("DB_PASSWORD")
    DB_HOST = os.getenv("DB_HOST")
    app.config["SQLALCHEMY_DATABASE_URI"] = f"postgresql://{DB_USER}:{DB_PASSWORD}@{DB_HOST}/{DB_NAME}"

app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False

db = SQLAlchemy(app)

# === Models ===
class User(db.Model):
    __tablename__ = "users"

    id = db.Column(db.Integer, primary_key=True)
    surname = db.Column(db.String(50))
    name = db.Column(db.String(50))
    gender = db.Column(db.String(10))
    email = db.Column(db.String(100), unique=True)
    password_hash = db.Column(db.String(255))
    level = db.Column(db.String(20), default="beginner")
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

class Recording(db.Model):
    __tablename__ = "recordings"

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey("users.id"))
    item = db.Column(db.String(50))
    recording_path = db.Column(db.String(255))
    score = db.Column(db.Float)
    timestamp = db.Column(db.DateTime, default=datetime.utcnow)

# === Route: Registration ===
@app.route("/register", methods=["POST"])
def register():
    data = request.json
    existing_user = User.query.filter_by(email=data["email"]).first()
    if existing_user:
        return jsonify({"message": "A user with this email already exists"}), 400

    hashed_password = generate_password_hash(data["password"])
    user = User(
        name=data["name"],
        surname=data["surname"],
        gender=data["gender"],
        email=data["email"],
        password_hash=hashed_password
    )
    db.session.add(user)
    db.session.commit()
    return jsonify({"message": "Registration successful"}), 200

# === Route: Login ===
@app.route("/login", methods=["POST"])
def login():
    data = request.json
    user = User.query.filter_by(email=data["email"]).first()
    if user and check_password_hash(user.password_hash, data["password"]):
        return jsonify({
            "user_id": user.id,
            "name": user.name,
            "level": user.level,
            "gender": user.gender
        }), 200
    return jsonify({"message": "Incorrect email or password"}), 401

# === Route: Save Recording ===
@app.route("/save_recording", methods=["POST"])
def save_recording():
    data = request.json
    recording = Recording(
        user_id=data["user_id"],
        item=data["item"],
        recording_path=data["recording_path"],
        score=data["score"]
    )
    db.session.add(recording)
    db.session.commit()
    return jsonify({"message": "Recording saved"}), 200

# === Route: Progress Dashboard ===
@app.route("/progress/<int:user_id>")
def get_progress(user_id):
    try:
        if os.getenv("DATABASE_URL"):
            conn = psycopg2.connect(os.getenv("DATABASE_URL"))
        else:
            conn = psycopg2.connect(
                dbname=os.getenv("DB_NAME"),
                user=os.getenv("DB_USER"),
                password=os.getenv("DB_PASSWORD"),
                host=os.getenv("DB_HOST")
            )
        cur = conn.cursor()
        cur.execute("""
            SELECT item, score, timestamp
            FROM recordings
            WHERE user_id = %s
            ORDER BY timestamp DESC
        """, (user_id,))
        rows = cur.fetchall()
        cur.close()
        conn.close()

        total = len(rows)
        average = sum([r[1] for r in rows]) / total if total > 0 else 0
        history = [{
            "item": r[0],
            "score": round(r[1], 2),
            "timestamp": r[2].strftime("%Y-%m-%d %H:%M")
        } for r in rows]

        return jsonify({
            "total": total,
            "average": average,
            "history": history
        }), 200
    except Exception as e:
        print("❌ /progress error:", e)
        return jsonify({"error": str(e)}), 500

# === Route: Initialize Tables ===
@app.route("/init_db")
def init_db():
    with app.app_context():
        db.create_all()
    return "Database initialized", 200

# === Run the App ===
if __name__ == "__main__":
    app.run(debug=True)
