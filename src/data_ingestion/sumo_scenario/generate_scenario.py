# src/data_ingestion/sumo_scenario/generate_scenario.py
import os
import subprocess

# Configuration for the scenario
SCENARIO_NAME = "city_grid"
SCENARIO_PATH = os.path.dirname(__file__) # The directory where this script is
NET_FILE = f"{SCENARIO_PATH}/{SCENARIO_NAME}.net.xml"
ROUTE_FILE = f"{SCENARIO_PATH}/{SCENARIO_NAME}.rou.xml"
CONFIG_FILE = f"{SCENARIO_PATH}/{SCENARIO_NAME}.sumocfg"
TRIP_FILE = f"{SCENARIO_PATH}/trips.trips.xml"

def generate_scenario():
    """
    Generates a complete SUMO scenario with a grid network and random traffic.
    """
    if os.path.exists(CONFIG_FILE):
        print("SUMO scenario already exists. Skipping generation.")
        return

    print("Generating SUMO scenario...")

    # 1. Generate the network file (a simple 5x5 grid)
    # netgenerate is a SUMO tool to create networks
    netgenerate_cmd = [
        "netgenerate",
        "--grid",
        "--grid.number=5",
        "-o", NET_FILE,
        "--no-turnarounds"
    ]
    subprocess.run(netgenerate_cmd, check=True)
    print(f"Successfully created network file: {NET_FILE}")

    # 2. Generate random trips for the network
    # randomTrips.py is a SUMO tool for this purpose
    randomtrips_cmd = [
        "python",
        "/usr/share/sumo/tools/randomTrips.py",
        "-n", NET_FILE,
        "-r", ROUTE_FILE,
        "-e", "1000",  # Number of trips to generate
        "-p", "0.5",   # Period: a new car is generated every 0.5 seconds on average
        "--validate"
    ]
    subprocess.run(randomtrips_cmd, check=True)
    print(f"Successfully created route file: {ROUTE_FILE}")

    # 3. Generate the SUMO configuration file
    config_content = f"""<configuration>
    <input>
        <net-file value="{SCENARIO_NAME}.net.xml"/>
        <route-files value="{SCENARIO_NAME}.rou.xml"/>
    </input>
    <time>
        <begin value="0"/>
    </time>
</configuration>
"""
    with open(CONFIG_FILE, "w") as f:
        f.write(config_content)
    print(f"Successfully created config file: {CONFIG_FILE}")

if __name__ == "__main__":
    generate_scenario()
