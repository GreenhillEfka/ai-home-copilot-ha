"""Tests for habitus_module_schema."""

import unittest
from habitus_module_schema import (
    ZONE_MODULE_SCHEMA,
    ZONE_DISPLAY_NAMES,
    MODULE_DESCRIPTIONS,
    get_zone_modules,
    is_module_allowed,
    all_zones,
    all_modules,
    MODULE_LIGHT,
    MODULE_AUDIO,
    MODULE_CLIMATE,
    MODULE_COVER,
    MODULE_ENERGY,
    MODULE_SCENE,
    MODULE_SECURITY,
)


class TestZoneModuleSchema(unittest.TestCase):

    def test_all_zones_have_modules(self):
        for zone in all_zones():
            mods = ZONE_MODULE_SCHEMA[zone]
            self.assertIsInstance(mods, list)
            self.assertGreater(len(mods), 0)

    def test_living_zone_has_all_expected_modules(self):
        mods = get_zone_modules("living")
        for m in (MODULE_LIGHT, MODULE_AUDIO, MODULE_CLIMATE, MODULE_COVER, MODULE_ENERGY, MODULE_SCENE):
            self.assertIn(m, mods)

    def test_transit_zone_light_only(self):
        mods = get_zone_modules("transit")
        self.assertEqual(mods, [MODULE_LIGHT])

    def test_outdoor_zone_security(self):
        mods = get_zone_modules("outdoor")
        self.assertIn(MODULE_SECURITY, mods)

    def test_sleeping_zone_no_audio(self):
        mods = get_zone_modules("sleeping")
        self.assertNotIn(MODULE_AUDIO, mods)

    def test_storage_zone_light_only(self):
        mods = get_zone_modules("storage")
        self.assertEqual(mods, [MODULE_LIGHT])

    def test_is_module_allowed_living_audio(self):
        self.assertTrue(is_module_allowed("living", MODULE_AUDIO))

    def test_is_module_allowed_transit_audio(self):
        self.assertFalse(is_module_allowed("transit", MODULE_AUDIO))

    def test_is_module_allowed_unknown_zone(self):
        self.assertEqual(get_zone_modules("nonexistent"), [])

    def test_all_zones_defined(self):
        self.assertEqual(len(all_zones()), 9)

    def test_all_modules_count(self):
        self.assertEqual(len(all_modules()), 7)

    def test_zone_display_names_complete(self):
        for zone in all_zones():
            self.assertIn(zone, ZONE_DISPLAY_NAMES, f"Missing display name for {zone}")

    def test_module_descriptions_complete(self):
        for mod in all_modules():
            self.assertIn(mod, MODULE_DESCRIPTIONS, f"Missing description for {mod}")

    def test_living_zone_modules_count(self):
        self.assertEqual(len(get_zone_modules("living")), 6)

    def test_child_zone_modules(self):
        mods = get_zone_modules("child")
        self.assertIn(MODULE_LIGHT, mods)
        self.assertIn(MODULE_CLIMATE, mods)

    def test_bathing_zone_light_climate(self):
        mods = get_zone_modules("bathing")
        self.assertIn(MODULE_LIGHT, mods)
        self.assertIn(MODULE_CLIMATE, mods)
        self.assertEqual(len(mods), 2)

    def test_cooking_zone_has_energy(self):
        mods = get_zone_modules("cooking")
        self.assertIn(MODULE_ENERGY, mods)

    def test_working_zone_has_energy(self):
        mods = get_zone_modules("working")
        self.assertIn(MODULE_ENERGY, mods)

    def test_outdoor_zone_has_light(self):
        mods = get_zone_modules("outdoor")
        self.assertIn(MODULE_LIGHT, mods)

    def test_no_duplicate_modules_in_zone(self):
        for zone, mods in ZONE_MODULE_SCHEMA.items():
            self.assertEqual(len(mods), len(set(mods)), f"Duplicate modules in {zone}")

    def test_all_modules_appear_in_at_least_one_zone(self):
        for mod in all_modules():
            appears = any(mod in mods for mods in ZONE_MODULE_SCHEMA.values())
            self.assertTrue(appears, f"Module {mod} not in any zone")

    def test_unmodified_schema(self):
        living_mods = get_zone_modules("living")
        self.assertIn(MODULE_LIGHT, living_mods)
        self.assertIn(MODULE_AUDIO, living_mods)
        self.assertIn(MODULE_CLIMATE, living_mods)
        self.assertIn(MODULE_COVER, living_mods)
        self.assertIn(MODULE_ENERGY, living_mods)
        self.assertIn(MODULE_SCENE, living_mods)


if __name__ == "__main__":
    unittest.main()
