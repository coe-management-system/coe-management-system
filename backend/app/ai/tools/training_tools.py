def get_training_status(student_id: str):
    """
    Returns the training status for a specific student.
    """
    # Mock data for prototype.
    # In production, this will call the FastAPI/service layer connected to PostgreSQL.
    return {
        "student_id": student_id,
        "completed_trainings": ["Python Basics", "Web Development"],
        "ongoing_trainings": ["Machine Learning"],
        "pending_trainings": ["Cloud Computing"]
    }
