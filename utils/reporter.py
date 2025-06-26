
# Path: BugHunterPro/utils/reporter.py

import json
import csv

def generate_report(data, format="txt", filename="report"):
    report_path = f"reports/{filename}.{format}"
    # Ensure reports directory exists
    import os
    os.makedirs("reports", exist_ok=True)

    if format == "json":
        with open(report_path, "w") as f:
            json.dump(data, f, indent=4)
    elif format == "csv":
        with open(report_path, "w", newline="") as f:
            writer = csv.writer(f)
            for key, value in data.items():
                writer.writerow([key, value])
    elif format == "txt":
        with open(report_path, "w") as f:
            for key, value in data.items():
                f.write(f"{key}: {value}\n")
    print(f"Report generated at {report_path}")


