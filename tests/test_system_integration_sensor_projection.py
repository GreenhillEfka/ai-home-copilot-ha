"""Projection contract tests for system_integration_sensor.py.

Verifies SystemIntegrationSensor is a pure projection shell on
`/api/v1/hub/integration` data with only trivial formatting.

HA-249
"""


class SystemIntegrationSensorContract:
    """Mirror of SystemIntegrationSensor projection logic."""

    @staticmethod
    def native_value(data):
        engines = data.get("engines_connected", 0)
        subs = data.get("active_subscriptions", 0)
        if engines == 0:
            return "Nicht verbunden"
        return f"{engines} Engines / {subs} Verknüpfungen"

    @staticmethod
    def icon(data):
        engines = data.get("engines_connected", 0)
        events = data.get("events_processed", 0)
        if engines == 0:
            return "mdi:hub-outline"
        if events > 0:
            return "mdi:hub"
        return "mdi:hub-outline"

    @staticmethod
    def attrs(data):
        attrs = {
            "engines_connected": data.get("engines_connected", 0),
            "events_processed": data.get("events_processed", 0),
            "active_subscriptions": data.get("active_subscriptions", 0),
            "last_event": data.get("last_event", ""),
            "last_event_time": data.get("last_event_time", ""),
            "engine_names": data.get("engine_names", []),
        }

        wiring = data.get("wiring_diagram", {})
        if wiring:
            attrs["wiring_diagram"] = wiring
            attrs["event_types"] = list(wiring.keys())

        event_log = data.get("event_log", [])
        if event_log:
            attrs["recent_events"] = [
                {
                    "event_type": e.get("event_type"),
                    "source": e.get("source"),
                    "handled_by": e.get("handled_by"),
                    "timestamp": e.get("timestamp"),
                }
                for e in event_log[:5]
            ]

        return attrs


class TestSystemIntegrationState:
    @staticmethod
    def _nv(data):
        return SystemIntegrationSensorContract.native_value(data)

    def test_si1_native_value_defaults_to_not_connected(self):
        assert self._nv({}) == "Nicht verbunden"

    def test_si2_native_value_zero_engines_stays_not_connected(self):
        assert self._nv({"engines_connected": 0, "active_subscriptions": 4}) == "Nicht verbunden"

    def test_si3_native_value_formats_engine_subscription_counts(self):
        assert self._nv({"engines_connected": 3, "active_subscriptions": 8}) == "3 Engines / 8 Verknüpfungen"

    def test_si4_native_value_formats_zero_subscriptions(self):
        assert self._nv({"engines_connected": 2, "active_subscriptions": 0}) == "2 Engines / 0 Verknüpfungen"


class TestSystemIntegrationIcon:
    @staticmethod
    def _icon(data):
        return SystemIntegrationSensorContract.icon(data)

    def test_si5_icon_defaults_to_outline(self):
        assert self._icon({}) == "mdi:hub-outline"

    def test_si6_icon_no_engines_stays_outline_even_with_events(self):
        assert self._icon({"engines_connected": 0, "events_processed": 9}) == "mdi:hub-outline"

    def test_si7_icon_engines_without_events_is_outline(self):
        assert self._icon({"engines_connected": 2, "events_processed": 0}) == "mdi:hub-outline"

    def test_si8_icon_engines_with_events_is_hub(self):
        assert self._icon({"engines_connected": 2, "events_processed": 1}) == "mdi:hub"


class TestSystemIntegrationAttrs:
    @staticmethod
    def _attrs(data):
        return SystemIntegrationSensorContract.attrs(data)

    def test_si9_attrs_defaults_when_empty(self):
        assert self._attrs({}) == {
            "engines_connected": 0,
            "events_processed": 0,
            "active_subscriptions": 0,
            "last_event": "",
            "last_event_time": "",
            "engine_names": [],
        }

    def test_si10_attrs_include_full_passthrough_data(self):
        data = {
            "engines_connected": 3,
            "events_processed": 21,
            "active_subscriptions": 7,
            "last_event": "scene_activated",
            "last_event_time": "2026-04-09T01:11:22Z",
            "engine_names": ["habitus", "neural", "energy"],
            "wiring_diagram": {
                "scene": ["habitus", "energy"],
                "presence": ["neural"],
            },
            "event_log": [
                {
                    "event_type": "scene",
                    "source": "ui",
                    "handled_by": ["habitus"],
                    "timestamp": "t1",
                    "ignored": "drop-me",
                },
                {
                    "event_type": "presence",
                    "source": "sensor",
                    "handled_by": ["neural"],
                    "timestamp": "t2",
                },
            ],
        }
        attrs = self._attrs(data)
        assert attrs["engines_connected"] == 3
        assert attrs["events_processed"] == 21
        assert attrs["active_subscriptions"] == 7
        assert attrs["last_event"] == "scene_activated"
        assert attrs["last_event_time"] == "2026-04-09T01:11:22Z"
        assert attrs["engine_names"] == ["habitus", "neural", "energy"]
        assert attrs["wiring_diagram"] == {
            "scene": ["habitus", "energy"],
            "presence": ["neural"],
        }
        assert attrs["event_types"] == ["scene", "presence"]
        assert attrs["recent_events"] == [
            {
                "event_type": "scene",
                "source": "ui",
                "handled_by": ["habitus"],
                "timestamp": "t1",
            },
            {
                "event_type": "presence",
                "source": "sensor",
                "handled_by": ["neural"],
                "timestamp": "t2",
            },
        ]

    def test_si11_attrs_omit_wiring_when_empty(self):
        attrs = self._attrs({"wiring_diagram": {}})
        assert "wiring_diagram" not in attrs
        assert "event_types" not in attrs

    def test_si12_attrs_recent_events_trim_to_five(self):
        attrs = self._attrs(
            {
                "event_log": [
                    {
                        "event_type": f"evt{i}",
                        "source": f"src{i}",
                        "handled_by": [f"eng{i}"],
                        "timestamp": f"t{i}",
                        "extra": i,
                    }
                    for i in range(7)
                ]
            }
        )
        assert len(attrs["recent_events"]) == 5
        assert attrs["recent_events"][0] == {
            "event_type": "evt0",
            "source": "src0",
            "handled_by": ["eng0"],
            "timestamp": "t0",
        }
        assert attrs["recent_events"][-1]["event_type"] == "evt4"

    def test_si13_attrs_omit_recent_events_when_log_empty(self):
        attrs = self._attrs({"event_log": []})
        assert "recent_events" not in attrs

    def test_si14_attrs_keep_none_values_without_local_inference(self):
        attrs = self._attrs(
            {
                "event_log": [
                    {
                        "event_type": None,
                        "source": None,
                        "handled_by": None,
                        "timestamp": None,
                    }
                ]
            }
        )
        assert attrs["recent_events"] == [
            {
                "event_type": None,
                "source": None,
                "handled_by": None,
                "timestamp": None,
            }
        ]


class TestSystemIntegrationGlobalContract:
    def test_gc1_sensor_targets_hub_integration_endpoint(self):
        src = open("custom_components/pilotsuite/sensors/system_integration_sensor.py").read()
        assert "/api/v1/hub/integration" in src
        assert "async_get_clientsession" in src
        assert "events_processed" in src
        assert "active_subscriptions" in src

    def test_gc2_sensor_only_uses_trivial_formatting_projection(self):
        src = open("custom_components/pilotsuite/sensors/system_integration_sensor.py").read()
        assert 'return "Nicht verbunden"' in src
        assert 'return f"{engines} Engines / {subs} Verknüpfungen"' in src
        assert 'return "mdi:hub"' in src
        assert 'return "mdi:hub-outline"' in src
        assert "for e in event_log[:5]" in src
        assert '"ignored"' not in src
