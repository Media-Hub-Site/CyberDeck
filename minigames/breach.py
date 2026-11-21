# minigames/breach.py
# Minijuego de hackeo de memoria / matriz hexadecimal estilo Cyberpunk 2077
import random
import pygame
from core.theme import (
    COLOR_BG, COLOR_PANEL, COLOR_BORDER, COLOR_BORDER_FOCUS,
    COLOR_CYAN, COLOR_GREEN, COLOR_MAGENTA, COLOR_YELLOW,
    COLOR_TEXT, COLOR_TEXT_MUTED, COLOR_TEXT_DARK, COLOR_ACCENT,
    WINDOW_WIDTH, WINDOW_HEIGHT
)

HEX_SYMBOLS = ["1C", "55", "7A", "BD", "E9"]

class BreachGame:
    def __init__(self, sound_engine):
        self.sounds = sound_engine
        self.level = 1
        self.score = 0
        self.time_left = 40.0
        self.game_state = "PLAYING" # PLAYING, WIN_LEVEL, GAME_OVER

        self.font_large = pygame.font.SysFont("Segoe UI, Arial, sans-serif", 30, bold=True)
        self.font_mid = pygame.font.SysFont("Consolas, Courier New, monospace", 20, bold=True)
        self.font_small = pygame.font.SysFont("Segoe UI, Arial, sans-serif", 13)

        self.last_tick_sec = 10
        self.init_level()

    def init_level(self):
        self.game_state = "PLAYING"
        self.grid_size = 5 if self.level <= 2 else 6
        self.buffer_size = 6 if self.level <= 2 else 7
        self.time_left = max(25.0, 45.0 - self.level * 3.0)
        self.last_tick_sec = 10

        # Selección de secuencias objetivo a descifrar (1 o 2 objetivos)
        seq_len = 3 if self.level <= 2 else 4
        
        # 1. Generar la matriz
        self.matrix = [[random.choice(HEX_SYMBOLS) for _ in range(self.grid_size)] for _ in range(self.grid_size)]
        self.used_cells = set()

        # 2. Generar al menos 1 secuencia con solución real válida
        # Simulamos un camino válido alternando fila -> col -> fila
        valid_path_symbols = []
        curr_r = 0
        curr_c = random.randint(0, self.grid_size - 1)
        valid_path_symbols.append(self.matrix[curr_r][curr_c])
        is_row_move = False # El siguiente se moverá en columna

        for _ in range(seq_len - 1):
            if not is_row_move:
                # Mover en columna curr_c a otra fila
                next_r = random.choice([r for r in range(self.grid_size) if r != curr_r])
                curr_r = next_r
                valid_path_symbols.append(self.matrix[curr_r][curr_c])
                is_row_move = True
            else:
                # Mover en fila curr_r a otra columna
                next_c = random.choice([c for c in range(self.grid_size) if c != curr_c])
                curr_c = next_c
                valid_path_symbols.append(self.matrix[curr_r][curr_c])
                is_row_move = False

        self.target_sequence = valid_path_symbols
        self.player_buffer = []

        # Estado del cursor
        self.is_horizontal = True # True: selecciona en fila actual. False: selecciona en columna actual.
        self.active_index = 0     # Inicia en la fila 0
        self.hovered_cell = None

        # Posicionamiento gráfico
        self.cell_w = 64
        self.cell_h = 58
        self.grid_offset_x = 340
        self.grid_offset_y = 170

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
        # Verificar clic en celda activa
        if (self.grid_offset_x <= mx < self.grid_offset_x + self.grid_size * self.cell_w and
            self.grid_offset_y <= my < self.grid_offset_y + self.grid_size * self.cell_h):
            c = (mx - self.grid_offset_x) // self.cell_w
            r = (my - self.grid_offset_y) // self.cell_h

            if (r, c) not in self.used_cells:
                # Comprobar si está en la fila o columna activa
                valid_pick = (self.is_horizontal and r == self.active_index) or (not self.is_horizontal and c == self.active_index)
                if valid_pick:
                    val = self.matrix[r][c]
                    self.player_buffer.append(val)
                    self.used_cells.add((r, c))
                    self.sounds.play('select')

                    # Alternar dirección
                    if self.is_horizontal:
                        self.is_horizontal = False
                        self.active_index = c
                    else:
                        self.is_horizontal = True
                        self.active_index = r

                    self.check_buffer_progress()

    def check_buffer_progress(self):
        # Comprobar si la secuencia objetivo aparece en el buffer
        buf_str = "".join(self.player_buffer)
        tgt_str = "".join(self.target_sequence)

        if tgt_str in buf_str:
            self.game_state = "WIN_LEVEL"
            bonus = max(150, int(self.time_left * 35))
            self.score += bonus
            self.sounds.play('win')
        elif len(self.player_buffer) >= self.buffer_size:
            self.game_state = "GAME_OVER"
            self.sounds.play('game_over')

    def update(self, dt):
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

        # Control de hover con mouse
        mx, my = pygame.mouse.get_pos()
        if (self.grid_offset_x <= mx < self.grid_offset_x + self.grid_size * self.cell_w and
            self.grid_offset_y <= my < self.grid_offset_y + self.grid_size * self.cell_h):
            c = (mx - self.grid_offset_x) // self.cell_w
            r = (my - self.grid_offset_y) // self.cell_h
            self.hovered_cell = (r, c)
        else:
            self.hovered_cell = None

    def draw(self, screen):
        # Panel lateral
        panel = pygame.Rect(20, 20, 280, WINDOW_HEIGHT - 40)
        pygame.draw.rect(screen, COLOR_PANEL, panel, border_radius=12)
        pygame.draw.rect(screen, COLOR_BORDER, panel, width=1, border_radius=12)

        screen.blit(self.font_small.render("MODULO // 02", True, COLOR_YELLOW), (40, 38))
        screen.blit(self.font_large.render("BREACH PROTOCOL", True, COLOR_TEXT), (40, 58))
        pygame.draw.line(screen, COLOR_BORDER, (40, 102), (280, 102), 1)

        y = 120
        stats = [
            ("NIVEL", f"{self.level:02d}"),
            ("PUNTAJE", f"{self.score:05d}"),
            ("BUFFER USADO", f"{len(self.player_buffer)} / {self.buffer_size}"),
            ("TIEMPO", f"{max(0, int(self.time_left))}s"),
        ]
        for label, val in stats:
            screen.blit(self.font_small.render(label, True, COLOR_TEXT_MUTED), (40, y))
            screen.blit(self.font_mid.render(val, True, COLOR_TEXT if label != "TIEMPO" or self.time_left > 10 else COLOR_MAGENTA), (40, y + 20))
            y += 52

        # Barra de tiempo
        bar_w = 240
        ratio = max(0.0, min(1.0, self.time_left / (45.0 if self.level <= 2 else 35.0)))
        pygame.draw.rect(screen, COLOR_BORDER, (40, y + 5, bar_w, 8), border_radius=4)
        pygame.draw.rect(screen, COLOR_GREEN if ratio > 0.25 else COLOR_MAGENTA, (40, y + 5, int(bar_w * ratio), 8), border_radius=4)

        # Reglas
        screen.blit(self.font_small.render("• Alterna: Fila <-> Columna", True, COLOR_TEXT_MUTED), (40, WINDOW_HEIGHT - 120))
        screen.blit(self.font_small.render("• Forma la secuencia objetivo", True, COLOR_TEXT_MUTED), (40, WINDOW_HEIGHT - 100))
        screen.blit(self.font_small.render("• [ESC]: Regresar al menú", True, COLOR_ACCENT), (40, WINDOW_HEIGHT - 80))

        # Panel superior: Secuencia Objetivo y Buffer
        top_box = pygame.Rect(330, 20, 600, 120)
        pygame.draw.rect(screen, COLOR_PANEL, top_box, border_radius=10)
        pygame.draw.rect(screen, COLOR_BORDER, top_box, width=1, border_radius=10)

        screen.blit(self.font_small.render("SECUENCIA REQUERIDA PARA VULNERAR SISTEMA:", True, COLOR_YELLOW), (350, 32))
        
        # Dibujar casillas de secuencia requerida
        sx = 350
        for code in self.target_sequence:
            code_rect = pygame.Rect(sx, 55, 48, 36)
            pygame.draw.rect(screen, (30, 38, 50), code_rect, border_radius=6)
            pygame.draw.rect(screen, COLOR_YELLOW, code_rect, width=1, border_radius=6)
            txt = self.font_mid.render(code, True, COLOR_YELLOW)
            screen.blit(txt, txt.get_rect(center=code_rect.center))
            sx += 58

        # Dibujar Buffer del Jugador
        screen.blit(self.font_small.render("BUFFER DE MEMORIA:", True, COLOR_TEXT_MUTED), (620, 32))
        bx = 620
        for i in range(self.buffer_size):
            b_rect = pygame.Rect(bx, 55, 44, 36)
            pygame.draw.rect(screen, (22, 27, 34), b_rect, border_radius=6)
            if i < len(self.player_buffer):
                pygame.draw.rect(screen, COLOR_CYAN, b_rect, width=1, border_radius=6)
                txt = self.font_mid.render(self.player_buffer[i], True, COLOR_CYAN)
                screen.blit(txt, txt.get_rect(center=b_rect.center))
            else:
                pygame.draw.rect(screen, COLOR_BORDER, b_rect, width=1, border_radius=6)
            bx += 50

        # Resaltado de la Fila o Columna activa (Línea de exploración láser)
        if self.is_horizontal:
            highlight = pygame.Rect(self.grid_offset_x - 4, self.grid_offset_y + self.active_index * self.cell_h - 2,
                                    self.grid_size * self.cell_w + 8, self.cell_h + 4)
            pygame.draw.rect(screen, (0, 240, 255, 25), highlight, border_radius=6)
            pygame.draw.rect(screen, COLOR_CYAN, highlight, width=1, border_radius=6)
        else:
            highlight = pygame.Rect(self.grid_offset_x + self.active_index * self.cell_w - 2, self.grid_offset_y - 4,
                                    self.cell_w + 4, self.grid_size * self.cell_h + 8)
            pygame.draw.rect(screen, (0, 240, 255, 25), highlight, border_radius=6)
            pygame.draw.rect(screen, COLOR_CYAN, highlight, width=1, border_radius=6)

        # Dibujar Matriz Hexadecimal
        for r in range(self.grid_size):
            for c in range(self.grid_size):
                x = self.grid_offset_x + c * self.cell_w
                y = self.grid_offset_y + r * self.cell_h
                cell_rect = pygame.Rect(x + 3, y + 3, self.cell_w - 6, self.cell_h - 6)

                is_used = (r, c) in self.used_cells
                is_active_path = (self.is_horizontal and r == self.active_index) or (not self.is_horizontal and c == self.active_index)
                is_hover = (r, c) == self.hovered_cell and is_active_path and not is_used

                bg_col = (13, 17, 23) if is_used else (COLOR_PANEL if not is_hover else (30, 42, 56))
                border_col = COLOR_BORDER
                if is_hover:
                    border_col = COLOR_CYAN
                elif is_active_path and not is_used:
                    border_col = COLOR_BORDER_FOCUS

                pygame.draw.rect(screen, bg_col, cell_rect, border_radius=6)
                pygame.draw.rect(screen, border_col, cell_rect, width=1, border_radius=6)

                code = self.matrix[r][c]
                if is_used:
                    txt = self.font_mid.render("[--]", True, COLOR_TEXT_DARK)
                elif is_active_path:
                    txt = self.font_mid.render(code, True, COLOR_CYAN if is_hover else COLOR_TEXT)
                else:
                    txt = self.font_mid.render(code, True, COLOR_TEXT_MUTED)

                screen.blit(txt, txt.get_rect(center=cell_rect.center))

        # Overlays de fin de nivel
        if self.game_state == "WIN_LEVEL":
            self._draw_overlay(screen, "¡MEMORIA VULNERADA!", f"Puntaje total: {self.score}", COLOR_GREEN)
        elif self.game_state == "GAME_OVER":
            self._draw_overlay(screen, "BUFFER OVERFLOW", "Secuencia fallida o tiempo agotado", COLOR_MAGENTA)

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
