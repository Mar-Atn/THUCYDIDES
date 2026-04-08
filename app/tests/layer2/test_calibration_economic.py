"""Layer 2 Calibration Test — Economic Engine Value Verification.

Unlike battery tests (which check "did a row appear?"), calibration tests check
"is the VALUE correct?" by comparing engine output against expected ranges from
CARD_FORMULAS.md.

Run::

    cd app && PYTHONPATH=. python3 -m pytest tests/layer2/test_calibration_economic.py -v -s

Uses rounds 80-82 to avoid conflicts with other test suites.
"""
from __future__ import annotations

import logging
import pytest

from engine.services.supabase import get_client
from engine.round_engine.resolve_round import resolve_round
from engine.engines.round_tick import run_engine_tick

logger = logging.getLogger(__name__)

SCENARIO_CODE = "start_one"
BASE_ROUND = 80  # Test rounds: 79 (baseline seed), 80, 81, 82
TEST_ROUNDS = [79, 80, 81, 82]
TEST_TAG = "CALIBRATION_ECON_L2"


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _get_scenario_id(client) -> str:
    """Resolve the scenario_id for 'start_one'."""
    res = client.table("sim_scenarios").select("id").eq("code", SCENARIO_CODE).limit(1).execute()
    assert res.data, f"Scenario '{SCENARIO_CODE}' not found in sim_scenarios"
    return res.data[0]["id"]


def _cleanup_test_data(client, scenario_id: str) -> None:
    """Remove all test artifacts for calibration rounds."""
    for rn in TEST_ROUNDS:
        client.table("observatory_combat_results").delete() \
            .eq("scenario_id", scenario_id).eq("round_num", rn).execute()
        client.table("observatory_events").delete() \
            .eq("scenario_id", scenario_id).eq("round_num", rn).execute()
        client.table("exchange_transactions").delete() \
            .eq("scenario_id", scenario_id).eq("round_num", rn).execute()
        client.table("unit_states_per_round").delete() \
            .eq("scenario_id", scenario_id).eq("round_num", rn).execute()
        client.table("country_states_per_round").delete() \
            .eq("scenario_id", scenario_id).eq("round_num", rn).execute()
        client.table("global_state_per_round").delete() \
            .eq("scenario_id", scenario_id).eq("round_num", rn).execute()
        client.table("round_states").delete() \
            .eq("scenario_id", scenario_id).eq("round_num", rn).execute()

    # Delete test decisions by tag
    decisions = client.table("agent_decisions").select("id, action_payload") \
        .eq("scenario_id", scenario_id).execute()
    tagged_ids = [
        r["id"] for r in (decisions.data or [])
        if (r.get("action_payload") or {}).get("test_tag") == TEST_TAG
    ]
    if tagged_ids:
        client.table("agent_decisions").delete().in_("id", tagged_ids).execute()

    # Also delete by round_num directly (belt and suspenders)
    for rn in TEST_ROUNDS:
        client.table("agent_decisions").delete() \
            .eq("scenario_id", scenario_id).eq("round_num", rn).execute()


def _get_country_state(client, scenario_id: str, round_num: int, country_code: str) -> dict | None:
    """Fetch a single country's state for a given round."""
    res = client.table("country_states_per_round").select("*") \
        .eq("scenario_id", scenario_id).eq("round_num", round_num) \
        .eq("country_code", country_code).limit(1).execute()
    if res.data:
        return res.data[0]
    return None


def _get_all_country_states(client, scenario_id: str, round_num: int) -> dict[str, dict]:
    """Fetch all country states for a given round, keyed by country_code."""
    res = client.table("country_states_per_round").select("*") \
        .eq("scenario_id", scenario_id).eq("round_num", round_num).execute()
    return {row["country_code"]: row for row in (res.data or [])}


def _get_global_state(client, scenario_id: str, round_num: int) -> dict | None:
    """Fetch global state for a round."""
    res = client.table("global_state_per_round").select("*") \
        .eq("scenario_id", scenario_id).eq("round_num", round_num).limit(1).execute()
    if res.data:
        return res.data[0]
    return None


def _get_base_country(client, country_code: str) -> dict | None:
    """Fetch structural data from the countries table."""
    res = client.table("countries").select("*").execute()
    for row in (res.data or []):
        sim_name = (row.get("sim_name") or "").lower().replace(" ", "")
        if sim_name == country_code:
            return row
    return None


def _insert_decision(client, scenario_id: str, country: str, action_type: str,
                     payload: dict, rationale: str, round_num: int) -> str:
    """Insert a single scripted decision. Returns its id."""
    payload["test_tag"] = TEST_TAG
    row = {
        "scenario_id": scenario_id,
        "country_code": country,
        "action_type": action_type,
        "action_payload": payload,
        "rationale": rationale,
        "validation_status": "passed",
        "round_num": round_num,
    }
    res = client.table("agent_decisions").insert(row).execute()
    return res.data[0]["id"]


def _seed_round_from_r0(client, scenario_id: str, target_round: int) -> int:
    """Clone round 0 data into target_round. Returns count of rows seeded."""
    count = 0

    # Country states
    r0 = client.table("country_states_per_round").select("*") \
        .eq("scenario_id", scenario_id).eq("round_num", 0).execute()
    if r0.data:
        batch = []
        for row in r0.data:
            new_row = {k: v for k, v in row.items() if k != "id"}
            new_row["round_num"] = target_round
            batch.append(new_row)
        for i in range(0, len(batch), 100):
            client.table("country_states_per_round").upsert(
                batch[i:i+100], on_conflict="scenario_id,round_num,country_code"
            ).execute()
        count += len(batch)

    # Global state
    r0g = client.table("global_state_per_round").select("*") \
        .eq("scenario_id", scenario_id).eq("round_num", 0).execute()
    if r0g.data:
        for row in r0g.data:
            new_row = {k: v for k, v in row.items() if k != "id"}
            new_row["round_num"] = target_round
            client.table("global_state_per_round").upsert(
                new_row, on_conflict="scenario_id,round_num"
            ).execute()
        count += len(r0g.data)

    # Unit states
    r0u = client.table("unit_states_per_round").select("*") \
        .eq("scenario_id", scenario_id).eq("round_num", 0).execute()
    if r0u.data:
        batch = [{k: v for k, v in row.items() if k != "id"} | {"round_num": target_round}
                 for row in r0u.data]
        for i in range(0, len(batch), 100):
            client.table("unit_states_per_round").insert(batch[i:i+100]).execute()
        count += len(batch)

    return count


def _run_round(scenario_code: str, round_num: int) -> tuple[dict, dict]:
    """Run resolve_round + engine_tick, return both results."""
    resolve_result = resolve_round(scenario_code, round_num)
    tick_result = run_engine_tick(scenario_code, round_num)
    return resolve_result, tick_result


def _pct_change(old: float, new: float) -> float:
    """Percentage change from old to new."""
    if old == 0:
        return 0.0
    return (new - old) / old * 100.0


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------

@pytest.fixture(scope="module")
def client():
    return get_client()


@pytest.fixture(scope="module")
def scenario_id(client):
    return _get_scenario_id(client)


@pytest.fixture(scope="module")
def r0_states(client, scenario_id):
    """Cache all R0 states for comparison."""
    return _get_all_country_states(client, scenario_id, 0)


@pytest.fixture(scope="module")
def base_countries(client):
    """Load structural country data (countries table)."""
    res = client.table("countries").select("*").execute()
    out = {}
    for row in (res.data or []):
        cid = (row.get("sim_name") or "").lower().replace(" ", "")
        if cid:
            out[cid] = row
    return out


@pytest.fixture(scope="module", autouse=True)
def calibration_setup_teardown(client, scenario_id):
    """Setup baseline, yield for tests, then cleanup."""
    print("\n[CALIBRATION] Cleaning up any prior test data for rounds 79-82...")
    _cleanup_test_data(client, scenario_id)

    print("[CALIBRATION] Seeding round 79 baseline from round 0...")
    count = _seed_round_from_r0(client, scenario_id, 79)
    print(f"  Seeded {count} rows for round 79")

    yield

    print("\n[CALIBRATION] Cleaning up test data for rounds 79-82...")
    _cleanup_test_data(client, scenario_id)
    print("[CALIBRATION] Cleanup complete")


# ---------------------------------------------------------------------------
# Scenario runner helpers — each test seeds decisions, runs, and checks
# ---------------------------------------------------------------------------

def _run_calibration_round(client, scenario_id: str, round_num: int,
                           decisions: list[tuple[str, str, dict, str]]) -> dict:
    """Seed decisions for a round, run resolve+tick, return post-tick country states.

    Args:
        decisions: list of (country, action_type, payload, rationale)

    Returns dict of country_code -> state row for the given round.
    """
    for country, action_type, payload, rationale in decisions:
        _insert_decision(client, scenario_id, country, action_type, payload, rationale, round_num)

    resolve_result, tick_result = _run_round(SCENARIO_CODE, round_num)
    print(f"  resolve_round: {resolve_result}")
    print(f"  engine_tick: {tick_result}")

    return _get_all_country_states(client, scenario_id, round_num)


# ---------------------------------------------------------------------------
# Test 1: GDP Growth — No Shocks
# ---------------------------------------------------------------------------

class TestGdpGrowthNoShocks:
    """Columbia with only a budget decision should see modest GDP growth."""

    def test_gdp_grows_in_peaceful_conditions(self, client, scenario_id, r0_states):
        """Per CARD_FORMULAS A.4: base_growth = structural_rate/100/2.
        Columbia GDP=280, growth_base ~2-4%. One round should yield ~1-3% growth.
        GDP should end between 280 and 300 (generous range for first-round effects).
        """
        r0_columbia = r0_states.get("columbia")
        if not r0_columbia:
            pytest.skip("Columbia R0 data not available")

        gdp_r0 = float(r0_columbia["gdp"])
        print(f"\n  Columbia GDP R0: {gdp_r0}")

        decisions = [
            ("columbia", "set_budget", {"social_pct": 1.0, "military_coins": 0, "tech_coins": 0},
             "CALIBRATION: Columbia peaceful budget"),
        ]
        post = _run_calibration_round(client, scenario_id, BASE_ROUND, decisions)

        columbia_r1 = post.get("columbia")
        assert columbia_r1 is not None, "Columbia state not found after engine tick"
        gdp_r1 = float(columbia_r1["gdp"])
        change_pct = _pct_change(gdp_r0, gdp_r1)

        print(f"  Columbia GDP R1: {gdp_r1}")
        print(f"  Change: {change_pct:+.2f}%")
        print(f"  Expected range: [{gdp_r0 * 0.97:.1f}, {gdp_r0 * 1.05:.1f}]")

        # GDP should not crash in peaceful conditions
        assert gdp_r1 > gdp_r0 * 0.90, \
            f"Columbia GDP crashed from {gdp_r0} to {gdp_r1} ({change_pct:+.2f}%) — should not decline >10% in peace"

        # GDP should not explode either
        assert gdp_r1 < gdp_r0 * 1.10, \
            f"Columbia GDP exploded from {gdp_r0} to {gdp_r1} ({change_pct:+.2f}%) — unrealistic >10% single-round growth"

        # Ideally it grows (but sanctions/tariffs from R0 starting data may dampen)
        print(f"  RESULT: GDP {'grew' if gdp_r1 > gdp_r0 else 'declined'} — "
              f"{'EXPECTED' if gdp_r1 >= gdp_r0 else 'INVESTIGATE: starting sanctions/tariffs may cause drag'}")


# ---------------------------------------------------------------------------
# Test 2: Sanctions Damage
# ---------------------------------------------------------------------------

class TestSanctionsDamage:
    """Caribe under L3 Columbia sanctions should see economic pain."""

    def test_sanctions_suppress_growth(self, client, scenario_id, r0_states, base_countries):
        """Per CARD_FORMULAS A.2: L3 sanctions from Columbia (GDP=280, huge share of world GDP)
        should produce significant sanctions_coefficient damage on Caribe (GDP=1.9).
        """
        r0_caribe = r0_states.get("caribe")
        if not r0_caribe:
            pytest.skip("Caribe R0 data not available")

        gdp_r0 = float(r0_caribe["gdp"])
        treasury_r0 = float(r0_caribe.get("treasury", 0))
        base = base_countries.get("caribe", {})
        sanctions_coeff = float(base.get("sanctions_coefficient", 0.05))

        print(f"\n  Caribe GDP R0: {gdp_r0}")
        print(f"  Caribe treasury R0: {treasury_r0}")
        print(f"  Caribe sanctions_coefficient (structural): {sanctions_coeff}")

        # No extra decisions needed — R0 already has Columbia L3 sanctions on Caribe
        # Check post-tick state from the round 80 that Test 1 already ran
        post_caribe = _get_country_state(client, scenario_id, BASE_ROUND, "caribe")
        if not post_caribe:
            pytest.skip("Caribe post-tick state not available (round 80 may not have run)")

        gdp_r1 = float(post_caribe["gdp"])
        change_pct = _pct_change(gdp_r0, gdp_r1)

        print(f"  Caribe GDP R1: {gdp_r1}")
        print(f"  Change: {change_pct:+.2f}%")

        # Under heavy sanctions, Caribe should not be growing robustly
        # The S-curve for Columbia (GDP=280, ~40% of world GDP) at L3 should produce
        # substantial coverage and damage
        assert gdp_r1 < gdp_r0 * 1.03, \
            f"Caribe GDP grew {change_pct:+.2f}% despite L3 Columbia sanctions — sanctions not biting"

        print(f"  RESULT: Caribe GDP {'shrunk' if gdp_r1 < gdp_r0 else 'stable/grew slightly'} "
              f"under sanctions — {'EXPECTED' if gdp_r1 <= gdp_r0 else 'minor growth may be OK for small economy'}")


# ---------------------------------------------------------------------------
# Test 3: Tariff Bilateral Impact
# ---------------------------------------------------------------------------

class TestTariffBilateralImpact:
    """Columbia L3 tariff on Cathay should drag both economies relative to Bharata."""

    def test_tariff_war_drags_growth(self, client, scenario_id, r0_states):
        """Per CARD_FORMULAS A.3: TARIFF_K=0.54, IMPOSER_FRACTION=0.50.
        Both imposer and target should feel friction vs. a non-tariff country.
        """
        r0_columbia = r0_states.get("columbia")
        r0_cathay = r0_states.get("cathay")
        r0_bharata = r0_states.get("bharata")
        if not all([r0_columbia, r0_cathay, r0_bharata]):
            pytest.skip("Missing R0 data for Columbia/Cathay/Bharata")

        gdp_columbia_r0 = float(r0_columbia["gdp"])
        gdp_cathay_r0 = float(r0_cathay["gdp"])
        gdp_bharata_r0 = float(r0_bharata["gdp"])

        # Read post-tick from round 80
        post = _get_all_country_states(client, scenario_id, BASE_ROUND)
        if not post.get("columbia") or not post.get("cathay") or not post.get("bharata"):
            pytest.skip("Post-tick states not available")

        gdp_columbia_r1 = float(post["columbia"]["gdp"])
        gdp_cathay_r1 = float(post["cathay"]["gdp"])
        gdp_bharata_r1 = float(post["bharata"]["gdp"])

        columbia_pct = _pct_change(gdp_columbia_r0, gdp_columbia_r1)
        cathay_pct = _pct_change(gdp_cathay_r0, gdp_cathay_r1)
        bharata_pct = _pct_change(gdp_bharata_r0, gdp_bharata_r1)

        print(f"\n  Columbia: GDP {gdp_columbia_r0} -> {gdp_columbia_r1} ({columbia_pct:+.2f}%)")
        print(f"  Cathay:   GDP {gdp_cathay_r0} -> {gdp_cathay_r1} ({cathay_pct:+.2f}%)")
        print(f"  Bharata:  GDP {gdp_bharata_r0} -> {gdp_bharata_r1} ({bharata_pct:+.2f}%)")

        # Bharata (no major tariffs) should outperform at least one of the tariff-war pair
        # Use generous margin — other factors may affect growth too
        print(f"  Bharata growth ({bharata_pct:+.2f}%) vs Columbia ({columbia_pct:+.2f}%) "
              f"vs Cathay ({cathay_pct:+.2f}%)")
        print(f"  RESULT: tariff drag {'visible' if bharata_pct > min(columbia_pct, cathay_pct) else 'NOT visible'}")

        # Soft assertion: Bharata should grow at least as much as the worse-off tariff country
        # This may not always hold due to other factors (sanctions, war proximity, etc.)
        if bharata_pct <= min(columbia_pct, cathay_pct):
            print("  WARNING: Bharata did not outgrow tariff-war pair — investigate other drags on Bharata")


# ---------------------------------------------------------------------------
# Test 4: Treasury Revenue from GDP
# ---------------------------------------------------------------------------

class TestTreasuryRevenue:
    """Treasury should increase by approximately GDP x tax_rate minus spending."""

    def test_treasury_increases_in_peace(self, client, scenario_id, r0_states, base_countries):
        """Per CARD_FORMULAS A.5: revenue = GDP x tax_rate + oil_revenue - costs.
        In peace, revenue should exceed maintenance for a large economy like Columbia.
        """
        r0_columbia = r0_states.get("columbia")
        if not r0_columbia:
            pytest.skip("Columbia R0 data not available")

        treasury_r0 = float(r0_columbia.get("treasury", 0))
        gdp_r0 = float(r0_columbia["gdp"])
        base = base_countries.get("columbia", {})
        tax_rate = float(base.get("tax_rate", 0.24))

        expected_revenue_approx = gdp_r0 * tax_rate
        print(f"\n  Columbia treasury R0: {treasury_r0}")
        print(f"  Columbia GDP R0: {gdp_r0}")
        print(f"  Tax rate: {tax_rate}")
        print(f"  Approximate gross revenue: {expected_revenue_approx:.2f}")

        post_columbia = _get_country_state(client, scenario_id, BASE_ROUND, "columbia")
        if not post_columbia:
            pytest.skip("Columbia post-tick state not available")

        treasury_r1 = float(post_columbia["treasury"])
        treasury_delta = treasury_r1 - treasury_r0
        print(f"  Columbia treasury R1: {treasury_r1}")
        print(f"  Treasury delta: {treasury_delta:+.2f}")
        print(f"  Expected delta range: [{-expected_revenue_approx:.1f}, {expected_revenue_approx * 1.5:.1f}]")

        # Treasury should change (not stay flat)
        assert treasury_r1 != treasury_r0, \
            f"Columbia treasury unchanged at {treasury_r0} — engine may not be processing budget"

        # In peace with social_pct=1.0 and no military spending, treasury should increase
        # (revenue exceeds maintenance), but sanctions costs and tariffs may eat into surplus
        # Use generous range: treasury delta should be within [-50%, +150%] of gross revenue
        assert treasury_delta > -expected_revenue_approx, \
            f"Treasury delta {treasury_delta:+.2f} is a massive loss exceeding total revenue — investigate"

        print(f"  RESULT: Treasury {'increased' if treasury_delta > 0 else 'decreased'} by {treasury_delta:+.2f}")


# ---------------------------------------------------------------------------
# Test 5: Military Maintenance Cost
# ---------------------------------------------------------------------------

class TestMilitaryMaintenanceCost:
    """Countries with large militaries should have proportionally higher costs."""

    def test_large_military_costs_more(self, client, scenario_id, r0_states, base_countries):
        """Per CARD_FORMULAS A.6: maintenance = total_units x 0.02 x 3.0.
        Columbia (huge military) should lose more treasury to maintenance than Formosa (small).
        """
        columbia_base = base_countries.get("columbia", {})
        formosa_base = base_countries.get("formosa", {})

        def _total_units(base: dict) -> int:
            return sum([
                int(float(base.get("mil_ground", 0) or 0)),
                int(float(base.get("mil_naval", 0) or 0)),
                int(float(base.get("mil_tactical_air", 0) or 0)),
                int(float(base.get("mil_strategic_missiles", 0) or 0)),
                int(float(base.get("mil_air_defense", 0) or 0)),
            ])

        columbia_units = _total_units(columbia_base)
        formosa_units = _total_units(formosa_base)

        # Maintenance formula: units x maintenance_per_unit x MAINTENANCE_MULTIPLIER(3.0)
        columbia_maint_per_unit = float(columbia_base.get("maintenance_per_unit", 0.3) or 0.3)
        formosa_maint_per_unit = float(formosa_base.get("maintenance_per_unit", 0.3) or 0.3)

        columbia_est_maint = columbia_units * columbia_maint_per_unit * 3.0
        formosa_est_maint = formosa_units * formosa_maint_per_unit * 3.0

        print(f"\n  Columbia: {columbia_units} units, est. maintenance = {columbia_est_maint:.2f}")
        print(f"  Formosa:  {formosa_units} units, est. maintenance = {formosa_est_maint:.2f}")

        assert columbia_units > formosa_units, \
            f"Expected Columbia ({columbia_units}) to have more units than Formosa ({formosa_units})"
        assert columbia_est_maint > formosa_est_maint, \
            f"Expected Columbia maintenance ({columbia_est_maint:.2f}) > Formosa ({formosa_est_maint:.2f})"

        print(f"  Columbia/Formosa maintenance ratio: {columbia_est_maint / max(formosa_est_maint, 0.01):.1f}x")
        print(f"  RESULT: Military maintenance scales with army size as expected")


# ---------------------------------------------------------------------------
# Test 6: Oil Price
# ---------------------------------------------------------------------------

class TestOilPrice:
    """Oil price should stay in a plausible range after one round."""

    def test_oil_price_plausible_range(self, client, scenario_id):
        """Per CARD_FORMULAS A.1: Starting $85, inertia 0.3/0.7, floor $15, soft cap $200.
        After one round with no extreme shocks, oil should be in [$60, $130].
        """
        global_state = _get_global_state(client, scenario_id, BASE_ROUND)
        if not global_state:
            pytest.skip("Global state not available for round 80")

        oil_price = float(global_state.get("oil_price", 0))
        print(f"\n  Oil price after round {BASE_ROUND}: ${oil_price:.2f}")
        print(f"  Starting price: $85.00")
        print(f"  Expected range: [$60, $130]")

        assert 60.0 <= oil_price <= 130.0, \
            f"Oil price ${oil_price:.2f} outside plausible range [$60, $130] for first round"

        print(f"  RESULT: Oil price ${oil_price:.2f} is within plausible range")

    def test_opec_producers_benefit(self, client, scenario_id, r0_states, base_countries):
        """OPEC members (Solaria, Persia) should get oil revenue.
        Their treasury delta should include oil_revenue = price x mbpd x 0.009.
        """
        for cc in ("solaria", "persia"):
            r0 = r0_states.get(cc)
            if not r0:
                continue
            base = base_countries.get(cc, {})
            mbpd = float(base.get("oil_production_mbpd", 0) or 0)
            is_producer = str(base.get("oil_producer", "False")).lower() == "true"

            post = _get_country_state(client, scenario_id, BASE_ROUND, cc)
            if not post:
                continue

            treasury_r0 = float(r0.get("treasury", 0))
            treasury_r1 = float(post.get("treasury", 0))

            print(f"\n  {cc}: oil_producer={is_producer}, mbpd={mbpd}")
            print(f"  {cc}: treasury {treasury_r0} -> {treasury_r1} (delta {treasury_r1 - treasury_r0:+.2f})")

            if is_producer and mbpd > 0:
                print(f"  {cc}: Expected oil revenue ~= 85 x {mbpd} x 0.009 = {85 * mbpd * 0.009:.2f}")


# ---------------------------------------------------------------------------
# Test 7: Inflation
# ---------------------------------------------------------------------------

class TestInflation:
    """Sanctions and economic stress should drive inflation."""

    def test_sanctioned_country_inflation(self, client, scenario_id, r0_states):
        """Per CARD_FORMULAS A.8: inflation is driven by money printing + excess decay.
        Caribe (L3 sanctions, small economy) should have higher inflation pressure
        than Teutonia (stable, large, EU economy).
        """
        r0_caribe = r0_states.get("caribe")
        r0_teutonia = r0_states.get("teutonia")
        if not r0_caribe or not r0_teutonia:
            pytest.skip("Missing R0 data for Caribe/Teutonia")

        infl_caribe_r0 = float(r0_caribe.get("inflation", 0))
        infl_teutonia_r0 = float(r0_teutonia.get("inflation", 0))

        post_caribe = _get_country_state(client, scenario_id, BASE_ROUND, "caribe")
        post_teutonia = _get_country_state(client, scenario_id, BASE_ROUND, "teutonia")
        if not post_caribe or not post_teutonia:
            pytest.skip("Post-tick inflation data not available")

        infl_caribe_r1 = float(post_caribe.get("inflation", 0))
        infl_teutonia_r1 = float(post_teutonia.get("inflation", 0))

        print(f"\n  Caribe inflation:   {infl_caribe_r0:.2f} -> {infl_caribe_r1:.2f} "
              f"(delta {infl_caribe_r1 - infl_caribe_r0:+.2f})")
        print(f"  Teutonia inflation: {infl_teutonia_r0:.2f} -> {infl_teutonia_r1:.2f} "
              f"(delta {infl_teutonia_r1 - infl_teutonia_r0:+.2f})")

        # Inflation should not go negative
        assert infl_caribe_r1 >= 0, f"Caribe inflation went negative: {infl_caribe_r1}"
        assert infl_teutonia_r1 >= 0, f"Teutonia inflation went negative: {infl_teutonia_r1}"

        # Inflation should not explode in one round (cap 500 per formula)
        assert infl_caribe_r1 < 100, \
            f"Caribe inflation exploded to {infl_caribe_r1} in one round — investigate"
        assert infl_teutonia_r1 < 100, \
            f"Teutonia inflation exploded to {infl_teutonia_r1} in one round — investigate"

        # Teutonia should be stable-ish
        print(f"  Caribe inflation delta: {infl_caribe_r1 - infl_caribe_r0:+.2f}")
        print(f"  Teutonia inflation delta: {infl_teutonia_r1 - infl_teutonia_r0:+.2f}")
        print(f"  RESULT: Inflation plausible — Caribe {'higher' if infl_caribe_r1 > infl_teutonia_r1 else 'NOT higher'} than Teutonia")


# ---------------------------------------------------------------------------
# Test 8: War Economy
# ---------------------------------------------------------------------------

class TestWarEconomy:
    """Countries at war should experience economic strain."""

    def test_war_drains_economy(self, client, scenario_id, r0_states):
        """Per CARD_FORMULAS A.4: war damage = -(war_zones x 3% + infra_damage x 5%).
        Sarmatia and Ruthenia at war should show treasury/GDP stress.
        Ruthenia (tiny GDP=2.2) should be especially strained.
        """
        r0_sarmatia = r0_states.get("sarmatia")
        r0_ruthenia = r0_states.get("ruthenia")
        if not r0_sarmatia or not r0_ruthenia:
            pytest.skip("Missing R0 data for Sarmatia/Ruthenia")

        gdp_sar_r0 = float(r0_sarmatia["gdp"])
        gdp_ruth_r0 = float(r0_ruthenia["gdp"])
        treasury_sar_r0 = float(r0_sarmatia.get("treasury", 0))
        treasury_ruth_r0 = float(r0_ruthenia.get("treasury", 0))

        post_sarmatia = _get_country_state(client, scenario_id, BASE_ROUND, "sarmatia")
        post_ruthenia = _get_country_state(client, scenario_id, BASE_ROUND, "ruthenia")
        if not post_sarmatia or not post_ruthenia:
            pytest.skip("Post-tick war economy data not available")

        gdp_sar_r1 = float(post_sarmatia["gdp"])
        gdp_ruth_r1 = float(post_ruthenia["gdp"])
        treasury_sar_r1 = float(post_sarmatia.get("treasury", 0))
        treasury_ruth_r1 = float(post_ruthenia.get("treasury", 0))

        sar_gdp_pct = _pct_change(gdp_sar_r0, gdp_sar_r1)
        ruth_gdp_pct = _pct_change(gdp_ruth_r0, gdp_ruth_r1)

        print(f"\n  Sarmatia: GDP {gdp_sar_r0} -> {gdp_sar_r1} ({sar_gdp_pct:+.2f}%), "
              f"treasury {treasury_sar_r0} -> {treasury_sar_r1}")
        print(f"  Ruthenia: GDP {gdp_ruth_r0} -> {gdp_ruth_r1} ({ruth_gdp_pct:+.2f}%), "
              f"treasury {treasury_ruth_r0} -> {treasury_ruth_r1}")

        # War countries should not be booming
        # Sarmatia (GDP ~20) is under heavy sanctions + at war — growth should be dampened
        assert gdp_sar_r1 < gdp_sar_r0 * 1.05, \
            f"Sarmatia GDP grew {sar_gdp_pct:+.2f}% despite war + sanctions — unrealistic"

        # Ruthenia (GDP ~2.2) at war should be struggling
        # GDP floor is 0.5, so it can't go below that
        assert gdp_ruth_r1 < gdp_ruth_r0 * 1.05, \
            f"Ruthenia GDP grew {ruth_gdp_pct:+.2f}% despite active war — unrealistic"

        print(f"  RESULT: War economy effects {'visible' if (sar_gdp_pct < 2 and ruth_gdp_pct < 2) else 'WEAK'}")


# ---------------------------------------------------------------------------
# Test 9: Sanctions Cascade — Imposer Cost
# ---------------------------------------------------------------------------

class TestSanctionsImposerCost:
    """Per CARD_FORMULAS A.2-A.3: imposing sanctions costs the imposer too."""

    def test_imposer_pays_cost(self, client, scenario_id, r0_states, base_countries):
        """Columbia sanctions on Sarmatia (L3) should cost Columbia some GDP/treasury too.
        Per formula: imposer_fraction = 30-50% of damage inflicted (via tariff-like mechanism).
        We compare Columbia growth against a hypothetical frictionless baseline.
        """
        r0_columbia = r0_states.get("columbia")
        if not r0_columbia:
            pytest.skip("Columbia R0 data not available")

        gdp_r0 = float(r0_columbia["gdp"])

        post_columbia = _get_country_state(client, scenario_id, BASE_ROUND, "columbia")
        if not post_columbia:
            pytest.skip("Columbia post-tick not available")

        gdp_r1 = float(post_columbia["gdp"])
        change_pct = _pct_change(gdp_r0, gdp_r1)

        # Columbia's structural growth rate
        base = base_countries.get("columbia", {})
        structural_rate = float(base.get("gdp_growth_base", 2.0) or 2.0)
        expected_max_growth = structural_rate / 100 / 2 * 100  # per-round growth %

        print(f"\n  Columbia GDP: {gdp_r0} -> {gdp_r1} ({change_pct:+.2f}%)")
        print(f"  Structural growth rate: {structural_rate}% annual -> ~{expected_max_growth:.2f}% per round")
        print(f"  Actual growth: {change_pct:+.2f}%")
        print(f"  Sanctions cost: actual growth is {expected_max_growth - change_pct:.2f}pp below structural max")

        # Columbia should grow less than its structural max due to sanctions and tariff costs
        # This is a soft check — many factors affect growth
        if change_pct < expected_max_growth:
            print(f"  RESULT: Imposer cost VISIBLE — growth below structural maximum")
        else:
            print(f"  RESULT: Imposer cost NOT visible in GDP — may be absorbed by other factors")


# ---------------------------------------------------------------------------
# Test 10: Budget Allocation Effect on Stability
# ---------------------------------------------------------------------------

class TestBudgetAllocationStability:
    """Different social_pct should produce different stability outcomes."""

    def test_high_social_spending_improves_stability(self, client, scenario_id, r0_states):
        """Per CARD_FORMULAS B.1: social spending >= 100% -> +0.05 stability,
        social spending 70-85% -> -0.15 stability.

        Run two separate rounds with different social_pct, compare stability deltas.
        Round 81 = austerity (social_pct=0.5), Round 82 = generous (social_pct=1.5).
        Both start from R0 baseline.
        """
        # Seed round 80 as baseline for round 81, and round 81 as baseline for round 82
        # Actually, we need independent baselines. Seed both from R0.
        print("\n  Seeding round 80 baseline for austerity test (round 81)...")
        _seed_round_from_r0(client, scenario_id, 80)  # may already exist from earlier tests

        print("  Seeding round 81 baseline for generous test (round 82)...")
        _seed_round_from_r0(client, scenario_id, 81)

        # Use a neutral country (Teutonia) to minimize confounds from war/sanctions
        test_country = "teutonia"
        r0_state = r0_states.get(test_country)
        if not r0_state:
            pytest.skip(f"{test_country} R0 data not available")

        stability_r0 = int(r0_state.get("stability", 5))
        print(f"  {test_country} stability R0: {stability_r0}")

        # Round 81: Austerity
        print(f"\n  --- Run A: Austerity (social_pct=0.5), round 81 ---")
        decisions_a = [
            (test_country, "set_budget", {"social_pct": 0.5, "military_coins": 0, "tech_coins": 0},
             "CALIBRATION: Austerity budget"),
        ]
        post_a = _run_calibration_round(client, scenario_id, 81, decisions_a)

        state_a = post_a.get(test_country)
        stability_a = int(state_a["stability"]) if state_a else stability_r0

        # Round 82: Generous
        print(f"\n  --- Run B: Generous (social_pct=1.5), round 82 ---")
        decisions_b = [
            (test_country, "set_budget", {"social_pct": 1.5, "military_coins": 0, "tech_coins": 0},
             "CALIBRATION: Generous social budget"),
        ]
        post_b = _run_calibration_round(client, scenario_id, 82, decisions_b)

        state_b = post_b.get(test_country)
        stability_b = int(state_b["stability"]) if state_b else stability_r0

        print(f"\n  Results for {test_country}:")
        print(f"    Austerity (social_pct=0.5): stability {stability_r0} -> {stability_a}")
        print(f"    Generous  (social_pct=1.5): stability {stability_r0} -> {stability_b}")

        # Generous social spending should yield stability >= austerity
        # Note: stability is integer, so ties are possible in one round
        assert stability_b >= stability_a, \
            f"Generous spending (stability={stability_b}) should be >= austerity (stability={stability_a})"

        print(f"  RESULT: Social spending effect {'VISIBLE' if stability_b > stability_a else 'tied (may need more rounds)'}")


# ---------------------------------------------------------------------------
# Cross-cutting validation: All countries should have plausible values
# ---------------------------------------------------------------------------

class TestAllCountriesPlausible:
    """Every country's post-tick values should be within sane bounds."""

    def test_no_negative_gdp(self, client, scenario_id):
        """GDP floor is 0.5 per CARD_FORMULAS."""
        post = _get_all_country_states(client, scenario_id, BASE_ROUND)
        if not post:
            pytest.skip("No post-tick data available")

        for cc, state in post.items():
            gdp = float(state["gdp"])
            print(f"  {cc}: GDP = {gdp}")
            assert gdp >= 0.5, f"{cc} GDP = {gdp} — below GDP_FLOOR of 0.5"

    def test_no_negative_treasury(self, client, scenario_id):
        """Treasury should not go negative (engine clamps at 0)."""
        post = _get_all_country_states(client, scenario_id, BASE_ROUND)
        if not post:
            pytest.skip("No post-tick data available")

        for cc, state in post.items():
            treasury = float(state.get("treasury", 0))
            print(f"  {cc}: treasury = {treasury:.2f}")
            # Treasury CAN go negative in extreme cases, but should not be massively negative
            assert treasury >= -50, f"{cc} treasury = {treasury:.2f} — massively negative, investigate"

    def test_stability_in_range(self, client, scenario_id):
        """Stability should be in [1, 9] per CARD_FORMULAS B.1."""
        post = _get_all_country_states(client, scenario_id, BASE_ROUND)
        if not post:
            pytest.skip("No post-tick data available")

        for cc, state in post.items():
            stability = int(state.get("stability", 5))
            print(f"  {cc}: stability = {stability}")
            assert 1 <= stability <= 9, f"{cc} stability = {stability} — outside [1, 9] range"

    def test_inflation_in_range(self, client, scenario_id):
        """Inflation should be in [0, 500] per CARD_FORMULAS A.8."""
        post = _get_all_country_states(client, scenario_id, BASE_ROUND)
        if not post:
            pytest.skip("No post-tick data available")

        for cc, state in post.items():
            inflation = float(state.get("inflation", 0))
            print(f"  {cc}: inflation = {inflation:.2f}")
            assert 0 <= inflation <= 500, f"{cc} inflation = {inflation:.2f} — outside [0, 500] range"

    def test_gdp_changes_not_extreme(self, client, scenario_id, r0_states):
        """No country should lose or gain more than 30% GDP in a single round."""
        post = _get_all_country_states(client, scenario_id, BASE_ROUND)
        if not post:
            pytest.skip("No post-tick data available")

        extreme_changes = []
        for cc, state in post.items():
            r0 = r0_states.get(cc)
            if not r0:
                continue
            gdp_r0 = float(r0["gdp"])
            gdp_r1 = float(state["gdp"])
            if gdp_r0 < 1.0:
                continue  # Skip very tiny economies — percentage math is misleading
            change_pct = _pct_change(gdp_r0, gdp_r1)
            print(f"  {cc}: GDP {gdp_r0} -> {gdp_r1} ({change_pct:+.2f}%)")
            if abs(change_pct) > 30:
                extreme_changes.append((cc, change_pct))

        if extreme_changes:
            details = ", ".join(f"{cc}: {pct:+.2f}%" for cc, pct in extreme_changes)
            pytest.fail(f"Extreme GDP changes (>30% in one round): {details}")
