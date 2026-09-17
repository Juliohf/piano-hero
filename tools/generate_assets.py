import json
import os
import wave
import numpy as np
import mido

HERE = os.path.dirname(os.path.abspath(__file__))
ASSETS = os.path.join(HERE, "..", "assets")
MIDI_PATH = os.path.join(HERE, "moonlight.mid")

SR = 44100
CLIP_SECONDS = 60.0
FADE_OUT = 2.5
LANES = 4


def extract_notes(path):
    mid = mido.MidiFile(path)
    tpb = mid.ticks_per_beat
    cur_tempo = 500000
    abs_sec = 0.0
    active = {}
    notes = []
    for msg in mido.merge_tracks(mid.tracks):
        abs_sec += mido.tick2second(msg.time, tpb, cur_tempo)
        if msg.type == "set_tempo":
            cur_tempo = msg.tempo
        elif msg.type == "note_on" and msg.velocity > 0:
            active.setdefault(msg.note, []).append((abs_sec, msg.velocity))
        elif msg.type == "note_off" or (msg.type == "note_on" and msg.velocity == 0):
            if active.get(msg.note):
                st, vel = active[msg.note].pop(0)
                notes.append((st, abs_sec, msg.note, vel))
    notes.sort()
    seen = set()
    uniq = []
    for n in notes:
        key = (round(n[0], 4), round(n[1], 4), n[2])
        if key not in seen:
            seen.add(key)
            uniq.append(n)
    return uniq


def midi_to_freq(m):
    return 440.0 * (2.0 ** ((m - 69) / 12.0))


def render_note(freq, dur, vel):
    dur = min(dur, 6.0) + 0.25
    n = int(dur * SR)
    t = np.arange(n) / SR
    harmonics = [(1, 1.0), (2, 0.45), (3, 0.30), (4, 0.18), (5, 0.10), (6, 0.06)]
    wave_arr = np.zeros(n, dtype=np.float32)
    for k, amp in harmonics:
        decay = np.exp(-t * (1.6 + 0.9 * k))
        wave_arr += amp * decay * np.sin(2 * np.pi * freq * k * t)
    atk = int(0.005 * SR)
    if atk > 0:
        wave_arr[:atk] *= np.linspace(0, 1, atk)
    rel = int(0.06 * SR)
    if rel > 0 and n > rel:
        wave_arr[-rel:] *= np.linspace(1, 0, rel)
    gain = 0.12 + 0.18 * (vel / 127.0)
    return (wave_arr * gain).astype(np.float32)


def synth_audio(notes):
    total = int((CLIP_SECONDS + 1.0) * SR)
    buf = np.zeros(total, dtype=np.float32)
    for st, en, pitch, vel in notes:
        if st >= CLIP_SECONDS:
            continue
        seg = render_note(midi_to_freq(pitch), en - st, vel)
        i = int(st * SR)
        j = min(i + len(seg), total)
        buf[i:j] += seg[: j - i]
    buf = buf[: int(CLIP_SECONDS * SR)]
    fade = int(FADE_OUT * SR)
    if fade > 0:
        buf[-fade:] *= np.linspace(1, 0, fade)
    peak = np.max(np.abs(buf)) or 1.0
    return buf / peak * 0.89


def write_wav(path, mono):
    data16 = np.int16(np.clip(mono, -1, 1) * 32767)
    with wave.open(path, "w") as w:
        w.setnchannels(1)
        w.setsampwidth(2)
        w.setframerate(SR)
        w.writeframes(data16.tobytes())


def synth_sfx():
    t = np.arange(int(0.09 * SR)) / SR
    hit = (np.sin(2 * np.pi * 880 * t) * np.exp(-t * 28) +
           0.6 * np.sin(2 * np.pi * 1320 * t) * np.exp(-t * 30))
    hit = hit / (np.max(np.abs(hit)) or 1) * 0.6
    write_wav(os.path.join(ASSETS, "hit.wav"), hit.astype(np.float32))
    t2 = np.arange(int(0.16 * SR)) / SR
    miss = np.sin(2 * np.pi * 150 * t2) * np.exp(-t2 * 14)
    miss = miss / (np.max(np.abs(miss)) or 1) * 0.5
    write_wav(os.path.join(ASSETS, "miss.wav"), miss.astype(np.float32))


def pitch_to_lane(pitch):
    if pitch < 59:
        return 0
    elif pitch < 63:
        return 1
    elif pitch < 67:
        return 2
    else:
        return 3


def build_chart(notes):
    events = []
    last_in_lane = {i: -10.0 for i in range(LANES)}
    for st, en, pitch, vel in sorted(notes):
        if st >= CLIP_SECONDS - 0.3:
            continue
        if en - st > 2.0:
            continue
        if pitch < 50:
            continue
        lane = pitch_to_lane(pitch)
        if st - last_in_lane[lane] < 0.12:
            continue
        last_in_lane[lane] = st
        events.append({"t": round(st, 4), "lane": lane})
    events.sort(key=lambda e: e["t"])
    return events


def main():
    os.makedirs(ASSETS, exist_ok=True)
    notes = extract_notes(MIDI_PATH)
    audio = synth_audio(notes)
    write_wav(os.path.join(ASSETS, "music.wav"), audio)
    synth_sfx()
    chart = build_chart(notes)
    meta = {
        "title": "Moonlight Sonata - 1o Movimento (Beethoven)",
        "duration": CLIP_SECONDS,
        "music": "music.wav",
        "lanes": LANES,
        "notes": chart,
    }
    with open(os.path.join(ASSETS, "chart.json"), "w", encoding="utf-8") as f:
        json.dump(meta, f, ensure_ascii=False, indent=1)
    print("music.wav, hit.wav, miss.wav, chart.json gerados |", len(chart), "setas")


if __name__ == "__main__":
    main()
