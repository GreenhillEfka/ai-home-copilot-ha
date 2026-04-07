from ..habitus_zones_store_v2 import HabitusZoneV2  # noqa: F401
import builtins

# Compatibility shim used by older tests that expect this symbol in global namespace.
builtins.HabitusZoneV2 = HabitusZoneV2

# Keep explicit module-level aliases for direct imports.
HabitusZone = HabitusZoneV2
