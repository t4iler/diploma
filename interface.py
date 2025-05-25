import streamlit as st
import requests
import datetime
from pathlib import Path
from io import BytesIO
from pydub import AudioSegment
from audiorecorder import audiorecorder
from pronunciation_evaluator import evaluate_pronunciation

# === Константы ===
BACKEND_URL = "http://127.0.0.1:5000"
AUDIO_PATH = "audio/etalon/letters"
USER_RECORDINGS = "audio/user"

# === Состояние ===
for key in ["user_id", "level", "gender", "name", "authenticated"]:
    if key not in st.session_state:
        st.session_state[key] = None if key != "authenticated" else False

st.set_page_config(page_title="Обучение арабскому алфавиту", layout="centered")
st.title("🕌 Обучение арабскому алфавиту")

# === Вход / Регистрация ===
if not st.session_state.authenticated:
    tab1, tab2 = st.tabs(["🔐 Вход", "📝 Регистрация"])

    with tab1:
        st.subheader("Вход")
        email = st.text_input("Email", key="login_email")
        password = st.text_input("Пароль", type="password", key="login_password")

        if st.button("Войти", key="login_button"):
            headers = {"Content-Type": "application/json"}
            response = requests.post(
                f"{BACKEND_URL}/login",
                json={"email": email, "password": password},
                headers=headers
            )

            try:
                res = response.json()
            except Exception:
                st.error("⚠️ Сервер вернул некорректный JSON.")
                res = {}

            if response.status_code == 200:
                required = ["user_id", "level", "gender", "name"]
                if all(k in res for k in required):
                    st.session_state.user_id = res["user_id"]
                    st.session_state.level = res["level"]
                    st.session_state.gender = res["gender"]
                    st.session_state.name = res["name"]
                    st.session_state.authenticated = True
                    st.rerun()
                else:
                    st.error("⚠️ Ответ от сервера неполный. Проверь backend.")
            else:
                st.error(f"Ошибка сервера: {response.status_code}")

    with tab2:
        st.subheader("Регистрация")
        name = st.text_input("Имя", key="register_name")
        surname = st.text_input("Фамилия", key="register_surname")
        gender = st.radio("Пол", ["male", "female"], format_func=lambda x: "Мужской" if x == "male" else "Женский", key="register_gender")
        reg_email = st.text_input("Email для регистрации", key="register_email")
        reg_password = st.text_input("Пароль", type="password", key="register_password")

        if st.button("Зарегистрироваться", key="register_button"):
            headers = {"Content-Type": "application/json"}
            data = {
                "name": name,
                "surname": surname,
                "gender": gender,
                "email": reg_email,
                "password": reg_password
            }
            response = requests.post(f"{BACKEND_URL}/register", json=data, headers=headers)
            try:
                res = response.json()
                if response.status_code == 200:
                    st.success("✅ Успешно зарегистрирован! Теперь войдите.")
                else:
                    st.error(res.get("message", "Ошибка регистрации"))
            except Exception:
                st.error(f"Ошибка сервера: {response.status_code}")

# === Основной интерфейс ===
if st.session_state.authenticated and st.session_state.level == "beginner":
    st.subheader("📖 Уровень: Начинающий — Буквы арабского алфавита")

    letters = [
        "ا", "ب", "ت", "ث", "ج", "ح", "خ", "د", "ذ", "ر", "ز", "س", "ش", "ص",
        "ض", "ط", "ظ", "ع", "غ", "ف", "ق", "ك", "ل", "م", "ن", "ه", "و", "ي"
    ]

    for i, letter in enumerate(letters):
        with st.expander(f"📘 Буква: {letter}"):
            etalon_path = Path(AUDIO_PATH) / st.session_state.gender / f"{i+1}.mp3"
            st.audio(str(etalon_path))

            ts = datetime.datetime.now().strftime("%Y%m%d%H%M%S")
            letter_id = i + 1
            filename = f"user_{st.session_state.user_id}_letter_{letter_id}_{ts}.wav"
            wav_path = Path(USER_RECORDINGS) / filename
            wav_path.parent.mkdir(parents=True, exist_ok=True)

            audio = audiorecorder(key=f"rec-{i}")
            if audio:
                buffer = BytesIO()
                audio.export(buffer, format="wav")
                with open(wav_path, "wb") as f:
                    f.write(buffer.getvalue())

                st.audio(str(wav_path))
                st.success("✅ Запись сохранена")

                score, feedback = evaluate_pronunciation(str(wav_path), str(etalon_path))
                if score is not None:
                    st.markdown(f"### 🎯 Точность: **{score}%**")
                    st.info(f"💬 Обратная связь: {feedback}")
                else:
                    st.error(feedback)
elif st.session_state.authenticated and st.session_state.user_id:
    st.sidebar.subheader("📈 Прогресс")
    if st.sidebar.button("Показать дашборд"):
        # Загрузка прогресса
        try:
            response = requests.get(f"{BACKEND_URL}/progress/{st.session_state.user_id}")
            if response.status_code == 200:
                data = response.json()
                st.subheader("📊 Ваш прогресс")
                st.markdown(f"**Всего записей:** {data['total']}")
                st.markdown(f"**Средняя точность:** {round(data['average'], 2)}%")

                st.markdown("### 📝 История")
                for r in data["history"]:
                    st.markdown(f"• {r['item']} — {r['score']}% — *{r['timestamp']}*")
            else:
                st.error("Не удалось загрузить прогресс.")
        except Exception as e:
            st.error(f"Ошибка: {e}")
