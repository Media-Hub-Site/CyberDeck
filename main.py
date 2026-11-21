# main.py
# Launcher & Hub principal de CYBERDECK para MediaHub
import sys
import os

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
if BASE_DIR not in sys.path:
    sys.path.insert(0, BASE_DIR)

import pygame
from core.theme import (
    COLOR_BG, COLOR_PANEL, COLOR_BORDER,
    COLOR_CYAN, COLOR_GREEN, COLOR_MAGENTA, COLOR_YELLOW,
    COLOR_TEXT, COLOR_TEXT_MUTED, COLOR_TEXT_DARK, COLOR_ACCENT,
    WINDOW_WIDTH, WINDOW_HEIGHT, FPS
)
from core.sound import SoundEngine
from minigames.circuit import CircuitGame
from minigames.breach import BreachGame
from minigames.signal import SignalGame

class CyberDeckLauncher:
    def __init__(self):
        pygame.init()
        pygame.font.init()
        self.screen = pygame.display.set_mode((WINDOW_WIDTH, WINDOW_HEIGHT))
        pygame.display.set_caption("CyberDeck - MediaHub Cyber Suite")
        self.clock = pygame.time.Clock()
        self.sounds = SoundEngine.get_instance()

        # Fuentes
        self.font_brand = pygame.font.SysFont("Segoe UI, Arial, sans-serif", 34, bold=True)
        self.font_title = pygame.font.SysFont("Segoe UI, Arial, sans-serif", 22, bold=True)
        self.font_mid = pygame.font.SysFont("Segoe UI, Arial, sans-serif", 16, bold=True)
        self.font_body = pygame.font.SysFont("Segoe UI, Arial, sans-serif", 13)
        self.font_mono = pygame.font.SysFont("Consolas, Courier New, monospace", 13)

        self.current_screen = "MENU" # "MENU", "GAME_CIRCUIT", "GAME_BREACH", "GAME_SIGNAL"
        self.active_game = None

        # Definición de módulos de minijuegos con descripciones concisas
        self.modules = [
            {
                "id": "CIRCUIT",
                "tag": "MODULO // 01",
                "title": "CYBER CIRCUIT",
                "desc": "Bypass físico de energía rotando nodos y enrutando líneas de datos al servidor.",
                "color": COLOR_CYAN,
                "diff": "DIFICULTAD: BAJA",
            },
            {
                "id": "BREACH",
                "tag": "MODULO // 02",
                "title": "BREACH PROTOCOL",
                "desc": "Infiltración en memoria RAM seleccionando secuencias hexadecimales (Fila <-> Columna).",
                "color": COLOR_YELLOW,
                "diff": "DIFICULTAD: MEDIA",
            },
            {
                "id": "SIGNAL",
                "tag": "MODULO // 03",
                "title": "SIGNAL SYNCHRONIZER",
                "desc": "Calibración de osciloscopio analógico (Amplitud, Freq y Fase) para interceptar señales.",
                "color": COLOR_MAGENTA,
                "diff": "DIFICULTAD: ALTA",
            }
        ]
        self.selected_module = 0

    def start_game(self, game_id):
        if game_id == "CIRCUIT":
            self.active_game = CircuitGame(self.sounds)
            self.current_screen = "GAME_CIRCUIT"
            self.sounds.play('power')
        elif game_id == "BREACH":
            self.active_game = BreachGame(self.sounds)
            self.current_screen = "GAME_BREACH"
            self.sounds.play('power')
        elif game_id == "SIGNAL":
            self.active_game = SignalGame(self.sounds)
            self.current_screen = "GAME_SIGNAL"
            self.sounds.play('power')

    def handle_menu_click(self, pos):
        mx, my = pos
        start_y = 150
        for idx, mod in enumerate(self.modules):
            card_rect = pygame.Rect(40, start_y + idx * 145, 880, 125)
            if card_rect.collidepoint(mx, my):
                self.selected_module = idx
                self.sounds.play('click')
                self.start_game(mod["id"])
                return

    def run(self):
        running = True
        while running:
            dt = self.clock.tick(FPS) / 1000.0

            # Procesamiento de eventos
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    running = False
                elif event.type == pygame.KEYDOWN:
                    if event.key == pygame.K_m:
                        self.sounds.toggle_mute()
                    elif event.key == pygame.K_ESCAPE:
                        if self.current_screen != "MENU":
                            self.current_screen = "MENU"
                            self.active_game = None
                            self.sounds.play('click')
                        else:
                            running = False
                    elif event.key == pygame.K_r and self.active_game:
                        self.active_game.init_level()

                if self.current_screen == "MENU":
                    if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                        self.handle_menu_click(event.pos)
                else:
                    if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                        if self.active_game:
                            self.active_game.handle_click(event.pos)

            # Lógica de actualización
            if self.current_screen != "MENU" and self.active_game:
                self.active_game.update(dt)

            # Renderizado
            self.screen.fill(COLOR_BG)

            if self.current_screen == "MENU":
                self.draw_menu()
            else:
                if self.active_game:
                    self.active_game.draw(self.screen)

            pygame.display.flip()

        pygame.quit()
        sys.exit()

    def draw_menu(self):
        # Header principal estilo Deck
        header_rect = pygame.Rect(40, 30, 880, 100)
        pygame.draw.rect(self.screen, COLOR_PANEL, header_rect, border_radius=12)
        pygame.draw.rect(self.screen, COLOR_BORDER, header_rect, width=1, border_radius=12)

        # Indicador de estado y sonido
        sound_status = "MUTED" if self.sounds.muted else "ACTIVO"
        sound_color = COLOR_MAGENTA if self.sounds.muted else COLOR_GREEN
        tag_status = self.font_mono.render(f"AUDIO: {sound_status} [Tecla M]  |  ESTADO: ONLINE", True, sound_color)
        self.screen.blit(tag_status, (65, 48))

        brand = self.font_brand.render("CYBERDECK", True, COLOR_CYAN)
        sub_brand = self.font_body.render("SUITE DE HACKEO Y PUZZLES // MEDIAHUB", True, COLOR_TEXT_MUTED)
        self.screen.blit(brand, (65, 70))
        self.screen.blit(sub_brand, (270, 82))

        # Tarjetas de selección de módulo
        mx, my = pygame.mouse.get_pos()
        start_y = 150
        for idx, mod in enumerate(self.modules):
            card_rect = pygame.Rect(40, start_y + idx * 145, 880, 125)
            is_hover = card_rect.collidepoint(mx, my)
            bg_col = (26, 33, 44) if is_hover else COLOR_PANEL
            border_col = mod["color"] if is_hover else COLOR_BORDER

            pygame.draw.rect(self.screen, bg_col, card_rect, border_radius=10)
            pygame.draw.rect(self.screen, border_col, card_rect, width=2 if is_hover else 1, border_radius=10)

            # Etiqueta y Título
            tag = self.font_mono.render(mod["tag"], True, mod["color"])
            title = self.font_title.render(mod["title"], True, COLOR_TEXT)
            desc = self.font_body.render(mod["desc"], True, COLOR_TEXT_MUTED)
            diff = self.font_mono.render(mod["diff"], True, COLOR_ACCENT)

            # Margen izquierdo ordenado y holgado
            self.screen.blit(tag, (65, start_y + idx * 145 + 18))
            self.screen.blit(title, (65, start_y + idx * 145 + 38))
            self.screen.blit(desc, (65, start_y + idx * 145 + 68))
            self.screen.blit(diff, (65, start_y + idx * 145 + 93))

            # Botón de acción lateral (con suficiente separación del texto)
            btn_rect = pygame.Rect(720, start_y + idx * 145 + 40, 175, 45)
            btn_bg = mod["color"] if is_hover else (30, 40, 52)
            btn_txt_col = COLOR_BG if is_hover else COLOR_TEXT
            pygame.draw.rect(self.screen, btn_bg, btn_rect, border_radius=6)
            pygame.draw.rect(self.screen, mod["color"], btn_rect, width=1, border_radius=6)
            btn_lbl = self.font_mid.render("EJECUTAR >", True, btn_txt_col)
            self.screen.blit(btn_lbl, btn_lbl.get_rect(center=btn_rect.center))

        # Footer informativo
        footer = self.font_body.render("MediaHub Ecosistema  •  Usa [ESC] para salir o volver al menú  •  [M] para alternar audio", True, COLOR_TEXT_DARK)
        self.screen.blit(footer, footer.get_rect(center=(WINDOW_WIDTH // 2, WINDOW_HEIGHT - 25)))

if __name__ == "__main__":
    app = CyberDeckLauncher()
    app.run()
