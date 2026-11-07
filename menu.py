import pygame
import fastf1
import threading

class Menu:
    def __init__(self):

        self.selected = 0

        self.seasons = [2023, 2024, 2025]
        self.season_idx = 2

        self.gps = []
        self.gp_idx = 0

        self.sessions = []
        self.session_idx = 0

        self.drivers = []
        self.driver_idx = 0

        self.schedule_cache = {}
        self.driver_cache = {}

        self.drivers_loading = False
        self.driver_loading_key = None

        self.update_gps()
        self.update_sessions()
        self.update_drivers()  

    def update_gps(self):

        year = self.seasons[self.season_idx]

        if year not in self.schedule_cache:

            schedule = fastf1.get_event_schedule(year)

            self.schedule_cache[year] = schedule

        else:

            schedule = self.schedule_cache[year]

        self.gps = schedule["EventName"].dropna().tolist()

        self.gp_idx = min(self.gp_idx, len(self.gps) - 1)

    def update_sessions(self):

        if not self.gps:
            self.sessions = []
            return

        year = self.seasons[self.season_idx]
        gp = self.gps[self.gp_idx]

        schedule = self.schedule_cache[year]

        event = schedule[schedule["EventName"] == gp].iloc[0]

        self.sessions = []

        session_names = {
        "Practice 1": "FP1",
        "Practice 2": "FP2",
        "Practice 3": "FP3",
        "Qualifying": "Q",
        "Race": "R",
        "Sprint Qualifying": "SQ",
        "Sprint": "Sprint"
    }

        for i in range(1, 6):

            column = f"Session{i}"

            if column in schedule.columns:

                session = event[column]

                if isinstance(session, str) and session:

                    self.sessions.append(
                    session_names.get(session, session))

    def update_drivers(self):

        if not self.gps or not self.sessions:
            self.drivers = []
            return

        year = self.seasons[self.season_idx]
        gp = self.gps[self.gp_idx]
        session = self.sessions[self.session_idx]

        key = (year, gp, session)

        if key in self.driver_cache:

            self.drivers = self.driver_cache[key]
            self.drivers_loading = False
            self.driver_loading_key = None

            self.driver_idx = min(
            self.driver_idx,
            len(self.drivers) - 1)

            return

        if self.driver_loading_key == key:
            return

        self.drivers = []
        self.drivers_loading = True
        self.driver_loading_key = key

        thread = threading.Thread(target=self._load_drivers_background, args=(key,), daemon=True)

        thread.start()

    def _load_drivers_background(self, key):

        year, gp, session = key

        try:

            print(f"Cargando pilotos: {year} - {gp} - {session}")

            f1_session = fastf1.get_session(
            year,
            gp,
            session
        )

            f1_session.load(
            laps=False,
            telemetry=False,
            weather=False,
            messages=False
        )

            drivers = []

            for driver in f1_session.drivers:

                info = f1_session.get_driver(driver)

                drivers.append({
        "number": info["DriverNumber"],
        "code": info["Abbreviation"],
        "name": info["FullName"]
    })

            self.driver_cache[key] = drivers

            current_key = (
            self.seasons[self.season_idx],
            self.gps[self.gp_idx],
            self.sessions[self.session_idx]
        )

            if current_key == key:

                self.drivers = drivers
                self.driver_idx = 0

        except Exception as e:

            print(
            f"Error cargando pilotos "
            f"{year} - {gp} - {session}: {e}")

            self.drivers = []

        finally:

            if self.driver_loading_key == key:
                self.drivers_loading = False
                self.driver_loading_key = None

    def navigate_up(self):
        self.selected = (self.selected - 1) % 5

    def navigate_down(self):
        self.selected = (self.selected + 1) % 5

    def change_value(self, direction):

        if self.selected == 0:

            self.season_idx = (self.season_idx + direction) % len(self.seasons)

            self.gp_idx = 0
            self.session_idx = 0
            self.driver_idx = 0

            self.update_gps()
            self.update_sessions()
            self.update_drivers()

        elif self.selected == 1:

            self.gp_idx = (self.gp_idx + direction) % len(self.gps)

            self.session_idx = 0
            self.driver_idx = 0

            self.update_sessions()
            self.update_drivers()

        elif self.selected == 2:

            self.session_idx = (self.session_idx + direction) % len(self.sessions)

            self.driver_idx = 0

            self.update_drivers()

        elif self.selected == 3:

            self.driver_idx = (self.driver_idx + direction) % len(self.drivers)

    def get_selected_config(self):
        return {
            "year": self.seasons[self.season_idx],
            "gp": self.gps[self.gp_idx],
            "session": self.sessions[self.session_idx],
            "driver": self.drivers[self.driver_idx]["code"]
        }

    def draw(self, screen, font):
        screen.fill((20, 20, 20))

        title = font.render(
        "F1 TELEMETRY SIMULATOR",
        True,
        (255, 255, 255)
    )
        screen.blit(title, (380, 60))

        if self.drivers:
            driver = self.drivers[self.driver_idx]
            driver_display = f"{driver['number']} - {driver['code']}"
        else:
            driver_display = "---"

        entries = [
        f"Season    : < {self.seasons[self.season_idx]} >",
        f"Grand Prix: < {self.gps[self.gp_idx]} >",
        f"Session   : < {self.sessions[self.session_idx]} >",

        (
            "Driver    : < LOADING... >"
            if self.drivers_loading
            else f"Driver    : < {driver_display} >"
        ),

        "",
        "[ ENTER : START SIMULATION ]"
    ]

        y = 180

        for i, line in enumerate(entries):

            color = (
            (255, 215, 0)
            if i == self.selected
            else (230, 230, 230)
        )

            txt = font.render(line, True, color)
            screen.blit(txt, (250, y))

            y += 50

        note_font = pygame.font.SysFont("Consolas", 14)

        note_text = (
        "This software simulates the fastest lap set by the chosen driver "
        "during the selected session, Grand Prix and season."
    )

        txt_note = note_font.render(
        note_text,
        True,
        (150, 150, 150)
    )

        note_x = (
        screen.get_width() - txt_note.get_width()
    ) // 2

        screen.blit(txt_note, (note_x, 660))