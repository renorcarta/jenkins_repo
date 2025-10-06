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

def get_architecture_metrics_from_overview(app_name, arch_dashboard_host, token):
    url = f"{arch_dashboard_host}/MentorStudio/Overview?TeamId=0"
    headers = {
        "Authorization": f"Bearer {token}",
        "User-Agent": "Mozilla/5.0"
    }

    print(f"[DEBUG] Requesting Overview page: {url}")
    response = requests.get(url, headers=headers)
    if response.status_code != 200:
        print(f"❌ Failed to fetch overview page. HTTP {response.status_code}")
        print(f"➡️ Response content:\n{response.text}")
        sys.exit(1)

    soup = BeautifulSoup(response.text, "html.parser")

    # Step 1: read the selected app(s) from the multiselect label
    selected_label = soup.select_one(".multiselect-label.has-selected-opts")
    selected_text = None
    if selected_label:
        selected_text = selected_label.get_text(strip=True)
        print(f"[DEBUG] Found selected application label: '{selected_text}'")
    else:
        print("[WARN] Could not find multiselect-label.has-selected-opts element for app name.")
        selected_text = app_name  # fallback to the passed app_name

    # Normalize names for matching
    norm_selected = selected_text.replace("-", "").lower() if selected_text else app_name.replace("-", "").lower()

    # Now find the “card” or UI block for that application
    # This depends on how the Overview page structures each application card
    # e.g. maybe each card has class "card" or "app-card"
    app_cards = soup.find_all("div", class_="card")
    target_card = None

    for card in app_cards:
        # Try to find a title or label inside the card for the application
        title_elem = card.find(class_="card-title") or card.find("h3")  # or whatever the structure is
        if title_elem:
            title_text = title_elem.get_text(strip=True).replace("-", "").lower()
            if title_text == norm_selected:
                target_card = card
                break

    if not target_card:
        print(f"❌ Could not find card for application matching '{norm_selected}' in overview.")
        sys.exit(1)

    # Now scrape fields inside that target_card
    # Rating
    rating_elem = target_card.select_one(".architecture-rating")  # adjust class
    architecture_rating = rating_elem.get_text(strip=True) if rating_elem else "N/A"

    # Violations
    violations_elem = target_card.select_one(".total-violations")
    total_violations = int(violations_elem.get_text(strip=True)) if violations_elem else 0

    # Technical debt %
    tech_debt_elem = target_card.find("div", class_="ph card card-content padding-base shadow-level-0 white-space-nowrap")
    technical_debt_percent = tech_debt_elem.get_text(strip=True) if tech_debt_elem else "N/A"

    # Scores
    scores = []
    scores_container = target_card.select_one("div.columns.columns3.gutter-base.tablet-break-none.phone-break-none.margin-y-base")
    if scores_container:
        for child in scores_container.find_all(recursive=False):
            text = child.get_text(strip=True)
            if text:
                scores.append(text)

    return {
        "ArchitectureRating": architecture_rating,
        "TotalViolations": total_violations,
        "TechnicalDebtPercent": technical_debt_percent,
        "Scores": scores,
        "SelectedApplicationName": selected_text
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

    metrics = get_architecture_metrics_from_overview(
        args.app_name, args.arch_dashboard_host, args.token
    )

    result = {
        "application_id": app_id,
        "application_name": app_name,
        "architecture_rating": metrics.get("ArchitectureRating", "N/A"),
        "total_violations": metrics.get("TotalViolations", 0),
        "technical_debt_percent": metrics.get("TechnicalDebtPercent", "N/A"),
        "scores": metrics.get("Scores", [])
    }

    # Ensure output directory exists before writing
    output_dir = os.path.dirname(args.output)
    if output_dir and not os.path.exists(output_dir):
        os.makedirs(output_dir)

    with open(args.output, "w") as f:
        json.dump(result, f, indent=2)

    print(f"✅ Architectural debt data saved to {args.output}")
    print(f"   Rating: {result['architecture_rating']}")
    print(f"   Violations: {result['total_violations']}")
    print(f"   Technical Debt %: {result['technical_debt_percent']}")
    print(f"   Scores: {result['scores']}")

if __name__ == "__main__":
    main()
