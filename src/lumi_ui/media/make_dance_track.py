import wave
import math
import struct
import os

def generate_techno_track(filename, duration_sec=15):
    filepath = f"/home/mallu/app_ui/lumi_ws/src/lumi_ui/media/{filename}"
    os.makedirs(os.path.dirname(filepath), exist_ok=True)
    
    sample_rate = 44100
    num_samples = duration_sec * sample_rate
    
    with wave.open(filepath, 'w') as wav_file:
        wav_file.setnchannels(1)
        wav_file.setsampwidth(2)
        wav_file.setframerate(sample_rate)
        
        for i in range(num_samples):
            t = i / sample_rate
            # 120 BPM = 2 beats per second = 0.5s per beat
            beat = t % 0.5
            
            # Kick drum simulation (pitch-drop at the start of every beat)
            kick_freq = max(50, 200 - (beat * 2000))
            kick = math.sin(2 * math.pi * kick_freq * t) * math.exp(-beat * 5)
            
            # Bassline (simple syncopated square wave)
            bass_note = 40 if int(t * 8) % 4 in [1, 2] else 55
            bass = 0.5 * (1 if math.sin(2 * math.pi * bass_note * t) > 0 else -1) * min(1.0, beat * 4)
            
            # Synth melody (changes every 2 seconds)
            melody_note = [440, 523.25, 659.25, 587.33][int(t / 2) % 4]
            synth = 0.3 * math.sin(2 * math.pi * melody_note * t) * math.exp(-(t % 0.25) * 4)
            
            # Mix together
            sample = (kick + bass + synth) * 0.4
            
            # Clamping to 16-bit PCM limit
            sample = max(-1.0, min(1.0, sample))
            wav_file.writeframes(struct.pack('h', int(sample * 32767.0)))

if __name__ == "__main__":
    generate_techno_track("dance_track.wav", 15)
    print("Synthetic dance track created successfully!")
