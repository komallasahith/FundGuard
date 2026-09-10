import requests
import json
import csv
import time
from pathlib import Path
from concurrent.futures import ThreadPoolExecutor, as_completed

BASE_DIR = Path(__file__).resolve().parent.parent
RAW_DIR = BASE_DIR / "data" / "raw"
PROCESSED_DIR = BASE_DIR / "data" / "processed"

BASE_URL = "https://mplads.mospi.gov.in/rest/PreLoginDashboardData"

STATE_ID = 129
HOUSE = 2

WORK_KEYS = [
    "Works Recommended",
    "Works Sanctioned",
    "Works Completed",
    "Expenditure on Completed and On-going Works as on Date",
]

MAX_WORKERS = 20

session = requests.Session()
session.headers.update({
    "Accept": "application/json, text/javascript, */*; q=0.01",
    "Content-Type": "application/json",
    "User-Agent": "Mozilla/5.0",
})


def post(endpoint, payload):
    url = f"{BASE_URL}/{endpoint}"

    try:
        r = session.post(url, json=payload, timeout=30)
        r.raise_for_status()
        return r.json()
    except Exception as e:
        print(f"ERROR {endpoint}: {e}")
        return None


# ------------------------------------------------------------
# GET STATES
# ------------------------------------------------------------

def get_states():
    data = post("getStateData", {})

    if isinstance(data, list):
        return data

    # Sometimes API may wrap the list
    if isinstance(data, dict):
        for value in data.values():
            if isinstance(value, list):
                return value

    return []


# ------------------------------------------------------------
# GET CONSTITUENCIES
# ------------------------------------------------------------

def get_constituencies(state_id):
    data = post(
        "getConstituencyData",
        {"id": str(state_id)}
    )

    if isinstance(data, list):
        return data

    if isinstance(data, dict):
        for value in data.values():
            if isinstance(value, list):
                return value

    return []


# ------------------------------------------------------------
# GET MPS
# ------------------------------------------------------------

def get_mps(state_id):
    data = post(
        "getMpNamesData",
        {"state_combo": f"{state_id},{HOUSE},"}
    )

    if isinstance(data, list):
        return data

    if isinstance(data, dict):
        for value in data.values():
            if isinstance(value, list):
                return value

    return []


# ------------------------------------------------------------
# TEST ONE MP + CONSTITUENCY
# ------------------------------------------------------------

def test_combination(mp, constituency):

    mp_id = mp["ID"]
    mp_name = str(mp["CAPTION"]).strip()

    constituency_id = constituency["ID"]
    constituency_name = str(constituency["CAPTION"]).strip()

    combo = f"{STATE_ID},{constituency_id},{mp_id},{HOUSE}"

    # Only one lightweight endpoint for discovery
    data = post(
        "getTilesReportData",
        {
            "combo": combo,
            "key": "Works Recommended"
        }
    )

    if not data:
        return None

    # API returns JSON strings inside outer JSON
    records = []

    if isinstance(data, dict):
        for value in data.values():

            if isinstance(value, str):
                try:
                    parsed = json.loads(value)
                except:
                    continue

            elif isinstance(value, list):
                parsed = value

            else:
                continue

            if isinstance(parsed, list):
                records.extend(parsed)

    # Validate that returned records really belong to this MP
    for record in records:

        if not isinstance(record, dict):
            continue

        returned_mp = str(record.get("MP_NAME", "")).strip()
        returned_const_id = record.get("CONSTITUENCY_ID")

        try:
            returned_const_id = int(float(returned_const_id))
        except:
            continue

        if (
            returned_mp.lower() == mp_name.lower()
            and returned_const_id == constituency_id
        ):
            return {
                "state_id": STATE_ID,
                "mp_id": mp_id,
                "mp_name": mp_name,
                "constituency_id": constituency_id,
                "constituency": constituency_name,
                "combo": combo
            }

    return None


# ------------------------------------------------------------
# DISCOVER VALID MAPPINGS IN PARALLEL
# ------------------------------------------------------------

def discover_mappings(mps, constituencies):

    combinations = [
        (mp, constituency)
        for mp in mps
        for constituency in constituencies
    ]

    print(f"\nTesting {len(combinations)} combinations")
    print(f"Using {MAX_WORKERS} parallel workers...\n")

    valid = []

    completed = 0

    with ThreadPoolExecutor(max_workers=MAX_WORKERS) as executor:

        futures = [
            executor.submit(test_combination, mp, constituency)
            for mp, constituency in combinations
        ]

        for future in as_completed(futures):

            completed += 1

            result = future.result()

            if result:
                valid.append(result)

                print(
                    f"[FOUND] {result['mp_name']} "
                    f"-> {result['constituency']}"
                )

            if completed % 25 == 0:
                print(
                    f"Progress: {completed}/{len(combinations)}"
                )

    # Remove duplicates
    unique = {}

    for item in valid:
        unique[item["mp_id"]] = item

    return list(unique.values())


# ------------------------------------------------------------
# COLLECT WORK DATA
# ------------------------------------------------------------

def collect_work_data(mapping):

    all_records = []

    mp_name = mapping["mp_name"]
    mp_id = mapping["mp_id"]
    constituency_id = mapping["constituency_id"]

    combo = mapping["combo"]

    print(
        f"\nCollecting: {mp_name} -> "
        f"{mapping['constituency']}"
    )

    for key in WORK_KEYS:

        data = post(
            "getTilesReportData",
            {
                "combo": combo,
                "key": key
            }
        )

        if not data:
            continue

        records = []

        if isinstance(data, dict):

            for value in data.values():

                if isinstance(value, str):
                    try:
                        parsed = json.loads(value)
                    except:
                        continue

                elif isinstance(value, list):
                    parsed = value

                else:
                    continue

                if isinstance(parsed, list):
                    records.extend(parsed)

        count = 0

        for record in records:

            if not isinstance(record, dict):
                continue

            # Ignore summary rows
            if "WORK_ID" not in record and \
               "WORK_RECOMMENDATION_DTL_ID" not in record:
                continue

            record["_SOURCE_KEY"] = key
            record["_MP_ID"] = mp_id
            record["_MP_NAME"] = mp_name
            record["_CONSTITUENCY_ID"] = constituency_id
            record["_CONSTITUENCY"] = mapping["constituency"]

            all_records.append(record)
            count += 1

        print(f"  {key}: {count} records")

    return all_records


# ------------------------------------------------------------
# SAVE RAW JSON
# ------------------------------------------------------------

def save_raw(records):

    RAW_DIR.mkdir(parents=True, exist_ok=True)

    path = RAW_DIR / "mplads_all_works.json"

    with open(path, "w", encoding="utf-8") as f:
        json.dump(
            records,
            f,
            indent=2,
            ensure_ascii=False,
            default=str
        )

    print(f"\nRaw data saved: {path}")


# ------------------------------------------------------------
# SAVE CSV
# ------------------------------------------------------------

def save_csv(records):

    PROCESSED_DIR.mkdir(parents=True, exist_ok=True)

    path = PROCESSED_DIR / "mplads_works_raw_combined.csv"

    if not records:
        print("No records to save.")
        return

    # Union of all fields
    columns = set()

    for record in records:
        columns.update(record.keys())

    columns = sorted(columns)

    with open(
        path,
        "w",
        newline="",
        encoding="utf-8-sig"
    ) as f:

        writer = csv.DictWriter(
            f,
            fieldnames=columns,
            extrasaction="ignore"
        )

        writer.writeheader()

        for record in records:
            writer.writerow(record)

    print(f"CSV saved: {path}")
    print(f"Raw records: {len(records):,}")


# ------------------------------------------------------------
# DEDUPLICATE WORKS
# ------------------------------------------------------------

def build_work_level(records):

    unique = {}

    for record in records:

        work_id = (
            record.get("WORK_RECOMMENDATION_DTL_ID")
            or record.get("WORK_ID")
        )

        if not work_id:
            continue

        # Keep one work-level record.
        # Prefer records containing sanction information.
        existing = unique.get(str(work_id))

        if existing is None:
            unique[str(work_id)] = record
            continue

        existing_score = sum(
            1 for field in [
                "SANCTION_AMOUNT",
                "ACTUAL_AMOUNT",
                "SANCTION_DATE",
                "ACTUAL_END_DATE",
                "WORK_STAGE"
            ]
            if existing.get(field) not in [None, "", "nan"]
        )

        new_score = sum(
            1 for field in [
                "SANCTION_AMOUNT",
                "ACTUAL_AMOUNT",
                "SANCTION_DATE",
                "ACTUAL_END_DATE",
                "WORK_STAGE"
            ]
            if record.get(field) not in [None, "", "nan"]
        )

        if new_score > existing_score:
            unique[str(work_id)] = record

    work_records = list(unique.values())

    path = PROCESSED_DIR / "mplads_work_level.csv"

    if work_records:

        columns = set()

        for record in work_records:
            columns.update(record.keys())

        columns = sorted(columns)

        with open(
            path,
            "w",
            newline="",
            encoding="utf-8-sig"
        ) as f:

            writer = csv.DictWriter(
                f,
                fieldnames=columns,
                extrasaction="ignore"
            )

            writer.writeheader()

            writer.writerows(work_records)

    print(
        f"\nUnique works: {len(work_records):,}"
    )

    print(f"Work-level dataset saved: {path}")


# ------------------------------------------------------------
# MAIN
# ------------------------------------------------------------

def main():

    start = time.time()

    print("=" * 70)
    print("FUNDGUARD - FAST MPLADS COLLECTOR")
    print("=" * 70)

    # 1. States
    print("\n[1/5] Getting states...")
    states = get_states()

    print(f"States available: {len(states)}")

    # 2. Telangana constituencies
    print("\n[2/5] Getting Telangana constituencies...")
    constituencies = get_constituencies(STATE_ID)

    print(
        f"Telangana constituencies: "
        f"{len(constituencies)}"
    )

    # 3. Telangana MPs
    print("\n[3/5] Getting Telangana MPs...")
    mps = get_mps(STATE_ID)

    print(f"Telangana MPs returned: {len(mps)}")

    # Filter obvious Rajya Sabha MPs
    # For Lok Sabha data, the MP list should correspond
    # to parliamentary constituencies. We don't blindly
    # assume every returned MP belongs to a constituency.
    print("\nMPs:")
    for mp in mps:
        print(
            f"  {mp['ID']} - "
            f"{mp['CAPTION']}"
        )

    # 4. Discover mappings
    print("\n[4/5] Discovering valid MP -> constituency mappings...")

    mappings = discover_mappings(
        mps,
        constituencies
    )

    print("\n" + "=" * 70)
    print("VALID MAPPINGS FOUND")
    print("=" * 70)

    for m in mappings:
        print(
            f"{m['mp_name']} -> "
            f"{m['constituency']} "
            f"(ID {m['constituency_id']})"
        )

    mapping_path = (
        PROCESSED_DIR /
        "mp_constituency_mapping.json"
    )

    with open(
        mapping_path,
        "w",
        encoding="utf-8"
    ) as f:

        json.dump(
            mappings,
            f,
            indent=4,
            ensure_ascii=False
        )

    # 5. Collect actual data
    print("\n[5/5] Collecting work data...")

    all_records = []

    for mapping in mappings:

        records = collect_work_data(mapping)

        all_records.extend(records)

    print("\n" + "=" * 70)
    print("COLLECTION COMPLETE")
    print("=" * 70)

    print(
        f"Total downloaded records: "
        f"{len(all_records):,}"
    )

    save_raw(all_records)
    save_csv(all_records)
    build_work_level(all_records)

    elapsed = time.time() - start

    print(
        f"\nCompleted in "
        f"{elapsed:.1f} seconds"
    )


if __name__ == "__main__":
    main()