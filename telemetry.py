import os
import fastf1
from car import CarState

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
CACHE_DIR = os.path.join(BASE_DIR, "cache")

os.makedirs(CACHE_DIR, exist_ok=True)

fastf1.Cache.enable_cache(CACHE_DIR)

class TelemetryPlayer:
    def __init__(self,
    year,
    grand_prix,
    session_type,
    driver_code="NOR"
):

        print(f"\nCargando sesión {year} {grand_prix} [{session_type}] para {driver_code}...")

        print("1. Obteniendo sesión...")
        self.session = fastf1.get_session(
        year,
        grand_prix,
        session_type
    )

        print("2. Cargando datos FastF1...")
        self.session.load(
        laps=True,
        telemetry=True,
        weather=False,
        messages=False
    )

        print("3. Datos FastF1 cargados.")

        print("4. Buscando vueltas del piloto...")
        driver_laps = self.session.laps.pick_driver(driver_code)

        print(f"5. Vueltas encontradas: {len(driver_laps)}")

        self.lap = driver_laps.pick_fastest()

        print("6. Vuelta rápida encontrada.")

        print("7. Obteniendo datos del coche...")
        self.car_data = self.lap.get_car_data()

        print("8. Obteniendo posición...")
        self.pos_data = self.lap.get_pos_data()

        print("9. Telemetría preparada.")

        self.car = CarState()
        self.df = None

    def update(self, frame):
        idx = min(int(frame), len(self.df) - 1)
        row = self.df.iloc[idx]

        self.car.x = row["X"]
        self.car.y = row["Y"]
        self.car.speed = row["Speed"]
        self.car.rpm = row["RPM"]
        self.car.gear = row["Gear"]
        self.car.throttle = row["Throttle"]
        self.car.brake = row["Brake"]
        self.car.drs = bool(row["DRS"])

        return self.car