"""
Create two test templates for TTT simulation.
Based on canonical template ttt_v1_0 (3b431689-945b-44d0-89f0-7b32a7f63b47).

Template 1: ttt_test_10 — 10 major powers, no elections, 4 rounds
Template 2: ttt_test_columbia — Columbia full team + 5 HoS, elections, 4 rounds

Idempotent: skips if template code already exists.
"""

import os
import sys
import json
import copy
from pathlib import Path

# Load .env from project root
from dotenv import load_dotenv
env_path = Path(__file__).resolve().parents[4] / ".env"
load_dotenv(env_path)

from supabase import create_client

SUPABASE_URL = os.environ["SUPABASE_URL"]
SUPABASE_SERVICE_ROLE_KEY = os.environ["SUPABASE_SERVICE_ROLE_KEY"]

supabase = create_client(SUPABASE_URL, SUPABASE_SERVICE_ROLE_KEY)

CANONICAL_ID = "3b431689-945b-44d0-89f0-7b32a7f63b47"

# ── Helpers ──────────────────────────────────────────────────────────────

def fetch_canonical():
    """Fetch the canonical template row."""
    resp = supabase.table("sim_templates").select("*").eq("id", CANONICAL_ID).execute()
    if not resp.data:
        print("ERROR: Canonical template not found!")
        sys.exit(1)
    return resp.data[0]


def filter_country_stats(stats: dict, keep: set) -> dict:
    """Keep only countries in `keep` set (plus _note if present)."""
    return {k: v for k, v in stats.items() if k in keep or k == "_note"}


def adjust_organizations(orgs: dict, members_map: dict) -> dict:
    """Set default_members for each org based on members_map."""
    result = copy.deepcopy(orgs)
    for org_code, members in members_map.items():
        if org_code in result:
            result[org_code]["default_members"] = members
    return result


def adjust_schedule(schedule: dict, default_rounds: int) -> dict:
    """Copy schedule but set default_rounds."""
    result = copy.deepcopy(schedule)
    result["default_rounds"] = default_rounds
    return result


def template_exists(code: str) -> bool:
    resp = supabase.table("sim_templates").select("id").eq("code", code).execute()
    return len(resp.data) > 0


def insert_template(data: dict):
    """Insert a template. Returns the inserted row."""
    resp = supabase.table("sim_templates").insert(data).execute()
    return resp.data[0] if resp.data else None


# ── Template 1: ttt_test_10 ─────────────────────────────────────────────

def build_template_10(canonical: dict) -> dict:
    countries_10 = {
        "columbia", "cathay", "sarmatia", "ruthenia", "persia",
        "teutonia", "yamato", "formosa", "solaria", "albion"
    }

    orgs_members = {
        "NATO":       ["columbia", "teutonia", "albion"],
        "OPEC":       ["solaria", "persia", "sarmatia"],
        "UNSC":       ["columbia", "cathay", "sarmatia", "teutonia", "albion"],
        "BRICS":      ["cathay", "sarmatia"],
        "EREB_UNION": ["teutonia", "albion"],
    }

    key_events = [
        {
            "name": "Ereb Union Session",
            "type": "mandatory_meeting",
            "round": 1,
            "subtype": "organization_session",
            "organization": "the_ereb_union"
        },
        {
            "name": "The Cartel Meeting",
            "type": "mandatory_meeting",
            "round": 1,
            "subtype": "organization_session",
            "organization": "the_cartel"
        },
        {
            "name": "Global Security Council Session on Persia Crisis",
            "type": "mandatory_meeting",
            "round": 1,
            "subtype": "organization_session",
            "organization": "the_council"
        },
        {
            "name": "Western Treaty Session",
            "type": "mandatory_meeting",
            "round": 2,
            "subtype": "organization_session",
            "organization": "western_treaty"
        },
    ]

    return {
        "code": "ttt_test_10",
        "name": "Ten Major Powers",
        "version": "1.0",
        "description": "Test template: 10 major powers. Two active wars, Formosa tension, nuclear dynamics, OPEC. No elections. 4 rounds.",
        "status": "published",
        "created_by": "build-team",
        "allowed_round_counts": [4],
        "default_unit_layout_id": canonical["default_unit_layout_id"],
        "map_config": canonical["map_config"],
        "formula_coefficients": canonical["formula_coefficients"],
        "default_role_briefings": canonical["default_role_briefings"],
        "default_relationships": canonical["default_relationships"],
        "default_country_stats": filter_country_stats(canonical["default_country_stats"], countries_10),
        "organizations": adjust_organizations(canonical["organizations"], orgs_members),
        "key_events_defaults": key_events,
        "schedule_defaults": adjust_schedule(canonical["schedule_defaults"], 4),
        "allowed_oil_price_range": canonical.get("allowed_oil_price_range"),
        "allowed_phase_a_duration_range": canonical.get("allowed_phase_a_duration_range"),
        "allowed_theaters": canonical.get("allowed_theaters"),
    }


# ── Template 2: ttt_test_columbia ────────────────────────────────────────

def build_template_columbia(canonical: dict) -> dict:
    countries_columbia = {
        "columbia", "cathay", "sarmatia", "persia", "ruthenia", "teutonia"
    }

    orgs_members = {
        "NATO":       ["columbia", "teutonia"],
        "OPEC":       ["sarmatia", "persia"],
        "UNSC":       ["columbia", "cathay", "sarmatia", "teutonia"],
        "BRICS":      ["cathay", "sarmatia"],
        "EREB_UNION": ["teutonia"],
    }

    key_events = [
        {
            "name": "Global Security Council Session on Persia Crisis",
            "type": "mandatory_meeting",
            "round": 1,
            "subtype": "organization_session",
            "organization": "the_council"
        },
        {
            "name": "Columbia Mid-Term Parliamentary Elections",
            "type": "election",
            "round": 2,
            "subtype": "parliamentary_midterm",
            "country_code": "columbia",
            "nominations_round": 1
        },
        {
            "name": "Western Treaty Session",
            "type": "mandatory_meeting",
            "round": 2,
            "subtype": "organization_session",
            "organization": "western_treaty"
        },
        {
            "name": "Columbia Presidential Election",
            "type": "election",
            "round": 4,
            "subtype": "presidential",
            "country_code": "columbia",
            "nominations_round": 3
        },
    ]

    return {
        "code": "ttt_test_columbia",
        "name": "Columbia Team + World",
        "version": "1.0",
        "description": "Test template: Columbia full team (7 roles) + 5 international HoS. Internal team dynamics, elections at R2 and R4. 4 rounds.",
        "status": "published",
        "created_by": "build-team",
        "allowed_round_counts": [4],
        "default_unit_layout_id": canonical["default_unit_layout_id"],
        "map_config": canonical["map_config"],
        "formula_coefficients": canonical["formula_coefficients"],
        "default_role_briefings": canonical["default_role_briefings"],
        "default_relationships": canonical["default_relationships"],
        "default_country_stats": filter_country_stats(canonical["default_country_stats"], countries_columbia),
        "organizations": adjust_organizations(canonical["organizations"], orgs_members),
        "key_events_defaults": key_events,
        "schedule_defaults": adjust_schedule(canonical["schedule_defaults"], 4),
        "allowed_oil_price_range": canonical.get("allowed_oil_price_range"),
        "allowed_phase_a_duration_range": canonical.get("allowed_phase_a_duration_range"),
        "allowed_theaters": canonical.get("allowed_theaters"),
    }


# ── Main ─────────────────────────────────────────────────────────────────

def main():
    print("Fetching canonical template ttt_v1_0...")
    canonical = fetch_canonical()
    print(f"  Canonical: {canonical['code']} / {canonical['name']}")
    print(f"  Countries: {len([k for k in canonical['default_country_stats'] if k != '_note'])}")

    # Template 1
    code_10 = "ttt_test_10"
    if template_exists(code_10):
        print(f"\n[SKIP] Template '{code_10}' already exists.")
    else:
        data_10 = build_template_10(canonical)
        row = insert_template(data_10)
        countries = [k for k in data_10["default_country_stats"] if k != "_note"]
        print(f"\n[CREATED] Template '{code_10}'")
        print(f"  ID:        {row['id']}")
        print(f"  Name:      {row['name']}")
        print(f"  Countries: {len(countries)} — {', '.join(sorted(countries))}")
        print(f"  Rounds:    {row['allowed_round_counts']}")
        print(f"  Events:    {len(data_10['key_events_defaults'])}")
        for evt in data_10["key_events_defaults"]:
            print(f"    R{evt['round']}: {evt['name']}")

    # Template 2
    code_col = "ttt_test_columbia"
    if template_exists(code_col):
        print(f"\n[SKIP] Template '{code_col}' already exists.")
    else:
        data_col = build_template_columbia(canonical)
        row = insert_template(data_col)
        countries = [k for k in data_col["default_country_stats"] if k != "_note"]
        print(f"\n[CREATED] Template '{code_col}'")
        print(f"  ID:        {row['id']}")
        print(f"  Name:      {row['name']}")
        print(f"  Countries: {len(countries)} — {', '.join(sorted(countries))}")
        print(f"  Rounds:    {row['allowed_round_counts']}")
        print(f"  Events:    {len(data_col['key_events_defaults'])}")
        for evt in data_col["key_events_defaults"]:
            print(f"    R{evt['round']}: {evt['name']}")

    # Verify
    print("\n── Verification ──")
    resp = supabase.table("sim_templates").select("code, name, status, allowed_round_counts").order("created_at").execute()
    for t in resp.data:
        print(f"  {t['code']:25s} | {t['name']:30s} | {t['status']:10s} | rounds={t['allowed_round_counts']}")

    print("\nDone.")


if __name__ == "__main__":
    main()
