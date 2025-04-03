import streamlit as st
import librosa
import numpy as np
from dtw import dtw
import pyaudio
import wave
import os

def record_audio(output_dir="audio/user_audio", filename="user_bismillah.wav"):
    CHUNK = 1024
    FORMAT = pyaudio.paInt16
    CHANNELS = 1
    RATE = 16000
    RECORD_SECONDS = 9
    OUTPUT_PATH = os.path.join(output_dir, filename)

    if not os.path.exists(output_dir):
        os.makedirs(output_dir)

    audio = pyaudio.PyAudio()
    stream = audio.open(format=FORMAT, channels=CHANNELS, rate=RATE, input=True, frames_per_buffer=CHUNK)
    st.write("Говори 'Bismillahir Rahmanir Rahim' сейчас!")
    frames = []

    for i in range(0, int(RATE / CHUNK * RECORD_SECONDS)):
        data = stream.read(CHUNK)
        frames.append(data)

    stream.stop_stream()
    stream.close()
    audio.terminate()

    wf = wave.open(OUTPUT_PATH, 'wb')
    wf.setnchannels(CHANNELS)
    wf.setsampwidth(audio.get_sample_size(FORMAT))
    wf.setframerate(RATE)
    wf.writeframes(b''.join(frames))
    wf.close()

def preprocess_audio(audio, sr):
    audio, _ = librosa.effects.trim(audio, top_db=20)
    audio = librosa.util.normalize(audio)
    return audio

st.title("Анализ произношения 'Bismillahir Rahmanir Rahim'")

if st.button("Записать произношение"):
    record_audio()
    user_file = "audio/user_audio/user_bismillah.wav"
    etalon_dir = "audio/etalon"

    user, sr = librosa.load(user_file, sr=16000)
    user = preprocess_audio(user, sr)
    segments = librosa.effects.split(user, top_db=15)
    parts = ["Bism", "Allah", "Rahman", "Rahim"]

    st.write(f"Найдено сегментов: {len(segments)}")

    etalon_files = [f for f in os.listdir(etalon_dir) if f.endswith(".wav")]
    min_distance_total = float('inf')
    best_etalon = None
    best_segments = None
    best_feedback = []

    for etalon_file in etalon_files:
        etalon_path = os.path.join(etalon_dir, etalon_file)
        etalon, sr = librosa.load(etalon_path, sr=16000)
        etalon = preprocess_audio(etalon, sr)
        
        if len(etalon) > len(user):
            etalon = etalon[:len(user)]
        elif len(etalon) < len(user):
            etalon = np.pad(etalon, (0, len(user) - len(etalon)), mode='constant')
        
        etalon_segments = librosa.effects.split(etalon, top_db=15)

        if len(segments) == len(etalon_segments):
            total_distance = 0
            segment_distances = []
            feedback = []
            for i, (user_seg, etalon_seg) in enumerate(zip(segments, etalon_segments)):
                user_part = user[user_seg[0]:user_seg[1]]
                etalon_part = etalon[etalon_seg[0]:etalon_seg[1]]
                
                mfcc_user = librosa.feature.mfcc(y=user_part, sr=sr, n_mfcc=13)
                mfcc_etalon = librosa.feature.mfcc(y=etalon_part, sr=sr, n_mfcc=13)
                
                # Исправленный DTW
                dtw_result = dtw(mfcc_user.T, mfcc_etalon.T, distance_only=True)
                distance = dtw_result.distance
                total_distance += distance
                segment_distances.append(distance)
                if distance > 50 and i < len(parts):
                    feedback.append(f"Проверьте часть '{parts[i]}' (расстояние: {distance:.2f})")

            if total_distance < min_distance_total:
                min_distance_total = total_distance
                best_etalon = etalon_file
                best_segments = segment_distances
                best_feedback = feedback

    st.write(f"Ближайший эталон: {best_etalon} с общим расстоянием {min_distance_total:.2f}")
    if best_segments:
        for i, dist in enumerate(best_segments):
            part_name = parts[i] if i < len(parts) else f"Сегмент {i+1}"
            st.write(f"Расстояние для '{part_name}': {dist:.2f}")

    for etalon_file in etalon_files:
        etalon_path = os.path.join(etalon_dir, etalon_file)
        etalon, sr = librosa.load(etalon_path, sr=16000)
        etalon = preprocess_audio(etalon, sr)
        if len(etalon) > len(user):
            etalon = etalon[:len(user)]
        elif len(etalon) < len(user):
            etalon = np.pad(etalon, (0, len(user) - len(etalon)), mode='constant')
        mfcc_etalon = librosa.feature.mfcc(y=etalon, sr=sr, n_mfcc=13)
        mfcc_user = librosa.feature.mfcc(y=user, sr=sr, n_mfcc=13)
        dtw_result = dtw(mfcc_user.T, mfcc_etalon.T, distance_only=True)
        distance = dtw_result.distance
        st.write(f"Расстояние до {etalon_file} (вся фраза): {distance}")

    if len(segments) < 4:
        st.error("Недостаточно сегментов. Возможно, фраза неполная.")
    elif min_distance_total < 200:
        st.success("Произношение похоже на эталон!")
    elif min_distance_total < 300 and len(best_feedback) <= 1:
        st.warning("Произношение близкое, но есть небольшие отличия:")
        for fb in best_feedback:
            st.write(fb)
    else:
        st.error("Есть явные отличия:")
        for fb in best_feedback:
            st.write(fb)

if st.button("Прослушать все эталонные записи"):
    etalon_dir = "audio/etalon"
    for etalon_file in os.listdir(etalon_dir):
        if etalon_file.endswith(".wav"):
            st.write(f"Эталон: {etalon_file}")
            st.audio(os.path.join(etalon_dir, etalon_file))