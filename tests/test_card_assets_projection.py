"""Contract test: card_assets.py uses canonical pilotsuite name in URL route."""

import ast
import re


def test_card_assets_url_uses_domain_variable():
    """CA1: CardAssetView.url uses DOMAIN variable (pilotsuite at runtime), not hardcoded copilot_ha."""
    with open("custom_components/pilotsuite/card_assets.py", "r") as f:
        source = f.read()

    tree = ast.parse(source)

    for node in ast.walk(tree):
        if isinstance(node, ast.ClassDef) and node.name == "CardAssetView":
            for item in node.body:
                if isinstance(item, ast.Assign):
                    for target in item.targets:
                        if isinstance(target, ast.Name) and target.id == "url":
                            # f-string: DOMAIN variable reference is expected
                            if isinstance(item.value, ast.JoinedStr):
                                has_domain_var = any(
                                    isinstance(v, ast.FormattedValue) and isinstance(v.value, ast.Name) and v.value.id == "DOMAIN"
                                    for v in item.value.values
                                )
                                has_copilot_ha = any(
                                    isinstance(v, ast.Constant) and "copilot_ha" in v.value
                                    for v in item.value.values
                                )
                                assert has_domain_var, (
                                    "CardAssetView.url must use DOMAIN variable"
                                )
                                assert not has_copilot_ha, (
                                    "CardAssetView.url must not hardcode copilot_ha"
                                )
                                return

    assert False, "CardAssetView.url assignment not found in card_assets.py"


def test_card_assets_name_is_pilotsuite():
    """CA2: CardAssetView.name attribute uses pilotsuite, not copilot_ha."""
    with open("custom_components/pilotsuite/card_assets.py", "r") as f:
        source = f.read()

    tree = ast.parse(source)

    for node in ast.walk(tree):
        if isinstance(node, ast.ClassDef) and node.name == "CardAssetView":
            for item in node.body:
                if isinstance(item, ast.Assign):
                    for target in item.targets:
                        if isinstance(target, ast.Name) and target.id == "name":
                            name_val = ast.literal_eval(item.value)
                            assert "pilotsuite" in name_val, (
                                f"CardAssetView.name must use pilotsuite, got: {name_val}"
                            )
                            assert "copilot_ha" not in name_val, (
                                f"CardAssetView.name must not contain copilot_ha, got: {name_val}"
                            )
                            return

    assert False, "CardAssetView.name assignment not found in card_assets.py"


def test_card_assets_no_stale_copilot_ha_in_source():
    """CA3: No stale copilot_ha string literals in card_assets.py source."""
    with open("custom_components/pilotsuite/card_assets.py", "r") as f:
        source = f.read()

    # Filter out docstrings and comments for string-literal scan
    tree = ast.parse(source)
    string_literals = []

    for node in ast.walk(tree):
        if isinstance(node, ast.Constant) and isinstance(node.value, str):
            string_literals.append(node.value)

    for literal in string_literals:
        assert "copilot_ha" not in literal, (
            f"Found stale copilot_ha in string literal: {literal!r}"
        )