# Design Notes

## B2 — idempotency key

State exactly what key your `cost_tag_check.py` uses to decide whether two resources in the
same run are "the same" for dedup purposes, and why running it twice against an unchanged
plan file produces identical output and exit code without the script keeping any record
between runs. Use the word "idempotency" in your explanation.

<!-- Your answer here -->

The cost-tag validation check is designed to be idempotent.

The exact key used for deduplication is:

`resource["address"]`

This is the Terraform resource-instance address, which uniquely identifies
a resource instance within a Terraform configuration and state.

The validator stores missing resource addresses in a Python set:

`missing_addresses = set()`

This ensures that duplicate findings for the same resource are reported
only once.

The validator also sorts resource addresses before printing the results,
ensuring deterministic output regardless of the order of resources in
the Terraform plan.

Therefore, rerunning the validator against an unchanged Terraform plan
produces the same output and exit code without modifying external state.

## Any other decision with a non-obvious alternative

<!-- Your answer here -->
Decision: Inspect every applicable entry in Terraform's resource_changes rather than hardcoding resource types or resource names.

Alternative: Write separate validation rules for individual AWS resource types, such as S3 buckets or Lambda functions.

Reason: A generic approach automatically covers new Terraform resource types that expose tags, reduces duplicated logic, and makes the policy easier to maintain as infrastructure grows