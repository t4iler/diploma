import streamlit as st
st.set_page_config(page_title="Arabic Pronunciation Training")
import requests
import datetime
import json
import os
from pathlib import Path
from io import BytesIO
from pydub import AudioSegment
from audiorecorder import audiorecorder
from pronunciation_evaluator import evaluate_pronunciation
from intermediate_module import render_intermediate

# === Переводы ===
translations = {
    "Login": {"ru": "Войти"},
    "Password": {"ru": "Пароль"},
    "Register": {"ru": "Регистрация"},
    "Surname": {"ru": "Фамилия"},
    "Name": {"ru": "Имя"},
    "Gender": {"ru": "Пол"},
    "Male": {"ru": "Мужской"},
    "Female": {"ru": "Женский"},
    "Level: Beginner (Letters)": {"ru": "Уровень: Начинающий (буквы)"},
    "Recording saved": {"ru": "Запись сохранена"},
    "Feedback:": {"ru": "Обратная связь:"},
    "Accuracy": {"ru": "Точность"},
    "Progress": {"ru": "Прогресс"},
    "History": {"ru": "История"},
    "Total recordings:": {"ru": "Всего записей:"},
    "Average accuracy:": {"ru": "Средняя точность:"},
    "Show": {"ru": "Показать"},
    "Logout": {"ru": "Выйти"},
    "Email": {"ru": "Email"},
    "Login failed": {"ru": "Ошибка входа"},
    "Registration error": {"ru": "Ошибка регистрации"},
    "Server not responding": {"ru": "Сервер не отвечает"},
    "Successfully registered! Please login.": {"ru": "Успешно зарегистрирован! Войдите."},
    "Arabic Pronunciation Training": {"ru": "Обучение арабскому произношению"},
    "Letter": {"ru": "Буква"},
    "Choose Level": {"ru": "Выберите уровень"},
    "Beginner": {"ru": "Начинающий"},
    "Intermediate": {"ru": "Средний"}
}

def t(text):
    lang = st.session_state.get("lang", "en")
    return translations.get(text, {}).get(lang, text)

# === Настройки ===
BACKEND_URL = "http://127.0.0.1:5000"
AUDIO_PATH = "audio/etalon/letters"
USER_RECORDINGS = "audio/user"
SESSION_FILE = ".session.json"

# === Язык по умолчанию ===
if "lang" not in st.session_state:
    st.session_state.lang = "en"

lang = st.radio("🌐 Language", ["en", "ru"], format_func=lambda x: "🇺🇸 English" if x == "en" else "🇷🇺 Русский", horizontal=True)
st.session_state.lang = lang

# === Сессия ===
default_session = {
    "user_id": None,
    "level": None,
    "gender": None,
    "name": None,
    "authenticated": False,
}

for key, val in default_session.items():
    if key not in st.session_state:
        st.session_state[key] = val

if not st.session_state.authenticated and os.path.exists(SESSION_FILE):
    with open(SESSION_FILE, "r") as f:
        session_data = json.load(f)
        st.session_state.update(session_data)

st.title(t("Arabic Pronunciation Training"))

# === Logout ===
if st.session_state.authenticated:
    if st.sidebar.button("🚪 " + t("Logout")):
        st.session_state.clear()
        if os.path.exists(SESSION_FILE):
            os.remove(SESSION_FILE)
        st.rerun()

# === Авторизация ===
if not st.session_state.authenticated:
    tab1, tab2 = st.tabs(["🔐 " + t("Login"), "📝 " + t("Register")])

    with tab1:
        email = st.text_input(t("Email"), key="login_email")
        password = st.text_input(t("Password"), type="password", key="login_password")
        if st.button(t("Login"), key="login_button"):
            try:
                response = requests.post(f"{BACKEND_URL}/login", json={
                    "email": email,
                    "password": password
                })
                res = response.json()
                if response.status_code == 200:
                    st.session_state.update({
                        "user_id": res["user_id"],
                        "level": res["level"],
                        "gender": res["gender"],
                        "name": res["name"],
                        "authenticated": True
                    })
                    with open(SESSION_FILE, "w") as f:
                        json.dump(dict(st.session_state), f)
                    st.rerun()
                else:
                    st.error(res.get("message", t("Login failed")))
            except Exception:
                st.error(t("Server not responding"))

    with tab2:
        name = st.text_input(t("Name"), key="register_name")
        surname = st.text_input(t("Surname"), key="register_surname")
        gender = st.radio(t("Gender"), ["male", "female"], format_func=lambda x: t("Male") if x == "male" else t("Female"), key="register_gender")
        reg_email = st.text_input(t("Email") + " (register)", key="register_email")
        reg_password = st.text_input(t("Password"), type="password", key="register_password")

        if st.button(t("Register"), key="register_button"):
            try:
                response = requests.post(f"{BACKEND_URL}/register", json={
                    "name": name,
                    "surname": surname,
                    "gender": gender,
                    "email": reg_email,
                    "password": reg_password
                })
                res = response.json()
                if response.status_code == 200:
                    st.success(t("Successfully registered! Please login."))
                else:
                    st.error(res.get("message", t("Registration error")))
            except Exception:
                st.error(t("Server not responding"))

# === Прогресс ===
if st.session_state.authenticated:
    st.sidebar.subheader("📈 " + t("Progress"))
    if st.sidebar.button(t("Show")):
        try:
            response = requests.get(f"{BACKEND_URL}/progress/{st.session_state.user_id}")
            if response.status_code == 200:
                data = response.json()
                st.subheader("📊 " + t("Progress"))
                st.markdown(f"**{t('Total recordings:')}** {data['total']}")
                st.markdown(f"**{t('Average accuracy:')}** {round(data['average'], 2)}%")

                st.markdown("### 📝 " + t("History"))
                for r in data["history"]:
                    st.markdown(f"• {r['item']} — {r['score']}% — *{r['timestamp']}*")
            else:
                st.error("Failed to load progress.")
        except Exception as e:
            st.error(f"Error: {e}")

# === Выбор уровня ===
if st.session_state.authenticated:
    level_choice = st.sidebar.selectbox("🎓 " + t("Choose Level"), ["beginner", "intermediate"], format_func=lambda x: t("Beginner") if x == "beginner" else t("Intermediate"))
    st.session_state.level = level_choice

# === Beginner ===
if st.session_state.authenticated and st.session_state.level == "beginner":
    st.subheader("📘 " + t("Level: Beginner (Letters)"))

    letters = [
        "ا", "ب", "ت", "ث", "ج", "ح", "خ", "د", "ذ", "ر", "ز", "س", "ش", "ص",
        "ض", "ط", "ظ", "ع", "غ", "ف", "ق", "ك", "ل", "م", "ن", "ه", "و", "ي"
    ]

    for i, letter in enumerate(letters):
        with st.expander(f"{t('Letter')} {letter}"):
            etalon_path = Path(AUDIO_PATH) / st.session_state.gender / f"{i+1}.mp3"
            st.audio(str(etalon_path))

            ts = datetime.datetime.now().strftime("%Y%m%d%H%M%S")
            filename = f"user_{st.session_state.user_id}_letter_{i+1}_{ts}.wav"
            wav_path = Path(USER_RECORDINGS) / filename
            wav_path.parent.mkdir(parents=True, exist_ok=True)

            audio = audiorecorder(start_prompt="🔴 Начать запись" if st.session_state.lang == "ru" else "🔴 Start recording",
                                  stop_prompt="⏹ Остановить запись" if st.session_state.lang == "ru" else "⏹ Stop recording",
                                  key=f"rec-{i}")
            if audio:
                buffer = BytesIO()
                audio.export(buffer, format="wav")
                with open(wav_path, "wb") as f:
                    f.write(buffer.getvalue())

                st.audio(str(wav_path))
                st.success("✅ " + t("Recording saved"))

                score, feedback = evaluate_pronunciation(str(wav_path), str(etalon_path), lang=st.session_state.lang)
                if score is not None:
                    st.markdown(f"🎯 {t('Accuracy')}: **{score}%**")
                    st.info(f"💬 {t('Feedback:')} {feedback}")
                    try:
                        requests.post(f"{BACKEND_URL}/save_recording", json={
                            "user_id": st.session_state.user_id,
                            "item": letter,
                            "recording_path": str(wav_path),
                            "score": score
                        })
                    except Exception:
                        st.warning("⚠️ Could not save to database")
                else:
                    st.error(feedback)

# === Intermediate ===
if st.session_state.authenticated and st.session_state.level == "intermediate":
    render_intermediate(user_id=st.session_state.user_id, gender=st.session_state.gender, lang=st.session_state.lang)
