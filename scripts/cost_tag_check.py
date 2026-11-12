"""
B2, part 2 — implement the cost-tagging check.

Read fixtures/plan.json for the shape of a `terraform show -json` plan: a `resource_changes`
list, where each entry has a `type`, an `address`, and `change.after.tags`.

Implement check_plan() so it:
  - Looks at every resource being created or updated (skip anything whose change.actions
    isn't "create" or "update" — a "no-op"/"read" change, or a "delete" with no `after`
    block at all).
  - Fails (returns a non-zero exit code) if the resource is missing the tag that identifies
    the real billing unit, per README.md's domain model — not whatever tag the resource
    happens to already carry.
  - Is idempotent: running this twice against the same plan file produces the same result,
    with no duplicate output and no flipped pass/fail. This is about a single run being
    stable and repeatable — it does not require remembering anything between runs.
  - Prints which specific resource address(es) are missing the tag.

Run manually: python scripts/cost_tag_check.py fixtures/plan.json
"""

import json
import sys
from pathlib import Path

REQUIRED_TAG = "landlord_account_id"

# Only validate resources being created or updated.
CHECKED_ACTIONS = {
    ("create",),
    ("update",),
}


def has_required_tag(after):
    """Check whether a resource has a valid landlord billing tag."""

    if not isinstance(after, dict):
        return False

    tags = after.get("tags")

    if not isinstance(tags, dict):
        return False

    value = tags.get(REQUIRED_TAG)

    return isinstance(value, str) and bool(value.strip())


def check_plan(plan_path):
    """Validate all applicable resources in a Terraform plan."""

    try:
        with Path(plan_path).open("r", encoding="utf-8") as file:
            plan = json.load(file)

    except (OSError, json.JSONDecodeError) as exc:
        print(f"ERROR: Cannot read plan: {exc}", file=sys.stderr)
        return 2

    if not isinstance(plan, dict):
        print("ERROR: Invalid Terraform plan", file=sys.stderr)
        return 2

    resources = plan.get("resource_changes")

    if not isinstance(resources, list):
      print(
        "ERROR: invalid Terraform plan: resource_changes must be a list",
        file=sys.stderr
    )
      return 2

    # Resource address is the idempotency/deduplication key.
    missing_addresses = set()

    for resource in resources:

        if not isinstance(resource, dict):
            continue

        change = resource.get("change")

        if not isinstance(change, dict):
            continue

        actions = change.get("actions")

        if not isinstance(actions, list):
            continue

        if tuple(actions) not in CHECKED_ACTIONS:
            continue

        address = resource.get("address")

        if not isinstance(address, str) or not address.strip():
            print(
                "ERROR: Resource is missing a valid address",
                file=sys.stderr
            )
            return 2

        after = change.get("after")

        if not has_required_tag(after):
            missing_addresses.add(address)

    # Sorted output ensures deterministic results.
    for address in sorted(missing_addresses):
        print(f"MISSING {REQUIRED_TAG}: {address}")

    if missing_addresses:
        print(
            f"FAILED: {len(missing_addresses)} resource(s) "
            f"missing {REQUIRED_TAG}"
        )
        return 1

    print(
        f"PASSED: All create/update resources have {REQUIRED_TAG}"
    )

    return 0


if __name__ == "__main__":

    if len(sys.argv) != 2:
        print(
            "Usage: python3 scripts/cost_tag_check.py "
            "<terraform-plan.json>"
        )
        sys.exit(2)

    sys.exit(check_plan(sys.argv[1]))

