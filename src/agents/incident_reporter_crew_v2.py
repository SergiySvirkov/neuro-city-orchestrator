# src/agents/incident_reporter_crew_v2.py

import os
from dotenv import load_dotenv
from crewai import Agent, Task, Crew, Process
from langchain_google_genai import ChatGoogleGenerativeAI
from .traffic_control_tools import traffic_tool # Import our new tool

load_dotenv()
llm = ChatGoogleGenerativeAI(model="gemini-1.5-flash", google_api_key=os.getenv("GEMINI_API_KEY"))

# --- Agent Definitions ---

# 1. Reporter Agent (same as before)
traffic_incident_reporter = Agent(
    role='Senior Traffic Control Reporter',
    goal='Generate clear, concise reports on traffic incidents.',
    backstory="An expert in urban traffic management, you analyze raw data to create human-readable reports.",
    verbose=False,
    allow_delegation=False,
    llm=llm
)

# 2. NEW: Control Agent
traffic_control_engineer = Agent(
    role='Traffic Control Systems Engineer',
    goal='Analyze incident reports and formulate an actionable plan to mitigate traffic congestion using available tools.',
    backstory=(
        "You are a skilled engineer responsible for real-time traffic light control. "
        "Based on reports from the reporting unit, you must devise and execute a plan "
        "to adjust traffic light timings to ease congestion. You must use the tools provided to you."
    ),
    verbose=True,
    allow_delegation=False,
    tools=[traffic_tool], # Give the agent access to our custom tool
    llm=llm
)

# --- Task Definitions ---

# 1. Reporting Task (same as before)
report_creation_task = Task(
    description=(
        "High traffic density detected. Analyze the data and generate a formal incident report. "
        "Data: District='{district}', Vehicle_Count='{vehicle_count}' vehicles per minute."
    ),
    expected_output="A well-formatted incident report summarizing the situation.",
    agent=traffic_incident_reporter
)

# 2. NEW: Mitigation Task
mitigation_planning_task = Task(
    description=(
        "Based on the incident report from the previous step, create and execute a plan to mitigate the traffic. "
        "First, get the list of all traffic lights to understand the available options. "
        "Then, select ONE relevant traffic light that is likely central to the congested district "
        "and use the tool to extend its green light duration to 60 seconds. "
        "Your final answer must be the result of the tool execution."
    ),
    expected_output="A confirmation message from the Traffic Light Control Tool stating the action taken.",
    agent=traffic_control_engineer,
    context=[report_creation_task] # This task depends on the output of the first task
)

# --- Crew Definition ---
incident_crew_v2 = Crew(
    agents=[traffic_incident_reporter, traffic_control_engineer],
    tasks=[report_creation_task, mitigation_planning_task],
    process=Process.sequential,
    verbose=2 # Set to 2 to see the agent's thought process and tool usage
)

def create_and_run_crew_v2(district, vehicle_count):
    """Runs the enhanced crew to report and mitigate the incident."""
    print(">>> Handing over to AI Agent Crew v2 (Report & Mitigate)...")
    incident_data = {'district': district, 'vehicle_count': vehicle_count}
    result = incident_crew_v2.kickoff(inputs=incident_data)
    return result
