# PilotSuite HA — Docker Image
# Home Assistant Custom Component Container

FROM homeassistant/home-assistant:stable

LABEL maintainer="PilotSuite Team"
LABEL version="15.3.26"
LABEL description="PilotSuite HA Integration — Home Assistant Custom Component"

# Set working directory
WORKDIR /config

# Copy custom component
COPY custom_components/copilot_ha/ ./custom_components/copilot_ha/

# Copy configuration example
COPY configuration.yaml.example ./configuration.yaml.example

# Expose default HA port
EXPOSE 8123

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=30s --retries=3 \
    CMD curl -f http://localhost:8123/api/config || exit 1

# Run Home Assistant
CMD ["hass"]
