"""Contract tests for entity_tags_store.py — pilotsuite entity tags store key parity."""
import ast
import pathlib
import sys

SRC = pathlib.Path("custom_components/pilotsuite/entity_tags_store.py")
CONST = pathlib.Path("custom_components/pilotsuite/const.py")


def test_entity_tags_store_key_is_pilotsuite():
    """ET1: ENTITY_TAGS_STORE_KEY uses pilotsuite namespace."""
    src = SRC.read_text()
    # Must contain the pilotsuite key
    assert 'pilotsuite.entity_tags' in src, (
        f"ENTITY_TAGS_STORE_KEY must be 'pilotsuite.entity_tags', got: "
        f"{src.split('ENTITY_TAGS_STORE_KEY')[1].split(chr(10))[0].strip()}"
    )
    # Must not contain the legacy copilot_ha key
    assert 'copilot_ha.entity_tags' not in src, (
        "ENTITY_TAGS_STORE_KEY must not contain legacy 'copilot_ha.entity_tags'"
    )


def test_const_entity_tags_store_key_is_pilotsuite():
    """ET2: const.ENTITY_TAGS_STORE_KEY uses pilotsuite namespace."""
    const_text = CONST.read_text()
    # Must contain the pilotsuite key
    assert 'pilotsuite.entity_tags' in const_text, (
        f"const.ENTITY_TAGS_STORE_KEY must be 'pilotsuite.entity_tags', got: "
        f"{const_text.split('ENTITY_TAGS_STORE_KEY')[1].split(chr(10))[0].strip()}"
    )
    # Must not contain the legacy copilot_ha key
    assert 'copilot_ha.entity_tags' not in const_text, (
        "const.ENTITY_TAGS_STORE_KEY must not contain legacy 'copilot_ha.entity_tags'"
    )


def test_no_stale_copilot_ha_literals_in_entity_tags_store():
    """ET3: No unexplained copilot_ha literals in entity_tags_store.py."""
    src = SRC.read_text()
    tree = ast.parse(src)
    literals = [
        node.value for node in ast.walk(tree)
        if isinstance(node, ast.Constant) and isinstance(node.value, str)
    ]
    stale = [s for s in literals if "copilot_ha" in s and "pilotsuite" not in s]
    assert not stale, f"Unexpected stale copilot_ha string literals: {stale}"


if __name__ == "__main__":
    import pytest
    sys.exit(pytest.main([__file__, "-v"]))
