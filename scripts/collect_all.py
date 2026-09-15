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
HOUSE = 2

WORK_KEYS = [
    "Works Recommended",
    "Works Sanctioned",
    "Works Completed",
    "Expenditure on Completed and On-going Works as on Date",
]

MAX_WORKERS = 20
REQUEST_TIMEOUT = 30
MAX_RETRIES = 3

session = requests.Session()
session.headers.update({
    "Accept": "application/json, text/javascript, */*; q=0.01",
    "Content-Type": "application/json",
    "User-Agent": "Mozilla/5.0",
})


# ============================================================
# API REQUEST
# ============================================================

def post(endpoint, payload):

    url = f"{BASE_URL}/{endpoint}"

    for attempt in range(1, MAX_RETRIES + 1):

        try:
            response = session.post(
                url,
                json=payload,
                timeout=REQUEST_TIMEOUT
            )

            response.raise_for_status()
            return response.json()

        except Exception as e:

            if attempt == MAX_RETRIES:
                print(
                    f"ERROR {endpoint}: {e}"
                )
                return None

            time.sleep(attempt)


# ============================================================
# EXTRACT LIST FROM API RESPONSE
# ============================================================

def extract_records(data):

    if isinstance(data, list):
        return data

    if isinstance(data, dict):

        records = []

        for value in data.values():

            if isinstance(value, str):

                try:
                    parsed = json.loads(value)
                except Exception:
                    continue

            elif isinstance(value, list):
                parsed = value

            else:
                continue

            if isinstance(parsed, list):
                records.extend(parsed)

        return records

    return []


# ============================================================
# GET STATES
# ============================================================

def get_states():

    data = post(
        "getStateData",
        {}
    )

    return extract_records(data)


# ============================================================
# GET CONSTITUENCIES
# ============================================================

def get_constituencies(state_id):

    data = post(
        "getConstituencyData",
        {
            "id": str(state_id)
        }
    )

    return extract_records(data)


# ============================================================
# GET MPS
# ============================================================

def get_mps(state_id):

    data = post(
        "getMpNamesData",
        {
            "state_combo": f"{state_id},{HOUSE},"
        }
    )

    return extract_records(data)


# ============================================================
# TEST MP + CONSTITUENCY
# ============================================================

def test_combination(state, mp, constituency):

    state_id = state["STATE_ID"]
    state_name = state["STATE_NAME"]

    mp_id = mp.get("ID")
    mp_name = str(
        mp.get("CAPTION", "")
    ).strip()

    constituency_id = constituency.get("ID")
    constituency_name = str(
        constituency.get("CAPTION", "")
    ).strip()

    if not mp_id or not constituency_id:
        return None

    combo = (
        f"{state_id},"
        f"{constituency_id},"
        f"{mp_id},"
        f"{HOUSE}"
    )

    data = post(
        "getTilesReportData",
        {
            "combo": combo,
            "key": "Works Recommended"
        }
    )

    records = extract_records(data)

    if not records:
        return None

    for record in records:

        if not isinstance(record, dict):
            continue

        returned_mp = str(
            record.get("MP_NAME", "")
        ).strip()

        returned_const_id = (
            record.get("CONSTITUENCY_ID")
        )

        try:
            returned_const_id = int(
                float(returned_const_id)
            )
        except Exception:
            continue

        if (
            returned_mp.lower()
            == mp_name.lower()
            and returned_const_id
            == int(constituency_id)
        ):

            return {
                "state_id": state_id,
                "state_name": state_name,
                "mp_id": mp_id,
                "mp_name": mp_name,
                "constituency_id": constituency_id,
                "constituency": constituency_name,
                "combo": combo
            }

    return None


# ============================================================
# DISCOVER VALID MAPPINGS
# ============================================================

def discover_mappings(
    state,
    mps,
    constituencies
):

    combinations = [
        (mp, constituency)
        for mp in mps
        for constituency in constituencies
    ]

    if not combinations:
        return []

    print(
        f"  Testing "
        f"{len(combinations):,} MP/constituency combinations..."
    )

    valid = []

    completed = 0

    with ThreadPoolExecutor(
        max_workers=MAX_WORKERS
    ) as executor:

        futures = [
            executor.submit(
                test_combination,
                state,
                mp,
                constituency
            )
            for mp, constituency in combinations
        ]

        for future in as_completed(futures):

            completed += 1

            try:
                result = future.result()
            except Exception:
                result = None

            if result:
                valid.append(result)

                print(
                    f"    [FOUND] "
                    f"{result['mp_name']} "
                    f"-> {result['constituency']}"
                )

            if (
                completed % 100 == 0
                or completed == len(combinations)
            ):
                print(
                    f"    Progress: "
                    f"{completed:,}/"
                    f"{len(combinations):,}"
                )

    # Deduplicate by MP + constituency
    unique = {}

    for item in valid:

        key = (
            item["mp_id"],
            item["constituency_id"]
        )

        unique[key] = item

    return list(unique.values())


# ============================================================
# COLLECT WORK DATA FOR ONE MAPPING
# ============================================================

def collect_work_data(mapping):

    all_records = []

    state_id = mapping["state_id"]
    state_name = mapping["state_name"]

    mp_id = mapping["mp_id"]
    mp_name = mapping["mp_name"]

    constituency_id = mapping["constituency_id"]
    constituency_name = mapping["constituency"]

    combo = mapping["combo"]

    print(
        f"    Collecting: "
        f"{mp_name} -> {constituency_name}"
    )

    for source_key in WORK_KEYS:

        data = post(
            "getTilesReportData",
            {
                "combo": combo,
                "key": source_key
            }
        )

        records = extract_records(data)

        count = 0

        for record in records:

            if not isinstance(record, dict):
                continue

            # Ignore summary/non-work rows
            if (
                "WORK_ID" not in record
                and
                "WORK_RECOMMENDATION_DTL_ID"
                not in record
            ):
                continue

            # Preserve source information
            record["_SOURCE_KEY"] = source_key

            # State
            record["_STATE_ID"] = state_id
            record["_STATE_NAME"] = state_name

            # MP
            record["_MP_ID"] = mp_id
            record["_MP_NAME"] = mp_name

            # Constituency
            record["_CONSTITUENCY_ID"] = constituency_id
            record["_CONSTITUENCY"] = constituency_name

            all_records.append(record)

            count += 1

        print(
            f"      {source_key}: "
            f"{count:,}"
        )

    return all_records


# ============================================================
# SAVE RAW JSON
# ============================================================

def save_raw(records):

    RAW_DIR.mkdir(
        parents=True,
        exist_ok=True
    )

    path = (
        RAW_DIR /
        "mplads_all_works.json"
    )

    with open(
        path,
        "w",
        encoding="utf-8"
    ) as f:

        json.dump(
            records,
            f,
            indent=2,
            ensure_ascii=False,
            default=str
        )

    print(
        f"\nRaw data saved:"
        f"\n{path}"
    )


# ============================================================
# SAVE CSV
# ============================================================

def save_csv(records):

    PROCESSED_DIR.mkdir(
        parents=True,
        exist_ok=True
    )

    path = (
        PROCESSED_DIR /
        "mplads_works_raw_combined.csv"
    )

    if not records:
        print("No records to save.")
        return

    columns = set()

    for record in records:
        columns.update(
            record.keys()
        )

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

        writer.writerows(records)

    print(
        f"\nCSV saved:"
        f"\n{path}"
    )

    print(
        f"Raw records: "
        f"{len(records):,}"
    )


# ============================================================
# BUILD WORK-LEVEL DATASET
# ============================================================

def build_work_level(records):

    unique = {}

    for record in records:

        work_key = (
            record.get(
                "WORK_RECOMMENDATION_DTL_ID"
            )
            or
            record.get("WORK_ID")
        )

        if not work_key:
            continue

        work_key = str(work_key)

        existing = unique.get(
            work_key
        )

        if existing is None:

            unique[work_key] = record
            continue

        important_fields = [
            "SANCTION_AMOUNT",
            "ACTUAL_AMOUNT",
            "SANCTION_DATE",
            "ACTUAL_END_DATE",
            "WORK_STAGE"
        ]

        existing_score = sum(
            1
            for field in important_fields
            if existing.get(field)
            not in [None, "", "nan"]
        )

        new_score = sum(
            1
            for field in important_fields
            if record.get(field)
            not in [None, "", "nan"]
        )

        if new_score > existing_score:
            unique[work_key] = record

    work_records = list(
        unique.values()
    )

    # IMPORTANT:
    # This is only a collection-stage output.
    # Later pipeline scripts will create the
    # final work master.

    path = (
        PROCESSED_DIR /
        "india_work_collection.csv"
    )

    if work_records:

        columns = set()

        for record in work_records:
            columns.update(
                record.keys()
            )

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
        f"\nUnique works collected: "
        f"{len(work_records):,}"
    )

    print(
        f"Collection-level dataset:"
        f"\n{path}"
    )


# ============================================================
# SAVE MAPPINGS
# ============================================================

def save_mappings(mappings):

    PROCESSED_DIR.mkdir(
        parents=True,
        exist_ok=True
    )

    path = (
        PROCESSED_DIR /
        "india_mp_constituency_mapping.json"
    )

    with open(
        path,
        "w",
        encoding="utf-8"
    ) as f:

        json.dump(
            mappings,
            f,
            indent=4,
            ensure_ascii=False
        )

    print(
        f"\nMappings saved:"
        f"\n{path}"
    )


# ============================================================
# MAIN
# ============================================================

def main():

    start = time.time()

    print("=" * 70)
    print("FUNDGUARD - INDIA-WIDE MPLADS COLLECTOR")
    print("=" * 70)

    # --------------------------------------------------------
    # 1. GET STATES
    # --------------------------------------------------------

    print("\n[1/4] Getting states...")

    states = get_states()

    if not states:

        print(
            "ERROR: No states returned by API."
        )

        return

    print(
        f"States available: "
        f"{len(states)}"
    )

    # --------------------------------------------------------
    # 2. DISCOVER ALL MAPPINGS
    # --------------------------------------------------------

    print(
        "\n[2/4] Discovering "
        "MP -> constituency mappings..."
    )

    all_mappings = []

    for index, state in enumerate(
        states,
        start=1
    ):

        state_id = state.get(
            "STATE_ID"
        )

        state_name = state.get(
            "STATE_NAME"
        )

        if not state_id or not state_name:
            continue

        print(
            f"\n[{index}/{len(states)}] "
            f"{state_name} "
            f"(ID {state_id})"
        )

        constituencies = (
            get_constituencies(
                state_id
            )
        )

        mps = get_mps(
            state_id
        )

        print(
            f"  Constituencies: "
            f"{len(constituencies)}"
        )

        print(
            f"  MPs returned: "
            f"{len(mps)}"
        )

        if not constituencies:
            print(
                "  No constituencies. "
                "Skipping."
            )
            continue

        if not mps:
            print(
                "  No MPs. Skipping."
            )
            continue

        mappings = discover_mappings(
            state,
            mps,
            constituencies
        )

        print(
            f"  Valid mappings: "
            f"{len(mappings)}"
        )

        all_mappings.extend(
            mappings
        )

    # --------------------------------------------------------
    # REMOVE DUPLICATE MAPPINGS
    # --------------------------------------------------------

    unique_mappings = {}

    for mapping in all_mappings:

        key = (
            mapping["state_id"],
            mapping["mp_id"],
            mapping["constituency_id"]
        )

        unique_mappings[key] = mapping

    all_mappings = list(
        unique_mappings.values()
    )

    print(
        "\nTotal valid MP/constituency "
        f"mappings: {len(all_mappings):,}"
    )

    save_mappings(
        all_mappings
    )

    # --------------------------------------------------------
    # 3. COLLECT ALL WORKS
    # --------------------------------------------------------

    print(
        "\n[3/4] Collecting MPLADS work data..."
    )

    all_records = []

    for index, mapping in enumerate(
        all_mappings,
        start=1
    ):

        print(
            f"\nMapping "
            f"{index}/{len(all_mappings)}"
        )

        records = collect_work_data(
            mapping
        )

        all_records.extend(
            records
        )

    print(
        "\nTotal downloaded records: "
        f"{len(all_records):,}"
    )

    # --------------------------------------------------------
    # 4. SAVE
    # --------------------------------------------------------

    print(
        "\n[4/4] Saving India-wide collection..."
    )

    save_raw(
        all_records
    )

    save_csv(
        all_records
    )

    build_work_level(
        all_records
    )

    elapsed = (
        time.time() - start
    )

    print("\n" + "=" * 70)
    print("INDIA-WIDE COLLECTION COMPLETE")
    print("=" * 70)

    print(
        f"States processed: "
        f"{len(states):,}"
    )

    print(
        f"Valid mappings: "
        f"{len(all_mappings):,}"
    )

    print(
        f"Raw records: "
        f"{len(all_records):,}"
    )

    print(
        f"Time: "
        f"{elapsed / 60:.1f} minutes"
    )

    print("=" * 70)


if __name__ == "__main__":
    main()