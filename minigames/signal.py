# minigames/signal.py
# Minijuego de calibración de osciloscopio analógico / sincronizador de frecuencias
import math
import random
import pygame
from core.theme import (
    COLOR_BG, COLOR_PANEL, COLOR_BORDER, COLOR_BORDER_FOCUS,
    COLOR_CYAN, COLOR_GREEN, COLOR_MAGENTA, COLOR_YELLOW,
    COLOR_TEXT, COLOR_TEXT_MUTED, COLOR_TEXT_DARK, COLOR_ACCENT,
    WINDOW_WIDTH, WINDOW_HEIGHT
)

class SignalGame:
    def __init__(self, sound_engine):
        self.sounds = sound_engine
        self.level = 1
        self.score = 0
        self.time_left = 45.0
        self.game_state = "PLAYING" # PLAYING, WIN_LEVEL, GAME_OVER

        self.font_large = pygame.font.SysFont("Segoe UI, Arial, sans-serif", 30, bold=True)
        self.font_mid = pygame.font.SysFont("Segoe UI, Arial, sans-serif", 18, bold=True)
        self.font_mono = pygame.font.SysFont("Consolas, Courier New, monospace", 14, bold=True)
        self.font_small = pygame.font.SysFont("Segoe UI, Arial, sans-serif", 13)

        self.wave_time = 0.0
        self.sync_progress = 0.0
        self.hold_sync_time = 0.0
        self.last_tick_sec = 10

        # Sliders analógicos grandes
        self.slider_y = 465
        self.card_w = 190
        self.card_h = 145
        self.track_margin_x = 20
        self.track_y_rel = 90
        self.track_h = 10

        self.sliders = [
            {"id": "amp", "name": "AMPLITUD", "val": 30, "min": 15, "max": 60, "step": 1, "unit": "mV"},
            {"id": "freq", "name": "FRECUENCIA", "val": 2.0, "min": 1.0, "max": 4.5, "step": 0.1, "unit": "GHz"},
            {"id": "phase", "name": "FASE", "val": 90, "min": 0, "max": 360, "step": 5, "unit": "°"}
        ]
        self.active_slider = None
        self.hovered_slider = None

        self.init_level()

    def init_level(self):
        self.game_state = "PLAYING"
        self.time_left = max(30.0, 50.0 - self.level * 3.0)
        self.hold_sync_time = 0.0
        self.last_tick_sec = 10

        # Generar onda objetivo aleatoria
        self.target_amp = random.randint(20, 55)
        self.target_freq = round(random.uniform(1.2, 4.0), 1)
        self.target_phase = random.randint(20, 320)

        # Distorsionar onda del jugador para que no empiece resuelta
        self.sliders[0]["val"] = 15 if self.target_amp > 35 else 55
        self.sliders[1]["val"] = 1.0 if self.target_freq > 2.5 else 4.0
        self.sliders[2]["val"] = (self.target_phase + 180) % 360

    def calculate_sync(self):
        d_amp = abs(self.sliders[0]["val"] - self.target_amp) / (self.sliders[0]["max"] - self.sliders[0]["min"])
        d_freq = abs(self.sliders[1]["val"] - self.target_freq) / (self.sliders[1]["max"] - self.sliders[1]["min"])
        
        phase_diff = abs(self.sliders[2]["val"] - self.target_phase)
        if phase_diff > 180:
            phase_diff = 360 - phase_diff
        d_phase = phase_diff / 180.0

        # Tolerancia permisiva para buena jugabilidad
        match_amp = max(0.0, 1.0 - (d_amp * 2.5))
        match_freq = max(0.0, 1.0 - (d_freq * 2.8))
        match_phase = max(0.0, 1.0 - (d_phase * 2.5))

        total_sync = (match_amp * 0.35 + match_freq * 0.40 + match_phase * 0.25)
        return min(1.0, max(0.0, total_sync))

    def _get_track_rect(self, idx):
        sx = 335 + idx * (self.card_w + 15)
        track_x = sx + self.track_margin_x
        track_y = self.slider_y + self.track_y_rel
        track_w = self.card_w - (self.track_margin_x * 2)
        return pygame.Rect(track_x, track_y, track_w, self.track_h)

    def _get_card_rect(self, idx):
        sx = 335 + idx * (self.card_w + 15)
        return pygame.Rect(sx, self.slider_y, self.card_w, self.card_h)

    def _update_slider_from_mouse(self, idx, mx):
        track_rect = self._get_track_rect(idx)
        s = self.sliders[idx]
        ratio = max(0.0, min(1.0, (mx - track_rect.x) / track_rect.width))
        new_val = s["min"] + ratio * (s["max"] - s["min"])
        if s["step"] >= 1:
            s["val"] = int(round(new_val))
        else:
            s["val"] = round(new_val, 1)

    def handle_click(self, pos):
        if self.game_state != "PLAYING":
            if self.game_state == "WIN_LEVEL":
                self.level += 1
                self.init_level()
            elif self.game_state == "GAME_OVER":
                self.level = 1
                self.score = 0
                self.init_level()
            return

        mx, my = pos
        # Comprobar si hizo clic en una tarjeta de slider o en su riel
        for idx in range(len(self.sliders)):
            card_rect = self._get_card_rect(idx)
            # Zona interactiva amplia de deslizador
            slider_touch_zone = pygame.Rect(card_rect.x, self.slider_y + 60, card_rect.width, 75)
            if slider_touch_zone.collidepoint(mx, my):
                self.active_slider = idx
                self._update_slider_from_mouse(idx, mx)
                self.sounds.play('click')
                return

    def update(self, dt):
        self.wave_time += dt * 3.0

        if self.game_state == "PLAYING":
            self.time_left -= dt
            sec = int(self.time_left)
            if sec <= 10 and sec < self.last_tick_sec and sec > 0:
                self.last_tick_sec = sec
                self.sounds.play('tick')

            if self.time_left <= 0:
                self.time_left = 0
                self.game_state = "GAME_OVER"
                self.sounds.play('game_over')

            # Manejo de arrastre fluido con el mouse
            mouse_buttons = pygame.mouse.get_pressed()
            mx, my = pygame.mouse.get_pos()

            if mouse_buttons[0]:
                if self.active_slider is not None:
                    self._update_slider_from_mouse(self.active_slider, mx)
                else:
                    # Iniciar arrastre si pulsa en cualquier deslizador
                    for idx in range(len(self.sliders)):
                        touch_zone = pygame.Rect(self._get_card_rect(idx).x, self.slider_y + 60, self.card_w, 75)
                        if touch_zone.collidepoint(mx, my):
                            self.active_slider = idx
                            self._update_slider_from_mouse(idx, mx)
                            break
            else:
                self.active_slider = None

            # Detectar hover para iluminar el dial
            self.hovered_slider = None
            for idx in range(len(self.sliders)):
                if self._get_card_rect(idx).collidepoint(mx, my):
                    self.hovered_slider = idx
                    break

            # Evaluar resonancia
            self.sync_progress = self.calculate_sync()
            if self.sync_progress >= 0.94:
                self.hold_sync_time += dt
                if self.hold_sync_time >= 0.7:
                    self.game_state = "WIN_LEVEL"
                    bonus = max(180, int(self.time_left * 40))
                    self.score += bonus
                    self.sounds.play('win')
            else:
                self.hold_sync_time = max(0.0, self.hold_sync_time - dt * 2.0)

    def draw(self, screen):
        # Panel lateral
        panel = pygame.Rect(20, 20, 280, WINDOW_HEIGHT - 40)
        pygame.draw.rect(screen, COLOR_PANEL, panel, border_radius=12)
        pygame.draw.rect(screen, COLOR_BORDER, panel, width=1, border_radius=12)

        screen.blit(self.font_small.render("MODULO // 03", True, COLOR_MAGENTA), (40, 38))
        screen.blit(self.font_large.render("SIGNAL SYNC", True, COLOR_TEXT), (40, 58))
        pygame.draw.line(screen, COLOR_BORDER, (40, 102), (280, 102), 1)

        y = 120
        stats = [
            ("NIVEL", f"{self.level:02d}"),
            ("PUNTAJE", f"{self.score:05d}"),
            ("RESONANCIA", f"{int(self.sync_progress * 100)}%"),
            ("TIEMPO", f"{max(0, int(self.time_left))}s"),
        ]
        for label, val in stats:
            screen.blit(self.font_small.render(label, True, COLOR_TEXT_MUTED), (40, y))
            val_col = COLOR_GREEN if label == "RESONANCIA" and self.sync_progress > 0.9 else COLOR_TEXT
            if label == "TIEMPO" and self.time_left <= 10:
                val_col = COLOR_MAGENTA
            screen.blit(self.font_mid.render(val, True, val_col), (40, y + 20))
            y += 52

        # Barra de tiempo
        bar_w = 240
        ratio = max(0.0, min(1.0, self.time_left / 45.0))
        pygame.draw.rect(screen, COLOR_BORDER, (40, y + 5, bar_w, 8), border_radius=4)
        pygame.draw.rect(screen, COLOR_GREEN if ratio > 0.25 else COLOR_MAGENTA, (40, y + 5, int(bar_w * ratio), 8), border_radius=4)

        # Controles
        screen.blit(self.font_small.render("• Arrastra los 3 deslizadores", True, COLOR_TEXT_MUTED), (40, WINDOW_HEIGHT - 120))
        screen.blit(self.font_small.render("• Sintoniza la onda cian con la roja", True, COLOR_TEXT_MUTED), (40, WINDOW_HEIGHT - 100))
        screen.blit(self.font_small.render("• [ESC]: Regresar al menú", True, COLOR_ACCENT), (40, WINDOW_HEIGHT - 80))

        # Pantalla del Osciloscopio
        scope_rect = pygame.Rect(330, 20, 600, 425)
        pygame.draw.rect(screen, (10, 14, 20), scope_rect, border_radius=12)
        pygame.draw.rect(screen, COLOR_BORDER_FOCUS if self.sync_progress > 0.9 else COLOR_BORDER, scope_rect, width=1, border_radius=12)

        # Rejilla del osciloscopio
        center_y = scope_rect.y + scope_rect.height // 2
        for gx in range(scope_rect.x, scope_rect.x + scope_rect.width, 50):
            pygame.draw.line(screen, (22, 28, 38), (gx, scope_rect.y), (gx, scope_rect.y + scope_rect.height), 1)
        for gy in range(scope_rect.y, scope_rect.y + scope_rect.height, 40):
            pygame.draw.line(screen, (22, 28, 38), (scope_rect.x, gy), (scope_rect.x + scope_rect.width, gy), 1)

        pygame.draw.line(screen, (40, 50, 68), (scope_rect.x, center_y), (scope_rect.x + scope_rect.width, center_y), 1)

        # Dibujar Ondas
        target_pts = []
        player_pts = []
        steps = scope_rect.width

        p_amp = self.sliders[0]["val"]
        p_freq = self.sliders[1]["val"]
        p_phase = math.radians(self.sliders[2]["val"])

        t_phase = math.radians(self.target_phase)

        for px in range(0, steps, 2):
            x = scope_rect.x + px
            angle = (px / 60.0)

            # Onda objetivo (roja/magenta)
            y_tgt = center_y + self.target_amp * math.sin(angle * self.target_freq + t_phase + self.wave_time)
            target_pts.append((x, int(y_tgt)))

            # Onda del jugador (cian)
            y_plr = center_y + p_amp * math.sin(angle * p_freq + p_phase + self.wave_time)
            player_pts.append((x, int(y_plr)))

        if len(target_pts) > 1:
            pygame.draw.lines(screen, COLOR_MAGENTA, False, target_pts, 2)
        if len(player_pts) > 1:
            color_wave = COLOR_GREEN if self.sync_progress >= 0.94 else COLOR_CYAN
            pygame.draw.lines(screen, color_wave, False, player_pts, 3)

        # Leyenda de onda en pantalla
        screen.blit(self.font_mono.render("[SEÑAL CIFRADA]", True, COLOR_MAGENTA), (scope_rect.x + 20, scope_rect.y + 20))
        screen.blit(self.font_mono.render("[TU MODULADOR]", True, COLOR_CYAN if self.sync_progress < 0.94 else COLOR_GREEN), (scope_rect.x + 20, scope_rect.y + 40))

        # Barra de Resonancia inferior en el osciloscopio
        res_rect = pygame.Rect(scope_rect.x + 20, scope_rect.bottom - 40, scope_rect.width - 40, 14)
        pygame.draw.rect(screen, COLOR_PANEL, res_rect, border_radius=7)
        res_fill = int(res_rect.width * self.sync_progress)
        pygame.draw.rect(screen, COLOR_GREEN if self.sync_progress >= 0.94 else COLOR_CYAN,
                         (res_rect.x, res_rect.y, res_fill, res_rect.height), border_radius=7)
        pygame.draw.rect(screen, COLOR_BORDER, res_rect, width=1, border_radius=7)

        # Controles Analógicos Inferiores (Sliders de ancho completo)
        for idx, s in enumerate(self.sliders):
            card_rect = self._get_card_rect(idx)
            is_hover = (self.hovered_slider == idx) or (self.active_slider == idx)

            pygame.draw.rect(screen, (24, 30, 40) if is_hover else COLOR_PANEL, card_rect, border_radius=10)
            pygame.draw.rect(screen, COLOR_CYAN if is_hover else COLOR_BORDER, card_rect, width=1, border_radius=10)

            # Nombre y valor en tiempo real
            screen.blit(self.font_small.render(s["name"], True, COLOR_TEXT_MUTED), (card_rect.x + 18, card_rect.y + 16))
            val_txt = f"{s['val']} {s['unit']}"
            screen.blit(self.font_large.render(val_txt, True, COLOR_CYAN), (card_rect.x + 18, card_rect.y + 36))

            # Riel del Slider
            track = self._get_track_rect(idx)
            val_ratio = (s["val"] - s["min"]) / (s["max"] - s["min"])

            # Fondo del riel
            pygame.draw.rect(screen, (15, 18, 24), track, border_radius=5)
            # Relleno activo del riel
            active_w = int(val_ratio * track.width)
            if active_w > 0:
                pygame.draw.rect(screen, COLOR_CYAN, (track.x, track.y, active_w, track.height), border_radius=5)

            # Pomo / Dial del Slider (grande y fácil de agarrar)
            thumb_cx = track.x + active_w
            thumb_cy = track.y + track.height // 2
            thumb_r = 12 if is_hover else 10
            # Resplandor al interactuar
            if is_hover:
                pygame.draw.circle(screen, (0, 240, 255, 60), (thumb_cx, thumb_cy), thumb_r + 4)
            pygame.draw.circle(screen, (255, 255, 255), (thumb_cx, thumb_cy), thumb_r)
            pygame.draw.circle(screen, COLOR_CYAN, (thumb_cx, thumb_cy), thumb_r - 3)

            # Guías mínimas y máximas en texto sutil
            min_lbl = self.font_small.render(f"{s['min']}", True, COLOR_TEXT_DARK)
            max_lbl = self.font_small.render(f"{s['max']}", True, COLOR_TEXT_DARK)
            screen.blit(min_lbl, (track.x, track.bottom + 8))
            screen.blit(max_lbl, (track.right - max_lbl.get_width(), track.bottom + 8))

        # Overlays
        if self.game_state == "WIN_LEVEL":
            self._draw_overlay(screen, "¡FRECUENCIA CALIBRADA!", f"Puntaje total: {self.score}", COLOR_GREEN)
        elif self.game_state == "GAME_OVER":
            self._draw_overlay(screen, "SEÑAL PERDIDA", "No se logró sintonizar la transmisión a tiempo", COLOR_MAGENTA)

    def _draw_overlay(self, screen, title, subtitle, color):
        overlay = pygame.Surface((WINDOW_WIDTH, WINDOW_HEIGHT), pygame.SRCALPHA)
        overlay.fill((13, 17, 23, 210))
        screen.blit(overlay, (0, 0))

        box = pygame.Rect((WINDOW_WIDTH - 440) // 2, (WINDOW_HEIGHT - 210) // 2, 440, 210)
        pygame.draw.rect(screen, COLOR_PANEL, box, border_radius=12)
        pygame.draw.rect(screen, color, box, width=2, border_radius=12)

        t1 = self.font_large.render(title, True, color)
        t2 = self.font_mid.render(subtitle, True, COLOR_TEXT)
        t3 = self.font_small.render("Haz clic en cualquier lugar para continuar", True, COLOR_ACCENT)

        screen.blit(t1, t1.get_rect(center=(WINDOW_WIDTH // 2, box.y + 60)))
        screen.blit(t2, t2.get_rect(center=(WINDOW_WIDTH // 2, box.y + 110)))
        screen.blit(t3, t3.get_rect(center=(WINDOW_WIDTH // 2, box.y + 160)))
