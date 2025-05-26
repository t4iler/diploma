# 🗣 Arabic Pronunciation Training Web App

This web application helps students practice and improve their Arabic pronunciation, including individual letters and phrases such as "بسم الله الرحمن الرحيم" (Bismillāhir-Raḥmānir-Raḥīm).

🌐 **Live Demo:** [http://34.107.44.238](http://34.107.44.238)

## 🚀 Features

- 📚 **Beginner Level** — Train pronunciation of all 28 Arabic alphabet letters.
- 📗 **Intermediate Level** — Practice the full phrase "Bismillah".
- 🧠 **Pronunciation Evaluation** — Your recording is compared with reference audio files.
- 💬 **Feedback System** — Get feedback based on pronunciation accuracy.
- 📈 **Progress Tracking** — Track number of recordings and average accuracy.
- 👤 **User Accounts** — Register, login, and store individual progress in a database.
- 🌐 **Multilingual UI** — Interface available in English and Russian.

## 🗂 Project Structure

```bash
├── interface.py                  # Streamlit interface (frontend)
├── backend.py                    # Flask backend (API & database)
├── pronunciation_evaluator.py   # Letter-level evaluation logic
├── phrase_evaluator.py          # Phrase-level evaluation logic
├── intermediate_module.py       # Module for "Bismillah" practice
├── requirements.txt
├── audio/
│   ├── etalon/
│   │   ├── letters/
│   │   │   ├── male/
│   │   │   └── female/
│   │   └── phrases/
│   │       ├── male/
│   │       └── female/
│   └── user/                    # User recordings
└── .session.json                # Local session data (login state)
