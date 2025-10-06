#!/usr/bin/env python3

import argparse
import json
import sys
import requests
from urllib.parse import urljoin

def parse_args():
    parser = argparse.ArgumentParser(description="Get architectural debt from LifeTime/Architecture Dashboard")
    parser.add_argument("--app_name", required=True, help="Name of the OutSystems app")
    parser.add_argument("--lifetime_host", required=True, help="Base URL of LifeTime (e.g. https://lt.example.com)")
    parser.add_argument("--token", required=True, help="Personal Access Token or Service Account token")
    parser.add_argument("--output", required=True, help="Output file path for the results (e.g. ./arch-debt.json)")
    return parser.parse_args()

def fetch_app_list(lifetime_host, token):
    url = urljoin(lifetime_host.rstrip('/') + '/', "lifetimeapi/v2/applications")
    print(f"[DEBUG] Fetching applications list from: {url}")

    headers = {
        "Authorization": f"Bearer {token}"
    }

    response = requests.get(url, headers=headers)

    if response.status_code != 200:
        print(f"❌ Failed to fetch application list. HTTP {response.status_code} from {url}")
        sys.exit(1)

    return response.json()

def get_app_by_name(apps, target_name):
    for app in apps:
        if app.get("Name") == target_name:
            return app
    return None

def get_architecture_metrics(app_id, lifetime_host, token):
    url = urljoin(lifetime_host.rstrip('/') + '/', f"architecture-dashboardapi/applications/{app_id}/metrics")
    print(f"[DEBUG] Fetching architecture metrics from: {url}")

    headers = {
        "Authorization": f"Bearer {token}"
    }

    response = requests.get(url, headers=headers)

    if response.status_code != 200:
        print(f"❌ Failed to fetch architecture metrics. HTTP {response.status_code} from {url}")
        sys.exit(1)

    return response.json()

def main():
    args = parse_args()

    print(f"🔍 Fetching application '{args.app_name}' from {args.lifetime_host}...")

    apps = fetch_app_list(args.lifetime_host, args.token)
    app = get_app_by_name(apps, args.app_name)

    if not app:
        print(f"❌ Application '{args.app_name}' not found in LifeTime.")
        sys.exit(1)

    app_id = app.get("Key")
    app_name = app.get("Name")

    print(f"📦 App found: {app_name} (ID: {app_id})")
    print("📊 Fetching architecture metrics...")

    metrics = get_architecture_metrics(app_id, args.lifetime_host, args.token)

    # Adjust these keys if API returns different field names
    result = {
        "application_id": app_id,
        "application_name": app_name,
        "architecture_rating": metrics.get("ArchitectureRating", "N/A"),
        "total_violations": metrics.get("TotalViolations", 0)
    }

    with open(args.output, "w") as f:
        json.dump(result, f, indent=2)

    print(f"✅ Architectural debt data saved to {args.output}")
    print(f"   Rating: {result['architecture_rating']}")
    print(f"   Violations: {result['total_violations']}")

if __name__ == "__main__":
    main()
