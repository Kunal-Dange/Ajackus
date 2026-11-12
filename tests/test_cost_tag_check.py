
"""Tests for generic Terraform billing-tag validation."""

import json

from scripts.cost_tag_check import check_plan


def test_fixture_flags_only_missing_billing_tags(capsys):
    result = check_plan("fixtures/plan.json")
    output = capsys.readouterr().out

    assert result == 1
    assert "aws_s3_bucket.listing_media" in output
    assert "aws_lambda_function.mls_feed_sync" in output

    assert "landlord_media[0]" not in output
    assert "screening_report_export" not in output
    assert "archive_media" not in output
    assert "decommissioned_media" not in output


def test_unchanged_plan_is_idempotent(capsys):
    first_result = check_plan("fixtures/plan.json")
    first_output = capsys.readouterr().out

    second_result = check_plan("fixtures/plan.json")
    second_output = capsys.readouterr().out

    assert (first_result, first_output) == (
        second_result, second_output
    )


def test_generic_resource_types_and_missing_tags(tmp_path, capsys):
    plan = {
        "resource_changes": [
            {
                "address": "aws_db_instance.example",
                "type": "aws_db_instance",
                "change": {
                    "actions": ["create"],
                    "after": {
                        "tags": {"tenant_id": "t-1"}
                    },
                },
            },
            {
                "address": "aws_sqs_queue.example",
                "type": "aws_sqs_queue",
                "change": {
                    "actions": ["update"],
                    "after": {
                        "tags": {"landlord_account_id": "  "}
                    },
                },
            },
            {
                "address": "aws_kms_key.example",
                "type": "aws_kms_key",
                "change": {
                    "actions": ["create"],
                    "after": {
                        "tags": {"landlord_account_id": "la-1"}
                    },
                },
            },
        ]
    }

    path = tmp_path / "plan.json"
    path.write_text(json.dumps(plan))

    assert check_plan(str(path)) == 1

    output = capsys.readouterr().out

    assert "aws_db_instance.example" in output
    assert "aws_sqs_queue.example" in output
    assert "aws_kms_key.example" not in output


def test_duplicate_address_is_reported_once(tmp_path, capsys):
    entry = {
        "address": "aws_s3_bucket.shared",
        "change": {
            "actions": ["create"],
            "after": {"tags": {}},
        },
    }

    path = tmp_path / "plan.json"
    path.write_text(
        json.dumps({"resource_changes": [entry, entry]})
    )

    assert check_plan(str(path)) == 1

    output = capsys.readouterr().out

    assert output.count("aws_s3_bucket.shared") == 1


def test_delete_noop_and_replacement_are_skipped(tmp_path, capsys):
    entries = [
        {
            "address": "x.delete",
            "change": {
                "actions": ["delete"],
                "after": None,
            },
        },
        {
            "address": "x.noop",
            "change": {
                "actions": ["no-op"],
                "after": {"tags": {}},
            },
        },
        {
            "address": "x.replace",
            "change": {
                "actions": ["delete", "create"],
                "after": {"tags": {}},
            },
        },
    ]

    path = tmp_path / "plan.json"
    path.write_text(json.dumps({"resource_changes": entries}))

    assert check_plan(str(path)) == 0
    assert "x." not in capsys.readouterr().out


def test_invalid_plan_returns_error(tmp_path, capsys):
    path = tmp_path / "bad.json"
    path.write_text('{"not_resource_changes": []}')

    assert check_plan(str(path)) == 2

    assert "invalid Terraform plan" in capsys.readouterr().err
