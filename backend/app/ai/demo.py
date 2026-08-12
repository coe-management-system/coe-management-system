import sys
import os

# Add the parent directory of backend to sys.path to allow imports like 'app.ai.assistant'
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../../')))

from app.ai.assistant import AIAssistant

def main():
    ai = AIAssistant()

    print("=========================================")
    print("DEMO 1: Low Attendance Students")
    print("User: What students have attendance below 75%?")
    print("-----------------------------------------")
    response = ai.ask("What students have attendance below 75%?")
    print(f"\nAI Response:\n{response}")
    print("=========================================\n")

    print("=========================================")
    print("DEMO 2: Student Lookup")
    print("User: Tell me about student CSE101.")
    print("-----------------------------------------")
    response = ai.ask("Tell me about student CSE101.")
    print(f"\nAI Response:\n{response}")
    print("=========================================\n")

    print("=========================================")
    print("DEMO 3: Faculty Workload")
    print("User: What is the workload of faculty member 12?")
    print("-----------------------------------------")
    response = ai.ask("What is the workload of faculty member 12?")
    print(f"\nAI Response:\n{response}")
    print("=========================================\n")

    print("=========================================")
    print("DEMO 4: Scheduling Conflict")
    print("User: Are there any timetable conflicts?")
    print("-----------------------------------------")
    response = ai.ask("Are there any timetable conflicts?")
    print(f"\nAI Response:\n{response}")
    print("=========================================\n")

if __name__ == "__main__":
    main()
