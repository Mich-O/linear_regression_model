"""Print aggregate checks for the original Nara cohort CSV."""

import argparse
import csv
import hashlib
from collections import Counter
from decimal import Decimal
from pathlib import Path

SOURCE_MD5 = "46ebf76abb3fcba1696c483945af4b23"
FEATURES = (
    "adm_age", "adm_kg", "adm_cm", "adm_muac",
    "adm_sex", "adm_oedema_YN", "adm_referral", "adm_whz06",
)
TARGET = "recovered_los"


def missing(value):
    return value.strip() in {"", ".", "NA"}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("csv_path", type=Path)
    path = parser.parse_args().csv_path
    with path.open("rb") as source:
        checksum = hashlib.file_digest(source, "md5").hexdigest()
    if checksum != SOURCE_MD5:
        parser.error("CSV checksum differs from the original Zenodo file")

    with path.open(encoding="utf-8-sig", newline="") as source:
        reader = csv.DictReader(source)
        rows = list(reader)
        columns = reader.fieldnames

    ids = {row["AnonID"] for row in rows}
    recovered = [row for row in rows if row["cured"] == "1"]
    health_centres = [row for row in rows if row["adm_site"] == "Health Center"]
    recovered_hc = [row for row in recovered if row["adm_site"] == "Health Center"]
    cohort = [
        row for row in recovered_hc
        if not missing(row[TARGET]) and Decimal(row[TARGET]) > 0
    ]
    complete = [
        row for row in cohort if all(not missing(row[field]) for field in FEATURES)
    ]
    durations = [Decimal(row[TARGET]) for row in cohort]

    print(f"Source MD5: {checksum}")
    print(f"Rows: {len(rows)}, columns: {len(columns)}, unique IDs: {len(ids)}")
    for site in sorted({row["adm_site"] for row in recovered}):
        site_rows = [row for row in recovered if row["adm_site"] == site]
        missing_height = sum(missing(row["adm_cm"]) for row in site_rows)
        print(f"{site}: {missing_height}/{len(site_rows)} recovered cases missing height")
    print(f"Recovered health-centre cases with positive duration: {len(cohort)}/{len(recovered_hc)}")
    print(f"Target range: {min(durations)} to {max(durations)} days")
    print(f"Fractional durations: {sum(day % 1 != 0 for day in durations)}")
    print("Missing fields:", {field: sum(missing(row[field]) for row in cohort)
                              for field in FEATURES})
    print(f"Complete with original fields: {sum(all(not missing(row[field]) for field in FEATURES[:-1]) for row in cohort)}")
    print(f"Complete with revised fields: {len(complete)}")
    for field in ("adm_sex", "adm_oedema_YN", "adm_referral"):
        print(f"{field}: {dict(sorted(Counter(row[field] for row in cohort).items()))}")
    print("Health-centre transfer flags by (cured, transfer_inpatient):",
          dict(sorted(Counter((row["cured"], row["transfer_inpatient"])
                              for row in health_centres).items())))
    print("Transfer flags in complete revised cohort:",
          dict(sorted(Counter(row["transfer_inpatient"] for row in complete).items())))


if __name__ == "__main__":
    main()
