async def async_setup_entry(hass, entry):
    hass.components.frontend.async_register_built_in_panel(
        component_name='iframe',
        sidebar_title='PilotSuite',
        sidebar_icon='mdi:brain',
        url_path='pilotsuite',
        config={'url': '/api/hassio_ingress/pilotsuite_core/'},
        require_admin=True
    )
    return True
