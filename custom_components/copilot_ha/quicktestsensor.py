class QuickTestSensor(CoordinatorEntity):
    """Sensor for Quick Test."""
    
    _attr_name = "Quick Test"
    _attr_unique_id = "sensor_quicktestsensor"
    _attr_icon = "mdi:sensor"
    
    def __init__(self, coordinator, config_entry):
        super().__init__(coordinator)
        self._config_entry = config_entry
        self._attr_device_info = {
            "identifiers": {(DOMAIN, config_entry.entry_id)},
        }
    
    @property
    def native_value(self):
        """Return the native value."""
        return self.coordinator.data.get("quick_test_value", None)
    
    @property
    def available(self) -> bool:
        """Return True if entity is available."""
        return super().available and self.coordinator.data is not None
