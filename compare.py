import librosa
import numpy as np
from scipy.spatial.distance import euclidean
import os

ETALON_DIR = "audio/etalon"
USER_FILE = "audio/user_audio/user_bismillah.wav"

user, sr = librosa.load(USER_FILE, sr=16000)
mfcc_user = librosa.feature.mfcc(y=user, sr=sr, n_mfcc=13)
mfcc_user_mean = np.mean(mfcc_user, axis=1)

etalon_files = [f for f in os.listdir(ETALON_DIR) if f.endswith(".wav")]
distances = []

for etalon_file in etalon_files:
    etalon_path = os.path.join(ETALON_DIR, etalon_file)
    etalon, sr = librosa.load(etalon_path, sr=16000)
    mfcc_etalon = librosa.feature.mfcc(y=etalon, sr=sr, n_mfcc=13)
    mfcc_etalon_mean = np.mean(mfcc_etalon, axis=1)
    
    distance = euclidean(mfcc_etalon_mean, mfcc_user_mean)
    distances.append((etalon_file, distance))
    print(f"Расстояние до {etalon_file}: {distance}")

min_distance = min(distances, key=lambda x: x[1])
print(f"Ближайший эталон: {min_distance[0]} с расстоянием {min_distance[1]}")

threshold = 100
if min_distance[1] < threshold:
    print("Произношение похоже на эталон! Отличная работа.")
elif min_distance[1] < 120:
    print("Произношение близкое, попробуйте чуть удлинить звуки, например, в 'Rahmaan' или 'Raheem'.")
else:
    print("Есть явные отличия, послушайте эталон и обратите внимание на 'Allah' или 'Rahim'.")