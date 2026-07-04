from datetime import datetime, timezone
from typing import Dict, List, Optional
from pydantic import BaseModel, Field

from models.orchestration_state_machine import (
    OrchestrationStateMachine, RunState, RunEvent, default_machine,
)


class TransitionRecord(BaseModel):
    from_state: RunState
    event: RunEvent
    to_state: RunState
    timestamp: str
    guard_results: Dict[str, bool] = Field(default_factory=dict)
    decision: str = ""


class StateDriver(BaseModel):
    machine: OrchestrationStateMachine = Field(default_factory=lambda: default_machine())
    current_state_id: RunState = RunState.CREATED
    history: List[TransitionRecord] = Field(default_factory=list)

    @property
    def is_terminal(self) -> bool:
        return self.current_state_id in set(self.machine.terminal_states)

    def available_events(self) -> List[RunEvent]:
        if self.is_terminal:
            return []
        return [
            t.event for t in self.machine.transitions
            if t.from_state == self.current_state_id
        ]

    def trigger(self, event: RunEvent, guard_results: Optional[Dict[str, bool]] = None) -> RunState:
        if self.is_terminal:
            raise ValueError(f"cannot trigger event {event.value}: machine is in terminal state {self.current_state_id.value}")

        matches = [
            t for t in self.machine.transitions
            if t.from_state == self.current_state_id and t.event == event
        ]
        if not matches:
            available = [e.value for e in self.available_events()]
            raise ValueError(f"no transition from {self.current_state_id.value} for event {event.value}; available events: {available}")

        transition = matches[0]
        resolved = guard_results or {}
        for g in transition.guards:
            if g.name in resolved and not resolved[g.name]:
                record = TransitionRecord(
                    from_state=self.current_state_id,
                    event=event,
                    to_state=self.current_state_id,
                    timestamp=datetime.now(timezone.utc).isoformat(),
                    guard_results={g.name: False},
                    decision=f"blocked by guard: {g.name}",
                )
                self.history.append(record)
                raise ValueError(f"guard '{g.name}' rejected transition {self.current_state_id.value} -> {transition.to_state.value} via {event.value}")

        record = TransitionRecord(
            from_state=self.current_state_id,
            event=event,
            to_state=transition.to_state,
            timestamp=datetime.now(timezone.utc).isoformat(),
            guard_results=resolved,
            decision="allowed",
        )
        self.history.append(record)
        self.current_state_id = transition.to_state
        return self.current_state_id
