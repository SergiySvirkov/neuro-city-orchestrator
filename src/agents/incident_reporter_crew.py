# src/agents/incident_reporter_crew.py

import os
from dotenv import load_dotenv
from crewai import Agent, Task, Crew, Process
from langchain_google_genai import ChatGoogleGenerativeAI

# Load environment variables from .env file
load_dotenv()

# --- LLM Configuration ---
# Set up the language model (Gemini) that the agent will use.
# Ensure you have your GEMINI_API_KEY in the .env file.
llm = ChatGoogleGenerativeAI(
    model="gemini-1.5-flash",
    verbose=False, # Set to True for detailed LLM logs
    temperature=0.5,
    google_api_key=os.getenv("GEMINI_API_KEY")
)

# --- Agent Definition ---
# Create a specialized agent for reporting traffic incidents.
traffic_incident_reporter = Agent(
    role='Senior Traffic Control Reporter',
    goal='Generate clear, concise, and actionable reports on traffic incidents for city operators.',
    backstory=(
        "You are an expert in urban traffic management systems. "
        "Your job is to analyze raw traffic data and create human-readable reports. "
        "These reports are critical for dispatching emergency services, rerouting traffic, "
        "and informing the public. Your reports must be accurate and easy to understand."
    ),
    verbose=False,
    allow_delegation=False,
    llm=llm
)

# --- Task Definition ---
# Define the task that the agent will perform.
# The input variables {{district}} and {{vehicle_count}} will be filled in dynamically.
report_creation_task = Task(
    description=(
        "A high traffic density event has been detected in the city. "
        "Analyze the following data and generate a formal incident report. "
        "Data: District='{district}', Vehicle_Count='{vehicle_count}' vehicles per minute.\n\n"
        "The report should include:\n"
        "1. A clear, bold title: 'TRAFFIC INCIDENT REPORT'.\n"
        "2. A summary of the incident.\n"
        "3. The severity level (e.g., High, Critical) based on the vehicle count.\n"
        "4. A list of recommended immediate actions for city operators (e.g., 'Monitor CCTV', 'Prepare to reroute traffic')."
    ),
    expected_output=(
        "A well-formatted, professional incident report in plain text. "
        "The report should be structured and easy to read."
    ),
    agent=traffic_incident_reporter
)

# --- Crew Definition ---
# Create the crew with the agent and the task.
incident_crew = Crew(
    agents=[traffic_incident_reporter],
    tasks=[report_creation_task],
    process=Process.sequential,
    verbose=False # Set to 2 for detailed crew logs
)

def create_and_run_crew(district, vehicle_count):
    """
    This function takes incident data, injects it into the task,
    and runs the CrewAI process to generate a report.
    """
    print(">>> Handing over to AI Agent Crew...")
    
    # Create a dictionary with the specific data for this incident
    incident_data = {
        'district': district,
        'vehicle_count': vehicle_count
    }
    
    # Kick off the crew's work with the specific context
    result = incident_crew.kickoff(inputs=incident_data)
    return result
