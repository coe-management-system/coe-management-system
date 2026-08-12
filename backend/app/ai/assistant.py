import json
from .tools.student_tools import get_student
from .tools.attendance_tools import get_low_attendance_students
from .tools.workload_tools import get_faculty_workload
from .tools.scheduling_tools import get_timetable_conflicts

class AIAssistant:
    """
    Mock AI Assistant for Member 5 Prototype.
    This routes user queries to the appropriate controlled tools
    and formats the data into natural language.
    """
    def __init__(self):
        pass

    def ask(self, query: str) -> str:
        query = query.lower()

        # Demonstration 1: Low attendance
        if "attendance below 75" in query:
            print("[AI Internal] Intent matched: Checking low attendance.")
            print("[AI Internal] Calling Tool: get_low_attendance_students()")
            data = get_low_attendance_students()
            print(f"[AI Internal] Data returned: {json.dumps(data, indent=2)}")
            
            # Formulate response
            names = [s["name"] for s in data]
            return f"The following students have attendance below 75%: {', '.join(names)}."
        
        # Demonstration 2: Student lookup
        elif "student cse101" in query:
            print("[AI Internal] Intent matched: Student lookup.")
            print("[AI Internal] Calling Tool: get_student('CSE101')")
            data = get_student("CSE101")
            print(f"[AI Internal] Data returned: {json.dumps(data, indent=2)}")
            
            if data:
                return f"Student {data['name']} (Roll No: {data['roll_no']}) is in the {data['department']} department with an attendance of {data['attendance']}%."
            return "Student not found."

        # Demonstration 3: Faculty workload
        elif "workload of faculty member 12" in query:
            print("[AI Internal] Intent matched: Faculty workload lookup.")
            print("[AI Internal] Calling Tool: get_faculty_workload('12')")
            data = get_faculty_workload("12")
            print(f"[AI Internal] Data returned: {json.dumps(data, indent=2)}")
            
            if data:
                return f"Faculty member {data['faculty_id']} has {data['remaining_hours']} remaining hours out of {data['allocated_hours']} allocated hours."
            return "Faculty workload not found."
            
        # Demonstration 4: Scheduling conflict
        elif "timetable conflicts" in query:
            print("[AI Internal] Intent matched: Checking timetable conflicts.")
            print("[AI Internal] Calling Tool: get_timetable_conflicts()")
            data = get_timetable_conflicts()
            print(f"[AI Internal] Data returned: {json.dumps(data, indent=2)}")
            
            if data:
                conflict = data[0]
                return f"Yes, there is a {conflict['conflict_type']} for {conflict['faculty']} at {conflict['time']} between {conflict['subject_1']} and {conflict['subject_2']}."
            return "There are no timetable conflicts."
            
        else:
            return "I'm sorry, I don't understand that query for this prototype."
