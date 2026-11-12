
"""
Tenant-isolated authorization for screening reports.
"""

from app.models import PropertyManager, ScreeningReport, Property, Tenant


def can_access_screening_report(
    actor: PropertyManager,
    report: ScreeningReport,
    *,
    properties: list[Property],
    tenants: list[Tenant],
) -> bool:

    # Fail closed if actor or report is missing.
    if actor is None or report is None:
        return False

    actor_account_id = actor.landlord_account_id

    if not isinstance(actor_account_id, str) or not actor_account_id.strip():
        return False

    if not isinstance(report.tenant_id, str) or not report.tenant_id.strip():
        return False

    # Find the tenant associated with the screening report.
    tenant_matches = [
        tenant for tenant in tenants
        if tenant is not None and tenant.id == report.tenant_id
    ]

    # Missing or duplicate tenant: deny access.
    if len(tenant_matches) != 1:
        return False

    tenant = tenant_matches[0]

    if not isinstance(tenant.property_id, str) or not tenant.property_id.strip():
        return False

    # Find the property associated with the tenant.
    property_matches = [
        prop for prop in properties
        if prop is not None and prop.id == tenant.property_id
    ]

    # Missing or duplicate property: deny access.
    if len(property_matches) != 1:
        return False

    landlord_account_id = property_matches[0].landlord_account_id

    if not isinstance(landlord_account_id, str) or not landlord_account_id.strip():
        return False

    # Only allow access within the same landlord account.
    return landlord_account_id == actor_account_id
