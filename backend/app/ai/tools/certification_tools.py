def get_certification_status(student_id: str):
    """
    Returns the certification status for a specific student.
    """
    # Mock data for prototype.
    # In production, this will call the FastAPI/service layer connected to PostgreSQL.
    return {
        "student_id": student_id,
        "certifications": [
            {
                "name": "AWS Certified Cloud Practitioner",
                "status": "Completed",
                "date": "2023-10-15"
            },
            {
                "name": "Google Cloud Associate Engineer",
                "status": "In Progress",
                "date": None
            }
        ]
    }
