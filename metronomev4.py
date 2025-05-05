import streamlit as st
import numpy as np
import random
import time
import io
from scipy.io import wavfile
from PIL import Image
import threading

sample_rate = 44100
note_freq_base = {'S': 261.63, 'R': 293.66, 'G': 329.63, 'M': 349.23, 'P': 392.00, 'D': 440.00, 'N': 493.88}
octave_multipliers = {'low': 0.5, 'medium': 1.0, 'high': 2.0}
image_base_url = "https://raw.githubusercontent.com/surajdwivedi0307/surajmetronome/main/images/"
stop_flag = threading.Event()

# --- Note and Audio Helpers ---
def parse_notes_input(note_string):
    parsed_sequence = []
    i = 0
    while i < len(note_string):
        if note_string[i] in [',', '-']:
            parsed_sequence.append(('-', 1, 'medium'))
            i += 1
        else:
            note = note_string[i]
            i += 1
            octave = 'medium'
            if i < len(note_string) and note_string[i] == '>':
                octave = 'high'; i += 1
            elif i < len(note_string) and note_string[i] == '<':
                octave = 'low'; i += 1
            count = 0
            while i < len(note_string) and note_string[i] == '_':
                count += 1; i += 1
            duration = 1 + count
            parsed_sequence.append((note, duration, octave))
    return parsed_sequence

def bpm_to_duration(bpm, note_length=1):
    return (60.0 / bpm) * note_length

def generate_note_wave(note, duration, octave='medium'):
    t = np.linspace(0, duration, int(sample_rate * duration), False)
    if note == '-': return np.zeros_like(t, dtype=np.int16)
    base_freq = note_freq_base[note] * octave_multipliers[octave]
    vibrato = 0.001 * np.sin(2 * np.pi * 2.5 * t)
    phase = 2 * np.pi * base_freq * t + vibrato
    tone = np.sin(phase) + 0.2 * np.sin(2 * phase) + 0.1 * np.sin(3 * phase)
    swell = np.sin(np.pi * t / duration)
    tone *= swell
    tone *= 32767 / np.max(np.abs(tone))
    return tone.astype(np.int16)

def play_notes_and_update_ui(sequence, bpm, audio_placeholder, note_display, timer_display, image_display):
    audio = np.array([], dtype=np.int16)
    total_duration = sum(bpm_to_duration(bpm, dur) for _, dur, _ in sequence)
    elapsed = 0

    # Generate audio
    for note, dur, octave in sequence:
        duration = bpm_to_duration(bpm, dur)
        wave = generate_note_wave(note, duration, octave)
        audio = np.concatenate((audio, wave))

    # Play audio in UI
    buf = io.BytesIO()
    wavfile.write(buf, sample_rate, audio)
    audio_placeholder.audio(buf.getvalue(), format='audio/wav')

    # Show progress in UI
    for note, dur, octave in sequence:
        if stop_flag.is_set(): break
        duration = bpm_to_duration(bpm, dur)
        elapsed += duration
        note_display.markdown(f"### 🎵 Playing: {note} ({octave})")
        timer_display.markdown(f"⏱️ {elapsed:.2f} / {total_duration:.2f} sec")

        if note != '-':
            img_url = f"{image_base_url}bansuri_notes_{note}.png"
            image_display.image(img_url, caption=f"{note} fingering", use_container_width=True)
        else:
            image_display.empty()
        time.sleep(duration)

# --- Streamlit UI ---
st.set_page_config(layout="centered")
st.title("🎶 Flute Metronome (Synced Audio + Image)")
bpm = st.number_input("BPM", min_value=40, max_value=200, value=60)
note_input = st.text_input("Enter melody:", "SRG-G,R-GS_")

audio_ph = st.empty()
note_ph = st.empty()
timer_ph = st.empty()
image_ph = st.empty()

if st.button("▶️ Play Notes"):
    stop_flag.clear()
    sequence = parse_notes_input(note_input)

    # Run UI updates and audio playback in a background thread
    threading.Thread(
        target=play_notes_and_update_ui,
        args=(sequence, bpm, audio_ph, note_ph, timer_ph, image_ph),
        daemon=True
    ).start()

if st.button("⏹️ Stop"):
    stop_flag.set()
