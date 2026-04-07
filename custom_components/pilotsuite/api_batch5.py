"""Batch 5: Styx & System APIs — Chat, Multi-Home, Dashboard, Debug."""
from __future__ import annotations
from .api import CopilotApiClient


class StyxAPI(CopilotApiClient):
    """Styx Chat & LLM API client."""
    
    async def styx_chat(self, message: str, context: list = None) -> dict:
        """Styx chat."""
        return await self._post_json("/api/v1/styx/chat", {"message": message, "context": context or []})
    
    async def get_styx_dashboard(self) -> dict:
        """Get Styx dashboard."""
        return await self._get_json("/api/v1/styx/dashboard")
    
    async def styx_voice(self, audio: str) -> dict:
        """Styx voice chat."""
        return await self._post_json("/api/v1/styx/voice", {"audio": audio})
    
    async def get_conversation(self) -> dict:
        """Get conversation."""
        return await self._get_json("/api/v1/conversation")
    
    async def get_conversation_history(self) -> dict:
        """Get conversation history."""
        return await self._get_json("/api/v1/conversation/history")
    
    async def get_conversation_preferences(self) -> dict:
        """Get conversation preferences."""
        return await self._get_json("/api/v1/conversation/preferences")
    
    async def get_conversation_stats(self) -> dict:
        """Get conversation stats."""
        return await self._get_json("/api/v1/conversation/stats")
    
    async def get_voice_status(self) -> dict:
        """Get voice status."""
        return await self._get_json("/api/v1/voice")
    
    async def get_voice_context(self) -> dict:
        """Get voice context."""
        return await self._get_json("/api/v1/voice/context")
    
    async def get_character_current(self) -> dict:
        """Get current character."""
        return await self._get_json("/api/v1/character/current")
    
    async def list_character_modes(self) -> dict:
        """List character modes."""
        return await self._get_json("/api/v1/character/modes")
    
    async def set_character_mode(self, mode: str) -> dict:
        """Set character mode."""
        return await self._post_json("/api/v1/character/mode", {"mode": mode})
    
    async def apply_character_mood(self, mood: str) -> dict:
        """Apply character mood."""
        return await self._post_json("/api/v1/character/mood", {"mood": mood})
    
    async def explain_suggestion(self, suggestion_id: str) -> dict:
        """Explain suggestion."""
        return await self._get_json(f"/api/v1/explain/suggestion/{suggestion_id}")
    
    async def explain_pattern(self, pattern_id: str) -> dict:
        """Explain pattern."""
        return await self._get_json(f"/api/v1/explain/pattern/{pattern_id}")
    
    async def attribute_action(self, action: dict) -> dict:
        """Attribute action."""
        return await self._post_json("/api/v1/action_attribution/attribute", action)
    
    async def get_action_history(self, user_id: str = None) -> dict:
        """Get action history."""
        if user_id:
            return await self._get_json(f"/api/v1/action_attribution/user/{user_id}")
        return await self._get_json("/api/v1/action_attribution/history")
    
    async def get_user_hints(self) -> dict:
        """Get user hints."""
        return await self._get_json("/api/v1/user_hints")
    
    async def list_llm_models(self) -> dict:
        """List LLM models."""
        return await self._get_json("/api/v1/models")


class MultiHomeAPI(CopilotApiClient):
    """Multi-Home & Sharing API client."""
    
    async def list_homes(self) -> dict:
        """List homes."""
        return await self._get_json("/api/v1/homes")
    
    async def get_home(self, home_id: str) -> dict:
        """Get home."""
        return await self._get_json(f"/api/v1/homes/{home_id}")
    
    async def add_home(self, home: dict) -> dict:
        """Add home."""
        return await self._post_json("/api/v1/homes", home)
    
    async def get_config_diff(self, source: str, target: str) -> dict:
        """Get config diff."""
        return await self._get_json(f"/api/v1/config/diff/{source}/{target}")
    
    async def sync_configs(self, data: dict) -> dict:
        """Sync configs."""
        return await self._post_json("/api/v1/config/sync", data)
    
    async def list_conflicts(self) -> dict:
        """List conflicts."""
        return await self._get_json("/api/v1/conflicts")
    
    async def resolve_conflict(self, conflict_id: str, resolution: dict) -> dict:
        """Resolve conflict."""
        return await self._post_json(f"/api/v1/conflicts/{conflict_id}/resolve", resolution)
    
    async def list_federated_models(self) -> dict:
        """List federated models."""
        return await self._get_json("/api/v1/federated/models")
    
    async def contribute_to_federated(self, contribution: dict) -> dict:
        """Contribute to federated learning."""
        return await self._post_json("/api/v1/federated/contribute", contribution)
    
    async def get_federated_status(self) -> dict:
        """Get federated status."""
        return await self._get_json("/api/v1/federated/status")
    
    async def get_sharing_status(self) -> dict:
        """Get sharing status."""
        return await self._get_json("/api/v1/sharing/status")
    
    async def get_collective_intelligence_status(self) -> dict:
        """Get collective intelligence status."""
        return await self._get_json("/api/v1/collective_intelligence/status")


class DashboardAPI(CopilotApiClient):
    """Dashboard & UI API client."""
    
    async def get_dashboard(self) -> dict:
        """Get main dashboard."""
        return await self._get_json("/api/v1/dashboard")
    
    async def get_dashboard_patterns(self) -> dict:
        """Get dashboard patterns."""
        return await self._get_json("/api/v1/dashboard/patterns")
    
    async def get_dashboard_zones(self) -> dict:
        """Get dashboard zones."""
        return await self._get_json("/api/v1/dashboard/zones")
    
    async def get_dashboard_rules(self) -> dict:
        """Get rule cards."""
        return await self._get_json("/api/v1/dashboard/rules")
    
    async def get_haushalt_overview(self) -> dict:
        """Get household overview."""
        return await self._get_json("/api/v1/haushalt/overview")
    
    async def remind_waste(self) -> dict:
        """Waste reminder."""
        return await self._post_json("/api/v1/haushalt/remind/waste", {})
    
    async def remind_birthday(self) -> dict:
        """Birthday reminder."""
        return await self._post_json("/api/v1/haushalt/remind/birthday", {})
    
    async def get_shopping_list(self) -> dict:
        """Get shopping list."""
        return await self._get_json("/api/v1/shopping")
    
    async def get_mcp_status(self) -> dict:
        """Get MCP status."""
        return await self._get_json("/api/v1/mcp/status")
    
    async def get_mcp_resources(self) -> dict:
        """Get MCP resources."""
        return await self._get_json("/api/v1/mcp/resources")
    
    async def get_mcp_tools(self) -> dict:
        """Get MCP tools."""
        return await self._get_json("/api/v1/mcp/tools")
    
    async def call_mcp_tool(self, tool: str, params: dict) -> dict:
        """Call MCP tool."""
        return await self._post_json("/api/v1/mcp/tools_call", {"tool": tool, "params": params})
    
    async def get_homekit_status(self) -> dict:
        """Get HomeKit status."""
        return await self._get_json("/api/v1/homekit/status")
    
    async def toggle_homekit(self) -> dict:
        """Toggle HomeKit."""
        return await self._post_json("/api/v1/homekit/toggle", {})
    
    async def update_homekit_cache(self) -> dict:
        """Update HomeKit cache."""
        return await self._post_json("/api/v1/homekit/update", {})


class SystemAPI(CopilotApiClient):
    """System & Debug API client."""
    
    async def get_debug_status(self) -> dict:
        """Get debug status."""
        return await self._get_json("/api/v1/debug")
    
    async def set_debug_status(self, enabled: bool) -> dict:
        """Set debug status."""
        return await self._post_json("/api/v1/debug", {"enabled": enabled})
    
    async def get_dev_logs(self) -> dict:
        """Get dev logs."""
        return await self._get_json("/api/v1/dev/logs")
    
    async def get_error_digest(self) -> dict:
        """Get error digest."""
        return await self._get_json("/api/v1/error_digest/digest")
    
    async def get_error_categories(self) -> dict:
        """Get error categories."""
        return await self._get_json("/api/v1/error_digest/categories")
    
    async def get_repair_suggestions(self, error: dict) -> dict:
        """Get repair suggestions."""
        return await self._post_json("/api/v1/error_digest/repair-suggestions", error)
    
    async def get_log_fixer_status(self) -> dict:
        """Get log fixer status."""
        return await self._get_json("/api/v1/log_fixer_tx/status")
    
    async def list_transactions(self) -> dict:
        """List transactions."""
        return await self._get_json("/api/v1/log_fixer_tx/transactions")
    
    async def get_transaction(self, tx_id: str) -> dict:
        """Get transaction."""
        return await self._get_json(f"/api/v1/log_fixer_tx/transactions/{tx_id}")
    
    async def rollback_transaction(self, tx_id: str) -> dict:
        """Rollback transaction."""
        return await self._post_json(f"/api/v1/log_fixer_tx/transactions/{tx_id}/rollback", {})
    
    async def recover(self, data: dict) -> dict:
        """Recover."""
        return await self._post_json("/api/v1/log_fixer_tx/recover", data)
    
    async def get_auth_status(self) -> dict:
        """Get auth status."""
        return await self._get_json("/api/v1/auth/status")
    
    async def get_security_status(self) -> dict:
        """Get security status."""
        return await self._get_json("/api/v1/security/status")
    
    async def get_rate_limit_status(self) -> dict:
        """Get rate limit status."""
        return await self._get_json("/api/v1/rate_limit/status")
    
    async def get_performance_status(self) -> dict:
        """Get performance status."""
        return await self._get_json("/api/v1/performance/status")
