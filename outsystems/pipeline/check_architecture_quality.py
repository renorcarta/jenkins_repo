#!/usr/bin/env python3
import json
import sys
import os

def main():
    artifacts_folder = "Artifacts"  # Or make this an argument/env variable
    file_path = os.path.join(artifacts_folder, "arch-debt.json")

    try:
        with open(file_path) as f:
            data = json.load(f)
    except FileNotFoundError:
        print(f"❌ File not found: {file_path}")
        sys.exit(1)
    except json.JSONDecodeError:
        print(f"❌ Invalid JSON in file: {file_path}")
        sys.exit(1)

    rating = data.get("architecture_rating", "").upper()
    violations = int(data.get("total_violations", 0))

    # Set your thresholds here or pass them as args/env
    min_rating = "B"
    max_violations = 5

    rating_order = ["A", "B", "C", "D", "E", "F"]

    if rating not in rating_order:
        print(f"❌ Unknown rating format: {rating}")
        sys.exit(1)

    if rating_order.index(rating) > rating_order.index(min_rating) or violations > max_violations:
        print(f"❌ Failed architecture quality gate.")
        print(f"    Rating: {rating} (required minimum: {min_rating})")
        print(f"    Violations: {violations} (max allowed: {max_violations})")
        sys.exit(1)

    print(f"✅ Architecture check passed.")
    print(f"    Rating: {rating}")
    print(f"    Violations: {violations}")

if __name__ == "__main__":
    main()
