import sys
import time

import requests


def check_health():
    try:
        response = requests.get("http://localhost:8000/api/v1/health/health")
        data = response.json()

        if data["status"] == "healthy":
            print(f"✅ Service healthy - Response time: {data['response_time_ms']}ms")
            return True
        else:
            print(
                f"⚠️ Service degraded - Issues with: "
                f"{[s for s, info in data['services'].items() if info['status'] != 'healthy']}"
            )
            return False
    except Exception as e:
        print(f"❌ Health check failed: {e}")
        return False


if __name__ == "__main__":
    while True:
        is_healthy = check_health()
        if not is_healthy and "--exit-on-failure" in sys.argv:
            sys.exit(1)
        time.sleep(60)  # Check every minute
