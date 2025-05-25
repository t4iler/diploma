import librosa
import numpy as np
from dtw import dtw
from numpy.linalg import norm

def evaluate_pronunciation(user_audio_path, etalon_audio_path):
    try:
        y_user, sr_user = librosa.load(user_audio_path, sr=None)
        y_etalon, sr_etalon = librosa.load(etalon_audio_path, sr=None)

        # Проверка: есть ли звук у пользователя
        if np.max(np.abs(y_user)) < 0.01 or len(y_user) < 1000:
            return 0.0, "Нет звука или голос слишком тихий."

        # Приведение к общей частоте
        if sr_user != sr_etalon:
            target_sr = min(sr_user, sr_etalon)
            y_user = librosa.resample(y_user, orig_sr=sr_user, target_sr=target_sr)
            y_etalon = librosa.resample(y_etalon, orig_sr=sr_etalon, target_sr=target_sr)
            sr = target_sr
        else:
            sr = sr_user

        # MFCC-признаки по времени
        mfcc_user = librosa.feature.mfcc(y=y_user, sr=sr, n_mfcc=13).T
        mfcc_etalon = librosa.feature.mfcc(y=y_etalon, sr=sr, n_mfcc=13).T

        # DTW сравнение
        distance, _, _, _ = dtw(mfcc_user, mfcc_etalon, dist=lambda x, y: norm(x - y))

        # Оценка по экспоненциальной шкале
        score = round(100 * np.exp(-distance / 30000), 2)

        # Интерпретация результата
        if score >= 90:
            feedback = "Отличное произношение!"
        elif score >= 75:
            feedback = "Хорошо, но можно немного улучшить."
        elif score >= 50:
            feedback = "Средне. Попробуй произнести чётче."
        else:
            feedback = "Попробуй ещё раз. Обрати внимание на звуки."

        return score, feedback

    except Exception as e:
        return None, f"❌ Ошибка при анализе: {str(e)}"
