"""
Timetable Version Manager (M3-11)

Manages versioned timetable changes, including creation, comparison,
approval workflow, and rollback capabilities.
"""

import json
from datetime import date, datetime
from typing import Optional, List, Dict, Any

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.models.timetable import TimetableEvent
from app.models.timetable_version import (
    TimetableVersion,
    TimetableVersionEvent,
    VersionStatus,
)
from app.models.user import User


class TimetableVersionManager:
    """
    Manages versioned timetable snapshots and change tracking.
    
    Features:
    - Create versioned snapshots of the timetable
    - Compare versions
    - Approval workflow (draft -> proposed -> approved -> published)
    - Rollback to previous versions
    - Change tracking with detailed diffs
    """

    def __init__(self, db: Session):
        self.db = db

    def _serialize_events(self, events: List[TimetableEvent]) -> str:
        """Serialize timetable events to JSON."""
        data = []
        for event in events:
            data.append({
                "id": event.id,
                "subject_id": event.subject_id,
                "faculty_id": event.faculty_id,
                "batch_id": event.batch_id,
                "room_id": event.room_id,
                "event_date": event.event_date.isoformat() if event.event_date else None,
                "start_time": event.start_time.isoformat() if event.start_time else None,
                "end_time": event.end_time.isoformat() if event.end_time else None,
                "priority": event.priority,
            })
        return json.dumps(data, default=str)

    def _deserialize_events(self, json_str: str) -> List[Dict[str, Any]]:
        """Deserialize JSON to event data."""
        return json.loads(json_str)

    def _get_next_version_number(self) -> int:
        """Get the next version number."""
        max_version = self.db.execute(
            select(func.max(TimetableVersion.version_number))
        ).scalar()
        return (max_version or 0) + 1

    def create_version(
        self,
        name: str,
        description: Optional[str] = None,
        created_by: Optional[int] = None,
        status: VersionStatus = VersionStatus.DRAFT,
        events: Optional[List[TimetableEvent]] = None,
    ) -> TimetableVersion:
        """
        Create a new timetable version.
        
        Args:
            name: Version name
            description: Optional description
            created_by: ID of user creating the version
            status: Initial version status
            events: Optional specific events to snapshot (defaults to all)
            
        Returns:
            Created TimetableVersion
        """
        if events is None:
            events = self.db.execute(select(TimetableEvent)).scalars().all()

        version_number = self._get_next_version_number()
        snapshot = self._serialize_events(events)

        version = TimetableVersion(
            version_number=version_number,
            name=name,
            description=description,
            status=status,
            snapshot=snapshot,
            created_by=created_by,
        )

        self.db.add(version)
        self.db.flush()

        # Store individual version events for detailed querying
        for event in events:
            version_event = TimetableVersionEvent(
                version_id=version.id,
                original_event_id=event.id,
                subject_id=event.subject_id,
                faculty_id=event.faculty_id,
                batch_id=event.batch_id,
                room_id=event.room_id,
                event_date=event.event_date,
                start_time=event.start_time,
                end_time=event.end_time,
                priority=event.priority,
                change_type="added",
            )
            self.db.add(version_event)

        self.db.commit()
        self.db.refresh(version)
        return version

    def create_version_from_changes(
        self,
        name: str,
        description: str,
        added_events: List[TimetableEvent],
        modified_events: List[tuple],  # (old_event, new_event)
        removed_event_ids: List[int],
        created_by: Optional[int] = None,
        status: VersionStatus = VersionStatus.PROPOSED,
    ) -> TimetableVersion:
        """
        Create a version based on specific changes.
        
        Args:
            name: Version name
            description: Description of changes
            added_events: New events to add
            modified_events: List of (old_event, new_event) tuples
            removed_event_ids: IDs of events to remove
            created_by: ID of user creating the version
            status: Initial status
            
        Returns:
            Created TimetableVersion
        """
        # Get current timetable state
        current_events = list(self.db.execute(select(TimetableEvent)).scalars().all())
        
        # Build new state
        event_dict = {e.id: e for e in current_events}
        
        # Apply removals
        for eid in removed_event_ids:
            event_dict.pop(eid, None)
        
        # Apply modifications
        for old_event, new_event in modified_events:
            event_dict[old_event.id] = new_event
        
        # Apply additions
        for event in added_events:
            event_dict[event.id] = event
        
        new_events = list(event_dict.values())
        
        version = self.create_version(
            name=name,
            description=description,
            created_by=created_by,
            status=status,
            events=new_events,
        )
        
        # Update change counters
        version.events_added = len(added_events)
        version.events_modified = len(modified_events)
        version.events_removed = len(removed_event_ids)
        version.changes_summary = description
        
        # Update version events with change types
        for event in added_events:
            ve = self.db.execute(
                select(TimetableVersionEvent)
                .where(
                    TimetableVersionEvent.version_id == version.id,
                    TimetableVersionEvent.original_event_id == event.id,
                )
            ).scalar_one_or_none()
            if ve:
                ve.change_type = "added"
        
        for old_event, new_event in modified_events:
            ve = self.db.execute(
                select(TimetableVersionEvent)
                .where(
                    TimetableVersionEvent.version_id == version.id,
                    TimetableVersionEvent.original_event_id == old_event.id,
                )
            ).scalar_one_or_none()
            if ve:
                ve.change_type = "modified"
        
        for eid in removed_event_ids:
            ve = self.db.execute(
                select(TimetableVersionEvent)
                .where(
                    TimetableVersionEvent.version_id == version.id,
                    TimetableVersionEvent.original_event_id == eid,
                )
            ).scalar_one_or_none()
            if ve:
                ve.change_type = "removed"
        
        self.db.commit()
        self.db.refresh(version)
        return version

    def get_version(self, version_id: int) -> Optional[TimetableVersion]:
        """Get a version by ID."""
        return self.db.execute(
            select(TimetableVersion).where(TimetableVersion.id == version_id)
        ).scalar_one_or_none()

    def get_version_by_number(self, version_number: int) -> Optional[TimetableVersion]:
        """Get a version by version number."""
        return self.db.execute(
            select(TimetableVersion).where(TimetableVersion.version_number == version_number)
        ).scalar_one_or_none()

    def list_versions(
        self,
        status: Optional[VersionStatus] = None,
        limit: int = 50,
        offset: int = 0,
    ) -> List[TimetableVersion]:
        """
        List timetable versions.
        
        Args:
            status: Optional filter by status
            limit: Maximum number of versions
            offset: Pagination offset
            
        Returns:
            List of versions
        """
        query = select(TimetableVersion).order_by(TimetableVersion.version_number.desc())
        
        if status:
            query = query.where(TimetableVersion.status == status)
        
        query = query.limit(limit).offset(offset)
        return list(self.db.execute(query).scalars().all())

    def get_latest_version(self) -> Optional[TimetableVersion]:
        """Get the most recent version."""
        return self.db.execute(
            select(TimetableVersion)
            .order_by(TimetableVersion.version_number.desc())
            .limit(1)
        ).scalar_one_or_none()

    def get_published_version(self) -> Optional[TimetableVersion]:
        """Get the currently published version."""
        return self.db.execute(
            select(TimetableVersion)
            .where(TimetableVersion.status == VersionStatus.PUBLISHED)
            .order_by(TimetableVersion.version_number.desc())
            .limit(1)
        ).scalar_one_or_none()

    def compare_versions(
        self,
        version_a_id: int,
        version_b_id: int,
    ) -> Dict[str, Any]:
        """
        Compare two timetable versions.
        
        Args:
            version_a_id: First version ID (base)
            version_b_id: Second version ID (compare to)
            
        Returns:
            Dictionary with comparison results
        """
        version_a = self.get_version(version_a_id)
        version_b = self.get_version(version_b_id)

        if not version_a or not version_b:
            raise ValueError("One or both versions not found")

        events_a = self._deserialize_events(version_a.snapshot)
        events_b = self._deserialize_events(version_b.snapshot)

        # Create lookup dictionaries
        events_a_dict = {e["id"]: e for e in events_a}
        events_b_dict = {e["id"]: e for e in events_b}

        # Find differences
        added = []
        removed = []
        modified = []
        unchanged = []

        all_ids = set(events_a_dict.keys()) | set(events_b_dict.keys())

        for eid in all_ids:
            event_a = events_a_dict.get(eid)
            event_b = events_b_dict.get(eid)

            if event_a is None:
                added.append(event_b)
            elif event_b is None:
                removed.append(event_a)
            else:
                # Check for modifications
                if self._events_differ(event_a, event_b):
                    modified.append({
                        "event_id": eid,
                        "old": event_a,
                        "new": event_b,
                        "changes": self._get_field_changes(event_a, event_b),
                    })
                else:
                    unchanged.append(event_a)

        return {
            "version_a": {
                "id": version_a.id,
                "version_number": version_a.version_number,
                "name": version_a.name,
            },
            "version_b": {
                "id": version_b.id,
                "version_number": version_b.version_number,
                "name": version_b.name,
            },
            "summary": {
                "total_events_a": len(events_a),
                "total_events_b": len(events_b),
                "added": len(added),
                "removed": len(removed),
                "modified": len(modified),
                "unchanged": len(unchanged),
            },
            "details": {
                "added": added,
                "removed": removed,
                "modified": modified,
                "unchanged": unchanged,
            },
        }

    def _events_differ(self, event_a: Dict, event_b: Dict) -> bool:
        """Check if two events differ in any significant field."""
        compare_fields = [
            "subject_id", "faculty_id", "batch_id", "room_id",
            "event_date", "start_time", "end_time", "priority",
        ]
        for field in compare_fields:
            if event_a.get(field) != event_b.get(field):
                return True
        return False

    def _get_field_changes(self, event_a: Dict, event_b: Dict) -> List[Dict]:
        """Get list of field changes between two events."""
        compare_fields = [
            "subject_id", "faculty_id", "batch_id", "room_id",
            "event_date", "start_time", "end_time", "priority",
        ]
        changes = []
        for field in compare_fields:
            if event_a.get(field) != event_b.get(field):
                changes.append({
                    "field": field,
                    "old": event_a.get(field),
                    "new": event_b.get(field),
                })
        return changes

    def approve_version(
        self,
        version_id: int,
        approved_by: int,
    ) -> TimetableVersion:
        """
        Approve a version (move from proposed to approved).
        
        Args:
            version_id: Version to approve
            approved_by: User ID approving
            
        Returns:
            Updated version
        """
        version = self.get_version(version_id)
        if not version:
            raise ValueError("Version not found")

        if version.status not in (VersionStatus.DRAFT, VersionStatus.PROPOSED):
            raise ValueError(f"Cannot approve version with status {version.status}")

        version.status = VersionStatus.APPROVED
        version.approved_by = approved_by
        version.approved_at = datetime.utcnow()

        self.db.commit()
        self.db.refresh(version)
        return version

    def publish_version(
        self,
        version_id: int,
        published_by: int,
    ) -> TimetableVersion:
        """
        Publish a version (make it the official timetable).
        
        Args:
            version_id: Version to publish
            published_by: User ID publishing
            
        Returns:
            Updated version
        """
        version = self.get_version(version_id)
        if not version:
            raise ValueError("Version not found")

        if version.status != VersionStatus.APPROVED:
            raise ValueError(f"Only approved versions can be published (current: {version.status})")

        # Unpublish any existing published version
        existing_published = self.get_published_version()
        if existing_published and existing_published.id != version_id:
            existing_published.status = VersionStatus.APPROVED

        version.status = VersionStatus.PUBLISHED
        version.approved_by = published_by
        version.approved_at = datetime.utcnow()

        self.db.commit()
        self.db.refresh(version)
        return version

    def rollback_to_version(
        self,
        version_id: int,
        rolled_back_by: int,
    ) -> TimetableVersion:
        """
        Create a new version that rolls back to a previous version.
        
        Args:
            version_id: Version to rollback to
            rolled_back_by: User ID performing rollback
            
        Returns:
            New version representing the rollback
        """
        target_version = self.get_version(version_id)
        if not target_version:
            raise ValueError("Version not found")

        # Create new version from target snapshot
        events_data = self._deserialize_events(target_version.snapshot)
        
        # Create temporary events for version creation
        temp_events = []
        for e in events_data:
            temp_event = TimetableEvent(
                id=e["id"],
                subject_id=e["subject_id"],
                faculty_id=e["faculty_id"],
                batch_id=e["batch_id"],
                room_id=e["room_id"],
                event_date=date.fromisoformat(e["event_date"]) if e["event_date"] else None,
                start_time=datetime.strptime(e["start_time"], "%H:%M:%S").time() if e["start_time"] else None,
                end_time=datetime.strptime(e["end_time"], "%H:%M:%S").time() if e["end_time"] else None,
                priority=e["priority"],
            )
            temp_events.append(temp_event)

        rollback_version = self.create_version(
            name=f"Rollback to v{target_version.version_number}",
            description=f"Rollback to version {target_version.version_number}: {target_version.name}",
            created_by=rolled_back_by,
            status=VersionStatus.PROPOSED,
            events=temp_events,
        )

        return rollback_version

    def apply_version_to_timetable(
        self,
        version_id: int,
    ) -> Dict[str, int]:
        """
        Apply a version's events to the official timetable.
        
        WARNING: This modifies the live timetable_events table.
        
        Args:
            version_id: Version to apply
            
        Returns:
            Dictionary with counts of changes applied
        """
        version = self.get_version(version_id)
        if not version:
            raise ValueError("Version not found")

        if version.status != VersionStatus.PUBLISHED:
            raise ValueError("Only published versions can be applied to timetable")

        events_data = self._deserialize_events(version.snapshot)

        # Clear current timetable
        current_count = self.db.execute(
            select(func.count(TimetableEvent.id))
        ).scalar() or 0
        
        self.db.execute(TimetableEvent.__table__.delete())

        # Insert version events
        added = 0
        for e in events_data:
            event = TimetableEvent(
                subject_id=e["subject_id"],
                faculty_id=e["faculty_id"],
                batch_id=e["batch_id"],
                room_id=e["room_id"],
                event_date=date.fromisoformat(e["event_date"]) if e["event_date"] else None,
                start_time=datetime.strptime(e["start_time"], "%H:%M:%S").time() if e["start_time"] else None,
                end_time=datetime.strptime(e["end_time"], "%H:%M:%S").time() if e["end_time"] else None,
                priority=e["priority"],
            )
            self.db.add(event)
            added += 1

        self.db.commit()

        return {
            "previous_events": current_count,
            "events_applied": added,
        }

    def get_version_events(self, version_id: int) -> List[Dict[str, Any]]:
        """Get all events in a version."""
        version = self.get_version(version_id)
        if not version:
            return []
        return self._deserialize_events(version.snapshot)

    def delete_version(self, version_id: int) -> bool:
        """
        Delete a version (only if DRAFT or REJECTED).
        
        Args:
            version_id: Version to delete
            
        Returns:
            True if deleted
        """
        version = self.get_version(version_id)
        if not version:
            return False

        if version.status not in (VersionStatus.DRAFT, VersionStatus.REJECTED):
            raise ValueError("Can only delete DRAFT or REJECTED versions")

        self.db.delete(version)
        self.db.commit()
        return True


def calculate_version_diff(
    version_a_events: List[Dict],
    version_b_events: List[Dict],
) -> Dict[str, Any]:
    """Utility to calculate diff between two version event lists."""
    # This mirrors the compare_versions logic for standalone use
    pass