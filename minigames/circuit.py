# minigames/circuit.py
import math
import random
import pygame
from collections import deque
from core.theme import (
    COLOR_BG, COLOR_PANEL, COLOR_BORDER, COLOR_GRID_BG,
    COLOR_CYAN, COLOR_GREEN, COLOR_MAGENTA, COLOR_TEXT,
    COLOR_TEXT_MUTED, COLOR_ACCENT, WINDOW_WIDTH, WINDOW_HEIGHT
)

DIRS = [(-1, 0), (0, 1), (1, 0), (0, -1)]

TILE_TEMPLATES = {
    'I': [True, False, True, False],
    'L': [True, True, False, False],
    'T': [True, True, True, False],
    'X': [True, True, True, True],
    'END': [True, False, False, False],
}

def rotate_connections(connections, rotation):
    rot = rotation % 4
    return connections[-rot:] + connections[:-rot]

class Tile:
    def __init__(self, r, c, tile_type, is_source=False, is_target=False):
        self.r = r
        self.c = c
        self.tile_type = tile_type
        self.is_source = is_source
        self.is_target = is_target
        self.rotation = 0
        self.target_rotation_deg = 0
        self.current_rotation_deg = 0.0
        self.powered = is_source

    def rotate(self):
        if self.is_source:
            return
        self.rotation = (self.rotation + 1) % 4
        self.target_rotation_deg += 90

    def update_animation(self):
        diff = self.target_rotation_deg - self.current_rotation_deg
        if abs(diff) > 0.5:
            self.current_rotation_deg += diff * 0.28
        else:
            self.current_rotation_deg = self.target_rotation_deg

    def get_connections(self):
        base = TILE_TEMPLATES[self.tile_type]
        return rotate_connections(base, self.rotation)

class CircuitGame:
    def __init__(self, sound_engine):
        self.sounds = sound_engine
        self.level = 1
        self.score = 0
        self.time_left = 60.0
        self.game_state = "PLAYING"
        self.rows = 4
        self.cols = 4
        self.moves = 0
        self.grid = []
        self.source_pos = (0, 0)
        self.target_pos = (self.rows - 1, self.cols - 1)
        self.pulse_phase = 0.0
        self.last_tick_sec = 10

        self.font_large = pygame.font.SysFont("Segoe UI, Arial, sans-serif", 30, bold=True)
        self.font_mid = pygame.font.SysFont("Segoe UI, Arial, sans-serif", 18, bold=True)
        self.font_small = pygame.font.SysFont("Segoe UI, Arial, sans-serif", 13)

        self.init_level()

    def init_level(self):
        self.moves = 0
        self.game_state = "PLAYING"
        if self.level == 1:
            self.rows, self.cols = 4, 4
            self.time_left = 60.0
        elif self.level == 2:
            self.rows, self.cols = 5, 5
            self.time_left = 55.0
        elif self.level == 3:
            self.rows, self.cols = 5, 6
            self.time_left = 50.0
        else:
            self.rows, self.cols = 6, 6
            self.time_left = 45.0

        self.last_tick_sec = 10
        self.cell_size = min(420 // self.rows, 420 // self.cols)
        self.grid_width = self.cols * self.cell_size
        self.grid_height = self.rows * self.cell_size
        self.grid_offset_x = 320 + (580 - self.grid_width) // 2
        self.grid_offset_y = (WINDOW_HEIGHT - self.grid_height) // 2

        self.generate_solvable_board()
        self.update_circuit_flow(play_sound=False)

    def generate_solvable_board(self):
        self.grid = []
        self.source_pos = (0, 0)
        self.target_pos = (self.rows - 1, self.cols - 1)

        path = [self.source_pos]
        curr = self.source_pos
        visited = {curr}

        while curr != self.target_pos:
            r, c = curr
            valid_next = []
            for d_idx, (dr, dc) in enumerate(DIRS):
                nr, nc = r + dr, c + dc
                if 0 <= nr < self.rows and 0 <= nc < self.cols and (nr, nc) not in visited:
                    dist_current = abs(self.target_pos[0] - r) + abs(self.target_pos[1] - c)
                    dist_next = abs(self.target_pos[0] - nr) + abs(self.target_pos[1] - nc)
                    weight = 2 if dist_next < dist_current else 1
                    valid_next.extend([(nr, nc)] * weight)
            
            if not valid_next:
                return self.generate_solvable_board()

            curr = random.choice(valid_next)
            visited.add(curr)
            path.append(curr)

        connections_map = {(r, c): [False, False, False, False] for r in range(self.rows) for c in range(self.cols)}

        for i in range(len(path)):
            r, c = path[i]
            if i > 0:
                pr, pc = path[i - 1]
                for d_idx, (dr, dc) in enumerate(DIRS):
                    if pr == r + dr and pc == c + dc:
                        connections_map[(r, c)][d_idx] = True
            if i < len(path) - 1:
                nr, nc = path[i + 1]
                for d_idx, (dr, dc) in enumerate(DIRS):
                    if nr == r + dr and nc == c + dc:
                        connections_map[(r, c)][d_idx] = True

        for r in range(self.rows):
            row = []
            for c in range(self.cols):
                conns = connections_map[(r, c)]
                is_src = (r, c) == self.source_pos
                is_tgt = (r, c) == self.target_pos

                active_dirs = [i for i, val in enumerate(conns) if val]
                count = len(active_dirs)

                if is_src or is_tgt or count == 1:
                    t_type = 'END'
                elif count == 0:
                    t_type = random.choice(['I', 'L', 'T'])
                elif count == 2:
                    d1, d2 = active_dirs
                    t_type = 'I' if abs(d1 - d2) == 2 else 'L'
                elif count == 3:
                    t_type = 'T'
                else:
                    t_type = 'X'

                tile = Tile(r, c, t_type, is_source=is_src, is_target=is_tgt)
                if is_src:
                    tile.rotation = active_dirs[0] if active_dirs else 1
                    tile.target_rotation_deg = tile.rotation * 90
                    tile.current_rotation_deg = float(tile.target_rotation_deg)
                else:
                    tile.rotation = random.randint(0, 3)
                    tile.target_rotation_deg = tile.rotation * 90
                    tile.current_rotation_deg = float(tile.target_rotation_deg)

                row.append(tile)
            self.grid.append(row)

    def update_circuit_flow(self, play_sound=True):
        prev_powered = sum(1 for row in self.grid for t in row if t.powered)
        for r in range(self.rows):
            for c in range(self.cols):
                self.grid[r][c].powered = False

        sr, sc = self.source_pos
        source_tile = self.grid[sr][sc]
        source_tile.powered = True
        queue = deque([source_tile])
        target_reached = False

        while queue:
            curr = queue.popleft()
            curr_conns = curr.get_connections()

            for d_idx, (dr, dc) in enumerate(DIRS):
                if curr_conns[d_idx]:
                    nr, nc = curr.r + dr, curr.c + dc
                    if 0 <= nr < self.rows and 0 <= nc < self.cols:
                        neighbor = self.grid[nr][nc]
                        if not neighbor.powered:
                            neighbor_conns = neighbor.get_connections()
                            opposite_d = (d_idx + 2) % 4
                            if neighbor_conns[opposite_d]:
                                neighbor.powered = True
                                if neighbor.is_target:
                                    target_reached = True
                                queue.append(neighbor)

        new_powered = sum(1 for row in self.grid for t in row if t.powered)
        if target_reached and self.game_state == "PLAYING":
            self.game_state = "WIN_LEVEL"
            bonus = max(100, int(self.time_left * 25)) - (self.moves * 5)
            self.score += max(50, bonus)
            self.sounds.play('win')
        elif play_sound and new_powered > prev_powered:
            self.sounds.play('power')

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
        if (self.grid_offset_x <= mx < self.grid_offset_x + self.grid_width and
            self.grid_offset_y <= my < self.grid_offset_y + self.grid_height):
            c = (mx - self.grid_offset_x) // self.cell_size
            r = (my - self.grid_offset_y) // self.cell_size
            if 0 <= r < self.rows and 0 <= c < self.cols:
                tile = self.grid[r][c]
                if not tile.is_source:
                    tile.rotate()
                    self.moves += 1
                    self.sounds.play('click')
                    self.update_circuit_flow(play_sound=True)

    def update(self, dt):
        self.pulse_phase += dt * 5.0
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

        for row in self.grid:
            for tile in row:
                tile.update_animation()

    def draw_wire_segment(self, surface, cx, cy, d_idx, length, width, color):
        dx, dy = DIRS[d_idx][1], DIRS[d_idx][0]
        pygame.draw.line(surface, color, (cx, cy), (cx + dx * length, cy + dy * length), width)

    def draw(self, screen):
        # Panel lateral
        panel = pygame.Rect(20, 20, 280, WINDOW_HEIGHT - 40)
        pygame.draw.rect(screen, COLOR_PANEL, panel, border_radius=12)
        pygame.draw.rect(screen, COLOR_BORDER, panel, width=1, border_radius=12)

        screen.blit(self.font_small.render("MODULO // 01", True, COLOR_CYAN), (40, 38))
        screen.blit(self.font_large.render("CYBER CIRCUIT", True, COLOR_TEXT), (40, 58))
        pygame.draw.line(screen, COLOR_BORDER, (40, 102), (280, 102), 1)

        y = 120
        stats = [
            ("NIVEL", f"{self.level:02d}"),
            ("PUNTAJE", f"{self.score:05d}"),
            ("MOVIMIENTOS", f"{self.moves}"),
            ("TIEMPO", f"{max(0, int(self.time_left))}s"),
        ]
        for label, val in stats:
            screen.blit(self.font_small.render(label, True, COLOR_TEXT_MUTED), (40, y))
            screen.blit(self.font_mid.render(val, True, COLOR_TEXT if label != "TIEMPO" or self.time_left > 10 else COLOR_MAGENTA), (40, y + 20))
            y += 52

        # Barra de tiempo
        bar_w = 240
        max_t = 60.0 if self.level == 1 else 50.0
        ratio = max(0.0, min(1.0, self.time_left / max_t))
        pygame.draw.rect(screen, COLOR_BORDER, (40, y + 5, bar_w, 8), border_radius=4)
        pygame.draw.rect(screen, COLOR_GREEN if ratio > 0.25 else COLOR_MAGENTA, (40, y + 5, int(bar_w * ratio), 8), border_radius=4)

        # Controles
        screen.blit(self.font_small.render("• Clic en nodo: Rotar 90°", True, COLOR_TEXT_MUTED), (40, WINDOW_HEIGHT - 120))
        screen.blit(self.font_small.render("• [ESC]: Regresar al menú", True, COLOR_ACCENT), (40, WINDOW_HEIGHT - 100))
        screen.blit(self.font_small.render("• [R]: Reiniciar nivel", True, COLOR_TEXT_MUTED), (40, WINDOW_HEIGHT - 80))

        # Dibujar tablero
        for r in range(self.rows):
            for c in range(self.cols):
                tile = self.grid[r][c]
                x = self.grid_offset_x + c * self.cell_size
                y_pos = self.grid_offset_y + r * self.cell_size
                sz = self.cell_size

                rect = pygame.Rect(x, y_pos, sz, sz)
                pygame.draw.rect(screen, COLOR_GRID_BG, rect, border_radius=6)
                pygame.draw.rect(screen, COLOR_BORDER, rect, width=1, border_radius=6)

                cx, cy = x + sz // 2, y_pos + sz // 2
                wire_w = max(4, sz // 8)
                tile_surf = pygame.Surface((sz, sz), pygame.SRCALPHA)
                tcx, tcy = sz // 2, sz // 2

                col_wire = (COLOR_CYAN if tile.powered else (60, 70, 85))
                if tile.powered:
                    pulse = int(30 * math.sin(self.pulse_phase))
                    col_wire = (min(255, max(0, COLOR_CYAN[0] + pulse)),
                                min(255, max(0, COLOR_CYAN[1] + pulse)),
                                min(255, max(0, COLOR_CYAN[2] + pulse)))

                for d_idx, active in enumerate(TILE_TEMPLATES[tile.tile_type]):
                    if active:
                        if tile.powered:
                            self.draw_wire_segment(tile_surf, tcx, tcy, d_idx, sz // 2, wire_w + 4, (0, 180, 220, 80))
                        self.draw_wire_segment(tile_surf, tcx, tcy, d_idx, sz // 2, wire_w, col_wire)

                core_r = max(5, sz // 7)
                pygame.draw.circle(tile_surf, col_wire, (tcx, tcy), core_r)
                rotated = pygame.transform.rotate(tile_surf, -tile.current_rotation_deg)
                screen.blit(rotated, rotated.get_rect(center=(cx, cy)).topleft)

                if tile.is_source:
                    pygame.draw.circle(screen, COLOR_GREEN, (cx, cy), core_r + 1)
                    pygame.draw.circle(screen, (255, 255, 255), (cx, cy), max(2, core_r // 2))
                elif tile.is_target:
                    col_tgt = COLOR_GREEN if tile.powered else COLOR_MAGENTA
                    pygame.draw.rect(screen, col_tgt, (cx - core_r, cy - core_r, core_r * 2, core_r * 2), border_radius=3)
                    pygame.draw.rect(screen, (255, 255, 255), (cx - 3, cy - 3, 6, 6))

        # Overlays
        if self.game_state == "WIN_LEVEL":
            self._draw_overlay(screen, "¡ACCESO CONCEDIDO!", f"Puntaje total: {self.score}", COLOR_GREEN)
        elif self.game_state == "GAME_OVER":
            self._draw_overlay(screen, "FIREWALL BLOQUEADO", f"Nivel alcanzado: {self.level}", COLOR_MAGENTA)

    def _draw_overlay(self, screen, title, subtitle, color):
        overlay = pygame.Surface((WINDOW_WIDTH, WINDOW_HEIGHT), pygame.SRCALPHA)
        overlay.fill((13, 17, 23, 210))
        screen.blit(overlay, (0, 0))

        box = pygame.Rect((WINDOW_WIDTH - 420) // 2, (WINDOW_HEIGHT - 200) // 2, 420, 200)
        pygame.draw.rect(screen, COLOR_PANEL, box, border_radius=12)
        pygame.draw.rect(screen, color, box, width=2, border_radius=12)

        t1 = self.font_large.render(title, True, color)
        t2 = self.font_mid.render(subtitle, True, COLOR_TEXT)
        t3 = self.font_small.render("Haz clic en cualquier lugar para continuar", True, COLOR_ACCENT)

        screen.blit(t1, t1.get_rect(center=(WINDOW_WIDTH // 2, box.y + 55)))
        screen.blit(t2, t2.get_rect(center=(WINDOW_WIDTH // 2, box.y + 105)))
        screen.blit(t3, t3.get_rect(center=(WINDOW_WIDTH // 2, box.y + 150)))
