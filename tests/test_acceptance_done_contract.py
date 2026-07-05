import pytest
from datetime import datetime
from models.acceptance_done_contract import (
    CriterionType, CriterionStatus, DoneCheckType, DoneStatus,
    CompletionDisposition,
    AcceptanceCriterionRecord, AcceptanceCriteriaSet,
    DefinitionOfDoneCheck, DefinitionOfDoneProfile,
    CompletionEvidenceRecord, CompletionAssessmentRecord,
    CompletionDecisionRecord, AcceptanceDoneEnvelope,
)


# ── Helpers ──────────────────────────────────────────────────────────────

def make_criterion(status=CriterionStatus.met, required=True, **kw):
    return AcceptanceCriterionRecord(
        criterion_id=kw.get("cid", "crit-001"),
        task_id=kw.get("tid", "task-001"),
        criterion_type=kw.get("ctype", CriterionType.functional),
        description=kw.get("desc", "The login endpoint must accept valid credentials"),
        priority=kw.get("priority", 0),
        required=required,
        status=status,
        test_method=kw.get("test_method"),
        expected_result=kw.get("expected_result"),
        owner=kw.get("owner"),
        notes=kw.get("notes"),
    )


def make_criteria_set(criteria=None, **kw):
    return AcceptanceCriteriaSet(
        criteria_set_id=kw.get("csid", "cs-001"),
        task_id=kw.get("tid", "task-001"),
        title=kw.get("title", "Criteria set"),
        criteria=criteria or [],
        created_by=kw.get("created_by", "agent-alpha"),
    )


def make_done_check(status=DoneStatus.passed, required=True, **kw):
    return DefinitionOfDoneCheck(
        done_check_id=kw.get("dcid", "dod-check-001"),
        done_check_type=kw.get("dtype", DoneCheckType.quality_gate),
        description=kw.get("desc", "All tests pass"),
        required=required,
        status=status,
        validation_method=kw.get("validation_method"),
        notes=kw.get("notes"),
    )


def make_dod_profile(checks=None, **kw):
    return DefinitionOfDoneProfile(
        dod_profile_id=kw.get("dpid", "dod-profile-001"),
        name=kw.get("name", "Standard Code DoD"),
        description=kw.get("desc", "Standard definition of done for code tasks"),
        checks=checks or [],
        owner=kw.get("owner", "team-lead"),
    )


def make_evidence(**kw):
    return CompletionEvidenceRecord(
        evidence_id=kw.get("eid", "ev-001"),
        task_id=kw.get("tid", "task-001"),
        criterion_or_check_ref=kw.get("ref"),
        evidence_type=kw.get("etype", "test_result"),
        artifact_refs=kw.get("artifacts", []),
        validation_refs=kw.get("validations", []),
        summary=kw.get("summary", "All tests passed"),
    )


def make_assessment(**kw):
    return CompletionAssessmentRecord(
        assessment_id=kw.get("aid", "asm-001"),
        task_id=kw.get("tid", "task-001"),
        criteria_met_count=kw.get("met", 0),
        criteria_failed_count=kw.get("failed", 0),
        dod_passed_count=kw.get("dod_pass", 0),
        dod_failed_count=kw.get("dod_fail", 0),
        waived_items=kw.get("waived", []),
        open_items=kw.get("open", []),
        assessment_summary=kw.get("summary", "All criteria met"),
    )


def make_decision(disposition=CompletionDisposition.accepted, **kw):
    return CompletionDecisionRecord(
        decision_id=kw.get("did", "dec-001"),
        task_id=kw.get("tid", "task-001"),
        completion_disposition=disposition,
        approved_by=kw.get("approver", "verifier-alpha"),
        decision_reason=kw.get("reason", "All criteria and DoD checks met"),
        release_ready=kw.get("release", False),
        followup_actions=kw.get("followup", []),
    )


def make_envelope(**kw):
    criteria = kw.get("criteria", [make_criterion()])
    checks = kw.get("checks", [make_done_check()])
    cs = kw.get("criteria_set") or make_criteria_set(criteria=criteria)
    dod = kw.get("dod_profile") or make_dod_profile(checks=checks)
    assessment = kw.get("assessment") or make_assessment(
        met=sum(1 for c in criteria if c.status == CriterionStatus.met),
        dod_pass=sum(1 for d in checks if d.status == DoneStatus.passed),
    )
    decision = kw.get("decision") or make_decision()
    evidence = kw.get("evidence", [])
    return AcceptanceDoneEnvelope(
        envelope_id=kw.get("eid", "env-completion-001"),
        acceptance_criteria_set=cs,
        definition_of_done_profile=dod,
        evidence_records=evidence,
        assessment=assessment,
        decision=decision,
    )


# ── Tests ────────────────────────────────────────────────────────────────

class TestCriterionType:
    def test_all_values(self):
        assert len(CriterionType) == 6
        assert CriterionType.functional.value == "functional"
        assert CriterionType.output.value == "output"
        assert CriterionType.quality.value == "quality"
        assert CriterionType.constraint.value == "constraint"
        assert CriterionType.approval.value == "approval"
        assert CriterionType.evidence.value == "evidence"


class TestCriterionStatus:
    def test_all_values(self):
        assert len(CriterionStatus) == 5
        assert CriterionStatus.not_started.value == "not_started"
        assert CriterionStatus.in_progress.value == "in_progress"
        assert CriterionStatus.met.value == "met"
        assert CriterionStatus.failed.value == "failed"
        assert CriterionStatus.waived.value == "waived"


class TestDoneCheckType:
    def test_all_values(self):
        assert len(DoneCheckType) == 5
        assert DoneCheckType.quality_gate.value == "quality_gate"
        assert DoneCheckType.verification_gate.value == "verification_gate"
        assert DoneCheckType.documentation_gate.value == "documentation_gate"
        assert DoneCheckType.policy_gate.value == "policy_gate"
        assert DoneCheckType.release_gate.value == "release_gate"


class TestDoneStatus:
    def test_all_values(self):
        assert len(DoneStatus) == 4
        assert DoneStatus.not_checked.value == "not_checked"
        assert DoneStatus.passed.value == "passed"
        assert DoneStatus.failed.value == "failed"
        assert DoneStatus.waived.value == "waived"


class TestCompletionDisposition:
    def test_all_values(self):
        assert len(CompletionDisposition) == 5
        assert CompletionDisposition.accepted.value == "accepted"
        assert CompletionDisposition.accepted_with_caveats.value == "accepted_with_caveats"
        assert CompletionDisposition.needs_rework.value == "needs_rework"
        assert CompletionDisposition.rejected.value == "rejected"
        assert CompletionDisposition.deferred.value == "deferred"


class TestAcceptanceCriterionRecord:
    def test_valid_criterion(self):
        c = make_criterion()
        assert c.criterion_id == "crit-001"
        assert c.status == CriterionStatus.met

    def test_blank_criterion_id_raises(self):
        with pytest.raises(ValueError):
            make_criterion(cid="  ")

    def test_blank_task_id_raises(self):
        with pytest.raises(ValueError):
            make_criterion(tid="  ")

    def test_blank_description_raises(self):
        with pytest.raises(ValueError):
            make_criterion(desc="  ")

    def test_default_status_is_not_started(self):
        c = AcceptanceCriterionRecord(
            criterion_id="crit-002",
            task_id="task-001",
            criterion_type=CriterionType.functional,
            description="Some criterion",
        )
        assert c.status == CriterionStatus.not_started

    def test_priority_default_zero(self):
        c = make_criterion()
        assert c.priority == 0

    def test_negative_priority_raises(self):
        with pytest.raises(ValueError):
            make_criterion(priority=-1)

    def test_all_criterion_types(self):
        for ct in CriterionType:
            c = make_criterion(ctype=ct)
            assert c.criterion_type == ct


class TestAcceptanceCriteriaSet:
    def test_valid_set(self):
        cs = make_criteria_set(criteria=[make_criterion()])
        assert cs.criteria_set_id == "cs-001"

    def test_blank_set_id_raises(self):
        with pytest.raises(ValueError):
            make_criteria_set(csid="  ")

    def test_blank_task_id_raises(self):
        with pytest.raises(ValueError):
            make_criteria_set(tid="  ")

    def test_required_criterion_waived_without_notes_raises(self):
        c = make_criterion(status=CriterionStatus.waived, required=True, notes=None)
        with pytest.raises(ValueError):
            make_criteria_set(criteria=[c])

    def test_required_criterion_waived_with_notes_ok(self):
        c = make_criterion(status=CriterionStatus.waived, required=True, notes="Waived by lead")
        cs = make_criteria_set(criteria=[c])
        assert len(cs.criteria) == 1

    def test_optional_criterion_waived_without_notes_ok(self):
        c = make_criterion(status=CriterionStatus.waived, required=False, notes=None)
        cs = make_criteria_set(criteria=[c])
        assert cs.criteria[0].status == CriterionStatus.waived

    def test_empty_criteria_list_default(self):
        cs = make_criteria_set()
        assert cs.criteria == []

    def test_default_version(self):
        cs = make_criteria_set()
        assert cs.version == "1.0"


class TestDefinitionOfDoneCheck:
    def test_valid_check(self):
        d = make_done_check()
        assert d.done_check_id == "dod-check-001"

    def test_blank_check_id_raises(self):
        with pytest.raises(ValueError):
            make_done_check(dcid="  ")

    def test_blank_description_raises(self):
        with pytest.raises(ValueError):
            make_done_check(desc="  ")

    def test_required_check_waived_without_notes_raises(self):
        with pytest.raises(ValueError):
            make_done_check(status=DoneStatus.waived, required=True, notes=None)

    def test_required_check_waived_with_notes_ok(self):
        d = make_done_check(status=DoneStatus.waived, required=True, notes="Waived for hotfix")
        assert d.notes == "Waived for hotfix"

    def test_optional_check_waived_without_notes_ok(self):
        d = make_done_check(status=DoneStatus.waived, required=False, notes=None)
        assert d.status == DoneStatus.waived

    def test_default_status_not_checked(self):
        d = DefinitionOfDoneCheck(
            done_check_id="dod-check-002",
            done_check_type=DoneCheckType.quality_gate,
            description="Lint check",
        )
        assert d.status == DoneStatus.not_checked

    def test_all_done_check_types(self):
        for dt in DoneCheckType:
            d = make_done_check(dtype=dt)
            assert d.done_check_type == dt


class TestDefinitionOfDoneProfile:
    def test_valid_profile(self):
        p = make_dod_profile(checks=[make_done_check()])
        assert p.dod_profile_id == "dod-profile-001"

    def test_blank_profile_id_raises(self):
        with pytest.raises(ValueError):
            make_dod_profile(dpid="  ")

    def test_blank_name_raises(self):
        with pytest.raises(ValueError):
            make_dod_profile(name="  ")

    def test_active_default_true(self):
        p = make_dod_profile()
        assert p.active is True

    def test_version_default(self):
        p = make_dod_profile()
        assert p.version == "1.0"

    def test_empty_checks_default(self):
        p = make_dod_profile()
        assert p.checks == []


class TestCompletionEvidenceRecord:
    def test_valid_evidence(self):
        ev = make_evidence(ref="crit-001")
        assert ev.evidence_id == "ev-001"

    def test_blank_evidence_id_raises(self):
        with pytest.raises(ValueError):
            make_evidence(eid="  ")

    def test_blank_task_id_raises(self):
        with pytest.raises(ValueError):
            make_evidence(tid="  ")

    def test_blank_evidence_type_raises(self):
        with pytest.raises(ValueError):
            make_evidence(etype="  ")

    def test_blank_summary_raises(self):
        with pytest.raises(ValueError):
            make_evidence(summary="  ")

    def test_ref_is_optional(self):
        ev = make_evidence(ref=None)
        assert ev.criterion_or_check_ref is None

    def test_default_lists_empty(self):
        ev = make_evidence()
        assert ev.artifact_refs == []
        assert ev.validation_refs == []


class TestCompletionAssessmentRecord:
    def test_valid_assessment(self):
        a = make_assessment()
        assert a.assessment_id == "asm-001"

    def test_blank_assessment_id_raises(self):
        with pytest.raises(ValueError):
            make_assessment(aid="  ")

    def test_blank_task_id_raises(self):
        with pytest.raises(ValueError):
            make_assessment(tid="  ")

    def test_counts_default_zero(self):
        a = make_assessment()
        assert a.criteria_met_count == 0

    def test_negative_counts_raises(self):
        with pytest.raises(ValueError):
            make_assessment(met=-1)
        with pytest.raises(ValueError):
            make_assessment(failed=-1)
        with pytest.raises(ValueError):
            make_assessment(dod_pass=-1)
        with pytest.raises(ValueError):
            make_assessment(dod_fail=-1)

    def test_waived_and_open_items_default_empty(self):
        a = make_assessment()
        assert a.waived_items == []
        assert a.open_items == []


class TestCompletionDecisionRecord:
    def test_valid_decision(self):
        d = make_decision()
        assert d.decision_id == "dec-001"

    def test_blank_decision_id_raises(self):
        with pytest.raises(ValueError):
            make_decision(did="  ")

    def test_blank_task_id_raises(self):
        with pytest.raises(ValueError):
            make_decision(tid="  ")

    def test_rejected_needs_reason(self):
        with pytest.raises(ValueError):
            make_decision(
                disposition=CompletionDisposition.rejected,
                reason=None,
            )

    def test_needs_rework_needs_reason(self):
        with pytest.raises(ValueError):
            make_decision(
                disposition=CompletionDisposition.needs_rework,
                reason=None,
            )

    def test_accepted_does_not_require_reason(self):
        d = make_decision(
            disposition=CompletionDisposition.accepted,
            reason=None,
        )
        assert d.completion_disposition == CompletionDisposition.accepted

    def test_accepted_with_caveats_needs_followup_or_reason(self):
        with pytest.raises(ValueError):
            make_decision(
                disposition=CompletionDisposition.accepted_with_caveats,
                followup=[],
                reason=None,
            )

    def test_accepted_with_caveats_and_followup_ok(self):
        d = make_decision(
            disposition=CompletionDisposition.accepted_with_caveats,
            followup=["Document known limitation"],
            reason="Accepted with minor caveats",
        )
        assert d.completion_disposition == CompletionDisposition.accepted_with_caveats

    def test_release_ready_default_false(self):
        d = make_decision()
        assert d.release_ready is False

    def test_followup_default_empty(self):
        d = make_decision()
        assert d.followup_actions == []


class TestAcceptanceDoneEnvelope:
    def test_valid_envelope(self):
        env = make_envelope()
        assert env.envelope_id == "env-completion-001"

    def test_blank_envelope_id_raises(self):
        with pytest.raises(ValueError):
            make_envelope(eid="  ")

    def test_evidence_references_unknown_criterion_raises(self):
        ev = make_evidence(ref="crit-999")
        with pytest.raises(ValueError):
            make_envelope(evidence=[ev])

    def test_evidence_references_unknown_dod_check_raises(self):
        check = make_done_check(dcid="dod-check-001")
        ev = make_evidence(ref="dod-check-999")
        with pytest.raises(ValueError):
            make_envelope(checks=[check], evidence=[ev])

    def test_evidence_references_valid_criterion_ok(self):
        c = make_criterion(cid="crit-001")
        ev = make_evidence(ref="crit-001")
        env = make_envelope(criteria=[c], evidence=[ev])
        assert len(env.evidence_records) == 1

    def test_evidence_references_valid_dod_check_ok(self):
        d = make_done_check(dcid="dod-check-001")
        ev = make_evidence(ref="dod-check-001")
        env = make_envelope(criteria=[], checks=[d], evidence=[ev])
        assert len(env.evidence_records) == 1

    def test_evidence_ref_none_ok(self):
        ev = make_evidence(ref=None)
        env = make_envelope(evidence=[ev])
        assert env.evidence_records[0].criterion_or_check_ref is None

    def test_accepted_with_failed_required_criterion_raises(self):
        c = make_criterion(cid="crit-001", status=CriterionStatus.failed, required=True)
        with pytest.raises(ValueError):
            make_envelope(criteria=[c])

    def test_accepted_with_passed_required_criterion_ok(self):
        c = make_criterion(cid="crit-001", status=CriterionStatus.met, required=True)
        env = make_envelope(criteria=[c])
        assert env.decision.completion_disposition == CompletionDisposition.accepted

    def test_accepted_with_waived_required_criterion_without_notes_raises(self):
        c = make_criterion(cid="crit-001", status=CriterionStatus.waived, required=True, notes=None)
        with pytest.raises(ValueError):
            make_envelope(criteria=[c])

    def test_accepted_with_waived_required_criterion_with_notes_ok(self):
        c = make_criterion(cid="crit-001", status=CriterionStatus.waived, required=True, notes="Waived by lead")
        env = make_envelope(criteria=[c])
        assert env.decision.completion_disposition == CompletionDisposition.accepted

    def test_accepted_with_failed_required_dod_check_raises(self):
        d = make_done_check(dcid="dod-check-001", status=DoneStatus.failed, required=True)
        with pytest.raises(ValueError):
            make_envelope(criteria=[], checks=[d])

    def test_accepted_with_waived_required_dod_no_notes_raises(self):
        d = DefinitionOfDoneCheck.model_construct(
            done_check_id="dod-check-001",
            done_check_type=DoneCheckType.quality_gate,
            description="test",
            required=True,
            status=DoneStatus.waived,
            notes=None,
        )
        with pytest.raises(ValueError):
            make_envelope(criteria=[], checks=[d])

    def test_model_validator_waived_check_without_notes_raises(self):
        with pytest.raises(ValueError):
            make_done_check(status=DoneStatus.waived, required=True, notes=None)

    def test_accepted_with_waived_required_dod_with_notes_ok(self):
        d = make_done_check(dcid="dod-check-001", status=DoneStatus.waived, required=True, notes="Emergency hotfix")
        env = make_envelope(criteria=[], checks=[d])
        assert env.decision.completion_disposition == CompletionDisposition.accepted

    def test_accepted_with_caveats_needs_followup_in_envelope(self):
        with pytest.raises(ValueError):
            make_envelope(
                decision=make_decision(
                    disposition=CompletionDisposition.accepted_with_caveats,
                    followup=[],
                    reason="Minor issues",
                ),
            )

    def test_accepted_with_caveats_and_followup_ok_in_envelope(self):
        env = make_envelope(
            decision=make_decision(
                disposition=CompletionDisposition.accepted_with_caveats,
                followup=["Fix documentation"],
            ),
        )
        assert env.decision.completion_disposition == CompletionDisposition.accepted_with_caveats

    def test_release_ready_with_failed_release_gate_raises(self):
        d = make_done_check(
            dcid="release-gate-001",
            dtype=DoneCheckType.release_gate,
            status=DoneStatus.failed,
            required=True,
        )
        with pytest.raises(ValueError):
            make_envelope(
                criteria=[make_criterion(cid="crit-001")],
                checks=[d],
                decision=make_decision(release=True),
            )

    def test_release_ready_with_passed_release_gate_ok(self):
        d = make_done_check(
            dcid="release-gate-001",
            dtype=DoneCheckType.release_gate,
            status=DoneStatus.passed,
            required=True,
        )
        env = make_envelope(
            criteria=[make_criterion(cid="crit-001")],
            checks=[d],
            decision=make_decision(release=True),
        )
        assert env.decision.release_ready is True

    def test_release_ready_with_no_release_gates_ok(self):
        d = make_done_check(dtype=DoneCheckType.quality_gate, status=DoneStatus.passed)
        env = make_envelope(checks=[d], decision=make_decision(release=True))
        assert env.decision.release_ready is True

    def test_non_accepted_disposition_allows_failed_checks(self):
        d = make_done_check(status=DoneStatus.failed, required=True)
        env = make_envelope(
            criteria=[make_criterion(cid="crit-001")],
            checks=[d],
            decision=make_decision(
                disposition=CompletionDisposition.needs_rework,
                reason="Failed required DoD checks",
            ),
        )
        assert env.decision.completion_disposition == CompletionDisposition.needs_rework


class TestExampleScenarios:
    def test_task_with_explicit_output_and_evidence_criteria(self):
        c1 = AcceptanceCriterionRecord(
            criterion_id="crit-001",
            task_id="task-001",
            criterion_type=CriterionType.functional,
            description="Login endpoint accepts valid credentials and returns JWT",
            required=True,
            test_method="integration_test",
            expected_result="200 OK with JWT token",
            status=CriterionStatus.met,
        )
        c2 = AcceptanceCriterionRecord(
            criterion_id="crit-002",
            task_id="task-001",
            criterion_type=CriterionType.output,
            description="OpenAPI spec updated with new endpoint",
            required=True,
            test_method="spec_review",
            expected_result="openapi.yaml includes /auth/login",
            status=CriterionStatus.met,
        )
        c3 = AcceptanceCriterionRecord(
            criterion_id="crit-003",
            task_id="task-001",
            criterion_type=CriterionType.evidence,
            description="Security review passed",
            required=True,
            test_method="review_ticket",
            expected_result="Review ticket marked approved",
            status=CriterionStatus.met,
        )
        cs = AcceptanceCriteriaSet(
            criteria_set_id="cs-001",
            task_id="task-001",
            title="Login endpoint criteria",
            criteria=[c1, c2, c3],
        )
        asm = CompletionAssessmentRecord(
            assessment_id="asm-001",
            task_id="task-001",
            criteria_met_count=3,
            criteria_failed_count=0,
            dod_passed_count=1,
            dod_failed_count=0,
        )
        env = make_envelope(criteria_set=cs, assessment=asm)
        assert env.assessment.criteria_met_count >= 3

    def test_reusable_dod_profile_for_code_tasks(self):
        checks = [
            DefinitionOfDoneCheck(
                done_check_id="dod-lint",
                done_check_type=DoneCheckType.quality_gate,
                description="All linters pass",
                required=True,
                validation_method="ruff check",
                status=DoneStatus.passed,
            ),
            DefinitionOfDoneCheck(
                done_check_id="dod-tests",
                done_check_type=DoneCheckType.verification_gate,
                description="All tests pass",
                required=True,
                validation_method="pytest",
                status=DoneStatus.passed,
            ),
            DefinitionOfDoneCheck(
                done_check_id="dod-docs",
                done_check_type=DoneCheckType.documentation_gate,
                description="Documentation updated",
                required=False,
                validation_method="doc review",
                status=DoneStatus.passed,
            ),
            DefinitionOfDoneCheck(
                done_check_id="dod-release",
                done_check_type=DoneCheckType.release_gate,
                description="Release checklist complete",
                required=True,
                validation_method="release_ticket",
                status=DoneStatus.passed,
            ),
        ]
        dod = DefinitionOfDoneProfile(
            dod_profile_id="dod-code",
            name="Standard Code DoD",
            description="Baseline quality gates for all code changes",
            checks=checks,
            version="2.0",
            owner="eng-team",
            active=True,
        )
        assert dod.active
        assert len(dod.checks) == 4
        assert dod.version == "2.0"

    def test_accepted_task_all_criteria_met(self):
        c = make_criterion(cid="crit-001", status=CriterionStatus.met, required=True)
        d = make_done_check(status=DoneStatus.passed, required=True)
        ev = make_evidence(ref="crit-001")
        env = make_envelope(
            criteria=[c],
            checks=[d],
            evidence=[ev],
        )
        assert env.decision.completion_disposition == CompletionDisposition.accepted
        assert env.decision.release_ready is False

    def test_accepted_with_caveats(self):
        c = make_criterion(cid="crit-001", status=CriterionStatus.met, required=True)
        d = make_done_check(dcid="dod-lint", status=DoneStatus.passed, required=True)
        env = make_envelope(
            criteria=[c],
            checks=[d],
            decision=make_decision(
                disposition=CompletionDisposition.accepted_with_caveats,
                reason="Minor doc gap",
                followup=["Update README with new endpoint"],
            ),
        )
        assert env.decision.completion_disposition == CompletionDisposition.accepted_with_caveats
        assert "Update README with new endpoint" in env.decision.followup_actions

    def test_failed_release_gate_needs_rework(self):
        c = make_criterion(cid="crit-001", status=CriterionStatus.met, required=True)
        release_check = DefinitionOfDoneCheck(
            done_check_id="release-gate-001",
            done_check_type=DoneCheckType.release_gate,
            description="Security scan passed",
            required=True,
            status=DoneStatus.failed,
            notes="Critical vulnerability found in dependency",
        )
        env = make_envelope(
            criteria=[c],
            checks=[release_check],
            decision=make_decision(
                disposition=CompletionDisposition.needs_rework,
                reason="Release gate failed — security scan found critical vulnerability",
            ),
        )
        assert env.decision.completion_disposition == CompletionDisposition.needs_rework
