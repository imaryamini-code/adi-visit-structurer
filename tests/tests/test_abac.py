"""
tests/test_abac.py

Unit tests for the ABAC policy engine.

The most important test is test_doctor_cannot_read_another_doctors_report.
That test is your academic argument in executable form:
two subjects with identical roles get different outcomes based on
a resource attribute (ownership). RBAC cannot express this.

Run:  pytest tests/test_abac.py -v
"""
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from abac import evaluate_policy


# ── subject helpers ──────────────────────────────────────────────────────────

def doctor(username="dr_rossi"):
    return {"username": username, "role": "medico", "department": "adi"}

def nurse(username="inf_bianchi"):
    return {"username": username, "role": "infermiere", "department": "adi"}

def finance():
    return {"username": "billing1", "role": "finance", "department": "billing"}

def admin():
    return {"username": "admin1", "role": "amministratore", "department": "admin"}

def anonymous():
    return {}


# ── clinical report: create ───────────────────────────────────────────────────

class TestCreate:
    def test_doctor_can_create(self):
        d = evaluate_policy(doctor(), "clinical_report", "create")
        # passes during shift hours (08:00–20:00); run tests in that window
        assert d.permitted, d.reason

    def test_nurse_can_create(self):
        d = evaluate_policy(nurse(), "clinical_report", "create")
        assert d.permitted, d.reason

    def test_finance_cannot_create(self):
        d = evaluate_policy(finance(), "clinical_report", "create")
        assert not d.permitted
        assert "finance" in d.reason.lower()

    def test_anonymous_cannot_create(self):
        d = evaluate_policy(anonymous(), "clinical_report", "create")
        assert not d.permitted

    def test_admin_can_create_any_time(self):
        d = evaluate_policy(admin(), "clinical_report", "create")
        assert d.permitted, d.reason


# ── clinical report: read (ownership check — the ABAC moment) ────────────────

class TestRead:
    def test_doctor_reads_own_report(self):
        d = evaluate_policy(doctor("dr_rossi"), "clinical_report", "read",
                            resource_owner="dr_rossi")
        assert d.permitted, d.reason

    def test_doctor_cannot_read_another_doctors_report(self):
        """
        THE KEY TEST.
        dr_rossi and dr_ferrari have the same role (medico).
        Pure RBAC would permit both.
        ABAC denies dr_rossi because subject.username != resource.owner.
        """
        d = evaluate_policy(doctor("dr_rossi"), "clinical_report", "read",
                            resource_owner="dr_ferrari")
        assert not d.permitted
        assert "owner" in d.reason.lower()

    def test_admin_reads_any_report(self):
        d = evaluate_policy(admin(), "clinical_report", "read",
                            resource_owner="dr_rossi")
        assert d.permitted, d.reason

    def test_finance_cannot_read_clinical_report(self):
        d = evaluate_policy(finance(), "clinical_report", "read",
                            resource_owner="dr_rossi")
        assert not d.permitted


# ── payment records ───────────────────────────────────────────────────────────

class TestPayments:
    def test_finance_reads_payments(self):
        d = evaluate_policy(finance(), "payment_record", "read")
        assert d.permitted, d.reason

    def test_doctor_cannot_read_payments(self):
        d = evaluate_policy(doctor(), "payment_record", "read")
        assert not d.permitted

    def test_nurse_cannot_read_payments(self):
        d = evaluate_policy(nurse(), "payment_record", "read")
        assert not d.permitted

    def test_admin_audit_read_payments(self):
        d = evaluate_policy(admin(), "payment_record", "read")
        assert d.permitted, d.reason

    def test_nobody_creates_payment_records(self):
        """Even finance cannot create payment records — read-only access."""
        for subj in [finance(), doctor(), admin()]:
            d = evaluate_policy(subj, "payment_record", "create")
            assert not d.permitted, f"Role {subj['role']} should not create payments"


# ── dashboard ─────────────────────────────────────────────────────────────────

class TestDashboard:
    def test_clinical_staff_access_dashboard(self):
        for subj in [doctor(), nurse(), admin()]:
            d = evaluate_policy(subj, "dashboard", "read")
            assert d.permitted, f"Role {subj['role']} should access dashboard"

    def test_finance_cannot_access_clinical_dashboard(self):
        d = evaluate_policy(finance(), "dashboard", "read")
        assert not d.permitted


# ── quiz ──────────────────────────────────────────────────────────────────────

class TestQuiz:
    def test_all_roles_access_quiz(self):
        for subj in [doctor(), nurse(), finance(), admin()]:
            d = evaluate_policy(subj, "quiz", "read")
            assert d.permitted, f"Role {subj['role']} should access quiz"


# ── defaults ──────────────────────────────────────────────────────────────────

class TestDefaults:
    def test_unknown_resource_denied(self):
        d = evaluate_policy(doctor(), "future_resource_type", "read")
        assert not d.permitted

    def test_unknown_action_denied(self):
        d = evaluate_policy(doctor(), "clinical_report", "delete")
        assert not d.permitted

    def test_anonymous_denied_everywhere(self):
        for rt in ["clinical_report", "dashboard", "payment_record", "audio_upload"]:
            d = evaluate_policy(anonymous(), rt, "read")
            assert not d.permitted, f"Anonymous should be denied {rt}"