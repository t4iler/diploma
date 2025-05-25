from flask import Flask, request, jsonify, session
from flask_sqlalchemy import SQLAlchemy
from flask_cors import CORS
from werkzeug.security import generate_password_hash, check_password_hash
from datetime import datetime
from dotenv import load_dotenv
import os

# Загрузка .env
load_dotenv()

app = Flask(__name__)
app.secret_key = os.getenv("SECRET_KEY")
app.config['SQLALCHEMY_DATABASE_URI'] = os.getenv("DATABASE_URL")
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

# ✅ Простой и надёжный CORS (универсально)
CORS(app, resources={r"/*": {"origins": "*"}})

db = SQLAlchemy(app)

# Модель пользователя
class User(db.Model):
    __tablename__ = 'users'
    id = db.Column(db.Integer, primary_key=True)
    surname = db.Column(db.String(50))
    name = db.Column(db.String(50))
    gender = db.Column(db.String(10), nullable=False)
    email = db.Column(db.String(100), unique=True, nullable=False)
    password_hash = db.Column(db.String(255), nullable=False)
    level = db.Column(db.String(20), default='beginner')
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

# Модель записей
class Recording(db.Model):
    __tablename__ = 'recordings'
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'))
    item = db.Column(db.String(50))
    recording_path = db.Column(db.String(255))
    score = db.Column(db.Float)
    timestamp = db.Column(db.DateTime, default=datetime.utcnow)

# Регистрация
@app.route('/register', methods=['POST', 'OPTIONS'])
def register():
    if request.method == "OPTIONS":
        return '', 204  # preflight
    data = request.json
    if User.query.filter_by(email=data['email']).first():
        return jsonify({"message": "Email already registered"}), 400
    hashed_pw = generate_password_hash(data['password'])
    new_user = User(
        surname=data['surname'],
        name=data['name'],
        gender=data['gender'],
        email=data['email'],
        password_hash=hashed_pw
    )
    db.session.add(new_user)
    db.session.commit()
    return jsonify({"message": "Registration successful"})

# Вход
@app.route('/login', methods=['POST', 'OPTIONS'])
def login():
    if request.method == "OPTIONS":
        return '', 204
    data = request.json
    user = User.query.filter_by(email=data['email']).first()
    if user and check_password_hash(user.password_hash, data['password']):
        return jsonify({
            "message": "Login successful",
            "user_id": user.id,
            "name": user.name,
            "level": user.level,
            "gender": user.gender
        })
    return jsonify({"message": "Invalid email or password"}), 401

# Профиль
@app.route('/profile/<int:user_id>', methods=['GET'])
def profile(user_id):
    user = User.query.get(user_id)
    if user:
        return jsonify({
            "id": user.id,
            "name": user.name,
            "surname": user.surname,
            "gender": user.gender,
            "email": user.email,
            "level": user.level
        })
    return jsonify({"message": "User not found"}), 404

@app.route("/progress/<int:user_id>")
def get_progress(user_id):
    conn = psycopg2.connect(
    dbname="pronunciation_db",
    user="aibeksatybaev",
    password="Qwerty!@#123",
    host="34.107.44.238")
    cur = conn.cursor()
    cur.execute("""
        SELECT item, score, timestamp
        FROM recordings
        WHERE user_id = %s
        ORDER BY timestamp DESC
    """, (user_id,))
    rows = cur.fetchall()
    conn.close()

    total = len(rows)
    average = sum([r[1] for r in rows]) / total if total > 0 else 0
    history = [{"item": r[0], "score": r[1], "timestamp": r[2].strftime("%Y-%m-%d %H:%M")} for r in rows]

    return jsonify({
        "total": total,
        "average": average,
        "history": history
    })


# Инициализация базы
if __name__ == '__main__':
    with app.app_context():
        db.create_all()
    app.run(debug=True)
