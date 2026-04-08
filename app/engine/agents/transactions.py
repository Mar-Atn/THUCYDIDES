"""Transaction system — AI agents propose, evaluate, and execute bilateral deals.

Implements the transaction flow from SEED E5 Section 7 and DET_C1:
1. Agent proposes a transaction to a counterpart
2. Counterpart evaluates (accept/reject/counter)
3. Accepted transactions execute (state changes applied)

Transaction types: coin_transfer, arms_sale, arms_gift, tech_transfer,
basing_rights, ceasefire, peace_treaty, alliance, trade_agreement,
sanctions_coordination.

Source: SEED_E5_AI_PARTICIPANT_MODULE_v1.md Section 7, DET_C1
"""

from __future__ import annotations

import logging
import uuid
from dataclasses import dataclass, field
from typing import Any, Optional

logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# TRANSACTION TYPES & VALIDATION
# ---------------------------------------------------------------------------

TRANSACTION_TYPES = {
    "coin_transfer",
    "arms_sale",
    "arms_gift",
    "tech_transfer",
    "basing_rights",
    "ceasefire",
    "peace_treaty",
    "alliance",
    "trade_agreement",
    "sanctions_coordination",
}

# Which types require active war between the parties
REQUIRES_WAR = {"ceasefire", "peace_treaty"}

# Which types involve resource exchange (gives/receives)
RESOURCE_TRANSACTIONS = {"coin_transfer", "arms_sale", "arms_gift", "tech_transfer"}


@dataclass
class TransactionProposal:
    """A proposed bilateral transaction between two agents."""
    id: str = ""
    type: str = ""
    proposer_role_id: str = ""
    proposer_country_id: str = ""
    counterpart_role_id: str = ""
    counterpart_country_id: str = ""
    terms: dict = field(default_factory=dict)
    status: str = "proposed"  # proposed → accepted/rejected/countered → executed
    reasoning: str = ""
    counter_terms: dict | None = None
    evaluation_reasoning: str = ""

    def __post_init__(self):
        if not self.id:
            self.id = f"txn_{uuid.uuid4().hex[:8]}"

    def to_dict(self) -> dict:
        """Serialize to dict matching DET_C1 event schema."""
        return {
            "id": self.id,
            "type": self.type,
            "proposer_role_id": self.proposer_role_id,
            "proposer_country_id": self.proposer_country_id,
            "counterpart_role_id": self.counterpart_role_id,
            "counterpart_country_id": self.counterpart_country_id,
            "terms": self.terms,
            "status": self.status,
            "reasoning": self.reasoning,
            "counter_terms": self.counter_terms,
            "evaluation_reasoning": self.evaluation_reasoning,
        }


# ---------------------------------------------------------------------------
# CONTEXT BUILDERS
# ---------------------------------------------------------------------------

def _build_propose_context(
    agent_country: dict,
    agent_role: dict,
    counterpart_country: dict,
    counterpart_role: dict,
    world_state: dict,
) -> str:
    """Build task-specific context for proposing a transaction."""
    my_id = agent_country.get("id", "")
    their_id = counterpart_country.get("id", "")

    # Resources
    my_treasury = agent_country.get("treasury", 0)
    my_ground = agent_country.get("mil_ground", 0)
    my_naval = agent_country.get("mil_naval", 0)
    my_air = agent_country.get("mil_tactical_air", 0)
    my_nuclear = agent_country.get("nuclear_level", 0)
    my_ai = agent_country.get("ai_level", 0)

    their_treasury = counterpart_country.get("treasury", 0)
    their_ground = counterpart_country.get("mil_ground", 0)
    their_naval = counterpart_country.get("mil_naval", 0)
    their_air = counterpart_country.get("mil_tactical_air", 0)

    at_war_with = agent_country.get("at_war_with", "")
    wars = world_state.get("wars", [])
    are_at_war = _are_at_war(my_id, their_id, wars)

    return f"""# Transaction Proposal Context

## Your Resources
- Treasury: {my_treasury:.1f} coins
- Ground units: {my_ground}, Naval: {my_naval}, Air: {my_air}
- Nuclear L{my_nuclear}, AI L{my_ai}

## Counterpart: {counterpart_role.get('character_name', their_id)} ({counterpart_country.get('sim_name', their_id)})
- Treasury: {their_treasury:.1f} coins
- Ground: {their_ground}, Naval: {their_naval}, Air: {their_air}
- At war with you: {'YES' if are_at_war else 'No'}

## Available Transaction Types
- **coin_transfer**: Give coins to {counterpart_country.get('sim_name', their_id)} (aid, tribute, bribe)
- **arms_sale**: Sell military units for coins (gives: units, receives: coins)
- **arms_gift**: Give military units (build alliance, strengthen partner)
- **tech_transfer**: Share technology access (nuclear/AI research boost)
- **basing_rights**: Let them use your zone (or request access to theirs)
- **ceasefire**: Stop hostilities {'(AVAILABLE — you are at war)' if are_at_war else '(NOT AVAILABLE — not at war)'}
- **peace_treaty**: Formal end to war {'(AVAILABLE)' if are_at_war else '(NOT AVAILABLE)'}
- **alliance**: Mutual defense commitment (will you fight for them?)
- **trade_agreement**: Mutual tariff reduction (both benefit from trade)
- **sanctions_coordination**: Coordinate sanctions against a third party

## Rules
- You can only give what you have (check units/coins)
- Arms sales: typical price is 2 coins per ground unit, 3 per naval/air
- Tech transfer: sharing nuclear/AI gives counterpart +0.1 progress per level shared
- Ceasefire/peace treaty requires active war between you
- Alliance means you MUST defend them if attacked
"""


def _build_evaluate_context(
    agent_country: dict,
    agent_role: dict,
    proposal: TransactionProposal,
) -> str:
    """Build task-specific context for evaluating a received proposal."""
    my_treasury = agent_country.get("treasury", 0)
    my_ground = agent_country.get("mil_ground", 0)
    my_naval = agent_country.get("mil_naval", 0)
    my_air = agent_country.get("mil_tactical_air", 0)

    terms = proposal.terms
    gives = terms.get("gives", {})
    receives = terms.get("receives", {})

    return f"""# Transaction Proposal Received

## Proposal from {proposal.proposer_role_id} ({proposal.proposer_country_id})
- Type: {proposal.type}
- They give: {gives if gives else 'nothing specified'}
- They receive (you give): {receives if receives else 'nothing specified'}
- Their reasoning: {proposal.reasoning}

## Your Resources (what you'd be giving up)
- Treasury: {my_treasury:.1f} coins
- Ground: {my_ground}, Naval: {my_naval}, Air: {my_air}

## Your Options
1. **Accept**: Agree to the deal as proposed
2. **Reject**: Decline the deal entirely
3. **Counter**: Propose modified terms (different amounts, add conditions)

## Considerations
- Does this serve your strategic interests?
- Can you afford what they're asking?
- What's the relationship value — is this ally worth investing in?
- Are the terms fair, or are you being taken advantage of?
- Would a counter-offer be better than outright rejection?
"""


# ---------------------------------------------------------------------------
# LLM INSTRUCTION PROMPTS
# ---------------------------------------------------------------------------

PROPOSE_INSTRUCTION = """Propose a transaction to your counterpart.

Return a JSON object:
{
  "type": "<transaction type from the list above>",
  "terms": {
    "gives": {"<resource>": <amount>, ...},
    "receives": {"<resource>": <amount>, ...}
  },
  "reasoning": "<1-2 sentences: why this deal makes strategic sense>"
}

Resource keys: "coins", "ground_units", "naval_units", "air_units",
"tech_nuclear", "tech_ai", "basing_zone" (zone_id string),
"target_country" (for sanctions_coordination).

For ceasefire/peace_treaty/alliance/trade_agreement: terms can be
{"condition": "description of mutual agreement"}.

Return ONLY valid JSON."""


EVALUATE_INSTRUCTION = """Evaluate this transaction proposal. Decide: accept, reject, or counter.

Return a JSON object:
{
  "decision": "<accept|reject|counter>",
  "counter_terms": null,
  "reasoning": "<1-2 sentences explaining your decision>"
}

If countering, provide counter_terms with modified gives/receives:
{
  "decision": "counter",
  "counter_terms": {
    "gives": {"coins": 3},
    "receives": {"ground_units": 1}
  },
  "reasoning": "I can offer 3 coins but only need 1 ground unit."
}

Return ONLY valid JSON."""


# ---------------------------------------------------------------------------
# PROPOSE — agent generates a transaction proposal
# ---------------------------------------------------------------------------

async def propose_transaction(
    cognitive_blocks: dict,
    agent_country: dict,
    agent_role: dict,
    counterpart_country: dict,
    counterpart_role: dict,
    world_state: dict,
    transaction_type: str | None = None,
) -> TransactionProposal:
    """Agent proposes a transaction to a counterpart.

    Args:
        cognitive_blocks: Agent's 4 cognitive blocks.
        agent_country: Proposer's country data.
        agent_role: Proposer's role data.
        counterpart_country: Counterpart's country data.
        counterpart_role: Counterpart's role data.
        world_state: Current world state.
        transaction_type: Optional type hint (agent may choose freely if None).

    Returns:
        TransactionProposal with status="proposed".
    """
    from engine.services.llm import call_llm
    from engine.config.settings import LLMUseCase
    from engine.agents.decisions import _build_system_prompt, _parse_json

    layer2 = _build_propose_context(
        agent_country, agent_role, counterpart_country, counterpart_role, world_state,
    )

    instruction = PROPOSE_INSTRUCTION
    if transaction_type:
        instruction = f"You want to propose a **{transaction_type}** transaction.\n\n" + instruction

    system = _build_system_prompt(cognitive_blocks, layer2)

    response = await call_llm(
        use_case=LLMUseCase.AGENT_DECISION,
        messages=[{"role": "user", "content": instruction}],
        system=system,
        max_tokens=500,
        temperature=0.6,
    )

    result = _parse_json(response.text)
    if result is None:
        logger.warning("Transaction proposal parse failed for %s", agent_role.get("id", "?"))
        return TransactionProposal(
            type="coin_transfer",
            proposer_role_id=agent_role.get("id", ""),
            proposer_country_id=agent_country.get("id", ""),
            counterpart_role_id=counterpart_role.get("id", ""),
            counterpart_country_id=counterpart_country.get("id", ""),
            terms={"gives": {"coins": 1}, "receives": {}},
            reasoning="parse_error",
        )

    txn_type = result.get("type", transaction_type or "coin_transfer")
    if txn_type not in TRANSACTION_TYPES:
        txn_type = "coin_transfer"

    return TransactionProposal(
        type=txn_type,
        proposer_role_id=agent_role.get("id", ""),
        proposer_country_id=agent_country.get("id", ""),
        counterpart_role_id=counterpart_role.get("id", ""),
        counterpart_country_id=counterpart_country.get("id", ""),
        terms=result.get("terms", {}),
        reasoning=result.get("reasoning", ""),
    )


# ---------------------------------------------------------------------------
# EVALUATE — counterpart reviews and responds to proposal
# ---------------------------------------------------------------------------

async def evaluate_transaction(
    cognitive_blocks: dict,
    agent_country: dict,
    agent_role: dict,
    proposal: TransactionProposal,
) -> dict:
    """Counterpart evaluates a transaction proposal.

    Args:
        cognitive_blocks: Evaluator's 4 cognitive blocks.
        agent_country: Evaluator's country data.
        agent_role: Evaluator's role data.
        proposal: The proposal to evaluate.

    Returns:
        {decision: "accept"|"reject"|"counter", counter_terms: dict|None, reasoning: str}
    """
    from engine.services.llm import call_llm
    from engine.config.settings import LLMUseCase
    from engine.agents.decisions import _build_system_prompt, _parse_json

    layer2 = _build_evaluate_context(agent_country, agent_role, proposal)
    system = _build_system_prompt(cognitive_blocks, layer2)

    response = await call_llm(
        use_case=LLMUseCase.AGENT_DECISION,
        messages=[{"role": "user", "content": EVALUATE_INSTRUCTION}],
        system=system,
        max_tokens=400,
        temperature=0.5,
    )

    result = _parse_json(response.text)
    if result is None:
        logger.warning("Transaction evaluation parse failed")
        return {"decision": "reject", "counter_terms": None, "reasoning": "parse_error"}

    decision = result.get("decision", "reject").lower().strip()
    if decision not in {"accept", "reject", "counter"}:
        decision = "reject"

    return {
        "decision": decision,
        "counter_terms": result.get("counter_terms"),
        "reasoning": result.get("reasoning", ""),
    }


# ---------------------------------------------------------------------------
# EXECUTE — apply accepted transaction to game state (simplified)
# ---------------------------------------------------------------------------

def execute_transaction(
    proposal: TransactionProposal,
    countries: dict[str, dict],
) -> dict[str, Any]:
    """Execute an accepted transaction by modifying country state.

    This is a simplified execution that directly mutates the countries dict.
    A future Transaction Engine will handle this more formally.

    Args:
        proposal: Accepted transaction proposal.
        countries: {country_id: country_data_dict} — will be mutated.

    Returns:
        {success: bool, changes: list[str], errors: list[str]}
    """
    if proposal.status != "accepted":
        return {"success": False, "changes": [], "errors": ["Transaction not accepted"]}

    proposer_cid = proposal.proposer_country_id
    counterpart_cid = proposal.counterpart_country_id
    terms = proposal.terms
    gives = terms.get("gives", {})
    receives = terms.get("receives", {})

    changes: list[str] = []
    errors: list[str] = []

    proposer = countries.get(proposer_cid)
    counterpart = countries.get(counterpart_cid)

    if not proposer or not counterpart:
        return {"success": False, "changes": [], "errors": ["Country not found"]}

    txn_type = proposal.type

    # --- COIN TRANSFER ---
    if txn_type == "coin_transfer":
        coins = float(gives.get("coins", 0))
        p_treasury = proposer.get("treasury", 0)
        if coins > p_treasury:
            coins = p_treasury
            errors.append(f"Reduced coins to available treasury: {coins:.1f}")
        proposer["treasury"] = p_treasury - coins
        counterpart["treasury"] = counterpart.get("treasury", 0) + coins
        changes.append(f"{proposer_cid} transferred {coins:.1f} coins to {counterpart_cid}")

    # --- ARMS SALE (proposer gives units, receives coins) ---
    elif txn_type == "arms_sale":
        _transfer_units(proposer, counterpart, gives, changes, errors, proposer_cid, counterpart_cid)
        # Counterpart pays coins
        coins = float(receives.get("coins", 0))
        c_treasury = counterpart.get("treasury", 0)
        if coins > c_treasury:
            coins = c_treasury
            errors.append(f"Reduced payment to counterpart treasury: {coins:.1f}")
        counterpart["treasury"] = c_treasury - coins
        proposer["treasury"] = proposer.get("treasury", 0) + coins
        changes.append(f"{counterpart_cid} paid {coins:.1f} coins to {proposer_cid}")

    # --- ARMS GIFT ---
    elif txn_type == "arms_gift":
        _transfer_units(proposer, counterpart, gives, changes, errors, proposer_cid, counterpart_cid)

    # --- TECH TRANSFER ---
    elif txn_type == "tech_transfer":
        tech_types = gives.get("tech_nuclear", 0), gives.get("tech_ai", 0)
        if tech_types[0]:
            boost = min(0.3, float(tech_types[0]) * 0.1)
            old = counterpart.get("nuclear_rd_progress", 0)
            counterpart["nuclear_rd_progress"] = old + boost
            changes.append(f"Nuclear tech shared: {counterpart_cid} +{boost:.1f} progress")
        if tech_types[1]:
            boost = min(0.3, float(tech_types[1]) * 0.1)
            old = counterpart.get("ai_rd_progress", 0)
            counterpart["ai_rd_progress"] = old + boost
            changes.append(f"AI tech shared: {counterpart_cid} +{boost:.1f} progress")

    # --- TREATY TYPES (ceasefire, peace, alliance, trade agreement, sanctions coord) ---
    elif txn_type in {"ceasefire", "peace_treaty", "alliance", "trade_agreement", "sanctions_coordination", "basing_rights"}:
        # These are recorded as events — no direct state mutation here.
        # The orchestrator or Live Action Engine processes them.
        changes.append(f"{txn_type} agreed between {proposer_cid} and {counterpart_cid}")

    else:
        errors.append(f"Unknown transaction type: {txn_type}")

    proposal.status = "executed"
    success = len(errors) == 0 or len(changes) > 0

    logger.info("Transaction %s executed: %s (%d changes, %d errors)",
                proposal.id, txn_type, len(changes), len(errors))

    return {"success": success, "changes": changes, "errors": errors}


# ---------------------------------------------------------------------------
# HELPERS
# ---------------------------------------------------------------------------

def _transfer_units(
    from_country: dict,
    to_country: dict,
    gives: dict,
    changes: list[str],
    errors: list[str],
    from_id: str,
    to_id: str,
) -> None:
    """Transfer military units between countries."""
    unit_map = {
        "ground_units": "mil_ground",
        "naval_units": "mil_naval",
        "air_units": "mil_tactical_air",
    }
    for give_key, country_key in unit_map.items():
        amount = int(gives.get(give_key, 0))
        if amount <= 0:
            continue
        available = from_country.get(country_key, 0)
        if amount > available:
            errors.append(f"Reduced {give_key} from {amount} to {available}")
            amount = available
        from_country[country_key] = available - amount
        to_country[country_key] = to_country.get(country_key, 0) + amount
        changes.append(f"{from_id} transferred {amount} {give_key} to {to_id}")


def validate_assets(country: dict, gives: dict) -> tuple[bool, list[str]]:
    """Validate that a country has enough assets to fulfill a transaction.

    Pure function — no DB calls.

    Args:
        country: Country state dict (treasury, mil_ground, etc.).
        gives: Dict of resources the country is giving away.

    Returns:
        (True, []) if valid, (False, ["insufficient X", ...]) if not.
    """
    errors: list[str] = []

    # Coins
    coins_needed = float(gives.get("coins", 0))
    if coins_needed > 0 and country.get("treasury", 0) < coins_needed:
        errors.append(f"insufficient coins: need {coins_needed:.1f}, have {country.get('treasury', 0):.1f}")

    # Ground units
    ground_needed = int(gives.get("ground_units", 0))
    if ground_needed > 0 and country.get("mil_ground", 0) < ground_needed:
        errors.append(f"insufficient ground_units: need {ground_needed}, have {country.get('mil_ground', 0)}")

    # Naval units
    naval_needed = int(gives.get("naval_units", 0))
    if naval_needed > 0 and country.get("mil_naval", 0) < naval_needed:
        errors.append(f"insufficient naval_units: need {naval_needed}, have {country.get('mil_naval', 0)}")

    # Air units
    air_needed = int(gives.get("air_units", 0))
    if air_needed > 0 and country.get("mil_tactical_air", 0) < air_needed:
        errors.append(f"insufficient air_units: need {air_needed}, have {country.get('mil_tactical_air', 0)}")

    # Tech/basing: always valid (replicable, no depletion)

    if errors:
        return (False, errors)
    return (True, [])


def _are_at_war(country_a: str, country_b: str, wars: list[dict]) -> bool:
    """Check if two countries are on opposite sides of any war."""
    for w in wars:
        a_set = set(w.get("belligerents_a", []))
        b_set = set(w.get("belligerents_b", []))
        if (country_a in a_set and country_b in b_set) or \
           (country_a in b_set and country_b in a_set):
            return True
    return False


# ---------------------------------------------------------------------------
# FULL TRANSACTION FLOW — convenience function
# ---------------------------------------------------------------------------

async def run_transaction_flow(
    proposer_agent,   # LeaderAgent
    counterpart_agent,  # LeaderAgent
    world_state: dict,
    countries: dict[str, dict],
    transaction_type: str | None = None,
) -> TransactionProposal:
    """Run the full propose → evaluate → execute flow.

    Args:
        proposer_agent: The agent initiating the transaction.
        counterpart_agent: The agent receiving the proposal.
        world_state: Current world state dict.
        countries: Country data dicts (for execution).
        transaction_type: Optional type hint.

    Returns:
        TransactionProposal with final status.
    """
    # Step 1: Propose
    proposer_blocks = proposer_agent._get_cognitive_blocks()
    proposal = await propose_transaction(
        cognitive_blocks=proposer_blocks,
        agent_country=proposer_agent.country,
        agent_role=proposer_agent.role,
        counterpart_country=counterpart_agent.country,
        counterpart_role=counterpart_agent.role,
        world_state=world_state,
        transaction_type=transaction_type,
    )

    logger.info("Transaction proposed: %s → %s (%s): %s",
                proposal.proposer_role_id, proposal.counterpart_role_id,
                proposal.type, proposal.reasoning)

    # Validate proposer has the assets to give
    if proposal.type in RESOURCE_TRANSACTIONS:
        valid, asset_errors = validate_assets(
            proposer_agent.country, proposal.terms.get("gives", {}))
        if not valid:
            proposal.status = "failed_validation"
            proposal.evaluation_reasoning = f"Proposer asset check failed: {'; '.join(asset_errors)}"
            logger.warning("Transaction %s failed validation: %s", proposal.id, asset_errors)
            proposer_agent.cognitive.add_decision(
                "transaction_failed_validation",
                f"Proposal {proposal.type} failed: {'; '.join(asset_errors)[:80]}",
            )
            return proposal

    # Record in proposer memory
    proposer_agent.cognitive.add_decision(
        "transaction_proposed",
        f"Proposed {proposal.type} to {proposal.counterpart_role_id}: {proposal.reasoning[:80]}",
    )

    # Step 2: Evaluate
    counterpart_blocks = counterpart_agent._get_cognitive_blocks()
    evaluation = await evaluate_transaction(
        cognitive_blocks=counterpart_blocks,
        agent_country=counterpart_agent.country,
        agent_role=counterpart_agent.role,
        proposal=proposal,
    )

    decision = evaluation["decision"]
    # Normalize: LLM returns "accept" but execution gate checks "accepted"
    proposal.status = "accepted" if decision == "accept" else decision
    proposal.evaluation_reasoning = evaluation.get("reasoning", "")
    proposal.counter_terms = evaluation.get("counter_terms")

    logger.info("Transaction %s %s by %s: %s",
                proposal.id, proposal.status, proposal.counterpart_role_id,
                proposal.evaluation_reasoning)

    # Record in counterpart memory
    counterpart_agent.cognitive.add_decision(
        f"transaction_{proposal.status}",
        f"{proposal.status.upper()} {proposal.type} from {proposal.proposer_role_id}: {proposal.evaluation_reasoning[:80]}",
    )

    # Step 2b: Handle counter-offer (1 counter max per spec)
    if proposal.status == "counter" and proposal.counter_terms:
        counter_proposal = TransactionProposal(
            type=proposal.type,
            proposer_role_id=proposal.counterpart_role_id,
            proposer_country_id=proposal.counterpart_country_id,
            counterpart_role_id=proposal.proposer_role_id,
            counterpart_country_id=proposal.proposer_country_id,
            terms=proposal.counter_terms,
            status="proposed",
            reasoning=proposal.evaluation_reasoning,
        )
        counter_eval = await evaluate_transaction(
            cognitive_blocks=proposer_blocks,
            agent_country=proposer_agent.country,
            agent_role=proposer_agent.role,
            proposal=counter_proposal,
        )
        if counter_eval["decision"] == "accept":
            proposal.status = "accepted"
            proposal.terms = proposal.counter_terms  # execute with counter terms
        else:
            proposal.status = "declined"

        # Record in proposer memory
        proposer_agent.cognitive.add_decision(
            f"counter_{counter_eval['decision']}",
            f"Counter from {proposal.counterpart_role_id}: {counter_eval['decision'].upper()} — {counter_eval.get('reasoning', '')[:80]}",
        )

    # Step 3: Validate both sides before execution
    exec_result = {"success": False, "changes": [], "errors": []}
    if proposal.status == "accepted":
        if proposal.type in RESOURCE_TRANSACTIONS:
            # Validate proposer's gives
            p_valid, p_errors = validate_assets(
                proposer_agent.country, proposal.terms.get("gives", {}))
            # Validate counterpart's gives (what they receive from proposer's perspective)
            c_valid, c_errors = validate_assets(
                counterpart_agent.country, proposal.terms.get("receives", {}))
            if not p_valid or not c_valid:
                all_errors = p_errors + c_errors
                proposal.status = "failed_validation"
                proposal.evaluation_reasoning = f"Pre-exec validation failed: {'; '.join(all_errors)}"
                logger.warning("Transaction %s failed pre-exec validation: %s",
                               proposal.id, all_errors)
                return proposal

        exec_result = execute_transaction(proposal, countries)
        logger.info("Transaction executed: %s", exec_result["changes"])

    return proposal
