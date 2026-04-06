#!/usr/bin/env python3
"""PilotSuite Core — Comprehensive Verification Script."""
from __future__ import annotations

import os
import sys
import json
import subprocess
import hashlib
from pathlib import Path
from typing import Dict, List, Any, Tuple
from dataclasses import dataclass
from datetime import datetime

# =============================================================================
# VERIFICATION RESULT
# =============================================================================

@dataclass
class CheckResult:
    """Result of a single check."""
    name: str
    passed: bool
    message: str
    severity: str = "info"  # info, warning, error, critical
    details: Dict[str, Any] = None

# =============================================================================
# FILE STRUCTURE CHECKS
# =============================================================================

def check_file_structure(base_path: str) -> List[CheckResult]:
    """Check that all required files exist."""
    results = []
    
    required_files = [
        # Core
        ("copilot_core/__init__.py", "critical"),
        ("copilot_core/manifest.json", "critical"),
        ("copilot_core/hacs.json", "critical"),
        ("copilot_core/README.md", "critical"),
        ("copilot_core/requirements.txt", "critical"),
        ("copilot_core/strings.json", "high"),
        
        # API
        ("copilot_core/api/rest_server.py", "critical"),
        ("copilot_core/api/gateway_v2.py", "high"),
        ("copilot_core/api/websocket_manager.py", "high"),
        
        # Security
        ("copilot_core/security/hardening.py", "critical"),
        
        # RAG
        ("copilot_core/rag/vector_store.py", "high"),
        ("copilot_core/rag/embedding_pipeline.py", "high"),
        ("copilot_core/rag/retrieval_engine.py", "high"),
        
        # ML
        ("copilot_core/ml/pattern_detection.py", "high"),
        ("copilot_core/ml/habit_learning.py", "high"),
        ("copilot_core/ml/anomaly_detection.py", "high"),
        
        # Presence
        ("copilot_core/presence/api.py", "high"),
        ("copilot_core/presence/sensor_fusion.py", "high"),
        ("copilot_core/presence/wilson_score.py", "high"),
        
        # Energy
        ("copilot_core/energy/or_tools_scheduler.py", "high"),
        ("copilot_core/energy/device_profiles.py", "high"),
        ("copilot_core/energy/scheduler_integration.py", "medium"),
        
        # Brain
        ("copilot_core/brain/graph_store.py", "high"),
        ("copilot_core/brain/graph_api.py", "high"),
        
        # Voice
        ("copilot_core/voice/stt_whisper.py", "medium"),
        ("copilot_core/voice/tts_piper.py", "medium"),
        ("copilot_core/voice/nlu_engine.py", "medium"),
        
        # Tests
        ("copilot_core/tests/test_integration.py", "high"),
        ("copilot_core/rag/tests/test_vector_store.py", "high"),
        ("copilot_core/presence/tests/test_presence.py", "high"),
        ("copilot_core/brain/tests/test_brain_graph_store.py", "high"),
        ("copilot_core/api/tests/test_rest_server.py", "high"),
        ("copilot_core/energy/tests/test_scheduler.py", "high"),
        
        # Documentation
        ("docs/RELEASE_v1.0.0.md", "critical"),
        ("docs/INSTALL.md", "high"),
        ("docs/TROUBLESHOOTING.md", "high"),
        ("docs/API_COMPLETE.md", "high"),
        ("docs/CONFIG_EXAMPLES.md", "medium"),
        ("docs/TUTORIAL_QUICKSTART.md", "medium"),
        ("docs/MONITORING.md", "medium"),
        ("docs/BACKUP_RECOVERY.md", "medium"),
        
        # CI/CD
        (".github/workflows/ci-cd.yml", "high"),
        
        # Optimization
        ("copilot_core/optimization/advanced_optimizations.py", "medium"),
    ]
    
    base = Path(base_path)
    
    for file_path, severity in required_files:
        full_path = base / file_path
        if full_path.exists():
            size = full_path.stat().st_size
            results.append(CheckResult(
                name=f"File: {file_path}",
                passed=True,
                message=f"Exists ({size / 1024:.1f} KB)",
                severity=severity,
                details={"size_bytes": size}
            ))
        else:
            results.append(CheckResult(
                name=f"File: {file_path}",
                passed=False,
                message="MISSING",
                severity=severity,
            ))
    
    return results

# =============================================================================
# JSON VALIDATION CHECKS
# =============================================================================

def check_json_files(base_path: str) -> List[CheckResult]:
    """Validate all JSON files."""
    results = []
    
    json_files = [
        "copilot_core/manifest.json",
        "copilot_core/hacs.json",
    ]
    
    base = Path(base_path)
    
    for file_path in json_files:
        full_path = base / file_path
        if not full_path.exists():
            continue
        
        try:
            with open(full_path) as f:
                data = json.load(f)
            
            # Validate manifest.json
            if "manifest.json" in file_path:
                required_fields = ["domain", "name", "version", "config_flow"]
                missing = [f for f in required_fields if f not in data]
                
                if missing:
                    results.append(CheckResult(
                        name=f"JSON: {file_path}",
                        passed=False,
                        message=f"Missing fields: {missing}",
                        severity="critical",
                    ))
                else:
                    results.append(CheckResult(
                        name=f"JSON: {file_path}",
                        passed=True,
                        message=f"Valid (version: {data.get('version', 'unknown')})",
                        severity="info",
                        details=data
                    ))
            
            # Validate hacs.json
            elif "hacs.json" in file_path:
                required_fields = ["domain", "name", "version"]
                missing = [f for f in required_fields if f not in data]
                
                if missing:
                    results.append(CheckResult(
                        name=f"JSON: {file_path}",
                        passed=False,
                        message=f"Missing fields: {missing}",
                        severity="critical",
                    ))
                else:
                    results.append(CheckResult(
                        name=f"JSON: {file_path}",
                        passed=True,
                        message=f"Valid (HACS ready)",
                        severity="info",
                        details=data
                    ))
        
        except json.JSONDecodeError as e:
            results.append(CheckResult(
                name=f"JSON: {file_path}",
                passed=False,
                message=f"Invalid JSON: {e}",
                severity="critical",
            ))
    
    return results

# =============================================================================
# VERSION CONSISTENCY CHECK
# =============================================================================

def check_version_consistency(base_path: str) -> List[CheckResult]:
    """Check that version strings are consistent across files."""
    results = []
    
    versions = {}
    
    # Check __init__.py
    init_path = Path(base_path) / "copilot_core/__init__.py"
    if init_path.exists():
        with open(init_path) as f:
            content = f.read()
            # Better version extraction
            import re
            match = re.search(r'__version__\s*=\s*["\']([^"\']+)["\']', content)
            if match:
                versions["__init__.py"] = match.group(1)
    
    # Check manifest.json
    manifest_path = Path(base_path) / "copilot_core/manifest.json"
    if manifest_path.exists():
        with open(manifest_path) as f:
            data = json.load(f)
            versions["manifest.json"] = data.get("version", "unknown")
    
    # Check hacs.json
    hacs_path = Path(base_path) / "copilot_core/hacs.json"
    if hacs_path.exists():
        with open(hacs_path) as f:
            data = json.load(f)
            versions["hacs.json"] = data.get("version", "unknown")
    
    # Check consistency
    unique_versions = set(versions.values())
    
    if len(unique_versions) == 1:
        version = list(unique_versions)[0]
        results.append(CheckResult(
            name="Version Consistency",
            passed=True,
            message=f"All files use version {version}",
            severity="info",
            details=versions
        ))
    else:
        results.append(CheckResult(
            name="Version Consistency",
            passed=False,
            message=f"Inconsistent versions: {versions}",
            severity="critical",
            details=versions
        ))
    
    return results

# =============================================================================
# TEST COVERAGE CHECK
# =============================================================================

def check_test_coverage(base_path: str) -> List[CheckResult]:
    """Check test file existence and basic structure."""
    results = []
    
    test_dirs = [
        "copilot_core/tests",
        "copilot_core/rag/tests",
        "copilot_core/presence/tests",
        "copilot_core/brain/tests",
        "copilot_core/api/tests",
        "copilot_core/energy/tests",
    ]
    
    base = Path(base_path)
    total_tests = 0
    
    for test_dir in test_dirs:
        full_dir = base / test_dir
        if full_dir.exists():
            test_files = list(full_dir.glob("test_*.py"))
            count = len(test_files)
            total_tests += count
            
            results.append(CheckResult(
                name=f"Tests: {test_dir}",
                passed=count > 0,
                message=f"{count} test file(s)" if count > 0 else "NO TESTS",
                severity="high" if count == 0 else "info",
                details={"test_count": count}
            ))
        else:
            results.append(CheckResult(
                name=f"Tests: {test_dir}",
                passed=False,
                message="Directory missing",
                severity="high",
            ))
    
    results.append(CheckResult(
        name="Total Test Files",
        passed=total_tests >= 10,
        message=f"{total_tests} test files found",
        severity="info" if total_tests >= 10 else "warning",
        details={"total": total_tests}
    ))
    
    return results

# =============================================================================
# DOCUMENTATION CHECK
# =============================================================================

def check_documentation(base_path: str) -> List[CheckResult]:
    """Check documentation completeness."""
    results = []
    
    docs = {
        "INSTALL.md": "Installation guide",
        "TROUBLESHOOTING.md": "Troubleshooting guide",
        "API_COMPLETE.md": "API reference",
        "CONFIG_EXAMPLES.md": "Configuration examples",
        "TUTORIAL_QUICKSTART.md": "Quick start tutorial",
        "MONITORING.md": "Monitoring guide",
        "BACKUP_RECOVERY.md": "Backup and recovery",
        "RELEASE_v1.0.0.md": "Release notes",
    }
    
    base = Path(base_path) / "docs"
    
    for doc_file, description in docs.items():
        full_path = base / doc_file
        if full_path.exists():
            size = full_path.stat().st_size
            lines = full_path.read_text().count("\n")
            
            results.append(CheckResult(
                name=f"Docs: {doc_file}",
                passed=True,
                message=f"{description} ({lines} lines)",
                severity="info",
                details={"lines": lines, "size_bytes": size}
            ))
        else:
            results.append(CheckResult(
                name=f"Docs: {doc_file}",
                passed=False,
                message=f"{description} - MISSING",
                severity="high",
            ))
    
    return results

# =============================================================================
# SECURITY CHECK
# =============================================================================

def check_security_implementation(base_path: str) -> List[CheckResult]:
    """Check security features are implemented."""
    results = []
    
    hardening_path = Path(base_path) / "copilot_core/security/hardening.py"
    
    if not hardening_path.exists():
        results.append(CheckResult(
            name="Security Hardening",
            passed=False,
            message="hardening.py MISSING",
            severity="critical",
        ))
        return results
    
    content = hardening_path.read_text()
    
    # Check for required security features
    security_features = {
        "SecureTokenGenerator": "Secure token generation",
        "PasswordHasher": "Password hashing",
        "EncryptionAtRest": "Encryption at rest",
        "APIKeyStore": "API key storage",
        "secrets.token_bytes": "Cryptographically secure random",
        "PBKDF2HMAC": "Key derivation",
        "Fernet": "Symmetric encryption",
        "hmac.compare_digest": "Constant-time comparison",
    }
    
    for feature, description in security_features.items():
        if feature in content:
            results.append(CheckResult(
                name=f"Security: {description}",
                passed=True,
                message="Implemented",
                severity="info",
            ))
        else:
            results.append(CheckResult(
                name=f"Security: {description}",
                passed=False,
                message="NOT implemented",
                severity="warning",
            ))
    
    return results

# =============================================================================
# API ENDPOINTS CHECK
# =============================================================================

def check_api_endpoints(base_path: str) -> List[CheckResult]:
    """Check REST API server has required endpoints."""
    results = []
    
    server_path = Path(base_path) / "copilot_core/api/rest_server.py"
    
    if not server_path.exists():
        results.append(CheckResult(
            name="REST API Server",
            passed=False,
            message="rest_server.py MISSING",
            severity="critical",
        ))
        return results
    
    content = server_path.read_text()
    
    # Check for required endpoint patterns
    endpoint_patterns = {
        "@app.get": "REST endpoints defined",
        "@app.post": "REST POST endpoints",
        "JWTAuth": "JWT authentication",
        "RateLimiter": "Rate limiting",
        "AuditLogger": "Audit logging",
        "/health": "Health endpoint",
        "/version": "Version endpoint",
        "/api/v1/": "API v1 routes",
    }
    
    for pattern, description in endpoint_patterns.items():
        if pattern in content:
            results.append(CheckResult(
                name=f"API: {description}",
                passed=True,
                message="Implemented",
                severity="info",
            ))
        else:
            results.append(CheckResult(
                name=f"API: {description}",
                passed=False,
                message="NOT implemented",
                severity="warning",
            ))
    
    return results

# =============================================================================
# CI/CD CHECK
# =============================================================================

def check_cicd(base_path: str) -> List[CheckResult]:
    """Check CI/CD pipeline configuration."""
    results = []
    
    cicd_path = Path(base_path) / ".github/workflows/ci-cd.yml"
    
    if not cicd_path.exists():
        results.append(CheckResult(
            name="CI/CD Pipeline",
            passed=False,
            message="ci-cd.yml MISSING",
            severity="high",
        ))
        return results
    
    content = cicd_path.read_text()
    
    # Check for required CI/CD stages
    stages = {
        "test:": "Test job",
        "lint:": "Lint job",
        "security:": "Security scan",
        "build:": "Build job",
        "deploy:": "Deploy job",
        "pytest": "Pytest runner",
        "flake8": "Flake8 linter",
        "black": "Black formatter",
        "mypy": "Type checking",
        "bandit": "Security scanner",
    }
    
    for stage, description in stages.items():
        if stage in content:
            results.append(CheckResult(
                name=f"CI/CD: {description}",
                passed=True,
                message="Configured",
                severity="info",
            ))
        else:
            results.append(CheckResult(
                name=f"CI/CD: {description}",
                passed=False,
                message="NOT configured",
                severity="warning",
            ))
    
    return results

# =============================================================================
# SUMMARY
# =============================================================================

def generate_summary(results: List[CheckResult]) -> Dict[str, Any]:
    """Generate summary statistics."""
    total = len(results)
    passed = sum(1 for r in results if r.passed)
    failed = total - passed
    
    by_severity = {
        "critical": {"total": 0, "failed": 0},
        "high": {"total": 0, "failed": 0},
        "medium": {"total": 0, "failed": 0},
        "warning": {"total": 0, "failed": 0},
        "info": {"total": 0, "failed": 0},
    }
    
    for result in results:
        severity = result.severity
        by_severity[severity]["total"] += 1
        if not result.passed:
            by_severity[severity]["failed"] += 1
    
    return {
        "total": total,
        "passed": passed,
        "failed": failed,
        "pass_rate": passed / total if total > 0 else 0,
        "by_severity": by_severity,
        "timestamp": datetime.now().isoformat(),
    }

# =============================================================================
# MAIN
# =============================================================================

def run_all_checks(base_path: str = "/config/clawd") -> int:
    """Run all verification checks."""
    print("=" * 80)
    print("PILOTSUITE CORE — COMPREHENSIVE VERIFICATION")
    print("=" * 80)
    print(f"Base Path: {base_path}")
    print(f"Timestamp: {datetime.now().isoformat()}")
    print("=" * 80)
    print()
    
    all_results = []
    
    # Run all checks
    print("🔍 Running checks...\n")
    
    print("1. File Structure...")
    all_results.extend(check_file_structure(base_path))
    
    print("2. JSON Validation...")
    all_results.extend(check_json_files(base_path))
    
    print("3. Version Consistency...")
    all_results.extend(check_version_consistency(base_path))
    
    print("4. Test Coverage...")
    all_results.extend(check_test_coverage(base_path))
    
    print("5. Documentation...")
    all_results.extend(check_documentation(base_path))
    
    print("6. Security Implementation...")
    all_results.extend(check_security_implementation(base_path))
    
    print("7. API Endpoints...")
    all_results.extend(check_api_endpoints(base_path))
    
    print("8. CI/CD Pipeline...")
    all_results.extend(check_cicd(base_path))
    
    # Generate summary
    summary = generate_summary(all_results)
    
    # Print results
    print("\n" + "=" * 80)
    print("RESULTS")
    print("=" * 80)
    
    # Show failures first
    failures = [r for r in all_results if not r.passed]
    if failures:
        print(f"\n❌ FAILURES ({len(failures)}):\n")
        for result in failures:
            severity_icon = {"critical": "🔴", "high": "🟠", "warning": "🟡", "info": "🔵"}.get(result.severity, "⚪")
            print(f"  {severity_icon} [{result.severity.upper()}] {result.name}")
            print(f"      {result.message}")
    
    # Show summary
    print("\n" + "=" * 80)
    print("SUMMARY")
    print("=" * 80)
    print(f"Total Checks: {summary['total']}")
    print(f"Passed: {summary['passed']} ✅")
    print(f"Failed: {summary['failed']} ❌")
    print(f"Pass Rate: {summary['pass_rate']*100:.1f}%")
    print()
    print("By Severity:")
    for severity, counts in summary['by_severity'].items():
        icon = {"critical": "🔴", "high": "🟠", "warning": "🟡", "info": "🔵"}.get(severity, "⚪")
        print(f"  {icon} {severity.upper()}: {counts['failed']}/{counts['total']} failed")
    
    print("\n" + "=" * 80)
    
    # Determine exit code
    critical_failures = summary['by_severity']['critical']['failed']
    high_failures = summary['by_severity']['high']['failed']
    
    if critical_failures > 0:
        print("❌ CRITICAL ISSUES FOUND — NOT READY FOR RELEASE")
        return 1
    elif high_failures > 0:
        print("⚠️ HIGH PRIORITY ISSUES FOUND — REVIEW RECOMMENDED")
        return 0
    else:
        print("✅ ALL CRITICAL CHECKS PASSED — READY FOR RELEASE")
        return 0


if __name__ == "__main__":
    base_path = sys.argv[1] if len(sys.argv) > 1 else "/config/clawd"
    exit_code = run_all_checks(base_path)
    sys.exit(exit_code)
