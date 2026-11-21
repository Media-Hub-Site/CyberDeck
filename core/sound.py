# core/sound.py
import math
import struct
import pygame

class SoundEngine:
    """Motor de síntesis procedimental en tiempo real sin dependencias de audio externas."""
    _instance = None

    @classmethod
    def get_instance(cls):
        if cls._instance is None:
            cls._instance = SoundEngine()
        return cls._instance

    def __init__(self):
        self.enabled = False
        self.muted = False
        self.sounds = {}
        try:
            if not pygame.mixer.get_init():
                pygame.mixer.init(frequency=44100, size=-16, channels=1, buffer=512)
            self.enabled = True
            self.sounds = {
                'click': self._generate_tone(lambda t, f: 550 - f * 220, 0.04, 0.20, 'sine'),
                'select': self._generate_tone(lambda t, f: 720, 0.03, 0.18, 'sine'),
                'power': self._generate_tone(lambda t, f: 600 + f * 450, 0.07, 0.22, 'sine'),
                'win': self._generate_arpeggio([523, 659, 784, 1046], 0.09, 0.25),
                'game_over': self._generate_tone(lambda t, f: 220 - f * 140, 0.35, 0.28, 'saw'),
                'tick': self._generate_tone(lambda t, f: 880, 0.02, 0.12, 'sine'),
                'match': self._generate_arpeggio([659, 880], 0.06, 0.22),
            }
        except Exception as e:
            print(f"[SoundEngine] Error de inicialización: {e}")

    def _generate_tone(self, freq_func, duration, volume=0.25, wave_type='sine'):
        sample_rate = 44100
        n_samples = int(sample_rate * duration)
        buf = bytearray()
        for i in range(n_samples):
            t = i / sample_rate
            frac = i / n_samples
            env = (1.0 - frac) if frac > 0.08 else (frac / 0.08)
            freq = freq_func(t, frac)
            phase = 2 * math.pi * freq * t
            if wave_type == 'sine':
                val = math.sin(phase)
            elif wave_type == 'saw':
                val = 2.0 * (t * freq - math.floor(0.5 + t * freq))
            else:
                val = 1.0 if math.sin(phase) > 0 else -1.0
            sample = int(32767 * volume * env * val)
            buf.extend(struct.pack('<h', max(-32767, min(32767, sample))))
        return pygame.mixer.Sound(buffer=bytes(buf))

    def _generate_arpeggio(self, freqs, note_duration, volume=0.25):
        sample_rate = 44100
        buf = bytearray()
        samples_per_note = int(sample_rate * note_duration)
        for freq in freqs:
            for i in range(samples_per_note):
                t = i / sample_rate
                frac = i / samples_per_note
                env = (1.0 - frac * 0.7) if frac > 0.1 else (frac / 0.1)
                val = math.sin(2 * math.pi * freq * t)
                sample = int(32767 * volume * env * val)
                buf.extend(struct.pack('<h', max(-32767, min(32767, sample))))
        return pygame.mixer.Sound(buffer=bytes(buf))

    def play(self, sound_name):
        if self.enabled and not self.muted and sound_name in self.sounds:
            try:
                self.sounds[sound_name].play()
            except Exception:
                pass

    def toggle_mute(self):
        self.muted = not self.muted
        return self.muted
