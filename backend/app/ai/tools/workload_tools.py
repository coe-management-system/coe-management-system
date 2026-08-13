def get_faculty_workload(faculty_id: int):
    """
    Returns workload information for a specific faculty member.
    """
    # Mock data for prototype.
    # In production, this will call the FastAPI/service layer connected to PostgreSQL.
    return {
        "faculty_id": faculty_id,
        "allocated_hours": 32,
        "completed_hours": 24,
        "remaining_hours": 8
    }
