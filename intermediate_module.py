import streamlit as st
import datetime
import numpy as np
import requests
from pathlib import Path
from io import BytesIO
from pydub import AudioSegment
from audiorecorder import audiorecorder
from phrase_evaluator import evaluate_phrase_pronunciation  # ✅ теперь используем внешний модуль

PHRASE_AUDIO_PATH = "audio/etalon/phrases"
USER_RECORDINGS = "audio/user"
BACKEND_URL = "http://127.0.0.1:5000"

def render_intermediate(user_id, gender, lang="en"):
    st.subheader("📗 Intermediate — Bismillah Phrase" if lang == "en" else "📗 Средний уровень — Фраза Бисмиллях")

    phrase = "بسم الله الرحمن الرحيم"
    gender_folder = "male" if gender == "male" else "female"
    etalon_files = list(Path(PHRASE_AUDIO_PATH).joinpath(gender_folder).glob("bismillah_*.mp3"))

    if etalon_files:
        st.markdown(f"### 📖 {phrase}")
        for f in etalon_files:
            st.audio(str(f), format="audio/mp3")

        ts = datetime.datetime.now().strftime("%Y%m%d%H%M%S")
        filename = f"user_{user_id}_bismillah_{ts}.wav"
        wav_path = Path(USER_RECORDINGS) / filename
        wav_path.parent.mkdir(parents=True, exist_ok=True)

        start_prompt = "🔴 Start recording" if lang == "en" else "🔴 Начать запись"
        stop_prompt = "⏹ Stop recording" if lang == "en" else "⏹ Остановить запись"

        audio = audiorecorder(start_prompt=start_prompt, stop_prompt=stop_prompt, key="rec-bismillah")
        if audio:
            buffer = BytesIO()
            audio.export(buffer, format="wav")
            with open(wav_path, "wb") as f:
                f.write(buffer.getvalue())

            st.audio(str(wav_path))
            st.success("✅ Recording saved" if lang == "en" else "✅ Запись сохранена")

            # ✅ Сравнение с несколькими эталонами
            scores = []
            for etalon in etalon_files:
                score, _ = evaluate_phrase_pronunciation(str(wav_path), str(etalon), lang=lang)
                if score is not None:
                    scores.append(score)

            if scores:
                final_score = round(np.mean(scores), 2)
                st.markdown(f"🎯 {'Accuracy' if lang == 'en' else 'Точность'}: **{final_score}%**")

                # Получаем одно сообщение обратной связи
                _, feedback = evaluate_phrase_pronunciation(str(wav_path), str(etalon_files[0]), lang=lang)
                st.info(f"💬 {'Feedback:' if lang == 'en' else 'Обратная связь:'} {feedback}")

                # Сохраняем в базу
                try:
                    requests.post(f"{BACKEND_URL}/save_recording", json={
                        "user_id": user_id,
                        "item": "bismillah",
                        "recording_path": str(wav_path),
                        "score": final_score
                    })
                except Exception:
                    st.warning("⚠️ Could not save to database")
            else:
                st.error("⚠️ No valid etalon scores.")
    else:
        st.warning("⚠️ No etalon files found.")
