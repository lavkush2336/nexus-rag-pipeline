#!/usr/bin/env python3
"""
Nexus RAG Pipeline - Health Check Monitoring Script

Monitors the health endpoint continuously and provides detailed diagnostics.
Usage: python health_monitor.py [service_url] [interval_seconds]
"""

import sys
import time
import json
import requests
from datetime import datetime
from typing import Optional, Dict, Any


class HealthMonitor:
    """Monitors application health with detailed diagnostics."""

    def __init__(self, service_url: str, check_interval: int = 30):
        self.service_url = service_url.rstrip("/")
        self.health_endpoint = f"{self.service_url}/health"
        self.check_interval = check_interval
        self.check_count = 0
        self.success_count = 0
        self.failure_count = 0
        self.last_health_status = None

    def check_health(self) -> Optional[Dict[str, Any]]:
        """Fetch and parse health status."""
        try:
            response = requests.get(self.health_endpoint, timeout=10)
            health_data = response.json()
            return {
                "status_code": response.status_code,
                "data": health_data,
                "timestamp": datetime.now(),
                "success": response.status_code in [200, 503],
            }
        except requests.exceptions.RequestException as e:
            return {
                "status_code": None,
                "data": None,
                "timestamp": datetime.now(),
                "success": False,
                "error": str(e),
            }

    def format_health_output(self, health: Dict[str, Any]) -> str:
        """Format health check output."""
        output = []
        timestamp = health["timestamp"].strftime("%Y-%m-%d %H:%M:%S")
        output.append(f"\n[{timestamp}] Health Check #{self.check_count}")
        output.append("=" * 70)

        if not health["success"] or health["status_code"] is None:
            output.append(f"❌ ERROR: {health.get('error', 'Unknown error')}")
            self.failure_count += 1
        else:
            data = health["data"]
            status = data.get("status", "unknown")

            if health["status_code"] == 200:
                output.append(f"✅ Status: {status.upper()}")
                self.success_count += 1
            elif health["status_code"] == 503:
                output.append(f"⚠️  Status: {status.upper()} (Degraded)")
                self.failure_count += 1
            else:
                output.append(f"❓ Status: {status.upper()}")

            # Dependency checks
            checks = data.get("checks", {})
            output.append("\nDependency Checks:")
            output.append(f"  Gemini API: {'✅' if checks.get('gemini_api_available') else '❌'}")
            output.append(f"  Elasticsearch: {'✅' if checks.get('elasticsearch_reachable') else '❌'}")
            if checks.get("elasticsearch_latency_ms"):
                output.append(f"  ES Latency: {checks['elasticsearch_latency_ms']}ms")

            # Configuration
            config = data.get("configuration", {})
            if config:
                output.append("\nConfiguration:")
                output.append(f"  Environment: {config.get('environment')}")
                output.append(f"  Model: {config.get('gemini_model')}")
                output.append(f"  Index: {config.get('elasticsearch_index')}")

        # Statistics
        output.append(f"\nStatistics: {self.success_count} successful, {self.failure_count} failed")

        return "\n".join(output)

    def run(self) -> None:
        """Run continuous health monitoring."""
        print("╔" + "=" * 68 + "╗")
        print("║" + " " * 68 + "║")
        print("║  Nexus RAG Pipeline - Health Check Monitor" + " " * 26 + "║")
        print("║" + " " * 68 + "║")
        print(f"║  Service: {self.service_url:<58}║")
        print(f"║  Check Interval: {self.check_interval} seconds" + " " * 47 + "║")
        print("║" + " " * 68 + "║")
        print("║  Press Ctrl+C to stop monitoring" + " " * 34 + "║")
        print("╚" + "=" * 68 + "╝")

        try:
            while True:
                self.check_count += 1
                health = self.check_health()
                print(self.format_health_output(health))
                time.sleep(self.check_interval)

        except KeyboardInterrupt:
            self.print_summary()

    def print_summary(self) -> None:
        """Print monitoring summary on exit."""
        print("\n" + "=" * 70)
        print("MONITORING SUMMARY")
        print("=" * 70)
        print(f"Total Checks: {self.check_count}")
        print(f"Successful: {self.success_count} ({self.success_count/max(1, self.check_count)*100:.1f}%)")
        print(f"Failed: {self.failure_count} ({self.failure_count/max(1, self.check_count)*100:.1f}%)")
        print("=" * 70)


def main():
    """Main entry point."""
    service_url = sys.argv[1] if len(sys.argv) > 1 else "http://localhost:8000"
    check_interval = int(sys.argv[2]) if len(sys.argv) > 2 else 30

    monitor = HealthMonitor(service_url, check_interval)
    try:
        monitor.run()
    except Exception as e:
        print(f"Error: {e}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
