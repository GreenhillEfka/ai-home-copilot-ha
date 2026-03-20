"""Tests for sort_entity_to_zone()."""

import unittest
from entity_zone_sorter import sort_entity_to_zone


class TestSortEntityToZoneBasic(unittest.TestCase):

    def test_wohnbereich_exact(self):
        z, c, _ = sort_entity_to_zone("light.wohnzimmer_decke", "Wohnzimmer Decke")
        self.assertEqual(z, "zone:wohnbereich")
        self.assertGreaterEqual(c, 0.60)

    def test_badbereich_exact(self):
        z, c, _ = sort_entity_to_zone("light.bad_decke", "Bad Decke")
        self.assertEqual(z, "zone:badbereich")
        self.assertGreaterEqual(c, 0.60)

    def test_kochbereich_exact(self):
        z, c, _ = sort_entity_to_zone("light.kueche_herd", "Küche Herd")
        self.assertEqual(z, "zone:kochbereich")
        self.assertGreaterEqual(c, 0.60)

    def test_buerobereich_exact(self):
        z, c, _ = sort_entity_to_zone("climate.buero_heizung", "Büro Heizung")
        self.assertEqual(z, "zone:buerobereich")
        self.assertGreaterEqual(c, 0.60)

    def test_gangbereich_exact(self):
        z, c, _ = sort_entity_to_zone("light.flur_decke", "Flur Decke")
        self.assertEqual(z, "zone:gangbereich")
        self.assertGreaterEqual(c, 0.60)

    def test_schlafbereich_exact(self):
        z, c, _ = sort_entity_to_zone("light.schlafzimmer_nachttisch", "Schlafzimmer Nachttisch")
        self.assertEqual(z, "zone:schlafbereich")
        self.assertGreaterEqual(c, 0.60)

    def test_aussenbereich(self):
        z, c, _ = sort_entity_to_zone("light.garten_laterne", "Garten Laterne")
        self.assertEqual(z, "zone:aussenbereich")
        self.assertGreaterEqual(c, 0.60)

    def test_kellerbereich(self):
        z, c, _ = sort_entity_to_zone("switch.kellerlicht", "Keller Licht")
        self.assertEqual(z, "zone:kellerbereich")
        self.assertGreaterEqual(c, 0.60)

    def test_zimmer_mira(self):
        z, c, _ = sort_entity_to_zone("climate.mira_zimmer", "Mira Zimmer")
        self.assertEqual(z, "zone:zimmer_mira")
        self.assertGreaterEqual(c, 0.60)

    def test_zimmer_paul(self):
        z, c, _ = sort_entity_to_zone("light.paul_decke", "Paul Decke")
        self.assertEqual(z, "zone:zimmer_paul")
        self.assertGreaterEqual(c, 0.60)


class TestConfidenceThreshold(unittest.TestCase):

    def test_unknown_entity_ungeordnet(self):
        z, c, extra = sort_entity_to_zone("climate.unknown_entity_xyz", "Something XYZ")
        self.assertEqual(z, "zone:ungeordnet")
        self.assertLess(c, 0.60)

    def test_area_virtual_ungeordnet(self):
        z, c, extra = sort_entity_to_zone("sensor.energie_verbrauch", area_name="Energie")
        self.assertEqual(z, "zone:ungeordnet")
        self.assertEqual(extra.get("is_virtual_area"), True)


class TestMatchTypes(unittest.TestCase):

    def test_match_type_reported(self):
        _, _, extra = sort_entity_to_zone("light.wohnzimmer", "Wohnzimmer")
        self.assertIn(extra["match_type"], ("exact", "substring", "area_exact"))

    def test_virtual_area_match_type(self):
        _, _, extra = sort_entity_to_zone("sensor.energie", area_name="Energie")
        self.assertEqual(extra["match_type"], "virtual_area")


class TestZoneNames(unittest.TestCase):

    def test_zone_name_de_reported(self):
        _, _, extra = sort_entity_to_zone("light.wohnzimmer")
        self.assertEqual(extra.get("zone_name_de"), "Wohnbereich")


if __name__ == "__main__":
    unittest.main()
