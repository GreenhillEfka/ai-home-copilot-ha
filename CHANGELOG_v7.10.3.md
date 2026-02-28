# Changelog v7.10.3

**Date:** 2026-02-28  
**Phase:** Phase 6 - Type Hints & API Improvements

## Summary

This release focuses on fixing the Notifications API and improving test coverage. All 51 notification and sharing tests are now passing.

## Bug Fixes

### Notifications API
- **Fixed:** POST `/api/v1/notifications` endpoint now properly creates notifications
- **Fixed:** Response format standardized to `{ok, count, ...}` convention
- **Fixed:** Numeric priority conversion (1=CRITICAL, 2=HIGH, 3=NORMAL, 4=LOW)
- **Fixed:** Deduplication for duplicate notifications within 60-second window

### Test Fixes
- **Fixed:** MockEntity metadata handling in sharing API tests
- **Fixed:** Test fixtures now properly use NotificationManager instead of NotificationEngine
- **Fixed:** Test isolation for notification tests

## New Features

### Notifications API Enhancements
- **Added:** GET `/api/v1/notifications/stats` - Get notification statistics
- **Added:** GET `/api/v1/notifications/pending` - Get unread notifications
- **Added:** GET `/api/v1/notifications/digest` - Get time-window digest summaries
- **Added:** Deduplication support with `deduplicated_or_rate_limited` status

## Test Results

```
tests/test_sharing_api.py: 28 passed
tests/test_notifications_api.py: 23 passed
Total: 51 passed, 0 failed
```

## Files Changed

- `copilot_core/api/v1/notifications.py` - Extended API endpoints
- `tests/test_notifications_api.py` - Fixed test fixtures and expectations
- `tests/test_sharing_api.py` - Fixed MockEntity metadata handling
- `copilot_core/VERSION` - Bumped to 7.10.3

## Upgrade Notes

No breaking changes. The Notifications API is now more compatible with the expected test format and provides additional endpoints for statistics and digest views.
