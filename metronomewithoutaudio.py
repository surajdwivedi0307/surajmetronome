import streamlit as st
import numpy as np
import random
import time
import threading

# Global
saved_melodies = []
stop_flag = threading.Event()

note_freq_base = {
    'S': 261.63, 'R': 293.66, 'G': 329.63, 'M': 349.23,
    'P': 392.00, 'D': 440.00, 'N': 493.88
}
octave_multipliers = {'low': 0.5, 'medium': 1.0, 'high': 2.0}
image_base_url = "https://raw.githubusercontent.com/surajdwivedi0307/surajmetronome/main/images/"

def parse_notes_input(note_string):
    parsed_sequence = []
    entry = note_string.strip()
    i = 0
    while i < len(entry):
        if entry[i] in [',', '-']:
            parsed_sequence.append(('-', 1, 'medium'))
            i += 1
        else:
            note = entry[i]
            i += 1
            if note not in note_freq_base:
                continue
            octave = 'medium'
            if i < len(entry) and entry[i] == '>':
                octave = 'high'
                i += 1
            elif i < len(entry) and entry[i] == '<':
                octave = 'low'
                i += 1
            count = 0
            while i < len(entry) and entry[i] == '_':
                count += 1
                i += 1
            duration = 1 + count
            parsed_sequence.append((note, duration, octave))
    return parsed_sequence

def bpm_to_duration(bpm, note_length=1):
    return (60.0 / bpm) * note_length

def generate_random_melody(length=12):
    notes = ['S', 'R', 'G', 'M', 'P', 'D', 'N', '-']
    octaves = ['', '>', '<']
    melody = ''
    for _ in range(length):
        note = random.choice(notes)
        octave = random.choice(octaves) if note != '-' else ''
        underscore = '_' * random.randint(0, 2)
        separator = ',' if random.random() < 0.15 else ''
        melody += f"{note}{octave}{underscore}{separator}"
    return melody

def save_melodies_to_file(melodies, filename='saved_melodies.txt'):
    with open(filename, 'w') as f:
        for melody in melodies:
            f.write(melody + '\n')

def display_note_progress_bar(parsed_sequence, bpm):
    note_text = st.empty()
    next_note_text = st.empty()
    progress_bar = st.progress(0)
    image_display = st.empty()
    container = st.empty()

    total_duration = sum(bpm_to_duration(bpm, duration) for _, duration, _ in parsed_sequence)
    elapsed = 0

    for i, (note, duration_mult, octave) in enumerate(parsed_sequence):
        if stop_flag.is_set():
            break

        duration = bpm_to_duration(bpm, duration_mult)
        next_note = parsed_sequence[i + 1][0] if i + 1 < len(parsed_sequence) else '—'
        current_note_label = f"{note} ({octave})" if note != '-' else "Rest"
        next_note_label = f"Next: {next_note}" if next_note != '-' else "Next: Rest"

        steps = 25
        for step in range(steps):
            if stop_flag.is_set():
                break

            time.sleep(duration / steps)
            elapsed += duration / steps
            overall_progress = min(int((elapsed / total_duration) * 100), 100)

            seconds_left = duration - (step * (duration / steps))
            seconds_left_disp = f"{seconds_left:.1f}s"

            # Flash effect
            flash = (seconds_left < 0.5) and (step % 2 == 0)
            color = "red" if flash else "black"

            note_text.markdown(f"<h3 style='color:{color}'>🎵 Playing: {current_note_label} — ⏱️ {seconds_left_disp}</h3>", unsafe_allow_html=True)
            next_note_text.markdown(f"<h5>⏭️ {next_note_label}</h5>", unsafe_allow_html=True)
            progress_bar.progress(overall_progress)

        # Show image
        if note in note_freq_base:
            img_url = f"{image_base_url}bansuri_notes_{note}.png"
            image_display.image(img_url, caption=f"{note} fingering", use_container_width=True)
        else:
            image_display.empty()

    note_text.markdown("### ✅ Done!")
    next_note_text.empty()
    image_display.empty()
    progress_bar.progress(100)

# Streamlit UI
st.set_page_config(layout="wide")
st.title("🎶 Indian Flute Visual Metronome + Melody Generator 🎶")
st.write("Follow note timing visually with progress bar and flute fingering images.")

bpm_input_user = st.number_input("Enter BPM:", min_value=1, max_value=200, value=60)
user_input = st.text_input("Enter sequence (e.g., SGRG_RSN):", "DS>DP,GRSR,G-GR,GPD_")

col1, col2 = st.columns([1, 1])
with col1:
    st.markdown("#### 🎵 Control Panel")
    if st.button("▶️ Play Notes"):
        stop_flag.clear()
        parsed_user = parse_notes_input(user_input)
        if not parsed_user:
            st.error("Invalid input sequence.")
        else:
            display_note_progress_bar(parsed_user, bpm_input_user)

with col2:
    st.markdown("#### 🎶 Melody Generator")
    if st.button("⏹️ Stop"):
        stop_flag.set()

    if st.button("🎲 Generate Random Melody"):
        stop_flag.clear()
        random_melody = generate_random_melody()
        saved_melodies.append(random_melody)
        st.write(f"**Random Melody:** `{random_melody}`")
        parsed_random = parse_notes_input(random_melody)
        display_note_progress_bar(parsed_random, bpm_input_user)

    if st.button("💾 Save All Generated Melodies"):
        if saved_melodies:
            save_melodies_to_file(saved_melodies)
            st.success("Melodies saved to 'saved_melodies.txt'.")
        else:
            st.warning("No melodies to save.")
