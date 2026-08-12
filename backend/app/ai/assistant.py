from .tools.attendance_tools import get_low_attendance_students
from .tools.student_tools import get_student
from .tools.workload_tools import get_faculty_workload
from .tools.scheduling_tools import get_timetable_conflicts

def process_query(query: str):
    """
    Mock AI Assistant query processor.
    In production, an LLM will parse the query and decide which controlled tool to call.
    """
    query_lower = query.lower()
    
    # 1. First demonstration - Low attendance
    if "attendance below 75" in query_lower:
        # Tool call
        data = get_low_attendance_students()
        # AI Natural-language answer generation based on tool data
        names = [student["name"] for student in data]
        return f"The students with attendance below 75% are {', '.join(names)}."
        
    # 2. Second demonstration - Student lookup
    elif "student cse101" in query_lower:
        # Tool call
        data = get_student("CSE101")
        if "error" in data:
            return data["error"]
        return f"Student {data['name']} (Roll No: {data['roll_no']}) has an attendance of {data['attendance']}%."
        
    # 3. Third demonstration - Faculty workload
    elif "workload of faculty member 12" in query_lower:
        # Tool call
        data = get_faculty_workload(12)
        return f"Faculty 12 has {data['allocated_hours']} allocated hours, {data['completed_hours']} completed, and {data['remaining_hours']} remaining."
        
    # 4. Fourth demonstration - Scheduling conflict
    elif "timetable conflicts" in query_lower:
        # Tool call
        data = get_timetable_conflicts()
        conflict = data[0]
        return f"Yes, there is a conflict: {conflict['faculty']} is scheduled for {conflict['subject_1']} and {conflict['subject_2']} at {conflict['time']}."
        
    return "I am not sure how to help with that yet. This is a prototype."
