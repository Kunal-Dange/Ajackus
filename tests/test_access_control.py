
"""Tests for landlord account-level screening report authorization."""

from app.access_control import can_access_screening_report
from app.models import ScreeningReport, Tenant


def test_cross_account_report_is_denied(
    property_managers, properties, tenants, screening_reports
):
    """Manager from la-001 cannot access a report belonging to la-002."""

    result = can_access_screening_report(
        property_managers[0],
        screening_reports[1],
        properties=properties,
        tenants=tenants,
    )

    assert result is False


def test_same_account_report_is_allowed(
    property_managers, properties, tenants, screening_reports
):
    """Manager from la-001 can access their own tenant's report."""

    result = can_access_screening_report(
        property_managers[0],
        screening_reports[0],
        properties=properties,
        tenants=tenants,
    )

    assert result is True


def test_reverse_cross_account_report_is_denied(
    property_managers, properties, tenants, screening_reports
):
    result = can_access_screening_report(
        property_managers[1],
        screening_reports[0],
        properties=properties,
        tenants=tenants,
    )

    assert result is False


def test_reverse_same_account_report_is_allowed(
    property_managers, properties, tenants, screening_reports
):
    result = can_access_screening_report(
        property_managers[1],
        screening_reports[1],
        properties=properties,
        tenants=tenants,
    )

    assert result is True


def test_missing_tenant_fails_closed(
    property_managers, properties, tenants
):
    orphan_report = ScreeningReport(
        "orphan", "missing-tenant", "0000", 600
    )

    assert not can_access_screening_report(
        property_managers[0],
        orphan_report,
        properties=properties,
        tenants=tenants,
    )


def test_missing_property_fails_closed(
    property_managers, properties, tenants
):
    broken_tenants = tenants + [
        Tenant("orphan-tenant", "Orphan", "missing-property")
    ]

    orphan_report = ScreeningReport(
        "orphan-report", "orphan-tenant", "0000", 600
    )

    assert not can_access_screening_report(
        property_managers[0],
        orphan_report,
        properties=properties,
        tenants=broken_tenants,
    )


def test_duplicate_tenant_ids_fail_closed(
    property_managers, properties, tenants, screening_reports
):
    duplicate_tenants = tenants + [tenants[0]]

    assert not can_access_screening_report(
        property_managers[0],
        screening_reports[0],
        properties=properties,
        tenants=duplicate_tenants,
    )
