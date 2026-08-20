from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    DATABASE_URL: str
    SECRET_KEY: str
    ALGORITHM: str
    ACCESS_TOKEN_EXPIRE_MINUTES: int

    # ------------------------------------------------------------------
    # Attendance calculator configuration
    # ------------------------------------------------------------------
    # Minimum attendance percentage before a student is flagged as deficient.
    ATTENDANCE_THRESHOLD_PERCENT: float = 75.0

    # Whether a Leave (L) mark counts towards "Total Classes Held" (denominator).
    # True  -> leave counts as held but not present (percentage = P / (P+A+L)).
    # False -> leave is excluded from the denominator entirely (like a holiday).
    ATTENDANCE_LEAVE_COUNTS_AS_HELD: bool = False

    # How a new upload merges with already-recorded dates:
    #   cumulative -> adds to existing totals (overlapping dates are overwritten
    #                 and logged in the processing summary).
    #   overwrite  -> totals are recomputed strictly from the events in this file.
    ATTENDANCE_UPDATE_MODE: str = "cumulative"

    # Numeric student references (roll/admission) at or above this threshold are
    # treated as sentinel/placeholder IDs (e.g. 999999) rather than real records.
    ATTENDANCE_SENTINEL_ROLL_THRESHOLD: int = 100000

    # Numeric subject codes at or above this threshold are treated as sentinels.
    ATTENDANCE_SENTINEL_SUBJECT_THRESHOLD: int = 9000

    model_config = SettingsConfigDict(
        env_file=".env",
        extra="ignore",
    )


settings = Settings()