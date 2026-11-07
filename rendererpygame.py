import pygame
import numpy as np

class PygameRenderer:
    def __init__(self, width=1280, height=720):
        pygame.init()
        pygame.font.init()
        
        self.width = width
        self.height = height
        self.screen = pygame.display.set_mode((width, height))
        pygame.display.set_caption("F1 Telemetry Viewer - 60 FPS")
        self.clock = pygame.time.Clock()

        self.font_large = pygame.font.SysFont("Consolas", 28, bold=True)
        self.font_medium = pygame.font.SysFont("Consolas", 22)
        self.font_small = pygame.font.SysFont("Consolas", 16)

        self.COLOR_BG = (20, 20, 20)
        self.COLOR_TRACK = (80, 80, 80)
        self.COLOR_CAR = (255, 50, 50)
        self.COLOR_GREEN = (50, 205, 50)
        self.COLOR_RED = (220, 50, 50)
        self.COLOR_WHITE = (240, 240, 240)
        self.COLOR_GRAY = (60, 60, 60)
        self.COLOR_YELLOW = (255, 215, 0)

        self.scale = 1.0
        self.offset_x = 0
        self.offset_y = 0

        self.camera_mode = "global"

    def fit_track_to_screen(self, pos_data):
        x = pos_data["X"].to_numpy()
        y = pos_data["Y"].to_numpy()
        speed = pos_data["Speed"].to_numpy()

        self.track_world = list(zip(x, y))
        self.track_speed = speed

        self.min_x = x.min()
        self.max_x = x.max()
        self.min_y = y.min()
        self.max_y = y.max()

        track_w = max(1.0, self.max_x - self.min_x)
        track_h = max(1.0, self.max_y - self.min_y)

        margin = 100
        render_w = self.width * 0.58 - margin * 2
        render_h = self.height - margin * 2

        self.scale = min(render_w / track_w, render_h / track_h)
        
        self.track_colors = []
        max_speed = max(1.0, self.track_speed.max())

        for i in range(len(self.track_world) - 1):
            hue = 240 - int(240 * min(1.0, max(0.0, self.track_speed[i] / max_speed)))
            color = pygame.Color(0)
            color.hsva = (hue, 100, 100, 100)
            self.track_colors.append(color)

    def world_to_screen_global(self, x, y):
        margin = 100
        sx = int(margin + (x - self.min_x) * self.scale)
        sy = int(margin + (self.max_y - y) * self.scale)
        return sx, sy

    def world_to_screen_follow(self, x, y, car):
        zoom = 12
        sx = int(self.width * 0.29 + (x - car.x) * self.scale * zoom)
        sy = int(self.height * 0.50 - (y - car.y) * self.scale * zoom)
        return sx, sy
    
    def draw_speed_legend(self, x, y, width=18, height=220):
        for i in range(height):
            t = 1 - i / height

            if t < 0.25:
                c = (0, int(255 * (t / 0.25)), 255)
            elif t < 0.5:
                c = (0, 255, int(255 * (1 - (t - 0.25) / 0.25)))
            elif t < 0.75:
                c = (int(255 * ((t - 0.5) / 0.25)), 255, 0)
            else:
                c = (255, int(255 * (1 - (t - 0.75) / 0.25)), 0)

            pygame.draw.line(self.screen, c, (x, y + i), (x + width, y + i))

        pygame.draw.rect(self.screen, self.COLOR_WHITE, (x, y, width, height), 2)

        txt = self.font_small.render("Speed", True, self.COLOR_WHITE)
        self.screen.blit(txt, (x - 8, y - 25))

        self.screen.blit(self.font_small.render("320", True, self.COLOR_WHITE), (x + width + 6, y - 8))
        self.screen.blit(self.font_small.render("80", True, self.COLOR_WHITE), (x + width + 6, y + height - 8))

    def draw_hud_info(self, car, lap_time_str, playback_speed, config):
        hud_x = int(self.width * 0.72)
        
        if config:
            clean_gp = str(config['gp']).replace("Grand Prix", "GP").strip()
            info_str = f"{config['year']} {clean_gp} - {config['session']} ({config['driver']})"
            txt_info = self.font_small.render(info_str, True, self.COLOR_YELLOW)
            self.screen.blit(txt_info, (hud_x, 15))

        txt_time = self.font_large.render(lap_time_str, True, self.COLOR_YELLOW)
        self.screen.blit(txt_time, (hud_x, 40))

        txt_speed = self.font_large.render(f"{car.speed:.0f} km/h", True, self.COLOR_WHITE)
        txt_gear = self.font_medium.render(f"Gear {car.gear}", True, self.COLOR_WHITE)
        txt_rpm = self.font_medium.render(f"RPM {car.rpm:.0f}", True, self.COLOR_WHITE)

        self.screen.blit(txt_speed, (hud_x, 90))
        self.screen.blit(txt_gear, (hud_x, 130))
        self.screen.blit(txt_rpm, (hud_x, 165))

        drs_color = self.COLOR_GREEN if car.drs else self.COLOR_RED
        drs_text = "DRS OPEN" if car.drs else "DRS CLOSED"
        txt_drs = self.font_medium.render(drs_text, True, drs_color)
        self.screen.blit(txt_drs, (hud_x, 210))

        txt_th = self.font_small.render("Throttle", True, self.COLOR_WHITE)
        self.screen.blit(txt_th, (hud_x, 270))
        pygame.draw.rect(self.screen, self.COLOR_GRAY, (hud_x, 295, 250, 20))
        th_w = int(250 * (car.throttle / 100.0))
        pygame.draw.rect(self.screen, self.COLOR_GREEN, (hud_x, 295, th_w, 20))

        txt_br = self.font_small.render("Brake", True, self.COLOR_WHITE)
        self.screen.blit(txt_br, (hud_x, 330))
        pygame.draw.rect(self.screen, self.COLOR_GRAY, (hud_x, 355, 250, 20))
        br_w = 250 if car.brake else 0
        pygame.draw.rect(self.screen, self.COLOR_RED, (hud_x, 355, br_w, 20))

        y = 480
        controls = ["CONTROLS", "SPACEBAR : Pause", "R        : Restart", "<- / ->  : -1 s / +1 s",
                    "+ / -    : Speed", "C        : Camera", "ESC      : Menu"]

        for line in controls:
            txt = self.font_small.render(line, True, (170, 170, 170))
            self.screen.blit(txt, (hud_x, y))
            y += 22

        txt_playback = self.font_small.render(f"Playback: x{playback_speed:g}", True, self.COLOR_WHITE)
        self.screen.blit(txt_playback, (hud_x, 425))
    def draw_global(self, car, lap_time_str, playback_speed, config=None, current_frame=0):
        self.screen.fill(self.COLOR_BG)

        for i in range(len(self.track_world) - 1):
            p1 = self.world_to_screen_global(self.track_world[i][0], self.track_world[i][1])
            p2 = self.world_to_screen_global(self.track_world[i + 1][0], self.track_world[i + 1][1])
            pygame.draw.line(self.screen, self.track_colors[i], p1, p2, 4)

        cx, cy = self.world_to_screen_global(car.x, car.y)
        pygame.draw.circle(self.screen, self.COLOR_CAR, (cx, cy), 7)
        pygame.draw.circle(self.screen, self.COLOR_WHITE, (cx, cy), 8, 2)

        legend_x = int(self.width * 0.61)
        legend_y = int(self.height * 0.35)
        self.draw_speed_legend(legend_x, legend_y)
        self.draw_hud_info(car, lap_time_str, playback_speed, config)

        pygame.display.flip()

    def draw_follow(self, car, lap_time_str, playback_speed, config=None, current_frame=0):
        self.screen.fill(self.COLOR_BG)

        for i in range(len(self.track_world) - 1):
            x1, y1 = self.world_to_screen_follow(self.track_world[i][0], self.track_world[i][1], car)
            x2, y2 = self.world_to_screen_follow(self.track_world[i + 1][0], self.track_world[i + 1][1], car)
            color = self.track_colors[i]
            pygame.draw.line(self.screen, color, (x1, y1), (x2, y2), 4)

        cx = int(self.width * 0.29)
        cy = int(self.height * 0.50)
        pygame.draw.circle(self.screen, self.COLOR_CAR, (cx, cy), 7)
        pygame.draw.circle(self.screen, self.COLOR_WHITE, (cx, cy), 8, 2)

        legend_x = int(self.width * 0.61)
        legend_y = int(self.height * 0.35)
        self.draw_speed_legend(legend_x, legend_y)

        self.draw_hud_info(car, lap_time_str, playback_speed, config)

        pygame.display.flip()

    def draw(self, car, lap_time_str, playback_speed, config=None, current_frame=0):
        if self.camera_mode == "global":
            self.draw_global(car, lap_time_str, playback_speed, config, current_frame)
        else:
            self.draw_follow(car, lap_time_str, playback_speed, config, current_frame)

    def toggle_camera(self):
        if self.camera_mode == "global":
            self.camera_mode = "follow"
        else:
            self.camera_mode = "global"