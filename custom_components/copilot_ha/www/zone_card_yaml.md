# Zone Dashboard Card YAML Configuration
# ========================================
# 
# Home Assistant Lovelace configuration for the Zone Dashboard Card.
# This card displays zone status, mood, neuron activity, and quick actions.
#
# USAGE:
# 1. Copy this to your HA configuration (lovelace or packages folder)
# 2. Adjust entity IDs to match your setup
# 3. Add to your dashboard via YAML or UI
#
# REQUIREMENTS:
# - sensor.pilotsuite_habitus_zones (required) - Zone overview
# - sensor.pilotsuite_zone_modes (optional) - Zone modes
# - sensor.pilotsuite_mood_{zone}_* (optional) - Mood sensors
# - sensor.pilotsuite_brain_graph_nodes (optional) - Neuron activity
# - light.{zone}_main (optional) - Light entities per zone
# - climate.{zone} (optional) - Thermostat entities

# =============================================================================
# Zone Dashboard Card (Full Configuration)
# =============================================================================

# --- Main Zone Card ---
- type: custom:styx-zone-card
  entity: sensor.pilotsuite_habitus_zones
  title: Zonen
  show_mood: true
  show_neuron_activity: true
  show_quick_actions: true

# =============================================================================
# Zone Status Grid (Alternative with standard cards)
# =============================================================================

# --- Grid Layout for Zone Overview ---
- type: grid
  title: Zonen Status
  columns: 2
  square: false
  cards:
    # --- Living Room Zone ---
    - type: vertical-stack
      cards:
        - type: custom:mushroom-entity-card
          entity: sensor.living_room_temperature
          name: Wohnzimmer
          icon: mdi:sofa
          secondary_info: temperature
          tap_action:
            action: navigate
            navigation_path: /lovelace/zones#living-room
        
        - type: horizontal-stack
          cards:
            - type: gauge
              entity: sensor.living_room_humidity
              name: Luftfeuchtigkeit
              unit: "%"
              min: 0
              max: 100
            
            - type: entity
              entity: light.living_room_main
              name: Licht
              icon: mdi:lightbulb

    # --- Bedroom Zone ---
    - type: vertical-stack
      cards:
        - type: custom:mushroom-entity-card
          entity: sensor.bedroom_temperature
          name: Schlafzimmer
          icon: mdi:bed
          secondary_info: temperature
          tap_action:
            action: navigate
            navigation_path: /lovelace/zones#bedroom
        
        - type: horizontal-stack
          cards:
            - type: gauge
              entity: sensor.bedroom_humidity
              name: Luftfeuchtigkeit
              unit: "%"
              min: 0
              max: 100
            
            - type: entity
              entity: light.bedroom_main
              name: Licht
              icon: mdi:lightbulb

# =============================================================================
# Zone Mood Card (Circlular Gauges)
# =============================================================================

# --- Mood Gauges per Zone ---
- type: custom:styx-mood-card
  entity: sensor.pilotsuite_mood_living_room_comfort
  zone: Wohnzimmer

- type: custom:styx-mood-card
  entity: sensor.pilotsuite_mood_bedroom_comfort
  zone: Schlafzimmer

# =============================================================================
# Zone Mode Card (Active Modes)
# =============================================================================

# --- Zone Modes Overview ---
- type: entities
  title: Aktive Zonen-Modi
  show_header_toggle: false
  entities:
    - entity: sensor.pilotsuite_zone_modes
      name: Aktive Modi
      icon: mdi:toggle-switch-variant
    - entity: input_select.zone_mode
      name: Modus ändern
      icon: mdi:gesture-tap

# =============================================================================
# Zone Quick Actions (Script Triggers)
# =============================================================================

# --- Zone Scene Buttons ---
- type: horizontal-stack
  cards:
    - type: button
      name: Entspannen
      icon: mdi:meditation
      tap_action:
        action: call-service
        service: script.turn_on
        service_data:
          entity_id: script.zone_scene_relaxing
        target:
          entity_id: script.zone_scene_relaxing
    
    - type: button
      name: Fokus
      icon: mdi:head-lightbulb
      tap_action:
        action: call-service
        service: script.turn_on
        service_data:
          entity_id: script.zone_scene_focus
        target:
          entity_id: script.zone_scene_focus
    
    - type: button
      name: Film
      icon: mdi:movie-open
      tap_action:
        action: call-service
        service: script.turn_on
        service_data:
          entity_id: script.zone_scene_movie
        target:
          entity_id: script.zone_scene_movie
    
    - type: button
      name: Nacht
      icon: mdi:weather-night
      tap_action:
        action: call-service
        service: script.turn_on
        service_data:
          entity_id: script.zone_scene_night
        target:
          entity_id: script.zone_scene_night

# =============================================================================
# Zone Neuron Activity (Brain Graph Integration)
# =============================================================================

# --- Brain Graph Card ---
- type: custom:styx-brain-card
  entity: sensor.pilotsuite_brain_graph_nodes
  edge_entity: sensor.pilotsuite_brain_graph_edges
  title: Neuronen-Aktivität

# =============================================================================
# Compact Zone List (Alternative)
# =============================================================================

# --- Zone List with Status ---
- type: entities
  title: Alle Zonen
  show_header_toggle: false
  entities:
    - type: section
      label: Aktiv
    - entity: sensor.living_room_occupancy
      name: Wohnzimmer
      icon: mdi:sofa
      secondary_info: last-changed
    - entity: sensor.kitchen_occupancy
      name: Küche
      icon: mdi:chef-hat
      secondary_info: last-changed
    
    - type: section
      label: Inaktiv
    - entity: sensor.bedroom_occupancy
      name: Schlafzimmer
      icon: mdi:bed
      secondary_info: last-changed
    - entity: sensor.office_occupancy
      name: Büro
      icon: mdi:desk
      secondary_info: last-changed

# =============================================================================
# Configuration Examples
# =============================================================================

# --- Minimal Configuration (only required entity) ---
# - type: custom:styx-zone-card
#   entity: sensor.pilotsuite_habitus_zones

# --- Configuration without mood gauges ---
# - type: custom:styx-zone-card
#   entity: sensor.pilotsuite_habitus_zones
#   show_mood: false
#   show_neuron_activity: true
#   show_quick_actions: true

# --- Configuration for single zone ---
# - type: custom:styx-zone-card
#   entity: sensor.pilotsuite_habitus_zones
#   title: Wohnzimmer
#   zones:
#     - living_room
