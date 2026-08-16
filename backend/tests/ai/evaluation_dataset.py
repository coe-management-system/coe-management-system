EVALUATION_QUESTIONS = [
    # Student
    {"q": "Tell me about CSE101", "intent": "student_info", "tools": ["get_student"]},
    {"q": "Who is student CSE102?", "intent": "student_info", "tools": ["get_student"]},
    {"q": "Give me info on CSE103", "intent": "student_info", "tools": ["get_student"]},
    {"q": "What's the email for CSE104?", "intent": "student_info", "tools": ["get_student"]},
    {"q": "Show details for CSE105", "intent": "student_info", "tools": ["get_student"]},
    
    # Attendance
    {"q": "What is CSE101's attendance?", "intent": "student_attendance", "tools": ["get_student_attendance"]},
    {"q": "Show attendance for CSE102", "intent": "student_attendance", "tools": ["get_student_attendance"]},
    {"q": "Did CSE103 attend classes?", "intent": "student_attendance", "tools": ["get_student_attendance"]},
    {"q": "Which students have attendance below 75%?", "intent": "low_attendance_students", "tools": ["get_low_attendance_students"]},
    {"q": "Who has low attendance?", "intent": "low_attendance_students", "tools": ["get_low_attendance_students"]},
    
    # Training / Certification
    {"q": "What is CSE101's training status?", "intent": "student_training", "tools": ["get_training_status"]},
    {"q": "Did CSE102 complete training?", "intent": "student_training", "tools": ["get_training_status"]},
    {"q": "Show training for CSE103", "intent": "student_training", "tools": ["get_training_status"]},
    
    # Student 360
    {"q": "Give me a summary of CSE101's attendance, training, and certification.", "intent": "student_360", "tools": ["get_student", "get_student_attendance", "get_training_status", "get_certification_status"]},
    {"q": "I need CSE102's attendance, training, and certification records.", "intent": "student_360", "tools": ["get_student", "get_student_attendance", "get_training_status", "get_certification_status"]},

    # Workload
    {"q": "What is faculty 12's workload?", "intent": "faculty_workload", "tools": ["get_faculty_workload"]},
    {"q": "Show workload for faculty 15", "intent": "faculty_workload", "tools": ["get_faculty_workload"]},
    {"q": "Who is overloaded?", "intent": "faculty_workload", "tools": ["get_faculty_workload"]},
    {"q": "Is faculty 12 overloaded?", "intent": "faculty_workload", "tools": ["get_faculty_workload"]},
    {"q": "Tell me about faculty workload", "intent": "faculty_workload", "tools": ["get_faculty_workload"]},

    # Scheduling
    {"q": "Are there timetable conflicts?", "intent": "timetable_conflicts", "tools": ["get_timetable_conflicts"]},
    {"q": "Show scheduling conflicts", "intent": "timetable_conflicts", "tools": ["get_timetable_conflicts"]},
    {"q": "What happens if faculty 12 is unavailable?", "intent": "what_if_simulation", "tools": ["run_what_if"]},
    {"q": "What if faculty 15 becomes unavailable?", "intent": "what_if_simulation", "tools": ["run_what_if"]},
    {"q": "Run simulation for unavailable faculty 12", "intent": "what_if_simulation", "tools": ["run_what_if"]},
    
    # Multi-tool
    {"q": "Which students have attendance below 75% and incomplete training?", "intent": "low_attendance_incomplete_training", "tools": ["get_low_attendance_students", "get_training_status"]},
    {"q": "Who has low attendance and incomplete training?", "intent": "low_attendance_incomplete_training", "tools": ["get_low_attendance_students", "get_training_status"]},
    
    # Context / Ambiguity (Evaluated manually in tests with session states)
    # Security (Tested in test_day4_scenarios.py)
]
