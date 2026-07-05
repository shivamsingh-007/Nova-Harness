import pytest
from datetime import datetime, timedelta
from models.capability_negotiation_contract import (
    CapabilityCategory, CompatibilityStatus, NegotiationMode,
    RequirementLevel, NegotiationDisposition,
    CapabilityDeclaration, CapabilityRequirementRecord,
    CapabilityOfferRecord, CompatibilityEvaluationRecord,
    NegotiatedCapabilitySet, CompatibilityGapRecord,
    NegotiationDecisionRecord, CapabilityNegotiationEnvelope,
)


def make_declaration(**kw):
    return CapabilityDeclaration(
        declaration_id=kw.get("did", "dec-001"),
        party_ref=kw.get("ref", "agent-alpha"),
        party_type=kw.get("ptype", "agent"),
        capability_category=kw.get("cat", CapabilityCategory.tooling),
        notes=kw.get("notes"),
    )


def make_requirement(**kw):
    return CapabilityRequirementRecord(
        requirement_id=kw.get("rid", "req-001"),
        declaration_id=kw.get("did", "dec-001"),
        capability_name=kw.get("name", "http_client"),
        requirement_level=kw.get("level", RequirementLevel.required),
        required_values=kw.get("values", ["rest", "graphql"]),
        minimum_version=kw.get("minv"),
        maximum_version=kw.get("maxv"),
        constraint_notes=kw.get("notes"),
    )


def make_offer(**kw):
    return CapabilityOfferRecord(
        offer_id=kw.get("oid", "off-001"),
        declaration_id=kw.get("did", "dec-002"),
        capability_name=kw.get("name", "http_client"),
        supported_values=kw.get("values", ["rest"]),
        supported_version=kw.get("ver", "2.0"),
        limits=kw.get("limits", []),
        conditions=kw.get("conditions", []),
        notes=kw.get("notes"),
    )


def make_evaluation(**kw):
    return CompatibilityEvaluationRecord(
        evaluation_id=kw.get("eid", "eval-001"),
        request_declaration_id=kw.get("reqd", "dec-001"),
        offer_declaration_id=kw.get("offd", "dec-002"),
        compatibility_status=kw.get("status", CompatibilityStatus.compatible),
        matched_requirement_ids=kw.get("matched", ["req-001"]),
        unmatched_requirement_ids=kw.get("unmatched", []),
        score=kw.get("score", 85.0),
        evaluation_notes=kw.get("notes"),
    )


def make_negotiated_set(**kw):
    return NegotiatedCapabilitySet(
        negotiated_set_id=kw.get("nid", "nset-001"),
        evaluation_id=kw.get("eid", "eval-001"),
        negotiation_mode=kw.get("mode", NegotiationMode.strict_intersection),
        negotiated_capabilities=kw.get("caps", ["http_client"]),
        required_satisfied=kw.get("reqsat", ["req-001"]),
        optional_satisfied=kw.get("optsat", []),
        session_effective_from=kw.get("eff_from"),
        session_effective_until=kw.get("eff_until"),
    )


def make_gap(**kw):
    return CompatibilityGapRecord(
        gap_id=kw.get("gid", "gap-001"),
        evaluation_id=kw.get("eid", "eval-001"),
        capability_name=kw.get("name", "websocket"),
        gap_summary=kw.get("summary", "Not supported by candidate"),
        blocking=kw.get("blocking", False),
        fallback_options=kw.get("fallbacks", ["polling"]),
        resolution_notes=kw.get("notes"),
    )


def make_decision(**kw):
    return NegotiationDecisionRecord(
        decision_id=kw.get("did", "nd-001"),
        evaluation_id=kw.get("eid", "eval-001"),
        negotiated_set_id=kw.get("nset"),
        negotiation_disposition=kw.get("disp", NegotiationDisposition.proceed),
        decision_reason=kw.get("reason"),
        selected_fallbacks=kw.get("fallbacks", []),
        approved_override_ref=kw.get("override"),
    )


def make_envelope(**kw):
    rd = kw.get("reqdec") or make_declaration(did="dec-001", ref="agent-alpha")
    od = kw.get("offdec") or make_declaration(did="dec-002", ref="tool-http", cat=CapabilityCategory.tooling)
    ev = kw.get("eval") or make_evaluation()
    ns = kw.get("nset")
    gaps = kw.get("gaps", [])
    dec = kw.get("decision")
    return CapabilityNegotiationEnvelope(
        envelope_id=kw.get("eid", "env-cap-001"),
        request_declaration=rd,
        offer_declaration=od,
        evaluation=ev,
        negotiated_set=ns,
        gaps=gaps,
        decision=dec,
    )


class TestCapabilityCategory:
    def test_all_values(self):
        assert len(CapabilityCategory) == 8
        assert CapabilityCategory.tooling.value == "tooling"
        assert CapabilityCategory.model_behavior.value == "model_behavior"
        assert CapabilityCategory.skill_support.value == "skill_support"
        assert CapabilityCategory.output_format.value == "output_format"
        assert CapabilityCategory.context_window.value == "context_window"
        assert CapabilityCategory.safety_control.value == "safety_control"
        assert CapabilityCategory.integration.value == "integration"
        assert CapabilityCategory.interaction_mode.value == "interaction_mode"


class TestCompatibilityStatus:
    def test_all_values(self):
        assert len(CompatibilityStatus) == 4
        assert CompatibilityStatus.compatible.value == "compatible"
        assert CompatibilityStatus.partially_compatible.value == "partially_compatible"
        assert CompatibilityStatus.incompatible.value == "incompatible"
        assert CompatibilityStatus.unknown.value == "unknown"


class TestNegotiationMode:
    def test_all_values(self):
        assert len(NegotiationMode) == 4
        assert NegotiationMode.strict_intersection.value == "strict_intersection"
        assert NegotiationMode.best_effort.value == "best_effort"
        assert NegotiationMode.required_only.value == "required_only"
        assert NegotiationMode.manual_override.value == "manual_override"


class TestRequirementLevel:
    def test_all_values(self):
        assert len(RequirementLevel) == 3
        assert RequirementLevel.required.value == "required"
        assert RequirementLevel.preferred.value == "preferred"
        assert RequirementLevel.optional.value == "optional"


class TestNegotiationDisposition:
    def test_all_values(self):
        assert len(NegotiationDisposition) == 5
        assert NegotiationDisposition.proceed.value == "proceed"
        assert NegotiationDisposition.proceed_with_fallbacks.value == "proceed_with_fallbacks"
        assert NegotiationDisposition.reroute.value == "reroute"
        assert NegotiationDisposition.reject.value == "reject"
        assert NegotiationDisposition.escalate.value == "escalate"


class TestCapabilityDeclaration:
    def test_valid(self):
        d = make_declaration()
        assert d.declaration_id == "dec-001"

    def test_blank_id_raises(self):
        with pytest.raises(ValueError):
            make_declaration(did="   ")

    def test_blank_party_ref_raises(self):
        with pytest.raises(ValueError):
            make_declaration(ref="   ")


class TestCapabilityRequirementRecord:
    def test_valid(self):
        r = make_requirement()
        assert r.requirement_id == "req-001"

    def test_blank_id_raises(self):
        with pytest.raises(ValueError):
            make_requirement(rid="   ")

    def test_blank_declaration_id_raises(self):
        with pytest.raises(ValueError):
            make_requirement(did="   ")

    def test_blank_capability_name_raises(self):
        with pytest.raises(ValueError):
            make_requirement(name="   ")

    def test_version_constraints_coherent(self):
        with pytest.raises(ValueError):
            make_requirement(minv="3.0", maxv="1.0")

    def test_version_constraints_ok(self):
        r = make_requirement(minv="1.0", maxv="3.0")
        assert r.minimum_version == "1.0"


class TestCapabilityOfferRecord:
    def test_valid(self):
        o = make_offer()
        assert o.offer_id == "off-001"

    def test_blank_id_raises(self):
        with pytest.raises(ValueError):
            make_offer(oid="   ")

    def test_blank_declaration_id_raises(self):
        with pytest.raises(ValueError):
            make_offer(did="   ")

    def test_blank_capability_name_raises(self):
        with pytest.raises(ValueError):
            make_offer(name="   ")


class TestCompatibilityEvaluationRecord:
    def test_valid(self):
        e = make_evaluation()
        assert e.evaluation_id == "eval-001"

    def test_blank_id_raises(self):
        with pytest.raises(ValueError):
            make_evaluation(eid="   ")

    def test_blank_request_declaration_id_raises(self):
        with pytest.raises(ValueError):
            make_evaluation(reqd="   ")

    def test_blank_offer_declaration_id_raises(self):
        with pytest.raises(ValueError):
            make_evaluation(offd="   ")

    def test_compatible_no_unmatched(self):
        with pytest.raises(ValueError):
            make_evaluation(status=CompatibilityStatus.compatible, matched=["req-001"], unmatched=["req-002"])

    def test_compatible_without_unmatched_ok(self):
        e = make_evaluation(status=CompatibilityStatus.compatible, matched=["req-001"], unmatched=[])
        assert e.compatibility_status == CompatibilityStatus.compatible

    def test_incompatible_must_have_unmatched(self):
        with pytest.raises(ValueError):
            make_evaluation(status=CompatibilityStatus.incompatible, matched=[], unmatched=[])

    def test_partial_allows_unmatched(self):
        e = make_evaluation(status=CompatibilityStatus.partially_compatible, matched=["req-001"], unmatched=["req-002"])
        assert e.compatibility_status == CompatibilityStatus.partially_compatible


class TestNegotiatedCapabilitySet:
    def test_valid(self):
        n = make_negotiated_set()
        assert n.negotiated_set_id == "nset-001"

    def test_blank_id_raises(self):
        with pytest.raises(ValueError):
            make_negotiated_set(nid="   ")

    def test_blank_evaluation_id_raises(self):
        with pytest.raises(ValueError):
            make_negotiated_set(eid="   ")


class TestCompatibilityGapRecord:
    def test_valid(self):
        g = make_gap()
        assert g.gap_id == "gap-001"

    def test_blank_id_raises(self):
        with pytest.raises(ValueError):
            make_gap(gid="   ")

    def test_blank_evaluation_id_raises(self):
        with pytest.raises(ValueError):
            make_gap(eid="   ")

    def test_blank_capability_name_raises(self):
        with pytest.raises(ValueError):
            make_gap(name="   ")

    def test_blank_summary_raises(self):
        with pytest.raises(ValueError):
            make_gap(summary="   ")


class TestNegotiationDecisionRecord:
    def test_valid(self):
        d = make_decision()
        assert d.decision_id == "nd-001"

    def test_blank_id_raises(self):
        with pytest.raises(ValueError):
            make_decision(did="   ")

    def test_blank_evaluation_id_raises(self):
        with pytest.raises(ValueError):
            make_decision(eid="   ")

    def test_proceed_with_fallbacks_requires_fallbacks(self):
        with pytest.raises(ValueError):
            make_decision(disp=NegotiationDisposition.proceed_with_fallbacks, fallbacks=[])

    def test_proceed_with_fallbacks_with_fallbacks_ok(self):
        d = make_decision(disp=NegotiationDisposition.proceed_with_fallbacks, fallbacks=["use_polling"], reason="Websocket not supported")
        assert len(d.selected_fallbacks) == 1

    def test_reroute_requires_reason(self):
        with pytest.raises(ValueError):
            make_decision(disp=NegotiationDisposition.reroute, reason=None)

    def test_reject_requires_reason(self):
        with pytest.raises(ValueError):
            make_decision(disp=NegotiationDisposition.reject, reason=None)


class TestCapabilityNegotiationEnvelope:
    def test_valid(self):
        e = make_envelope()
        assert e.envelope_id == "env-cap-001"

    def test_blank_envelope_id_raises(self):
        with pytest.raises(ValueError):
            make_envelope(eid="   ")

    def test_incompatible_no_proceed_without_override(self):
        ev = make_evaluation(status=CompatibilityStatus.incompatible, unmatched=["req-001"])
        dec = make_decision(disp=NegotiationDisposition.proceed, override=None)
        with pytest.raises(ValueError):
            make_envelope(eval=ev, decision=dec)

    def test_incompatible_proceed_with_override_ok(self):
        ev = make_evaluation(status=CompatibilityStatus.incompatible, unmatched=["req-001"])
        dec = make_decision(disp=NegotiationDisposition.proceed, override="override-approval-001", reason="Override for testing")
        e = make_envelope(eval=ev, decision=dec)
        assert e.decision.approved_override_ref == "override-approval-001"

    def test_proceed_with_fallbacks_needs_gaps(self):
        ev = make_evaluation(status=CompatibilityStatus.partially_compatible, matched=["req-001"], unmatched=["req-002"])
        dec = make_decision(disp=NegotiationDisposition.proceed_with_fallbacks, fallbacks=["use_polling"], reason="Websocket missing")
        with pytest.raises(ValueError):
            make_envelope(eval=ev, decision=dec, gaps=[])

    def test_proceed_with_fallbacks_with_gaps_ok(self):
        ev = make_evaluation(status=CompatibilityStatus.partially_compatible, matched=["req-001"], unmatched=["req-002"])
        dec = make_decision(disp=NegotiationDisposition.proceed_with_fallbacks, fallbacks=["use_polling"], reason="Websocket missing")
        g = make_gap()
        e = make_envelope(eval=ev, decision=dec, gaps=[g])
        assert len(e.gaps) == 1


class TestExampleScenarios:
    def test_full_compatibility_between_task_and_role(self):
        rd = CapabilityDeclaration(
            declaration_id="dec-task-001", party_ref="task-analysis",
            party_type="task", capability_category=CapabilityCategory.tooling,
        )
        od = CapabilityDeclaration(
            declaration_id="dec-role-001", party_ref="role-analyst",
            party_type="role", capability_category=CapabilityCategory.tooling,
        )
        ev = CompatibilityEvaluationRecord(
            evaluation_id="eval-full",
            request_declaration_id="dec-task-001",
            offer_declaration_id="dec-role-001",
            compatibility_status=CompatibilityStatus.compatible,
            matched_requirement_ids=["req-analysis-tool"],
            score=100.0,
        )
        ns = NegotiatedCapabilitySet(
            negotiated_set_id="nset-full",
            evaluation_id="eval-full",
            negotiation_mode=NegotiationMode.strict_intersection,
            negotiated_capabilities=["data_analysis", "charting"],
            required_satisfied=["req-analysis-tool"],
        )
        dec = NegotiationDecisionRecord(
            decision_id="nd-full",
            evaluation_id="eval-full",
            negotiated_set_id="nset-full",
            negotiation_disposition=NegotiationDisposition.proceed,
        )
        e = CapabilityNegotiationEnvelope(
            envelope_id="env-full",
            request_declaration=rd,
            offer_declaration=od,
            evaluation=ev,
            negotiated_set=ns,
            decision=dec,
        )
        assert e.evaluation.compatibility_status == CompatibilityStatus.compatible
        assert e.decision.negotiation_disposition == NegotiationDisposition.proceed

    def test_partial_compatibility_with_fallback(self):
        rd = CapabilityDeclaration(
            declaration_id="dec-task-002", party_ref="task-data-pipeline",
            party_type="task", capability_category=CapabilityCategory.output_format,
        )
        od = CapabilityDeclaration(
            declaration_id="dec-tool-002", party_ref="tool-renderer",
            party_type="tool", capability_category=CapabilityCategory.output_format,
        )
        ev = CompatibilityEvaluationRecord(
            evaluation_id="eval-partial",
            request_declaration_id="dec-task-002",
            offer_declaration_id="dec-tool-002",
            compatibility_status=CompatibilityStatus.partially_compatible,
            matched_requirement_ids=["req-csv"],
            unmatched_requirement_ids=["req-html"],
            score=60.0,
        )
        g = CompatibilityGapRecord(
            gap_id="gap-partial",
            evaluation_id="eval-partial",
            capability_name="html_output",
            gap_summary="Tool does not support HTML output",
            blocking=False,
            fallback_options=["csv_only", "markdown"],
        )
        dec = NegotiationDecisionRecord(
            decision_id="nd-partial",
            evaluation_id="eval-partial",
            negotiation_disposition=NegotiationDisposition.proceed_with_fallbacks,
            decision_reason="HTML not supported, falling back to CSV",
            selected_fallbacks=["csv_only"],
        )
        e = CapabilityNegotiationEnvelope(
            envelope_id="env-partial",
            request_declaration=rd,
            offer_declaration=od,
            evaluation=ev,
            gaps=[g],
            decision=dec,
        )
        assert e.evaluation.compatibility_status == CompatibilityStatus.partially_compatible
        assert "csv_only" in e.decision.selected_fallbacks

    def test_incompatible_tool_rejected(self):
        rd = CapabilityDeclaration(
            declaration_id="dec-task-003", party_ref="task-db-migrate",
            party_type="task", capability_category=CapabilityCategory.tooling,
        )
        od = CapabilityDeclaration(
            declaration_id="dec-tool-003", party_ref="tool-legacy",
            party_type="tool", capability_category=CapabilityCategory.tooling,
        )
        ev = CompatibilityEvaluationRecord(
            evaluation_id="eval-incomp",
            request_declaration_id="dec-task-003",
            offer_declaration_id="dec-tool-003",
            compatibility_status=CompatibilityStatus.incompatible,
            unmatched_requirement_ids=["req-transactional"],
            score=0.0,
        )
        g = CompatibilityGapRecord(
            gap_id="gap-incomp",
            evaluation_id="eval-incomp",
            capability_name="transactional_write",
            gap_summary="Legacy tool does not support transactional writes",
            blocking=True,
        )
        dec = NegotiationDecisionRecord(
            decision_id="nd-incomp",
            evaluation_id="eval-incomp",
            negotiation_disposition=NegotiationDisposition.reject,
            decision_reason="Critical capability missing: transactional write",
        )
        e = CapabilityNegotiationEnvelope(
            envelope_id="env-incomp",
            request_declaration=rd,
            offer_declaration=od,
            evaluation=ev,
            gaps=[g],
            decision=dec,
        )
        assert e.evaluation.compatibility_status == CompatibilityStatus.incompatible
        assert e.decision.negotiation_disposition == NegotiationDisposition.reject

    def test_negotiated_session_effective_capability_subset(self):
        rd = CapabilityDeclaration(
            declaration_id="dec-task-004", party_ref="task-multi-skill",
            party_type="task", capability_category=CapabilityCategory.skill_support,
        )
        od = CapabilityDeclaration(
            declaration_id="dec-agent-004", party_ref="agent-generalist",
            party_type="agent", capability_category=CapabilityCategory.skill_support,
        )
        ev = CompatibilityEvaluationRecord(
            evaluation_id="eval-subset",
            request_declaration_id="dec-task-004",
            offer_declaration_id="dec-agent-004",
            compatibility_status=CompatibilityStatus.compatible,
            matched_requirement_ids=["req-search", "req-summarize"],
            score=90.0,
        )
        ns = NegotiatedCapabilitySet(
            negotiated_set_id="nset-subset",
            evaluation_id="eval-subset",
            negotiation_mode=NegotiationMode.required_only,
            negotiated_capabilities=["search", "summarize"],
            required_satisfied=["req-search", "req-summarize"],
            session_effective_from=datetime.now(),
            session_effective_until=datetime.now() + timedelta(hours=1),
        )
        dec = NegotiationDecisionRecord(
            decision_id="nd-subset",
            evaluation_id="eval-subset",
            negotiated_set_id="nset-subset",
            negotiation_disposition=NegotiationDisposition.proceed,
        )
        e = CapabilityNegotiationEnvelope(
            envelope_id="env-subset",
            request_declaration=rd,
            offer_declaration=od,
            evaluation=ev,
            negotiated_set=ns,
            decision=dec,
        )
        assert "search" in e.negotiated_set.negotiated_capabilities
        assert e.negotiated_set.session_effective_until is not None

    def test_manual_override_for_non_blocking_preferred_gap(self):
        rd = CapabilityDeclaration(
            declaration_id="dec-task-005", party_ref="task-optimizer",
            party_type="task", capability_category=CapabilityCategory.model_behavior,
        )
        od = CapabilityDeclaration(
            declaration_id="dec-model-005", party_ref="model-lite",
            party_type="model", capability_category=CapabilityCategory.model_behavior,
        )
        ev = CompatibilityEvaluationRecord(
            evaluation_id="eval-override",
            request_declaration_id="dec-task-005",
            offer_declaration_id="dec-model-005",
            compatibility_status=CompatibilityStatus.partially_compatible,
            matched_requirement_ids=["req-basic-reasoning"],
            unmatched_requirement_ids=["req-advanced-reasoning"],
            score=50.0,
        )
        g = CompatibilityGapRecord(
            gap_id="gap-override",
            evaluation_id="eval-override",
            capability_name="advanced_reasoning",
            gap_summary="Model does not support advanced reasoning chain",
            blocking=False,
            fallback_options=["basic_reasoning", "override_with_monitoring"],
        )
        dec = NegotiationDecisionRecord(
            decision_id="nd-override",
            evaluation_id="eval-override",
            negotiation_disposition=NegotiationDisposition.proceed_with_fallbacks,
            decision_reason="Preferred reasoning gap accepted per manual override",
            selected_fallbacks=["override_with_monitoring"],
            approved_override_ref="override-approval-005",
        )
        e = CapabilityNegotiationEnvelope(
            envelope_id="env-override",
            request_declaration=rd,
            offer_declaration=od,
            evaluation=ev,
            gaps=[g],
            decision=dec,
        )
        assert e.decision.approved_override_ref == "override-approval-005"
        assert "override_with_monitoring" in e.decision.selected_fallbacks
