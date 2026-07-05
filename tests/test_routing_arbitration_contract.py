import pytest
from datetime import datetime, timezone
from pydantic import ValidationError
from models.routing_arbitration_contract import (
    RouteTargetType, RoutingStrategy, ArbitrationPolicy,
    RoutingDecisionStatus, RoutingOutcome,
    RoutingInputRecord, RouteCandidate, RouteScoreRecord,
    RoutingConstraintSet, RoutingDecisionRecord, ArbitrationRecord,
    RoutingFallbackRecord, RoutingEnvelope,
)


NOW = datetime.now(timezone.utc)


def make_input(**overrides) -> RoutingInputRecord:
    defaults = dict(routing_id="rt-001", request_summary="Implement user auth",
                    task_type="coding", risk_level="low")
    defaults.update(overrides)
    return RoutingInputRecord(**defaults)


def make_candidate(**overrides) -> RouteCandidate:
    defaults = dict(candidate_id="c-001", target_type=RouteTargetType.DIRECT_EXECUTOR,
                    target_id="agent-main-001", target_role="primary",
                    capability_tags=["python", "auth"], supports_verification=True)
    defaults.update(overrides)
    return RouteCandidate(**defaults)


def make_score(**overrides) -> RouteScoreRecord:
    defaults = dict(score_id="sc-001", candidate_id="c-001",
                    strategy=RoutingStrategy.RULE_BASED,
                    overall_score=0.9, threshold_passed=True)
    defaults.update(overrides)
    return RouteScoreRecord(**defaults)


def make_constraints(**overrides) -> RoutingConstraintSet:
    defaults = dict(constraint_id="cst-rt-001")
    defaults.update(overrides)
    return RoutingConstraintSet(**defaults)


def make_decision(**overrides) -> RoutingDecisionRecord:
    defaults = dict(decision_id="dec-001", routing_id="rt-001",
                    strategy_used=RoutingStrategy.RULE_BASED,
                    decision_status=RoutingDecisionStatus.SELECTED,
                    selected_candidate_id="c-001",
                    selected_target_type=RouteTargetType.DIRECT_EXECUTOR,
                    selected_target_id="agent-main-001",
                    decision_reason="Rule match for auth tasks",
                    confidence=0.9)
    defaults.update(overrides)
    return RoutingDecisionRecord(**defaults)


def make_arbitration(**overrides) -> ArbitrationRecord:
    defaults = dict(arbitration_id="arb-001", routing_id="rt-001",
                    policy=ArbitrationPolicy.HIGHEST_SCORE,
                    competing_candidate_ids=["c-001", "c-002"],
                    selected_candidate_id="c-001",
                    tie_break_reason="Higher capability_score")
    defaults.update(overrides)
    return ArbitrationRecord(**defaults)


def make_fallback(**overrides) -> RoutingFallbackRecord:
    defaults = dict(fallback_id="fb-001", routing_id="rt-001",
                    trigger_reason="Primary candidate unavailable",
                    fallback_candidate_id="c-002",
                    fallback_target_type=RouteTargetType.FALLBACK_PATH)
    defaults.update(overrides)
    return RoutingFallbackRecord(**defaults)


def make_envelope(**overrides) -> RoutingEnvelope:
    defaults = dict(envelope_id="env-rt-001",
                    routing_input=make_input(),
                    candidates=[make_candidate()],
                    scores=[make_score()],
                    constraints=make_constraints())
    defaults.update(overrides)
    return RoutingEnvelope(**defaults)


class TestEnums:
    def test_route_target_type(self):
        assert RouteTargetType.DIRECT_EXECUTOR.value == "direct_executor"
        assert RouteTargetType.BLOCKED.value == "blocked"
        assert len(RouteTargetType) == 8

    def test_routing_strategy(self):
        assert RoutingStrategy.RULE_BASED.value == "rule_based"
        assert RoutingStrategy.FALLBACK_ONLY.value == "fallback_only"
        assert len(RoutingStrategy) == 5

    def test_arbitration_policy(self):
        assert ArbitrationPolicy.HIGHEST_SCORE.value == "highest_score"
        assert ArbitrationPolicy.HUMAN_OVERRIDE.value == "human_override"
        assert len(ArbitrationPolicy) == 6

    def test_routing_decision_status(self):
        assert RoutingDecisionStatus.EVALUATED.value == "evaluated"
        assert RoutingDecisionStatus.BLOCKED.value == "blocked"
        assert len(RoutingDecisionStatus) == 7

    def test_routing_outcome(self):
        assert RoutingOutcome.FALLBACK_USED.value == "fallback_used"
        assert RoutingOutcome.MANUAL_INTERVENTION_REQUIRED.value == "manual_intervention_required"
        assert len(RoutingOutcome) == 6


class TestRoutingInputRecord:
    def test_valid(self):
        r = make_input()
        assert r.routing_id == "rt-001"

    def test_blank_routing_id_raises(self):
        with pytest.raises(ValidationError):
            make_input(routing_id="")

    def test_blank_request_summary_raises(self):
        with pytest.raises(ValidationError):
            make_input(request_summary="")

    def test_risk_level_default(self):
        r = make_input()
        assert r.risk_level == "low"

    def test_high_risk(self):
        r = make_input(risk_level="high", requires_verification=True)
        assert r.risk_level == "high"

    def test_with_refs(self):
        r = make_input(input_refs=["spec/auth.md", "state/current"])
        assert len(r.input_refs) == 2


class TestRouteCandidate:
    def test_valid(self):
        c = make_candidate()
        assert c.candidate_id == "c-001"

    def test_blank_candidate_id_raises(self):
        with pytest.raises(ValidationError):
            make_candidate(candidate_id="")

    def test_blank_target_id_raises(self):
        with pytest.raises(ValidationError):
            make_candidate(target_id="")

    def test_specialist_agent(self):
        c = make_candidate(target_type=RouteTargetType.SPECIALIST_AGENT,
                           target_id="agent-spec-001")
        assert c.target_type == RouteTargetType.SPECIALIST_AGENT

    def test_verifier_agent(self):
        c = make_candidate(target_type=RouteTargetType.VERIFIER_AGENT)
        assert c.target_type == RouteTargetType.VERIFIER_AGENT

    def test_approval_gate(self):
        c = make_candidate(target_type=RouteTargetType.HUMAN_APPROVAL_GATE,
                           requires_approval=True)
        assert c.requires_approval is True

    def test_availability(self):
        c = make_candidate(availability_status="busy")
        assert c.availability_status == "busy"

    def test_capability_tags(self):
        c = make_candidate(capability_tags=["python", "django", "auth"])
        assert len(c.capability_tags) == 3


class TestRouteScoreRecord:
    def test_valid(self):
        s = make_score()
        assert s.score_id == "sc-001"

    def test_blank_score_id_raises(self):
        with pytest.raises(ValidationError):
            make_score(score_id="")

    def test_score_range_low_raises(self):
        with pytest.raises(ValidationError, match="score must be between"):
            make_score(overall_score=-0.1)

    def test_score_range_high_raises(self):
        with pytest.raises(ValidationError, match="score must be between"):
            make_score(overall_score=1.5)

    def test_policy_score_valid(self):
        s = make_score(policy_score=0.75)
        assert s.policy_score == 0.75

    def test_threshold_failed(self):
        s = make_score(threshold_passed=False, overall_score=0.3)
        assert s.threshold_passed is False


class TestRoutingConstraintSet:
    def test_valid(self):
        c = make_constraints()
        assert c.constraint_id == "cst-rt-001"

    def test_blank_id_raises(self):
        with pytest.raises(ValidationError):
            make_constraints(constraint_id="")

    def test_allowed_target_types(self):
        types = [RouteTargetType.DIRECT_EXECUTOR, RouteTargetType.SPECIALIST_AGENT]
        c = make_constraints(allowed_target_types=types)
        assert len(c.allowed_target_types) == 2

    def test_disallowed_ids(self):
        c = make_constraints(disallowed_target_ids=["agent-untrusted-001"])
        assert c.disallowed_target_ids[0] == "agent-untrusted-001"

    def test_must_verify(self):
        c = make_constraints(must_verify=True)
        assert c.must_verify is True

    def test_must_use_specialist(self):
        c = make_constraints(must_use_specialist=True)
        assert c.must_use_specialist is True


class TestRoutingDecisionRecord:
    def test_valid(self):
        d = make_decision()
        assert d.decision_id == "dec-001"

    def test_blank_decision_id_raises(self):
        with pytest.raises(ValidationError):
            make_decision(decision_id="")

    def test_selected_needs_candidate_id(self):
        with pytest.raises(ValidationError, match="SELECTED/DISPATCHED status requires a selected_candidate_id"):
            make_decision(decision_status=RoutingDecisionStatus.SELECTED,
                          selected_candidate_id=None)

    def test_drafted_not_require_candidate(self):
        d = make_decision(decision_status=RoutingDecisionStatus.DRAFT,
                          selected_candidate_id=None)
        assert d.decision_status == RoutingDecisionStatus.DRAFT

    def test_blocked_needs_reason(self):
        with pytest.raises(ValidationError, match="BLOCKED/REJECTED status requires decision_reason"):
            make_decision(decision_status=RoutingDecisionStatus.BLOCKED,
                          decision_reason="", selected_candidate_id=None)

    def test_blocked_with_reason_valid(self):
        d = make_decision(decision_status=RoutingDecisionStatus.BLOCKED,
                          decision_reason="No eligible route available",
                          selected_candidate_id=None)
        assert d.decision_reason == "No eligible route available"

    def test_rejected_needs_reason(self):
        with pytest.raises(ValidationError, match="BLOCKED/REJECTED status requires decision_reason"):
            make_decision(decision_status=RoutingDecisionStatus.REJECTED,
                          decision_reason="", selected_candidate_id=None)

    def test_confidence_range_raises(self):
        with pytest.raises(ValidationError, match="confidence must be between"):
            make_decision(confidence=1.5)

    def test_confidence_valid(self):
        d = make_decision(confidence=0.85)
        assert d.confidence == 0.85

    def test_with_dispatch_time(self):
        d = make_decision(decision_status=RoutingDecisionStatus.DISPATCHED,
                          dispatched_at=NOW)
        assert d.dispatched_at is not None


class TestArbitrationRecord:
    def test_valid(self):
        a = make_arbitration()
        assert a.arbitration_id == "arb-001"

    def test_blank_id_raises(self):
        with pytest.raises(ValidationError):
            make_arbitration(arbitration_id="")

    def test_less_than_two_candidates_raises(self):
        with pytest.raises(ValidationError, match="arbitration requires at least 2 competing candidates"):
            make_arbitration(competing_candidate_ids=["c-001"])

    def test_two_candidates_valid(self):
        a = make_arbitration(competing_candidate_ids=["c-001", "c-002"])
        assert len(a.competing_candidate_ids) == 2

    def test_selection_needs_tie_break_reason(self):
        with pytest.raises(ValidationError, match="arbitration with selection requires tie_break_reason"):
            make_arbitration(selected_candidate_id="c-001", tie_break_reason="")

    def test_selection_with_reason_valid(self):
        a = make_arbitration(selected_candidate_id="c-001",
                             tie_break_reason="Higher overall_score")
        assert a.tie_break_reason == "Higher overall_score"

    def test_review_required(self):
        a = make_arbitration(review_required=True, review_notes="Check tie-break")
        assert a.review_required is True

    def test_human_override_policy(self):
        a = make_arbitration(policy=ArbitrationPolicy.HUMAN_OVERRIDE)
        assert a.policy == ArbitrationPolicy.HUMAN_OVERRIDE


class TestRoutingFallbackRecord:
    def test_valid(self):
        f = make_fallback()
        assert f.fallback_id == "fb-001"

    def test_blank_fallback_id_raises(self):
        with pytest.raises(ValidationError):
            make_fallback(fallback_id="")

    def test_blank_trigger_reason_raises(self):
        with pytest.raises(ValidationError):
            make_fallback(trigger_reason="")

    def test_manual_intervention(self):
        f = make_fallback(manual_intervention_required=True)
        assert f.manual_intervention_required is True

    def test_blocked_fallback(self):
        f = make_fallback(fallback_target_type=RouteTargetType.BLOCKED,
                          trigger_reason="No fallback available",
                          manual_intervention_required=True)
        assert f.fallback_target_type == RouteTargetType.BLOCKED


class TestRoutingEnvelope:
    def test_valid(self):
        e = make_envelope()
        assert e.envelope_id == "env-rt-001"

    def test_blank_envelope_id_raises(self):
        with pytest.raises(ValidationError):
            make_envelope(envelope_id="")

    def test_no_candidates_raises(self):
        with pytest.raises(ValidationError, match="at least one RouteCandidate is required"):
            make_envelope(candidates=[])

    def test_no_candidates_with_blocked_valid(self):
        e = make_envelope(
            candidates=[],
            decision=make_decision(decision_status=RoutingDecisionStatus.BLOCKED,
                                   selected_candidate_id=None,
                                   decision_reason="All candidates unavailable"),
        )
        assert e.decision.decision_status == RoutingDecisionStatus.BLOCKED

    def test_selected_candidate_must_exist(self):
        with pytest.raises(ValidationError, match="selected_candidate_id must reference an existing candidate"):
            make_envelope(decision=make_decision(selected_candidate_id="c-999"))

    def test_selected_candidate_exists_valid(self):
        e = make_envelope(
            candidates=[make_candidate(candidate_id="c-001"),
                        make_candidate(candidate_id="c-002", target_id="agent-other")],
            scores=[make_score(candidate_id="c-001"),
                    make_score(score_id="sc-002", candidate_id="c-002")],
            decision=make_decision(selected_candidate_id="c-002",
                                   selected_target_id="agent-other"),
        )
        assert e.decision.selected_candidate_id == "c-002"

    def test_fallback_without_decision_raises(self):
        with pytest.raises(ValidationError, match="fallback requires a RoutingDecisionRecord"):
            make_envelope(fallback=make_fallback())

    def test_fallback_with_decision_valid(self):
        e = make_envelope(decision=make_decision(),
                          fallback=make_fallback())
        assert e.fallback.trigger_reason == "Primary candidate unavailable"


class TestSerialization:
    def test_input_to_dict_and_back(self):
        r = make_input()
        data = r.model_dump()
        restored = RoutingInputRecord(**data)
        assert restored.routing_id == r.routing_id

    def test_envelope_to_dict_and_back(self):
        e = make_envelope()
        data = e.model_dump()
        restored = RoutingEnvelope(**data)
        assert restored.envelope_id == e.envelope_id

    def test_full_envelope_roundtrip(self):
        e = make_envelope(
            candidates=[make_candidate(candidate_id="c-001"),
                        make_candidate(candidate_id="c-002", target_id="agent-spec")],
            scores=[make_score(candidate_id="c-001"),
                    make_score(score_id="sc-002", candidate_id="c-002")],
            decision=make_decision(selected_candidate_id="c-002",
                                   selected_target_id="agent-spec"),
            arbitration=make_arbitration(competing_candidate_ids=["c-001", "c-002"]),
        )
        data = e.model_dump()
        restored = RoutingEnvelope(**data)
        assert restored.decision.decision_id == "dec-001"
        assert restored.arbitration.arbitration_id == "arb-001"


class TestIntegration:
    def test_direct_execution_rule_based(self):
        inp = RoutingInputRecord(routing_id="rt-int-001", run_id="run-001",
                                 step_id="step-003", task_id="task-auth-001",
                                 request_summary="Add login endpoint",
                                 task_type="coding", risk_level="low")
        c1 = RouteCandidate(candidate_id="c-int-001",
                            target_type=RouteTargetType.DIRECT_EXECUTOR,
                            target_id="agent-main-001",
                            capability_tags=["python", "auth"],
                            supports_verification=True)
        sc1 = RouteScoreRecord(score_id="sc-int-001", candidate_id="c-int-001",
                               strategy=RoutingStrategy.RULE_BASED,
                               capability_score=1.0, policy_score=1.0,
                               overall_score=1.0)
        cst = RoutingConstraintSet(constraint_id="cst-int-001",
                                    allowed_target_types=[RouteTargetType.DIRECT_EXECUTOR])
        dec = RoutingDecisionRecord(decision_id="dec-int-001", routing_id="rt-int-001",
                                    selected_candidate_id="c-int-001",
                                    selected_target_type=RouteTargetType.DIRECT_EXECUTOR,
                                    selected_target_id="agent-main-001",
                                    strategy_used=RoutingStrategy.RULE_BASED,
                                    decision_status=RoutingDecisionStatus.DISPATCHED,
                                    decision_reason="Rule match for coding tasks",
                                    dispatched_at=NOW)
        env = RoutingEnvelope(envelope_id="env-rt-int-001", routing_input=inp,
                              candidates=[c1], scores=[sc1], constraints=cst,
                              decision=dec)
        assert env.decision.selected_target_type == RouteTargetType.DIRECT_EXECUTOR
        assert env.decision.strategy_used == RoutingStrategy.RULE_BASED

    def test_specialist_route_after_score_comparison(self):
        inp = make_input(routing_id="rt-int-002", request_summary="Optimize DB queries",
                         task_type="database", risk_level="medium",
                         requires_specialization=True)
        c1 = make_candidate(candidate_id="c-int-002a",
                            target_type=RouteTargetType.DIRECT_EXECUTOR,
                            target_id="agent-main-001", risk_fit="medium",
                            supports_verification=False)
        c2 = make_candidate(candidate_id="c-int-002b",
                            target_type=RouteTargetType.SPECIALIST_AGENT,
                            target_id="agent-db-001", target_role="db_specialist",
                            capability_tags=["postgres", "query_optimization"],
                            risk_fit="high")
        sc1 = RouteScoreRecord(score_id="sc-int-002a", candidate_id="c-int-002a",
                               capability_score=0.5, policy_score=0.8,
                               overall_score=0.6)
        sc2 = RouteScoreRecord(score_id="sc-int-002b", candidate_id="c-int-002b",
                               capability_score=1.0, policy_score=1.0,
                               overall_score=0.95)
        cst = make_constraints(constraint_id="cst-int-002", must_use_specialist=True)
        arb = ArbitrationRecord(arbitration_id="arb-int-002", routing_id="rt-int-002",
                                policy=ArbitrationPolicy.HIGHEST_SCORE,
                                competing_candidate_ids=["c-int-002a", "c-int-002b"],
                                selected_candidate_id="c-int-002b",
                                tie_break_reason="Specialist has higher capability and risk fit")
        dec = RoutingDecisionRecord(decision_id="dec-int-002", routing_id="rt-int-002",
                                    selected_candidate_id="c-int-002b",
                                    selected_target_type=RouteTargetType.SPECIALIST_AGENT,
                                    selected_target_id="agent-db-001",
                                    strategy_used=RoutingStrategy.HYBRID,
                                    decision_status=RoutingDecisionStatus.DISPATCHED,
                                    decision_reason="Specialist best match for DB optimization",
                                    confidence=0.95)
        env = RoutingEnvelope(envelope_id="env-rt-int-002", routing_input=inp,
                              candidates=[c1, c2],
                              scores=[sc1, sc2], constraints=cst,
                              decision=dec, arbitration=arb)
        assert env.decision.selected_target_type == RouteTargetType.SPECIALIST_AGENT
        assert env.arbitration.selected_candidate_id == "c-int-002b"

    def test_verifier_first_for_high_risk(self):
        inp = make_input(routing_id="rt-int-003", request_summary="Audit security config",
                         task_type="security", risk_level="high",
                         requires_verification=True)
        c1 = make_candidate(candidate_id="c-int-003a",
                            target_type=RouteTargetType.DIRECT_EXECUTOR,
                            target_id="agent-main-001",
                            supports_verification=False)
        c2 = make_candidate(candidate_id="c-int-003b",
                            target_type=RouteTargetType.VERIFIER_AGENT,
                            target_id="agent-verifier-001",
                            target_role="security_verifier",
                            capability_tags=["security_audit", "static_analysis"],
                            supports_verification=True, risk_fit="high")
        sc1 = RouteScoreRecord(score_id="sc-int-003a", candidate_id="c-int-003a",
                               capability_score=0.4, risk_score=0.3,
                               overall_score=0.35, threshold_passed=False)
        sc2 = RouteScoreRecord(score_id="sc-int-003b", candidate_id="c-int-003b",
                               capability_score=1.0, risk_score=1.0,
                               overall_score=0.95)
        cst = make_constraints(constraint_id="cst-int-003", must_verify=True)
        dec = RoutingDecisionRecord(decision_id="dec-int-003", routing_id="rt-int-003",
                                    selected_candidate_id="c-int-003b",
                                    selected_target_type=RouteTargetType.VERIFIER_AGENT,
                                    selected_target_id="agent-verifier-001",
                                    strategy_used=RoutingStrategy.RULE_BASED,
                                    decision_status=RoutingDecisionStatus.DISPATCHED,
                                    decision_reason="High-risk task routed to verifier",
                                    confidence=0.9)
        env = RoutingEnvelope(envelope_id="env-rt-int-003", routing_input=inp,
                              candidates=[c1, c2], scores=[sc1, sc2],
                              constraints=cst, decision=dec)
        assert env.routing_input.risk_level == "high"
        assert env.decision.selected_target_type == RouteTargetType.VERIFIER_AGENT

    def test_blocked_route_due_to_policy(self):
        inp = make_input(routing_id="rt-int-004", request_summary="Delete production data",
                         task_type="admin", risk_level="high")
        c1 = make_candidate(candidate_id="c-int-004",
                            target_type=RouteTargetType.DIRECT_EXECUTOR,
                            target_id="agent-main-001",
                            capability_tags=["admin"])
        cst = RoutingConstraintSet(constraint_id="cst-int-004",
                                    disallowed_target_ids=["agent-main-001"],
                                    must_require_approval_for_sensitive=True)
        dec = RoutingDecisionRecord(decision_id="dec-int-004", routing_id="rt-int-004",
                                    selected_candidate_id=None,
                                    strategy_used=RoutingStrategy.RULE_BASED,
                                    decision_status=RoutingDecisionStatus.BLOCKED,
                                    decision_reason="No eligible route: target disallowed and sensitive operation requires approval gate",
                                    confidence=0.0)
        env = RoutingEnvelope(envelope_id="env-rt-int-004", routing_input=inp,
                              candidates=[c1], constraints=cst, decision=dec)
        assert env.decision.decision_status == RoutingDecisionStatus.BLOCKED
        assert "No eligible route" in env.decision.decision_reason

    def test_fallback_route_after_primary_rejection(self):
        inp = make_input(routing_id="rt-int-005", request_summary="Generate monthly report",
                         task_type="reporting", risk_level="low")
        c1 = make_candidate(candidate_id="c-int-005a",
                            target_type=RouteTargetType.DIRECT_EXECUTOR,
                            target_id="agent-main-001",
                            availability_status="busy")
        c2 = make_candidate(candidate_id="c-int-005b",
                            target_type=RouteTargetType.FALLBACK_PATH,
                            target_id="agent-fallback-001",
                            capability_tags=["reporting"])
        sc1 = RouteScoreRecord(score_id="sc-int-005a", candidate_id="c-int-005a",
                               overall_score=0.9, threshold_passed=True)
        sc2 = RouteScoreRecord(score_id="sc-int-005b", candidate_id="c-int-005b",
                               overall_score=0.7, threshold_passed=True)
        cst = make_constraints(constraint_id="cst-int-005", fallback_required=True)
        dec = RoutingDecisionRecord(decision_id="dec-int-005", routing_id="rt-int-005",
                                    selected_candidate_id="c-int-005b",
                                    selected_target_type=RouteTargetType.FALLBACK_PATH,
                                    selected_target_id="agent-fallback-001",
                                    strategy_used=RoutingStrategy.HYBRID,
                                    decision_status=RoutingDecisionStatus.DISPATCHED,
                                    decision_reason="Primary busy, fallback selected",
                                    confidence=0.7)
        fb = RoutingFallbackRecord(fallback_id="fb-int-005", routing_id="rt-int-005",
                                    trigger_reason="Primary candidate agent-main-001 busy",
                                    fallback_candidate_id="c-int-005b",
                                    fallback_target_type=RouteTargetType.FALLBACK_PATH)
        env = RoutingEnvelope(envelope_id="env-rt-int-005", routing_input=inp,
                              candidates=[c1, c2], scores=[sc1, sc2],
                              constraints=cst, decision=dec, fallback=fb)
        assert env.fallback.trigger_reason == "Primary candidate agent-main-001 busy"
        assert env.decision.selected_target_type == RouteTargetType.FALLBACK_PATH
