import json
import csv
import os

def generate_report(data, format="txt", filename="report"):
    report_dir = "reports"
    os.makedirs(report_dir, exist_ok=True)
    report_path = os.path.join(report_dir, f"{filename}.{format}")

    print(f"Generating report in {format} format...")

    if format == "json":
        with open(report_path, "w") as f:
            json.dump(data, f, indent=4)
    elif format == "csv":
        # For CSV, we need to flatten the data. This is a basic flattening.
        # More complex data structures would require a more sophisticated flattening logic.
        with open(report_path, "w", newline="") as f:
            writer = csv.writer(f)
            writer.writerow(["Category", "Finding"])
            for category, findings in data.items():
                if isinstance(findings, list):
                    for item in findings:
                        writer.writerow([category, item])
                elif isinstance(findings, dict):
                    for sub_category, sub_findings in findings.items():
                        writer.writerow([f"{category}_{sub_category}", sub_findings])
                else:
                    writer.writerow([category, findings])
    elif format == "txt":
        with open(report_path, "w") as f:
            f.write("BugHunterPro Scan Report\n")
            f.write("=========================\n\n")
            for category, findings in data.items():
                f.write(f"Category: {category.replace("_", " ").title()}\n")
                f.write("-------------------------\n")
                if isinstance(findings, list):
                    if findings:
                        for item in findings:
                            f.write(f"  - {item}\n")
                    else:
                        f.write("  No findings.\n")
                elif isinstance(findings, dict):
                    if findings:
                        for sub_category, sub_findings in findings.items():
                            f.write(f"  {sub_category.replace("_", " ").title()}: {sub_findings}\n")
                    else:
                        f.write("  No findings.\n")
                else:
                    f.write(f"  {findings}\n")
                f.write("\n")
    print(f"Report generated at {report_path}")

    # Placeholder for integration with bug bounty platforms
    print("\nConsider integrating with platforms like HackerOne or Bugcrowd for direct submission.")
    print("This would typically involve using their APIs to submit findings automatically.")


