import librosa
import numpy as np
from scipy.spatial.distance import euclidean
from fastdtw import fastdtw

def feedback_message(score, lang="en"):
    if lang == "ru":
        if score >= 90:
            return "Отличное произношение!"
        elif score >= 75:
            return "Хорошо, но можно улучшить."
        elif score >= 50:
            return "Средне. Попробуйте произнести чётче."
        else:
            return "Попробуйте ещё раз. Обратите внимание на звуки."
    else:
        if score >= 90:
            return "Excellent pronunciation!"
        elif score >= 75:
            return "Good, but could be improved."
        elif score >= 50:
            return "Average. Try to pronounce more clearly."
        else:
            return "Try again. Focus on the sounds."

def evaluate_phrase_pronunciation(user_audio_path, etalon_audio_path, lang="en"):
    try:
        y_user, sr_user = librosa.load(user_audio_path, sr=None)
        y_etalon, sr_etalon = librosa.load(etalon_audio_path, sr=None)

        if sr_user != sr_etalon:
            sr = min(sr_user, sr_etalon)
            y_user = librosa.resample(y_user, orig_sr=sr_user, target_sr=sr)
            y_etalon = librosa.resample(y_etalon, orig_sr=sr_etalon, target_sr=sr)
        else:
            sr = sr_user

        mfcc_user = librosa.feature.mfcc(y=y_user, sr=sr, n_mfcc=13)
        mfcc_etalon = librosa.feature.mfcc(y=y_etalon, sr=sr, n_mfcc=13)

        distance, _ = fastdtw(mfcc_user.T, mfcc_etalon.T, dist=euclidean)
        score = round(100 * np.exp(-distance / 150000), 2)
        feedback = feedback_message(score, lang)

        return score, feedback

    except Exception as e:
        return None, f"Ошибка при анализе: {str(e)}"
