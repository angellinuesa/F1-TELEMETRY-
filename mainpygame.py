import sys
import pygame
import numpy as np
import pandas as pd
from telemetry import TelemetryPlayer
from playback import PlaybackController
from rendererpygame import PygameRenderer
from menu import Menu

active_config = None
fps_objetivo = 60

renderer = PygameRenderer()
menu = Menu()
state = "menu"

player = None
playback = None

def load_simulation_data(config):
    """Carga los datos de FastF1 e interpola a 60 FPS según la selección del usuario."""
    player = TelemetryPlayer(config["year"], config["gp"], config["session"], config["driver"])

    pos_time_sec = (player.pos_data["Time"] - player.pos_data["Time"].iloc[0]).dt.total_seconds().to_numpy()
    car_time_sec = (player.car_data["Time"] - player.car_data["Time"].iloc[0]).dt.total_seconds().to_numpy()

    duration = max(pos_time_sec[-1], car_time_sec[-1])
    t_common = np.arange(0, duration, 1.0 / fps_objetivo)

    gear_col = "nGear" if "nGear" in player.car_data.columns else "Gear"

    drs_numeric = pd.to_numeric(player.car_data["DRS"], errors="coerce").fillna(0).to_numpy()

    player.df = pd.DataFrame({
    "TimeSec": t_common,
    "X": np.interp(t_common, pos_time_sec, player.pos_data["X"].to_numpy()),
    "Y": np.interp(t_common, pos_time_sec, player.pos_data["Y"].to_numpy()),
    "Speed": np.interp(t_common, car_time_sec, player.car_data["Speed"].to_numpy()),
    "RPM": np.interp(t_common, car_time_sec, player.car_data["RPM"].to_numpy()),
    "Throttle": np.interp(t_common, car_time_sec, player.car_data["Throttle"].to_numpy()),
    "Brake": np.interp(t_common, car_time_sec, player.car_data["Brake"].to_numpy()),
    "Gear": np.interp(t_common, car_time_sec, player.car_data[gear_col].to_numpy()).astype(int),
    "DRS": np.interp(t_common, car_time_sec, drs_numeric) >= 10})

    playback = PlaybackController(len(player.df) - 1)
    renderer.fit_track_to_screen(player.df)
    
    return player, playback

def get_lap_time(frame_idx, df):
    frame_idx = int(frame_idx)
    total_seconds = df["TimeSec"].iloc[frame_idx]

    minutos = int(total_seconds // 60)
    segundos = int(total_seconds % 60)
    milisegundos = int((total_seconds % 1) * 1000)

    return f"{minutos}:{segundos:02d}.{milisegundos:03d}"

running = True

while running:
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            running = False

        if event.type == pygame.KEYDOWN:
            if state == "menu":
                if event.key == pygame.K_UP:
                    menu.navigate_up()
                elif event.key == pygame.K_DOWN:
                    menu.navigate_down()
                elif event.key == pygame.K_LEFT:
                    menu.change_value(-1)
                elif event.key == pygame.K_RIGHT:
                    menu.change_value(1)
                elif event.key == pygame.K_RETURN:
                    renderer.screen.fill((20, 20, 20))
                    txt_loading = renderer.font_large.render("LOADING TELEMETRY DATA...", True, (255, 215, 0))
                    renderer.screen.blit(txt_loading, (380, 320))
                    pygame.display.flip()

                    active_config = menu.get_selected_config()
                    player, playback = load_simulation_data(active_config)
                    
                    pygame.event.clear()
                    state = "simulation"

            elif state == "simulation":
                if event.key == pygame.K_SPACE:
                    playback.toggle_pause()
                elif event.key == pygame.K_LEFT:
                    playback.rewind(60)
                elif event.key == pygame.K_RIGHT:
                    playback.forward(60)
                elif event.key == pygame.K_r:
                    playback.restart()
                elif event.key in (pygame.K_EQUALS, pygame.K_PLUS, pygame.K_KP_PLUS):
                    playback.increase_speed()
                elif event.key in (pygame.K_MINUS, pygame.K_KP_MINUS):
                    playback.decrease_speed()
                elif event.key == pygame.K_c:
                    renderer.toggle_camera()
                elif event.key == pygame.K_ESCAPE:
                    state = "menu"

    if state == "menu":
        menu.draw(renderer.screen, renderer.font_large)
        pygame.display.flip()

    elif state == "simulation":
        playback.update()
        current_frame = playback.frame
        car = player.update(current_frame)
        lap_time_str = get_lap_time(current_frame, player.df)

        renderer.draw(car, lap_time_str, playback.playback_speed, active_config)
        renderer.clock.tick(fps_objetivo)

pygame.quit()
sys.exit()