"""
abac.py — Attribute-Based Access Control for ADI Assistant
Drop into your project root. No new dependencies needed.

HOW TO ACTIVATE (3 steps at the bottom of this file summary):
  1. Place this file in project root (same level as app.py)
  2. Replace app.py with the patched version (app_patched.py)
  3. Replace login.html and register.html with the new templates

WHAT THIS ADDS:
  - Real user storage in users.json (flat file, swap for SQLite later)
  - Flask session-based authentication
  - ABAC policy engine: every access decision checks subject + resource + env attributes
  - Access log in access_log.jsonl — one JSON line per decision
  - @require_access decorator wraps your existing routes with zero changes to pipeline logic
"""
from __future__ import annotations

import json
import functools
from datetime import datetime, time
from pathlib import Path
from typing import Any, Dict, Optional, Tuple

from flask import jsonify, request, session


# ---------------------------------------------------------------------------
# User store  (SQLite — thread-safe, no extra dependencies)
# ---------------------------------------------------------------------------

import sqlite3

DB_FILE = Path("users.db")


def _get_db() -> sqlite3.Connection:
    """Open a connection to the SQLite database and ensure the users table exists."""
    conn = sqlite3.connect(str(DB_FILE), check_same_thread=False)
    conn.row_factory = sqlite3.Row
    conn.execute("""
        CREATE TABLE IF NOT EXISTS users (
            username   TEXT PRIMARY KEY,
            password   TEXT NOT NULL,
            salt       TEXT NOT NULL,
            role       TEXT NOT NULL,
            department TEXT NOT NULL,
            active     INTEGER NOT NULL DEFAULT 1,
            created_at TEXT NOT NULL
        )
    """)
    conn.commit()
    return conn


def _get_user(username: str) -> Optional[Dict[str, Any]]:
    """Fetch a single user by username. Returns dict or None."""
    with _get_db() as conn:
        row = conn.execute(
            "SELECT * FROM users WHERE username = ?", (username,)
        ).fetchone()
    return dict(row) if row else None


def _insert_user(user: Dict[str, Any]) -> None:
    """Insert a new user row into the database."""
    with _get_db() as conn:
        conn.execute("""
            INSERT INTO users (username, password, salt, role, department, active, created_at)
            VALUES (:username, :password, :salt, :role, :department, :active, :created_at)
        """, user)
        conn.commit()


def register_user(username: str, password: str, role: str, department: str) -> Tuple[bool, str]:
    """
    Create a new user with ABAC attributes, stored in SQLite.

    Valid roles:  infermiere | medico | amministratore | finance
    Department:   free text — adi, cardiologia, billing, admin, etc.

    Passwords are salted and hashed with SHA-256 before storage.
    Salt is generated with os.urandom(16) — unique per user.
    """
    if _get_user(username):
        return False, "Username already exists"

    valid_roles = {"infermiere", "medico", "amministratore", "finance"}
    if role not in valid_roles:
        return False, f"Role must be one of: {', '.join(sorted(valid_roles))}"
    if not password:
        return False, "Password required"

    import hashlib, os
    salt = os.urandom(16).hex()
    hashed = hashlib.sha256((salt + password).encode()).hexdigest()

    _insert_user({
        "username": username,
        "password": hashed,
        "salt": salt,
        "role": role,
        "department": department,
        "active": 1,
        "created_at": datetime.now().isoformat(timespec="seconds"),
    })
    return True, "Account created"


def login_user(username: str, password: str) -> Tuple[bool, str]:
    """Verify credentials against SQLite and write subject attributes into the Flask session."""
    user = _get_user(username)

    import hashlib
    stored_hash = user.get("password", "") if user else ""
    salt = user.get("salt", "") if user else ""
    input_hash = hashlib.sha256((salt + password).encode()).hexdigest()
    if not user or stored_hash != input_hash:
        _log(
            subject={"username": username, "role": "unknown", "department": ""},
            resource_type="auth", action="login",
            permitted=False, reason="Invalid credentials",
        )
        return False, "Invalid username or password"

    if not user.get("active", 1):
        return False, "This account has been disabled"

    session["subject"] = {
        "username": username,
        "role": user["role"],
        "department": user["department"],
    }
    _log(
        subject=session["subject"],
        resource_type="auth", action="login",
        permitted=True, reason="Valid credentials",
    )
    return True, "Login successful"


def logout_user() -> None:
    session.pop("subject", None)


def get_current_user() -> Optional[Dict[str, Any]]:
    return session.get("subject")


# ---------------------------------------------------------------------------
# Access log  (one JSON object per line — easy to analyse with pandas)
# ---------------------------------------------------------------------------

ACCESS_LOG = Path("access_log.jsonl")


def _log(
    subject: Dict[str, Any],
    resource_type: str,
    action: str,
    permitted: bool,
    reason: str,
    resource_owner: Optional[str] = None,
) -> None:
    """
    Every access decision — permit AND deny — is written here.
    This is the raw material for access_log_analysis.py.
    Columns: timestamp, who (role+dept), what (resource+action), outcome, why.
    """
    entry = {
        "timestamp": datetime.now().isoformat(timespec="seconds"),
        "subject_username": subject.get("username", "anonymous"),
        "subject_role": subject.get("role", "unknown"),
        "subject_department": subject.get("department", ""),
        "resource_type": resource_type,
        "resource_owner": resource_owner,
        "action": action,
        "permitted": permitted,
        "reason": reason,
        "endpoint": request.path if request else None,
        "method": request.method if request else None,
    }
    with ACCESS_LOG.open("a", encoding="utf-8") as f:
        f.write(json.dumps(entry, ensure_ascii=False) + "\n")


# ---------------------------------------------------------------------------
# Policy engine — the academic core of the project
# ---------------------------------------------------------------------------

class PolicyDecision:
    def __init__(self, permitted: bool, reason: str):
        self.permitted = permitted
        self.reason = reason


def evaluate_policy(
    subject: Dict[str, Any],
    resource_type: str,
    action: str,
    resource_owner: Optional[str] = None,
) -> PolicyDecision:
    """
    Pure ABAC evaluation. No side effects. Easy to unit-test.

    WHY THIS IS ABAC AND NOT RBAC
    ──────────────────────────────
    Role-Based Access Control (RBAC) only checks the subject's role.
    It can say "doctors can read reports" but it CANNOT say
    "doctors can only read their OWN reports."

    That ownership check — subject.username == resource.owner — requires
    comparing subject attributes against resource attributes at evaluation time.
    That is the defining capability of ABAC.

    Subject attributes (from Flask session, set at login):
        role:       infermiere | medico | amministratore | finance
        department: adi | cardiologia | billing | admin | ...
        username:   unique string identifier

    Resource types in this system:
        clinical_report  — output of /process_text and /process_audio
        audio_upload     — files sent to /process_audio
        dashboard        — the /assistant page
        quiz             — the /quiz page
        payment_record   — financial data (finance role only)

    Environment attributes checked internally:
        shift hours — clinical staff restricted to 08:00–20:00

    Conflict resolution: deny-overrides (safest default for medical data).
    Unknown resource type or action → default deny.
    """

    role = subject.get("role", "")
    username = subject.get("username", "")

    now = datetime.now().time()
    in_shift = time(8, 0) <= now <= time(20, 0)

    # No role = unauthenticated
    if not role:
        return PolicyDecision(False, "Unauthenticated subject — no role attribute")

    # QUIZ — open to all authenticated users
    if resource_type == "quiz":
        return PolicyDecision(True, "Quiz accessible to all authenticated users")

    # DASHBOARD — clinical staff and admin only; finance excluded
    if resource_type == "dashboard":
        if role in ("infermiere", "medico", "amministratore"):
            return PolicyDecision(True, f"Role '{role}' permitted to view dashboard")
        return PolicyDecision(
            False,
            f"Role '{role}' has no clinical access — dashboard denied. "
            "Finance users access the billing system, not the clinical dashboard."
        )

    # CLINICAL REPORTS
    if resource_type == "clinical_report":

        # Finance: hard deny on ALL clinical data — this is the key separation
        if role == "finance":
            return PolicyDecision(
                False,
                "Finance role is explicitly denied all clinical report access. "
                "Attribute resource.type=clinical_report conflicts with subject.role=finance."
            )

        if action == "create":
            if role in ("infermiere", "medico"):
                if not in_shift:
                    return PolicyDecision(
                        False,
                        f"Clinical report creation denied outside shift hours (08:00–20:00). "
                        f"Current time: {now.strftime('%H:%M')}. "
                        "Environment attribute env.time conflicts with policy."
                    )
                return PolicyDecision(True, f"Role '{role}' permitted to create reports during shift")
            if role == "amministratore":
                return PolicyDecision(True, "Admin can create reports at any time")
            return PolicyDecision(False, f"Role '{role}' not authorised to create clinical reports")

        if action == "read":
            if role == "amministratore":
                return PolicyDecision(True, "Admin can read all reports (audit access)")
            if role in ("infermiere", "medico"):
                if resource_owner is None:
                    # Owner unknown — permit but flag for audit review
                    return PolicyDecision(
                        True,
                        "Owner unknown — access permitted but flagged for audit. "
                        "Add resource_owner attribute to enable full ownership enforcement."
                    )
                if resource_owner == username:
                    return PolicyDecision(
                        True, f"Subject is the resource owner — read permitted"
                    )
                # THIS IS THE ABAC MOMENT: same role, different outcome based on ownership
                return PolicyDecision(
                    False,
                    f"Subject '{username}' is not the owner of this report "
                    f"(owner: '{resource_owner}'). "
                    "ABAC ownership check: subject.username != resource.owner — deny."
                )

        if action == "list":
            if role == "amministratore":
                return PolicyDecision(True, "Admin can list all reports")
            return PolicyDecision(False, "Only administrators can list all reports")

    # AUDIO UPLOADS
    if resource_type == "audio_upload":
        if role == "finance":
            return PolicyDecision(False, "Finance role cannot upload clinical audio")
        if role in ("infermiere", "medico", "amministratore"):
            if role != "amministratore" and not in_shift:
                return PolicyDecision(
                    False,
                    f"Audio upload denied outside shift hours. "
                    f"Current time: {now.strftime('%H:%M')}"
                )
            return PolicyDecision(True, f"Role '{role}' permitted to upload audio")

    # PAYMENT RECORDS
    if resource_type == "payment_record":
        if role == "finance" and action == "read":
            return PolicyDecision(True, "Finance role permitted to read payment records")
        if role == "finance" and action != "read":
            return PolicyDecision(False, "Finance role has read-only access to payment records")
        if role == "amministratore" and action == "read":
            return PolicyDecision(True, "Admin read access to payments (audit function)")
        return PolicyDecision(
            False,
            f"Role '{role}' is not authorised to access payment records. "
            "Only finance and admin (read-only) have access to resource.type=payment_record."
        )

    # ADMIN PANEL
    if resource_type == "admin_panel":
        if role == "amministratore":
            return PolicyDecision(True, "Administrator permitted to access admin panel")
        return PolicyDecision(False, f"Role '{role}' is not authorised to access the admin panel")

    # Default deny — no policy matched
    return PolicyDecision(
        False,
        f"No policy found for resource_type='{resource_type}', action='{action}'. "
        "Default deny applies."
    )


# ---------------------------------------------------------------------------
# Flask decorator — wraps your existing routes
# ---------------------------------------------------------------------------

def require_access(resource_type: str, action: str = "read", resource_owner_fn=None):
    """
    Decorator that enforces ABAC before the route handler runs.

    Usage:
        @app.route("/process_text", methods=["POST"])
        @require_access("clinical_report", "create")
        def process_text():
            ...  # your code is completely unchanged

    resource_owner_fn: optional callable returning the resource owner string,
    used for ownership-based read policies:
        @require_access("clinical_report", "read",
                        resource_owner_fn=lambda: request.args.get("owner"))

    Returns 401 if not authenticated, 403 if policy denies, or runs the route normally.
    """
    def decorator(f):
        @functools.wraps(f)
        def wrapper(*args, **kwargs):
            subject = get_current_user()

            if subject is None:
                _log(
                    subject={"username": "anonymous", "role": "", "department": ""},
                    resource_type=resource_type, action=action,
                    permitted=False, reason="No active session — authentication required",
                )
                from flask import redirect as _redirect
                return _redirect("/")

            resource_owner = None
            if resource_owner_fn:
                try:
                    resource_owner = resource_owner_fn()
                except Exception:
                    pass

            decision = evaluate_policy(subject, resource_type, action, resource_owner)

            _log(
                subject=subject,
                resource_type=resource_type,
                action=action,
                permitted=decision.permitted,
                reason=decision.reason,
                resource_owner=resource_owner,
            )

            if not decision.permitted:
                # API endpoints (called by JS fetch) get JSON
                # Page routes (navigated in browser) get a nice HTML error page
                wants_json = (
                    request.is_json
                    or request.method == "POST"
                    or request.path.startswith("/api/")
                    or request.path.startswith("/process_")
                )
                if wants_json:
                    return jsonify({
                        "error": "Access denied",
                        "reason": decision.reason,
                        "code": "ABAC_DENY"
                    }), 403
                from flask import render_template as _rt
                return _rt(
                    "access_denied.html",
                    role=subject.get("role", "unknown"),
                    reason=decision.reason,
                ), 403

            return f(*args, **kwargs)
        return wrapper
    return decorator