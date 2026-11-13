#!/usr/bin/env python3
"""
Nexus RAG Pipeline - Deployment Validation Script

This script validates all pre-deployment requirements before going to production.
Run this before deploying to ensure all configurations are correct.
"""

import os
import sys
import re
import json
from urllib.parse import urlparse
from pathlib import Path
from typing import Dict, List, Tuple


class DeploymentValidator:
    """Validates deployment configuration and prerequisites."""

    def __init__(self):
        self.checks: List[Tuple[str, bool, str]] = []
        self.warnings: List[str] = []
        self.errors: List[str] = []

    def check(self, name: str, condition: bool, message: str = "") -> None:
        """Record a check result."""
        self.checks.append((name, condition, message))
        if not condition:
            self.errors.append(f"❌ {name}: {message}")

    def warn(self, message: str) -> None:
        """Record a warning."""
        self.warnings.append(f"⚠️  {message}")

    def validate_environment_variables(self) -> bool:
        """Validate required environment variables."""
        print("\n[1/8] Validating Environment Variables...")

        required_vars = [
            "GEMINI_API_KEY",
            "ELASTICSEARCH_URL",
            "ELASTICSEARCH_API_KEY",
        ]

        all_set = True
        for var in required_vars:
            value = os.getenv(var)
            self.check(
                f"Environment variable {var}",
                value is not None and value != "",
                f"Missing or empty" if not value else "",
            )
            if not value:
                all_set = False

        return all_set

    def validate_api_key_lengths(self) -> bool:
        """Validate API key lengths."""
        print("[2/8] Validating API Key Lengths...")

        gemini_key = os.getenv("GEMINI_API_KEY", "")
        self.check(
            "GEMINI_API_KEY length",
            len(gemini_key) >= 30,
            f"Too short ({len(gemini_key)} chars, min 30)",
        )

        es_key = os.getenv("ELASTICSEARCH_API_KEY", "")
        self.check(
            "ELASTICSEARCH_API_KEY length",
            len(es_key) >= 30,
            f"Too short ({len(es_key)} chars, min 30)",
        )

        return len(gemini_key) >= 30 and len(es_key) >= 30

    def validate_urls(self) -> bool:
        """Validate URL formats."""
        print("[3/8] Validating URLs...")

        es_url = os.getenv("ELASTICSEARCH_URL", "")
        if es_url:
            parsed = urlparse(es_url)
            self.check(
                "ELASTICSEARCH_URL uses HTTPS",
                parsed.scheme == "https",
                f"Must use HTTPS, not {parsed.scheme}",
            )
            self.check(
                "ELASTICSEARCH_URL is valid",
                parsed.netloc != "",
                "Invalid URL format",
            )
            return parsed.scheme == "https" and parsed.netloc != ""

        return False

    def validate_environment_setting(self) -> bool:
        """Validate environment setting."""
        print("[4/8] Validating Environment Setting...")

        environment = os.getenv("ENVIRONMENT", "")
        valid_values = ["production", "staging", "development"]

        self.check(
            "ENVIRONMENT value",
            environment in valid_values,
            f"Must be one of {valid_values}, got {environment}",
        )

        if environment == "development":
            self.warn("ENVIRONMENT is set to 'development' (not recommended for production)")

        return environment in valid_values

    def validate_log_level(self) -> bool:
        """Validate log level."""
        print("[5/8] Validating Log Level...")

        log_level = os.getenv("LOG_LEVEL", "INFO")
        valid_levels = ["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"]

        self.check(
            "LOG_LEVEL value",
            log_level in valid_levels,
            f"Invalid log level: {log_level}",
        )

        if log_level == "DEBUG":
            self.warn("DEBUG log level enabled (wastes resources in production)")

        return log_level in valid_levels

    def validate_cors_origins(self) -> bool:
        """Validate CORS origins."""
        print("[6/8] Validating CORS Origins...")

        cors_origins = os.getenv("CORS_ORIGINS", "")

        if cors_origins == "*":
            self.warn("CORS_ORIGINS is wildcard (not recommended for production)")
            return False

        if cors_origins:
            for origin in cors_origins.split(","):
                origin = origin.strip()
                if not origin.startswith("https://"):
                    self.warn(f"CORS origin does not use HTTPS: {origin}")

        return True

    def validate_port(self) -> bool:
        """Validate port configuration."""
        print("[7/8] Validating Port Configuration...")

        port_str = os.getenv("PORT", "8000")
        try:
            port = int(port_str)
            self.check(
                "PORT is valid",
                1024 <= port <= 65535,
                f"Port must be 1024-65535, got {port}",
            )
            return 1024 <= port <= 65535
        except ValueError:
            self.check("PORT is numeric", False, f"PORT must be numeric, got {port_str}")
            return False

    def validate_rate_limiting(self) -> bool:
        """Validate rate limiting configuration."""
        print("[8/8] Validating Rate Limiting...")

        rate_limit_enabled = os.getenv("RATE_LIMIT_ENABLED", "true").lower() == "true"

        if rate_limit_enabled:
            try:
                rpm = int(os.getenv("RATE_LIMIT_REQUESTS_PER_MINUTE", "60"))
                rph = int(os.getenv("RATE_LIMIT_REQUESTS_PER_HOUR", "1000"))

                self.check(
                    "Rate limit per minute is reasonable",
                    30 <= rpm <= 10000,
                    f"Should be 30-10000, got {rpm}",
                )
                self.check(
                    "Rate limit per hour is reasonable",
                    100 <= rph <= 100000,
                    f"Should be 100-100000, got {rph}",
                )
                return True
            except ValueError:
                self.warn("Could not parse rate limit values")
                return False
        else:
            self.warn("Rate limiting is disabled")
            return False

    def validate_files(self) -> bool:
        """Validate required files exist."""
        print("\n[Bonus] Validating Required Files...")

        required_files = [
            "requirements.txt",
            "Dockerfile",
            "backend/main.py",
            ".env.production",
        ]

        all_exist = True
        for file_path in required_files:
            exists = Path(file_path).exists()
            self.check(
                f"File {file_path}",
                exists,
                "File not found" if not exists else "",
            )
            if not exists:
                all_exist = False

        return all_exist

    def print_summary(self) -> int:
        """Print validation summary and return exit code."""
        print("\n" + "=" * 60)
        print("DEPLOYMENT VALIDATION SUMMARY")
        print("=" * 60)

        passed = sum(1 for _, result, _ in self.checks if result)
        total = len(self.checks)

        print(f"\n✅ Checks Passed: {passed}/{total}")
        for name, result, message in self.checks:
            if result:
                print(f"  ✓ {name}")
            else:
                print(f"  ✗ {name}: {message}")

        if self.warnings:
            print(f"\n⚠️  Warnings ({len(self.warnings)}):")
            for warning in self.warnings:
                print(f"  {warning}")

        if self.errors:
            print(f"\n❌ Errors ({len(self.errors)}):")
            for error in self.errors:
                print(f"  {error}")

        print("\n" + "=" * 60)

        if self.errors:
            print("❌ VALIDATION FAILED - Fix errors above before deploying")
            return 1
        elif self.warnings:
            print("⚠️  VALIDATION PASSED WITH WARNINGS - Review warnings above")
            return 0
        else:
            print("✅ ALL VALIDATION CHECKS PASSED - Ready to deploy!")
            return 0

    def run(self) -> int:
        """Run all validation checks."""
        print("╔" + "=" * 58 + "╗")
        print("║" + " " * 58 + "║")
        print("║  Nexus RAG Pipeline - Deployment Validation Script" + " " * 8 + "║")
        print("║" + " " * 58 + "║")
        print("╚" + "=" * 58 + "╝")

        self.validate_environment_variables()
        self.validate_api_key_lengths()
        self.validate_urls()
        self.validate_environment_setting()
        self.validate_log_level()
        self.validate_cors_origins()
        self.validate_port()
        self.validate_rate_limiting()
        self.validate_files()

        return self.print_summary()


def main():
    """Main entry point."""
    validator = DeploymentValidator()
    exit_code = validator.run()
    sys.exit(exit_code)


if __name__ == "__main__":
    main()
