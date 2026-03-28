"""
TTT SEED — Test Orchestrator
==============================
Runs the complete simulation -- like the human moderator.
Imports the three engines and the agent system.
Manages the round sequence: Phase A (free action), Phase B (world model),
Phase C (deployment). Saves everything.

Author: ATLAS (World Model Engineer)
Version: 2.0 (SEED)
"""

import copy
import json
import os
import time
from typing import Dict, List, Optional, Any

from world_state import WorldState, SCHEDULED_EVENTS
from transaction_engine import TransactionEngine
from live_action_engine import LiveActionEngine
from world_model_engine import WorldModelEngine
from ai_agent import AIAgent, load_agents_from_seeds


class TestOrchestrator:
    """Runs the complete simulation -- like the human moderator."""

    def __init__(self, world_state: WorldState,
                 engines: dict,
                 agents: Dict[str, AIAgent],
                 test_config: dict):
        self.world_state = world_state
        self.transaction_engine: TransactionEngine = engines["transaction"]
        self.live_action_engine: LiveActionEngine = engines["live_action"]
        self.world_model_engine: WorldModelEngine = engines["world_model"]
        self.agents = agents
        self.config = test_config
        self.collected_actions: Dict[str, dict] = {}
        self.pending_transactions: List[dict] = []
        self.round_results: Dict[int, dict] = {}
        self.simulation_log: List[dict] = []
        self.output_dir = test_config.get("output_dir", "test_results")

    def run_simulation(self, num_rounds: int = 8) -> dict:
        """Run the complete simulation for num_rounds."""
        print(f"\n{'='*60}")
        print(f"  TTT SEED SIMULATION: {self.config.get('name', 'Unknown')}")
        print(f"  Rounds: {num_rounds} | Agents: {len(self.agents)}")
        print(f"  Seed: {self.config.get('seed', 0)}")
        print(f"{'='*60}\n")

        start_time = time.time()

        # Save initial state
        self._save_world_state(0, "initial")

        for round_num in range(1, num_rounds + 1):
            round_start = time.time()
            print(f"\n--- ROUND {round_num} ---")

            self.world_state.round_num = round_num
            self.collected_actions = {}
            self.pending_transactions = []

            # PHASE A: Free action (agents deliberate + negotiate + act)
            print(f"  Phase A: Agent deliberation and negotiation...")
            self.phase_a_free_action(round_num)

            # PHASE A continued: Process transactions
            print(f"  Phase A: Processing {len(self.pending_transactions)} transactions...")
            self.process_pending_transactions()

            # PHASE A continued: Process live actions (combat, covert ops)
            print(f"  Phase A: Processing live actions...")
            self.process_live_actions(round_num)

            # Check scheduled events (elections, summits)
            self.check_scheduled_events(round_num)

            # Aggregate actions for world model
            aggregated = self._aggregate_actions()

            # PHASE B: World Model Engine (batch processing)
            print(f"  Phase B: World Model Engine processing...")
            results, narrative, flags = self.world_model_engine.process_round(
                self.world_state, aggregated, round_num)

            # PHASE C: Deployment window
            print(f"  Phase C: Deployment window...")
            self.deployment_window(round_num)

            # Log and save
            round_time = time.time() - round_start
            round_summary = self._build_round_summary(round_num, results, narrative, flags, round_time)
            self.round_results[round_num] = round_summary
            self.save_round(round_num, results, narrative, flags)

            # Print summary
            self._print_round_summary(round_num, round_summary)

            # Check for simulation-ending conditions
            if self._check_end_conditions(round_num):
                print(f"\n  *** SIMULATION ENDED EARLY AT ROUND {round_num} ***")
                break

        total_time = time.time() - start_time
        final_report = self._build_final_report(num_rounds, total_time)
        self._save_final_report(final_report)

        print(f"\n{'='*60}")
        print(f"  SIMULATION COMPLETE in {total_time:.1f}s")
        print(f"{'='*60}")

        return final_report

    # ===================================================================
    # PHASE A: FREE ACTION
    # ===================================================================

    def phase_a_free_action(self, round_num: int) -> None:
        """All agents deliberate and negotiate."""

        # Step 1: Each agent decides actions
        for role_id, agent in self.agents.items():
            actions = agent.deliberate(self.world_state, round_num)
            self.collected_actions[role_id] = actions

        # Step 2: Negotiation rounds (up to 5 bilateral exchanges)
        negotiation_results = []
        for neg_round in range(5):
            round_deals = 0
            for role_id, agent in self.agents.items():
                # Only heads of state negotiate on behalf of countries
                if not agent.profile.get("head_of_state", False):
                    continue

                target_id = agent.choose_negotiation_target(self.world_state)
                if target_id and target_id in self.agents:
                    target_agent = self.agents[target_id]
                    result = agent.negotiate(target_agent, self.world_state)
                    if result:
                        negotiation_results.append({
                            "round": round_num,
                            "neg_round": neg_round,
                            "proposer": role_id,
                            "target": target_id,
                            "terms": result,
                        })
                        # Convert successful negotiation to transaction
                        self._convert_negotiation_to_transaction(
                            agent, target_agent, result)
                        round_deals += 1

            if round_deals == 0:
                break  # No more deals to be made

        self.simulation_log.append({
            "round": round_num,
            "phase": "negotiation",
            "deals_made": len(negotiation_results),
            "details": negotiation_results,
        })

    def _convert_negotiation_to_transaction(self, proposer: AIAgent,
                                             target: AIAgent,
                                             terms: dict) -> None:
        """Convert negotiation results into actionable transactions."""
        if terms.get("military_cooperation") or terms.get("intelligence_sharing"):
            # Soft agreement -- stored as treaty
            self.pending_transactions.append({
                "sender": proposer.country_id,
                "receiver": target.country_id,
                "tx_type": "treaty",
                "details": {
                    "text": f"Cooperation agreement: {list(terms.keys())}",
                    "signatories": [proposer.country_id, target.country_id],
                },
            })

        if terms.get("tariff_reduction"):
            # Reduce tariffs between the two
            current = self.world_state.bilateral.get("tariffs", {}).get(
                proposer.country_id, {}).get(target.country_id, 0)
            if current > 0:
                if proposer.country_id not in self.collected_actions:
                    self.collected_actions[proposer.country_id] = {}
                tariff_changes = self.collected_actions.get(proposer.role_id, {}).get("tariffs", {})
                tariff_changes[target.country_id] = max(current - 1, 0)

        if terms.get("sanctions_reduction"):
            current = self.world_state.bilateral.get("sanctions", {}).get(
                proposer.country_id, {}).get(target.country_id, 0)
            if current > 0:
                sanc_changes = self.collected_actions.get(proposer.role_id, {}).get("sanctions", {})
                sanc_changes[target.country_id] = max(current - 1, 0)

    # ===================================================================
    # TRANSACTION PROCESSING
    # ===================================================================

    def process_pending_transactions(self) -> None:
        """Process all pending transactions from negotiations and agent decisions."""

        # Process transactions from agent decisions
        for role_id, actions in self.collected_actions.items():
            agent = self.agents.get(role_id)
            if not agent:
                continue
            txs = actions.get("transactions", [])
            if isinstance(txs, list):
                for tx in txs:
                    result = self.transaction_engine.process_transaction(
                        agent.country_id,
                        tx.get("receiver", ""),
                        tx.get("type", "coin_transfer"),
                        tx.get("details", {}),
                    )
                    self.simulation_log.append({
                        "round": self.world_state.round_num,
                        "phase": "transaction",
                        "result": result,
                    })

        # Process negotiation-generated transactions
        for tx in self.pending_transactions:
            result = self.transaction_engine.process_transaction(
                tx["sender"], tx["receiver"], tx["tx_type"], tx["details"])
            self.simulation_log.append({
                "round": self.world_state.round_num,
                "phase": "transaction",
                "result": result,
            })

    # ===================================================================
    # LIVE ACTION PROCESSING
    # ===================================================================

    def process_live_actions(self, round_num: int) -> None:
        """Process combat, covert ops, propaganda, etc."""
        self.live_action_engine.new_round()

        for role_id, actions in self.collected_actions.items():
            agent = self.agents.get(role_id)
            if not agent:
                continue

            mil = actions.get("military", {})
            if not isinstance(mil, dict):
                continue

            # Process attacks
            for attack in mil.get("attacks", []):
                target_country = attack.get("target_country", "")
                zone = attack.get("preferred_zone", "")
                units = attack.get("units", 1)

                if target_country and zone and units > 0:
                    result = self.live_action_engine.resolve_attack(
                        agent.country_id, target_country, zone, units)
                    self.simulation_log.append({
                        "round": round_num, "phase": "combat", "result": result})

            # Process blockades
            if mil.get("gulf_gate") == "maintain_blockade":
                result = self.live_action_engine.resolve_blockade(
                    agent.country_id, "cp_gulf_gate")
                self.simulation_log.append({
                    "round": round_num, "phase": "blockade", "result": result})

            if mil.get("formosa_action") in ("blockade", "full_blockade"):
                for sea_zone in ["w(17,4)", "w(16,7)"]:
                    result = self.live_action_engine.resolve_blockade(
                        agent.country_id, sea_zone)
                    self.simulation_log.append({
                        "round": round_num, "phase": "blockade", "result": result})

            # Process mobilization
            mob = mil.get("mobilization")
            if mob:
                # Aggregated into world model actions later
                pass

        # Process covert ops from private actions
        for role_id, actions in self.collected_actions.items():
            agent = self.agents.get(role_id)
            if not agent:
                continue

            private = actions.get("private", {})
            if isinstance(private, dict):
                for op in private.get("covert", []):
                    result = self.live_action_engine.resolve_covert_op(
                        agent.country_id,
                        op.get("type", "espionage"),
                        op.get("target", ""),
                        op.get("details"),
                    )
                    self.simulation_log.append({
                        "round": round_num, "phase": "covert_op", "result": result})

    # ===================================================================
    # SCHEDULED EVENTS
    # ===================================================================

    def check_scheduled_events(self, round_num: int) -> None:
        """Check and process scheduled events for this round."""
        events = SCHEDULED_EVENTS.get(round_num, [])
        for event in events:
            if event["type"] == "election":
                print(f"  ** ELECTION: {event['subtype']} in {event['country']} **")
                if event["subtype"] == "columbia_midterms":
                    self._run_columbia_midterms(round_num)
                elif event["subtype"] in ("heartland_wartime", "heartland_wartime_runoff"):
                    self._run_heartland_election(round_num)
                elif event["subtype"] == "columbia_presidential":
                    self._run_columbia_presidential(round_num)

    def _run_columbia_midterms(self, round_num: int) -> None:
        """Columbia midterms Round 2: team votes + AI popular vote (50/50)."""
        # Collect team votes (president's camp vs opposition)
        presidents_camp = 0
        opposition = 0

        for role_id in ["dealer", "volt", "anchor", "shield", "shadow", "tribune", "challenger"]:
            agent = self.agents.get(role_id)
            if not agent:
                continue
            faction = agent.profile.get("faction", "")
            if faction in ("presidents_camp", "Presidents"):
                presidents_camp += 1
            elif faction == "opposition":
                opposition += 1
            else:
                # Shield and Shadow: institutional, lean president
                presidents_camp += 0.6
                opposition += 0.4

        player_incumbent_pct = (presidents_camp / max(presidents_camp + opposition, 1)) * 100

        self.simulation_log.append({
            "round": round_num,
            "phase": "election",
            "type": "columbia_midterms",
            "player_votes": {"presidents_camp": presidents_camp, "opposition": opposition},
            "player_incumbent_pct": player_incumbent_pct,
        })

    def _run_heartland_election(self, round_num: int) -> None:
        """Heartland wartime election Round 3-4: AI judges on gameplay outcomes."""
        c = self.world_state.countries.get("heartland", {})
        pol = c.get("political", {})

        # Beacon vs Bulwark: Bulwark has military credibility advantage
        beacon_score = pol.get("political_support", 50)
        bulwark_bonus = 10  # military credibility
        war_tiredness_penalty = pol.get("war_tiredness", 0) * 2

        beacon_final = beacon_score - war_tiredness_penalty
        bulwark_final = (100 - beacon_score) + bulwark_bonus

        beacon_wins = beacon_final > bulwark_final

        self.simulation_log.append({
            "round": round_num,
            "phase": "election",
            "type": "heartland_wartime",
            "beacon_score": beacon_final,
            "bulwark_score": bulwark_final,
            "beacon_wins": beacon_wins,
        })

        if not beacon_wins:
            # Bulwark becomes head of state
            beacon_role = self.world_state.roles.get("beacon")
            bulwark_role = self.world_state.roles.get("bulwark")
            if beacon_role:
                beacon_role["is_head_of_state"] = False
            if bulwark_role:
                bulwark_role["is_head_of_state"] = True
            # Update agent profiles
            if "bulwark" in self.agents:
                self.agents["bulwark"].profile["head_of_state"] = True
            if "beacon" in self.agents:
                self.agents["beacon"].profile["head_of_state"] = False
            print("  >> Heartland election: BULWARK wins, becomes president")
        else:
            print("  >> Heartland election: BEACON retains presidency")

    def _run_columbia_presidential(self, round_num: int) -> None:
        """Columbia presidential election Round 5."""
        c = self.world_state.countries.get("columbia", {})
        pol = c.get("political", {})

        # Incumbent camp (Volt or Anchor) vs Challenger
        incumbent_support = pol.get("political_support", 50)

        self.simulation_log.append({
            "round": round_num,
            "phase": "election",
            "type": "columbia_presidential",
            "incumbent_support": incumbent_support,
        })

        # Dealer's endorsement matters
        dealer_approval = incumbent_support
        if dealer_approval < 35:
            # Low approval makes endorsement toxic
            print("  >> Columbia presidential: Dealer's low approval hurts endorsed candidate")

    # ===================================================================
    # DEPLOYMENT WINDOW
    # ===================================================================

    def deployment_window(self, round_num: int) -> None:
        """5-minute deployment window after batch processing.
        AI agents deploy newly produced/mobilized units."""
        for role_id, agent in self.agents.items():
            if not agent.profile.get("head_of_state", False):
                continue
            if not agent.profile.get("military_chief", False) and not agent.profile.get("head_of_state", False):
                continue

            c = self.world_state.countries.get(agent.country_id, {})
            mil = c.get("military", {})

            # Simple deployment: new units go to home zones
            home_zones = c.get("home_zones", [])
            if home_zones:
                primary_zone = home_zones[0]
                # Newly produced units are already counted in military totals
                # Just ensure they're deployed to appropriate zones

    # ===================================================================
    # ACTION AGGREGATION
    # ===================================================================

    def _aggregate_actions(self) -> dict:
        """Aggregate per-agent actions into the format expected by WorldModelEngine."""
        aggregated = {
            "budgets": {},
            "tariff_changes": {},
            "sanction_changes": {},
            "opec_production": {},
            "mobilizations": {},
            "combat": [],
            "blockades": [],
            "missile_strikes": [],
            "covert_ops": [],
            "propaganda": {},
            "tech_rd": {},
            "votes": {},
        }

        # Group by country -- head of state actions take priority
        country_actions: Dict[str, dict] = {}

        for role_id, actions in self.collected_actions.items():
            agent = self.agents.get(role_id)
            if not agent:
                continue

            cid = agent.country_id
            if cid not in country_actions:
                country_actions[cid] = {}

            # Head of state actions override
            if agent.profile.get("head_of_state", False):
                country_actions[cid] = actions

        for cid, actions in country_actions.items():
            # Budget
            budget = actions.get("budget", {})
            if budget:
                aggregated["budgets"][cid] = budget

            # Tariffs
            tariff_changes = actions.get("tariffs", {})
            if tariff_changes:
                aggregated["tariff_changes"][cid] = tariff_changes

            # Sanctions
            sanc_changes = actions.get("sanctions", {})
            if sanc_changes:
                aggregated["sanction_changes"][cid] = sanc_changes

            # OPEC
            opec = actions.get("opec")
            if opec:
                aggregated["opec_production"][cid] = opec

            # Mobilization
            mil = actions.get("military", {})
            if isinstance(mil, dict):
                mob = mil.get("mobilization")
                if mob:
                    aggregated["mobilizations"][cid] = mob

            # Tech R&D allocation from budget
            if budget:
                tech_pct = budget.get("tech_pct", 0.1)
                c = self.world_state.countries.get(cid, {})
                gdp = c.get("economic", {}).get("gdp", 0)
                tech_coins = gdp * c.get("economic", {}).get("tax_rate", 0.2) * tech_pct
                aggregated["tech_rd"][cid] = {
                    "nuclear": tech_coins * 0.3,
                    "ai": tech_coins * 0.7,
                }

        return aggregated

    # ===================================================================
    # SAVE / REPORT
    # ===================================================================

    def save_round(self, round_num: int, results: dict,
                   narrative: str, flags: List[str]) -> None:
        """Save complete round data to output directory."""
        os.makedirs(self.output_dir, exist_ok=True)

        # World state snapshot
        self._save_world_state(round_num, "end")

        # Round results
        round_file = os.path.join(self.output_dir, f"round_{round_num}_results.json")
        round_data = {
            "round": round_num,
            "narrative": narrative,
            "flags": flags,
            "results_summary": self._summarize_results(results),
            "actions_taken": {k: str(v)[:500] for k, v in self.collected_actions.items()},
            "transactions": self.transaction_engine.get_transaction_history(),
            "combat_results": [r for r in self.live_action_engine.action_log
                               if r.get("type") in ("attack", "blockade", "missile_strike")],
            "negotiations": [e for e in self.simulation_log
                             if e.get("round") == round_num and e.get("phase") == "negotiation"],
        }
        with open(round_file, "w") as f:
            json.dump(round_data, f, indent=2, default=str)

        # Narrative file
        narrative_file = os.path.join(self.output_dir, f"round_{round_num}_narrative.txt")
        with open(narrative_file, "w") as f:
            f.write(narrative)

    def _save_world_state(self, round_num: int, label: str) -> None:
        os.makedirs(self.output_dir, exist_ok=True)
        path = os.path.join(self.output_dir, f"world_state_r{round_num}_{label}.json")
        self.world_state.save_to_json(path)

    def _summarize_results(self, results: dict) -> dict:
        """Create a compact summary of round results."""
        summary = {
            "oil_price": self.world_state.oil_price,
            "countries": {},
        }
        for cid, c in self.world_state.countries.items():
            summary["countries"][cid] = {
                "gdp": round(c["economic"]["gdp"], 1),
                "growth": round(c["economic"]["gdp_growth_rate"], 1),
                "stability": round(c["political"]["stability"], 1),
                "support": round(c["political"]["political_support"], 1),
                "treasury": round(c["economic"]["treasury"], 1),
                "inflation": round(c["economic"]["inflation"], 1),
                "ground": c["military"]["ground"],
                "naval": c["military"]["naval"],
            }
        return summary

    def _build_round_summary(self, round_num: int, results: dict,
                              narrative: str, flags: List[str],
                              elapsed: float) -> dict:
        return {
            "round": round_num,
            "elapsed_seconds": round(elapsed, 2),
            "oil_price": self.world_state.oil_price,
            "flags_count": len(flags),
            "flags": flags,
            "narrative_length": len(narrative),
            "deals_made": sum(
                e.get("deals_made", 0) for e in self.simulation_log
                if e.get("round") == round_num and e.get("phase") == "negotiation"
            ),
            "combats": len(self.live_action_engine.combat_results),
            "transactions": len([
                tx for tx in self.transaction_engine.transaction_log
                if tx.get("round") == round_num and tx.get("status") == "executed"
            ]),
        }

    def _build_final_report(self, num_rounds: int, total_time: float) -> dict:
        """Build the final simulation report."""
        report = {
            "test_name": self.config.get("name", "Unknown"),
            "seed": self.config.get("seed", 0),
            "rounds_played": self.world_state.round_num,
            "total_time_seconds": round(total_time, 2),
            "agents_count": len(self.agents),
            "final_state": {},
            "round_summaries": self.round_results,
            "key_events": [],
            "nuclear_used": self.world_state.nuclear_used_this_sim,
        }

        # Final country state summary
        major_countries = ["columbia", "cathay", "nordostan", "heartland", "persia",
                           "gallia", "teutonia", "albion", "bharata", "levantia", "formosa"]
        for cid in major_countries:
            c = self.world_state.countries.get(cid, {})
            if c:
                report["final_state"][cid] = {
                    "gdp": round(c["economic"]["gdp"], 1),
                    "stability": round(c["political"]["stability"], 1),
                    "support": round(c["political"]["political_support"], 1),
                    "military_total": self.world_state.get_total_military(cid),
                    "treasury": round(c["economic"]["treasury"], 1),
                    "nuclear_level": c["technology"]["nuclear_level"],
                    "ai_level": c["technology"]["ai_level"],
                }

        # Key events
        for event in self.world_state.events_log:
            if event.get("type") in ("election", "coup", "nuclear_strike",
                                     "global_alert", "assassination"):
                report["key_events"].append(event)

        return report

    def _save_final_report(self, report: dict) -> None:
        os.makedirs(self.output_dir, exist_ok=True)
        path = os.path.join(self.output_dir, "final_report.json")
        with open(path, "w") as f:
            json.dump(report, f, indent=2, default=str)
        print(f"\n  Final report saved to: {path}")

    def _print_round_summary(self, round_num: int, summary: dict) -> None:
        print(f"\n  Round {round_num} Summary:")
        print(f"    Oil: ${self.world_state.oil_price:.0f} | "
              f"Flags: {summary['flags_count']} | "
              f"Combats: {summary['combats']} | "
              f"Deals: {summary['deals_made']} | "
              f"Time: {summary['elapsed_seconds']:.1f}s")

        # Top 5 countries
        sorted_c = sorted(
            self.world_state.countries.items(),
            key=lambda x: x[1]["economic"]["gdp"], reverse=True
        )
        for cid, c in sorted_c[:6]:
            name = c.get("sim_name", cid)
            print(f"    {name:12s}: GDP={c['economic']['gdp']:7.1f} "
                  f"Stab={c['political']['stability']:.1f} "
                  f"Sup={c['political']['political_support']:.0f}% "
                  f"Mil={self.world_state.get_total_military(cid)}")

        if summary["flags"]:
            for flag in summary["flags"][:3]:
                print(f"    ! {flag}")

    def _check_end_conditions(self, round_num: int) -> bool:
        """Check if simulation should end early."""
        # Nuclear exchange
        if self.world_state.nuclear_used_this_sim:
            # Count how many nuclear events
            nuc_events = sum(
                1 for e in self.world_state.events_log
                if e.get("type") == "global_alert" and "nuclear" in str(e.get("subtype", ""))
            )
            if nuc_events >= 3:
                return True  # Multiple nuclear exchanges = end

        # All major countries collapsed (stability 1 = failed state)
        collapsed = sum(
            1 for cid in ["columbia", "cathay", "nordostan"]
            if self.world_state.countries.get(cid, {}).get(
                "political", {}).get("stability", 5) <= 1.0
        )
        if collapsed >= 2:
            return True

        return False
