#!/usr/bin/env python3

import argparse
import json
import sys
import os
import requests
from bs4 import BeautifulSoup

def parse_args():
    parser = argparse.ArgumentParser(description="Get architectural debt from LifeTime and Architecture Dashboard")
    parser.add_argument("--app_name", required=True, help="Name of the OutSystems app")
    parser.add_argument("--artifacts", required=True, help="Path to artifacts folder containing applications.cache")
    parser.add_argument("--lifetime_host", required=True, help="Base URL of LifeTime (e.g. https://lt.example.com)")
    parser.add_argument("--arch_dashboard_host", required=True, help="Base URL of Architecture Dashboard (e.g. https://aimentorstudio.outsystems.com)")
    parser.add_argument("--token", required=True, help="Personal Access Token or Service Account token")
    parser.add_argument("--output", required=True, help="Output file path for the results (e.g. ./arch-debt.json)")
    return parser.parse_args()

def load_applications(artifacts_path):
    apps_path = os.path.join(artifacts_path, "applications.cache")
    if not os.path.isfile(apps_path):
        print(f"❌ Applications file not found at {apps_path}")
        sys.exit(1)

    with open(apps_path, "r") as f:
        try:
            apps = json.load(f)
        except json.JSONDecodeError as e:
            print(f"❌ Failed to parse applications.cache: {e}")
            sys.exit(1)

    return apps

def get_app_by_name(apps, target_name):
    normalized_target = target_name.replace("-", "").lower()
    for app in apps:
        if app.get("Name", "").replace("-", "").lower() == normalized_target:
            return app
    return None

def get_architecture_metrics_from_report(app_id, arch_dashboard_host, token):
    # Construct the URL with ApplicationId param
    url = f"{arch_dashboard_host}/MentorStudio/Report?ApplicationId={app_id}&ModuleId=0&TeamId=0"
    headers = {
        "Authorization": f"Bearer {token}",
        "User-Agent": "Mozilla/5.0"
    }

    print(f"[DEBUG] Requesting Architecture Report page: {url}")

    response = requests.get(url, headers=headers)

    if response.status_code != 200:
        print(f"❌ Failed to fetch architecture report page. HTTP {response.status_code}")
        print(f"➡️ Response content:\n{response.text}")
        sys.exit(1)

    # Parse HTML
    soup = BeautifulSoup(response.text, 'html.parser')

    # You need to inspect the HTML to find where the rating and violations are shown
    # Example placeholders:
    rating_element = soup.find(id="architectureRating")  # Replace with actual selector
    violations_element = soup.find(id="totalViolations")  # Replace with actual selector

    architecture_rating = rating_element.text.strip() if rating_element else "N/A"
    total_violations = int(violations_element.text.strip()) if violations_element else 0

    return {
        "ArchitectureRating": architecture_rating,
        "TotalViolations": total_violations
    }

def main():
    args = parse_args()

    print(f"🔍 Loading applications list from artifacts folder '{args.artifacts}'...")
    apps = load_applications(args.artifacts)

    print(f"🔍 Searching for application '{args.app_name}'...")
    app = get_app_by_name(apps, args.app_name)
    if not app:
        print(f"❌ Application '{args.app_name}' not found in applications.cache")
        sys.exit(1)

    app_id = app.get("Key")
    app_name = app.get("Name")
    print(f"📦 Found application: {app_name} (ID: {app_id})")

    print(f"📊 Fetching architecture metrics for app ID {app_id}...")
    metrics = get_architecture_metrics_from_report(app_id, args.arch_dashboard_host, args.token)

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
