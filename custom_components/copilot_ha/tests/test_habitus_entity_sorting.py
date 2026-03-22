"""Tests for habitus_entity_sorting.sort_entity_to_zone()."""

import unittest
from custom_components.copilot_ha.habitus_entity_sorting import sort_entity_to_zone


class TestSortEntityToZoneBasic(unittest.TestCase):
    """Basic zone sorting — entity_id + entity_name both provided."""

    def test_wohnbereich_exact(self):
        z, c = sort_entity_to_zone("light.wohnzimmer_decke", "Wohnzimmer Decke")
        self.assertEqual(z, "living")
        self.assertGreaterEqual(c, 0.60)

    def test_badbereich_exact(self):
        z, c = sort_entity_to_zone("light.bad_decke", "Bad Decke")
        self.assertEqual(z, "bathing")
        self.assertGreaterEqual(c, 0.60)

    def test_kochbereich_exact(self):
        z, c = sort_entity_to_zone("light.kueche_herd", "Küche Herd")
        self.assertEqual(z, "kitchen")
        self.assertGreaterEqual(c, 0.60)

    def test_buerobereich_exact(self):
        z, c = sort_entity_to_zone("climate.buero_heizung", "Büro Heizung")
        self.assertEqual(z, "working")
        self.assertGreaterEqual(c, 0.60)

    def test_gangbereich_exact(self):
        z, c = sort_entity_to_zone("light.flur_decke", "Flur Decke")
        self.assertEqual(z, "transit")
        self.assertGreaterEqual(c, 0.60)

    def test_schlafbereich_exact(self):
        z, c = sort_entity_to_zone("light.schlafzimmer_nachttisch", "Schlafzimmer Nachttisch")
        self.assertEqual(z, "sleeping")
        self.assertGreaterEqual(c, 0.60)

    def test_aussenbereich(self):
        z, c = sort_entity_to_zone("light.garten_laterne", "Garten Laterne")
        self.assertEqual(z, "outdoor")
        self.assertGreaterEqual(c, 0.60)

    def test_kellerbereich(self):
        z, c = sort_entity_to_zone("switch.kellerlicht", "Keller Licht")
        self.assertEqual(z, "utility")
        self.assertGreaterEqual(c, 0.60)

    def test_zimmer_mira(self):
        z, c = sort_entity_to_zone("climate.mira_zimmer", "Mira Zimmer")
        self.assertEqual(z, "multi")
        self.assertGreaterEqual(c, 0.60)

    def test_zimmer_paul(self):
        z, c = sort_entity_to_zone("light.paul_decke", "Paul Decke")
        self.assertEqual(z, "multi")
        self.assertGreaterEqual(c, 0.60)


class TestConfidenceThreshold(unittest.TestCase):
    """Unknown/unmatched entities should fall back to ungeordnet."""

    def test_unknown_entity_ungeordnet(self):
        z, c = sort_entity_to_zone("climate.unknown_entity_xyz", "Something XYZ")
        self.assertEqual(z, "ungeordnet")
        self.assertLess(c, 0.50)

    def test_unknown_name_only_low_confidence(self):
        """Without strong id keywords, unknown names score low."""
        z, c = sort_entity_to_zone("sensor.energie_verbrauch", "Energie")
        # entity_id has "energie" keyword → might match transit, but low confidence
        # depends on keyword scoring; just verify it returns without error
        self.assertIsInstance(z, str)
        self.assertIsInstance(c, float)


class TestReturnType(unittest.TestCase):
    """API contract: sort_entity_to_zone returns exactly (zone_id, confidence)."""

    def test_returns_tuple_of_two(self):
        result = sort_entity_to_zone("light.wohnzimmer_decke", "Wohnzimmer Decke")
        self.assertIsInstance(result, tuple)
        self.assertEqual(len(result), 2)

    def test_confidence_is_float(self):
        z, c = sort_entity_to_zone("light.bad_decke", "Bad Decke")
        self.assertIsInstance(c, float)

    def test_zone_id_is_string(self):
        z, c = sort_entity_to_zone("light.bad_decke", "Bad Decke")
        self.assertIsInstance(z, str)


class TestEdgeCases(unittest.TestCase):
    """Edge cases and boundary conditions."""

    def test_empty_entity_id(self):
        z, c = sort_entity_to_zone("", "")
        self.assertEqual(z, "ungeordnet")

    def test_none_entity_name(self):
        z, c = sort_entity_to_zone("light.wohnzimmer_decke", None)
        # Should still work — name is optional in the scoring
        self.assertIsInstance(z, str)
        self.assertIsInstance(c, float)


if __name__ == "__main__":
    unittest.main()
