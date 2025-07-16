# src/agents/traffic_control_tools.py

import os
import sys
from crewai_tools import BaseTool

# --- Add SUMO tools to system path ---
if 'SUMO_HOME' in os.environ:
    tools = os.path.join(os.environ['SUMO_HOME'], 'tools')
    sys.path.append(tools)
else:
    sys.exit("Please declare environment variable 'SUMO_HOME'")

import traci

# --- Tool Definition ---
# We define a custom tool that our AI agent can use.
# This tool encapsulates the logic for interacting with the SUMO simulation via Traci.

class TrafficLightControlTool(BaseTool):
    name: str = "Traffic Light Control Tool"
    description: str = (
        "A tool to control traffic lights in the SUMO simulation. "
        "Use it to get the IDs of traffic lights or to change the duration of their green phases. "
        "This is the primary method for mitigating traffic congestion."
    )
    
    def _run(self, command: str, **kwargs) -> str:
        """
        The main execution method for the tool.
        It connects to Traci, executes a command, and returns the result.
        """
        # Traci requires a connection for each set of commands.
        try:
            traci.init(port=8813) # Connect to the SUMO instance exposed on port 8813
            
            if command == "get_all_light_ids":
                light_ids = traci.trafficlight.getIDList()
                return f"Successfully retrieved traffic light IDs: {list(light_ids)}"
            
            elif command == "set_green_phase_duration":
                light_id = kwargs.get("light_id")
                duration = kwargs.get("duration")
                if not light_id or not duration:
                    return "Error: 'light_id' and 'duration' are required for set_green_phase_duration."
                
                # A simple, robust way to extend a green phase.
                # WARNING: This is a simplified logic. A real system would be more complex.
                current_program = traci.trafficlight.getProgram(light_id)
                all_logics = traci.trafficlight.getAllProgramLogics(light_id)
                logic_to_modify = next((l for l in all_logics if l.programID == current_program), None)
                
                if not logic_to_modify:
                    return f"Error: Could not find program logic for light {light_id}."

                # Find a green phase and extend its duration
                phase_extended = False
                for phase in logic_to_modify.phases:
                    if 'g' in phase.state.lower() and 'y' not in phase.state.lower():
                        phase.duration = int(duration)
                        phase_extended = True
                        break # Modify only the first green phase found
                
                if not phase_extended:
                    return f"Error: No suitable green phase found to modify for light {light_id}."

                # Set the new program logic
                traci.trafficlight.setProgramLogic(light_id, logic_to_modify)
                
                return (f"Action Executed: Successfully set green phase duration for traffic light "
                        f"'{light_id}' to {duration} seconds.")

            else:
                return "Error: Unknown command. Available commands are 'get_all_light_ids', 'set_green_phase_duration'."

        except traci.TraCIException as e:
            return f"Error connecting to or controlling SUMO: {e}. Ensure the simulation is running."
        finally:
            # Always close the connection
            traci.close()

# Instantiate the tool for the agent to use
traffic_tool = TrafficLightControlTool()
