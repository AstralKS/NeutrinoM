"""Analysis timeline - tracks phase-level timestamps.

Records when each analysis phase starts, completes, or fails,
enabling users to see progress, identify bottlenecks, and debug errors.
"""

from dataclasses import dataclass, field
from datetime import UTC, datetime
from typing import Any


@dataclass
class PhaseTimestamp:
    """Timestamp for a single analysis phase."""

    phase: str
    started_at: datetime | None = None
    completed_at: datetime | None = None
    error: str | None = None
    status: str = "pending"  # pending, running, completed, failed
    api_calls: list[dict[str, Any]] = field(default_factory=list)

    @property
    def duration_seconds(self) -> float | None:
        """Duration in seconds, or None if not complete."""
        if self.started_at and self.completed_at:
            return round(
                (self.completed_at - self.started_at).total_seconds(), 2
            )
        return None

    def to_dict(self) -> dict[str, Any]:
        """Convert to serializable dict."""
        result: dict[str, Any] = {
            "phase": self.phase,
            "status": self.status,
            "started_at": self.started_at.isoformat() if self.started_at else None,
            "completed_at": self.completed_at.isoformat() if self.completed_at else None,
            "duration_seconds": self.duration_seconds,
        }
        if self.error:
            result["error"] = self.error
        if self.api_calls:
            result["api_calls"] = self.api_calls
        return result


@dataclass
class AnalysisTimeline:
    """Tracks timestamps across the full analysis pipeline.

    Every phase from start to finish is recorded with:
    - Start time, end time, duration
    - Status (running / completed / failed)
    - Error message if the phase failed
    - Per-API-call timing within each phase
    """

    phases: dict[str, PhaseTimestamp] = field(default_factory=dict)
    analysis_started_at: datetime | None = None

    def start_phase(self, phase_name: str) -> None:
        """Mark a phase as started."""
        self.phases[phase_name] = PhaseTimestamp(
            phase=phase_name,
            started_at=datetime.now(UTC),
            status="running",
        )
        if phase_name == "analysis_start":
            self.analysis_started_at = self.phases[phase_name].started_at

    def complete_phase(self, phase_name: str) -> None:
        """Mark a phase as successfully completed."""
        if phase_name in self.phases:
            self.phases[phase_name].completed_at = datetime.now(UTC)
            self.phases[phase_name].status = "completed"

    def fail_phase(self, phase_name: str, error: str) -> None:
        """Mark a phase as failed with error details."""
        if phase_name in self.phases:
            self.phases[phase_name].completed_at = datetime.now(UTC)
            self.phases[phase_name].status = "failed"
            self.phases[phase_name].error = error
        else:
            # Phase was never started — record it anyway
            self.phases[phase_name] = PhaseTimestamp(
                phase=phase_name,
                started_at=datetime.now(UTC),
                completed_at=datetime.now(UTC),
                status="failed",
                error=error,
            )

    def add_api_call(
        self,
        phase_name: str,
        call_name: str,
        duration_ms: int,
    ) -> None:
        """Record a per-API-call timing entry within a phase."""
        if phase_name not in self.phases:
            return
        self.phases[phase_name].api_calls.append({
            "name": call_name,
            "duration_ms": duration_ms,
            "timestamp": datetime.now(UTC).isoformat(),
        })

    @property
    def total_duration_seconds(self) -> float | None:
        """Total duration from analysis start to last completion."""
        if not self.analysis_started_at:
            return None
        last_completed = max(
            (p.completed_at for p in self.phases.values() if p.completed_at),
            default=None,
        )
        if last_completed:
            return round(
                (last_completed - self.analysis_started_at).total_seconds(), 2
            )
        return None

    @property
    def failed_phases(self) -> list[str]:
        """List of phase names that failed."""
        return [
            name for name, p in self.phases.items() if p.status == "failed"
        ]

    def to_dict(self) -> dict[str, Any]:
        """Convert full timeline to serializable dict."""
        return {
            "total_duration_seconds": self.total_duration_seconds,
            "failed_phases": self.failed_phases,
            "phases": {
                name: phase.to_dict()
                for name, phase in self.phases.items()
            },
        }
