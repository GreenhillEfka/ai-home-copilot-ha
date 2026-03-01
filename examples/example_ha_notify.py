#!/usr/bin/env python3
"""HomeAssistant Notify Adapter Examples.

Demonstrates usage of the HANotifyAdapter for sending notifications
through HomeAssistant's notify.* services.

Requirements:
    - HomeAssistant instance with notify services configured
    - PilotSuite Core with notifications module

Usage:
    python example_ha_notify.py
"""

from copilot_core.notifications.ha_notify_adapter import (
    HANotifyAdapter,
    get_ha_notify_adapter,
    reset_ha_notify_adapter,
)


def example_basic_setup(hass):
    """Example: Basic adapter setup."""
    print("\n" + "="*60)
    print("EXAMPLE 1: Basic Setup")
    print("="*60)
    
    # Create adapter with HA instance
    adapter = HANotifyAdapter(hass)
    
    # Test connection
    result = adapter.test_connection()
    print(f"\nConnection: {'✓ Connected' if result['connected'] else '✗ Disconnected'}")
    print(f"Available notify services: {', '.join(result.get('notify_services', []))}")
    
    return adapter


def example_device_registration(adapter, user_id: str = "demo_user"):
    """Example: Register notification devices."""
    print("\n" + "="*60)
    print("EXAMPLE 2: Device Registration")
    print("="*60)
    
    # Register mobile device
    mobile_device = adapter.register_ha_device(
        user_id=user_id,
        ha_entity_id="notify.mobile_app_iphone",
        device_name="Demo iPhone",
        device_type="mobile"
    )
    print(f"\n✓ Registered mobile device: {mobile_device.id}")
    print(f"  Name: {mobile_device.device_name}")
    print(f"  Entity: {mobile_device.ha_entity_id}")
    print(f"  Type: {mobile_device.device_type}")
    
    # Register Telegram device
    telegram_device = adapter.register_ha_device(
        user_id=user_id,
        ha_entity_id="notify.telegram",
        device_name="Demo Telegram",
        device_type="telegram"
    )
    print(f"\n✓ Registered Telegram device: {telegram_device.id}")
    
    # Register WhatsApp device
    whatsapp_device = adapter.register_ha_device(
        user_id=user_id,
        ha_entity_id="notify.whatsapp",
        device_name="Demo WhatsApp",
        device_type="whatsapp"
    )
    print(f"✓ Registered WhatsApp device: {whatsapp_device.id}")
    
    # Show all devices for user
    devices = adapter.get_devices_for_user(user_id)
    print(f"\nTotal devices for {user_id}: {len(devices)}")
    
    return devices


def example_send_notification(adapter, device_id: str):
    """Example: Send basic notification."""
    print("\n" + "="*60)
    print("EXAMPLE 3: Send Notification")
    print("="*60)
    
    success = adapter.send_to_ha_service(
        device_id=device_id,
        title="Welcome Home",
        message="Arrival detected. Turning on lights and adjusting temperature.",
        priority="normal",
        category="system"
    )
    
    print(f"\nNotification sent: {'✓ Success' if success else '✗ Failed'}")
    return success


def example_priority_levels(adapter, device_id: str):
    """Example: Different priority levels."""
    print("\n" + "="*60)
    print("EXAMPLE 4: Priority Levels")
    print("="*60)
    
    priorities = [
        ("low", "Background Update", "New automation rules available"),
        ("normal", "Status Update", "Evening routine started"),
        ("high", "Important Alert", "Motion detected in garage"),
        ("urgent", "Critical Warning", "Water leak detected in basement!")
    ]
    
    for priority, title, message in priorities:
        success = adapter.send_to_ha_service(
            device_id=device_id,
            title=title,
            message=message,
            priority=priority,
            category="alert" if priority in ["high", "urgent"] else "info"
        )
        print(f"  {priority:8s}: {'✓' if success else '✗'} - {title}")


def example_categories(adapter, device_id: str):
    """Example: Notification categories."""
    print("\n" + "="*60)
    print("EXAMPLE 5: Notification Categories")
    print("="*60)
    
    categories = [
        ("mood_change", "Mood Update", "Living room mood changed to 'Relaxing Evening'"),
        ("alert", "Security Alert", "Front door opened"),
        ("suggestion", "Automation Suggestion", "Consider turning off lights in unused rooms"),
        ("system", "System Status", "Backup completed successfully"),
        ("warning", "Warning", "Battery level low in hallway sensor"),
        ("error", "Error", "Failed to connect to weather service")
    ]
    
    for category, title, message in categories:
        success = adapter.send_to_ha_service(
            device_id=device_id,
            title=title,
            message=message,
            priority="normal",
            category=category
        )
        print(f"  {category:15s}: {'✓' if success else '✗'}")


def example_custom_payload(adapter, device_id: str):
    """Example: Custom payload data for interactive notifications."""
    print("\n" + "="*60)
    print("EXAMPLE 6: Custom Payload (Interactive)")
    print("="*60)
    
    # Mobile app with action buttons
    custom_data = {
        "action_id": "suggestion_123",
        "actions": [
            {"title": "✓ Accept", "action": "ACCEPT"},
            {"title": "✗ Dismiss", "action": "DISMISS"},
            {"title": "⏰ Remind Later", "action": "REMIND"}
        ],
        "image": "/local/images/automation_suggestion.png",
        "url": "/config/automations/suggestion_123"
    }
    
    success = adapter.send_to_ha_service(
        device_id=device_id,
        title="New Automation Suggestion",
        message="Based on your patterns, consider automating the evening lights.",
        priority="normal",
        category="suggestion",
        data=custom_data
    )
    
    print(f"\nInteractive notification sent: {'✓ Success' if success else '✗ Failed'}")
    print(f"Custom data: {len(custom_data)} fields")
    
    return success


def example_multi_user(adapter):
    """Example: Multi-user notifications."""
    print("\n" + "="*60)
    print("EXAMPLE 7: Multi-User Notifications")
    print("="*60)
    
    # Register devices for multiple users
    users = ["alice", "bob", "charlie"]
    
    for user in users:
        adapter.register_ha_device(
            user_id=user,
            ha_entity_id=f"notify.mobile_app_{user}",
            device_name=f"{user.title()}'s Device"
        )
    
    # Send to all users
    for user in users:
        devices = adapter.get_devices_for_user(user)
        for device in devices:
            adapter.send_to_ha_service(
                device_id=device.id,
                title="House Meeting",
                message="Reminder: Family meeting at 7 PM in the living room",
                priority="normal",
                category="info"
            )
            print(f"  ✓ Sent to {device.device_name}")


def example_direct_entity(adapter):
    """Example: Send directly to HA entity."""
    print("\n" + "="*60)
    print("EXAMPLE 8: Direct Entity Notification")
    print("="*60)
    
    # Send to specific entity without device registration
    success = adapter.send_to_entity(
        entity_id="notify.telegram",
        title="System Report",
        message="Daily summary: 15 automations triggered, 3 suggestions created",
        priority="low"
    )
    
    print(f"Direct entity notification: {'✓ Success' if success else '✗ Failed'}")
    return success


def example_error_handling(adapter):
    """Example: Error handling and fallbacks."""
    print("\n" + "="*60)
    print("EXAMPLE 9: Error Handling")
    print("="*60)
    
    # Try to send to non-existent device
    try:
        success = adapter.send_to_ha_service(
            device_id="non_existent_device",
            title="Test",
            message="This should fail gracefully"
        )
        print(f"Result: {'Success (unexpected)' if success else 'Failed (expected)'}")
    except Exception as e:
        print(f"Exception caught: {type(e).__name__}: {e}")
    
    # Check connection before sending
    result = adapter.test_connection()
    if not result["connected"]:
        print("⚠ HA not connected - using fallback notification method")
        # Implement fallback logic here


def example_remove_device(adapter, device_id: str):
    """Example: Remove device registration."""
    print("\n" + "="*60)
    print("EXAMPLE 10: Remove Device")
    print("="*60)
    
    success = adapter.remove_device(device_id)
    print(f"Device removed: {'✓ Success' if success else '✗ Failed'}")
    
    return success


def main():
    """Run all examples."""
    print("\n" + "="*60)
    print("PILOTSUITE HA NOTIFY ADAPTER EXAMPLES")
    print("="*60)
    
    # Mock HomeAssistant instance for demonstration
    # In production, use actual hass instance from HomeAssistant
    class MockHomeAssistant:
        def __init__(self):
            self.services = MockServices()
        
        class services:
            @staticmethod
            def async_services():
                return {
                    "notify": {
                        "mobile_app_iphone": {},
                        "mobile_app_android": {},
                        "telegram": {},
                        "whatsapp": {},
                        "pushover": {},
                        "email": {}
                    }
                }
            
            @staticmethod
            def call(domain, service, service_data):
                print(f"    [HA Service Call] {domain}.{service}: {service_data.get('title')}")
                return True
    
    hass = MockHomeAssistant()
    
    try:
        # Run examples
        adapter = example_basic_setup(hass)
        devices = example_device_registration(adapter)
        
        if devices:
            device_id = devices[0].id
            example_send_notification(adapter, device_id)
            example_priority_levels(adapter, device_id)
            example_categories(adapter, device_id)
            example_custom_payload(adapter, device_id)
        
        example_multi_user(adapter)
        example_direct_entity(adapter)
        example_error_handling(adapter)
        
        print("\n" + "="*60)
        print("All examples completed!")
        print("="*60 + "\n")
        
    except Exception as e:
        print(f"\n❌ Error: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    main()
