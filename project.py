import os
import json
import argparse


def main():
    parser = argparse.ArgumentParser(description="Bookkeeping Assistant")
    parser.add_argument("--year", type=int, required=True, help="Year of financial records to process")
    args = parser.parse_args()

    if not validate_environment(args.year):
        print("Missing required input files. Please check your data directory.")
        return

    rules = load_rules("config/allocation_rules.json")
    run_pipeline(year=args.year, rules=rules)


def validate_environment(year: int) -> bool:
    required_files = [
        f"data/chequing_activity_{year}.csv",
    ]
    # Add credit cards monthly statements if input files exist (to be implemented)
    return all(os.path.isfile(file) for file in required_files)


def load_rules(path: str) -> dict:
    try:
        with open(path, "r") as file:
            return json.load(file)
    except Exception as e:
        print(f"Error loading rules: {e}")
        return {}


def run_pipeline(year: int, rules: dict):
    print(f"Running bookkeeping pipeline for year {year} with rules: {rules}")
    # Placeholder for the actual pipeline logic
    # This would include reading input files, processing transactions, and exporting results


if __name__ == "__main__":
    main()