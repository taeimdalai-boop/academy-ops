import pytest

from app.attendance.connectors.adt_caps.connector import load_events
from app.attendance.daily import summarize_month
from app.classes.teaching import compute_teaching
from app.hr.contracts import load_contracts
from app.policy import load_policy

S = "samples/2026-09"


@pytest.fixture(scope="session")
def contracts():
    return load_contracts(f"{S}/employees.xlsx")


@pytest.fixture(scope="session")
def policy():
    return load_policy(f"{S}/policy.yaml")


@pytest.fixture(scope="session")
def attendance(contracts, policy):
    ev, _ = load_events(f"{S}/caps_events.xlsx", set(contracts))
    return summarize_month(ev, f"{S}/attendance_corrections.xlsx", contracts, policy, 2026, 9)


@pytest.fixture(scope="session")
def teaching(contracts, policy):
    return compute_teaching(f"{S}/schedule.xlsx", f"{S}/class_changes.xlsx", contracts, policy, 2026, 9)


@pytest.fixture(scope="session")
def pipeline(contracts, policy, attendance, teaching):
    from app.payroll.engine import calculate
    from app.payroll.inputs import build_inputs
    inputs, _ = build_inputs(contracts, attendance[0], teaching[0], f"{S}/allowances.xlsx", 2026, 9)
    return calculate(inputs, contracts, policy)
