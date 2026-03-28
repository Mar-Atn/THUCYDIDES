"""
TTT SEED — Transaction (Market) Engine
=======================================
Real-time bilateral transfers. Both parties must confirm.
No calculation, no dice. Pure data operations.

Handles: coin transfers, arms transfers, tech transfers,
         basing rights, treaties, organization creation.

Author: ATLAS (World Model Engineer)
Version: 2.0 (SEED)
"""

import copy
import time
from typing import Dict, List, Optional, Any, Tuple

from world_state import WorldState, UNIT_TYPES, clamp


# ---------------------------------------------------------------------------
# TRANSACTION TYPES
# ---------------------------------------------------------------------------

TRANSACTION_TYPES = {
    "coin_transfer": {
        "exclusive": True,       # sender loses, receiver gains
        "requires_balance": True,
        "authorization": ["head_of_state"],
        "reversible": False,
    },
    "arms_transfer": {
        "exclusive": True,
        "requires_balance": True,
        "authorization": ["head_of_state", "military_chief"],
        "reversible": False,
        "reduced_effectiveness_rounds": 1,
    },
    "tech_transfer": {
        "exclusive": False,  # replicable: receiver gains, sender keeps
        "requires_balance": False,
        "authorization": ["head_of_state"],
        "reversible": False,
    },
    "basing_rights": {
        "exclusive": False,  # replicable: access granted, sovereignty retained
        "requires_balance": False,
        "authorization": ["head_of_state"],
        "reversible": True,  # uniquely revocable by host
    },
    "treaty": {
        "exclusive": False,
        "requires_balance": False,
        "authorization": ["head_of_state"],
        "reversible": False,
        "stored_not_enforced": True,
    },
    "agreement": {
        "exclusive": False,
        "requires_balance": False,
        "authorization": ["head_of_state"],
        "reversible": False,
        "stored_not_enforced": False,  # ceasefire/peace has mechanical effect
    },
    "org_creation": {
        "exclusive": False,
        "requires_balance": False,
        "authorization": ["head_of_state"],
        "reversible": False,
    },
}


# ---------------------------------------------------------------------------
# TRANSACTION ENGINE
# ---------------------------------------------------------------------------

class TransactionEngine:
    """Processes bilateral transactions between countries/roles.

    All transactions require confirmation from both parties.
    Execution is immediate upon confirmation.
    All transactions are logged with timestamp, parties, and terms.
    """

    def __init__(self, world_state: WorldState):
        self.ws = world_state
        self.transaction_log: List[dict] = []
        self.pending_transactions: List[dict] = []
        self._tx_counter = 0

    def propose_transaction(self, sender: str, receiver: str,
                            tx_type: str, details: dict) -> dict:
        """Create a transaction proposal. Returns the proposal with an ID."""
        self._tx_counter += 1
        proposal = {
            "tx_id": self._tx_counter,
            "sender": sender,
            "receiver": receiver,
            "tx_type": tx_type,
            "details": copy.deepcopy(details),
            "status": "pending",
            "timestamp": time.time(),
            "round": self.ws.round_num,
            "sender_confirmed": True,  # proposer auto-confirms
            "receiver_confirmed": False,
        }

        # Validate sender's ability to propose
        validation = self._validate_proposal(proposal)
        if not validation["valid"]:
            proposal["status"] = "rejected"
            proposal["rejection_reason"] = validation["reason"]
            self.transaction_log.append(proposal)
            return proposal

        self.pending_transactions.append(proposal)
        return proposal

    def confirm_transaction(self, tx_id: int, confirmer: str) -> dict:
        """Receiver confirms a pending transaction. Executes if all confirmed."""
        for tx in self.pending_transactions:
            if tx["tx_id"] == tx_id and tx["status"] == "pending":
                if confirmer == tx["receiver"] or confirmer == tx["sender"]:
                    if confirmer == tx["receiver"]:
                        tx["receiver_confirmed"] = True
                    if confirmer == tx["sender"]:
                        tx["sender_confirmed"] = True

                    if tx["sender_confirmed"] and tx["receiver_confirmed"]:
                        return self._execute_transaction(tx)
                    return tx
        return {"error": f"Transaction {tx_id} not found or not pending"}

    def reject_transaction(self, tx_id: int, rejector: str) -> dict:
        """Reject a pending transaction."""
        for tx in self.pending_transactions:
            if tx["tx_id"] == tx_id and tx["status"] == "pending":
                tx["status"] = "rejected"
                tx["rejected_by"] = rejector
                self.pending_transactions.remove(tx)
                self.transaction_log.append(tx)
                return tx
        return {"error": f"Transaction {tx_id} not found or not pending"}

    def process_transaction(self, sender: str, receiver: str,
                            tx_type: str, details: dict) -> dict:
        """Validate and execute a bilateral transaction immediately.
        Used when both parties have already agreed (e.g., AI negotiation result).
        """
        self._tx_counter += 1
        tx = {
            "tx_id": self._tx_counter,
            "sender": sender,
            "receiver": receiver,
            "tx_type": tx_type,
            "details": copy.deepcopy(details),
            "status": "pending",
            "timestamp": time.time(),
            "round": self.ws.round_num,
            "sender_confirmed": True,
            "receiver_confirmed": True,
        }

        validation = self._validate_proposal(tx)
        if not validation["valid"]:
            tx["status"] = "failed"
            tx["failure_reason"] = validation["reason"]
            self.transaction_log.append(tx)
            self.ws.log_event({
                "type": "transaction_failed",
                "tx_type": tx_type,
                "sender": sender,
                "receiver": receiver,
                "reason": validation["reason"],
            })
            return tx

        return self._execute_transaction(tx)

    # --- Validation ---

    def _validate_proposal(self, tx: dict) -> dict:
        """Validate a transaction proposal."""
        tx_type = tx["tx_type"]
        sender = tx["sender"]
        receiver = tx["receiver"]
        details = tx["details"]

        if tx_type not in TRANSACTION_TYPES:
            return {"valid": False, "reason": f"Unknown transaction type: {tx_type}"}

        spec = TRANSACTION_TYPES[tx_type]

        # Check sender exists
        sender_country = self._resolve_country(sender)
        if not sender_country and tx_type != "treaty":
            return {"valid": False, "reason": f"Sender {sender} not found"}

        # Check receiver exists
        receiver_country = self._resolve_country(receiver)
        if not receiver_country and tx_type not in ("treaty", "org_creation"):
            return {"valid": False, "reason": f"Receiver {receiver} not found"}

        # Balance check for exclusive transfers
        if spec["requires_balance"] and spec["exclusive"]:
            if tx_type == "coin_transfer":
                amount = details.get("amount", 0)
                if amount <= 0:
                    return {"valid": False, "reason": "Amount must be positive"}
                treasury = self.ws.countries[sender_country]["economic"]["treasury"]
                if amount > treasury:
                    return {"valid": False,
                            "reason": f"Insufficient funds: {sender} has {treasury}, needs {amount}"}

            elif tx_type == "arms_transfer":
                unit_type = details.get("unit_type", "ground")
                count = details.get("count", 0)
                if count <= 0:
                    return {"valid": False, "reason": "Count must be positive"}
                if unit_type not in UNIT_TYPES:
                    return {"valid": False, "reason": f"Unknown unit type: {unit_type}"}
                available = self.ws.countries[sender_country]["military"].get(unit_type, 0)
                if count > available:
                    return {"valid": False,
                            "reason": f"Insufficient units: {sender} has {available} {unit_type}, needs {count}"}

        # Authorization check
        if spec["authorization"]:
            valid_auth = self._check_authorization(sender, sender_country, spec["authorization"])
            if not valid_auth:
                return {"valid": False, "reason": f"Authorization failed for {sender}"}

        return {"valid": True, "reason": ""}

    def _check_authorization(self, actor: str, country_id: str,
                             required_roles: List[str]) -> bool:
        """Check if actor has authorization. For AI test, country-level actors auto-pass."""
        # In test mode, the country head of state is always authorized
        if actor == country_id:
            return True
        # Check if the actor is a role with the required authority
        role = self.ws.roles.get(actor)
        if role and role["country_id"] == country_id:
            if role["is_head_of_state"]:
                return True
            if "military_chief" in required_roles and role["is_military_chief"]:
                return True
        return True  # permissive for AI test

    def _resolve_country(self, actor: str) -> Optional[str]:
        """Resolve an actor ID to a country ID."""
        if actor in self.ws.countries:
            return actor
        role = self.ws.roles.get(actor)
        if role:
            return role["country_id"]
        return None

    # --- Execution ---

    def _execute_transaction(self, tx: dict) -> dict:
        """Execute a validated, confirmed transaction."""
        tx_type = tx["tx_type"]
        sender = tx["sender"]
        receiver = tx["receiver"]
        details = tx["details"]

        sender_country = self._resolve_country(sender)
        receiver_country = self._resolve_country(receiver)

        if tx_type == "coin_transfer":
            amount = details["amount"]
            self.ws.countries[sender_country]["economic"]["treasury"] -= amount
            self.ws.countries[receiver_country]["economic"]["treasury"] += amount
            tx["execution_details"] = {
                "amount_transferred": amount,
                "sender_new_treasury": self.ws.countries[sender_country]["economic"]["treasury"],
                "receiver_new_treasury": self.ws.countries[receiver_country]["economic"]["treasury"],
            }

        elif tx_type == "arms_transfer":
            unit_type = details["unit_type"]
            count = details["count"]
            self.ws.countries[sender_country]["military"][unit_type] -= count
            self.ws.countries[receiver_country]["military"][unit_type] = (
                self.ws.countries[receiver_country]["military"].get(unit_type, 0) + count
            )
            # Transferred units have reduced effectiveness for 1 round
            tx["execution_details"] = {
                "unit_type": unit_type,
                "count": count,
                "reduced_effectiveness_until_round": self.ws.round_num + 1,
            }

        elif tx_type == "tech_transfer":
            tech_domain = details.get("domain", "ai")  # "ai" or "nuclear"
            # Replicable: receiver gains sender's level, sender keeps
            sender_level = self.ws.countries[sender_country]["technology"].get(
                f"{tech_domain}_level", 0)
            receiver_level = self.ws.countries[receiver_country]["technology"].get(
                f"{tech_domain}_level", 0)
            if sender_level > receiver_level:
                # Transfer grants one level up, not full sender level
                new_level = min(receiver_level + 1, sender_level)
                self.ws.countries[receiver_country]["technology"][f"{tech_domain}_level"] = new_level
                tx["execution_details"] = {
                    "domain": tech_domain,
                    "receiver_old_level": receiver_level,
                    "receiver_new_level": new_level,
                }
            else:
                tx["execution_details"] = {"domain": tech_domain, "no_advancement": True}

        elif tx_type == "basing_rights":
            zone_id = details.get("zone_id", "")
            self.ws.basing_rights.append({
                "host": sender_country,
                "guest": receiver_country,
                "zone": zone_id,
                "granted_round": self.ws.round_num,
                "revoked": False,
            })
            tx["execution_details"] = {"zone": zone_id}

        elif tx_type == "treaty":
            treaty_text = details.get("text", "")
            signatories = details.get("signatories", [sender, receiver])
            treaty = {
                "id": f"treaty_{len(self.ws.treaties) + 1}",
                "text": treaty_text,
                "signatories": signatories,
                "signed_round": self.ws.round_num,
                "active": True,
            }
            self.ws.treaties.append(treaty)
            tx["execution_details"] = {"treaty_id": treaty["id"]}

        elif tx_type == "agreement":
            agreement_name = details.get("name", "Unnamed Agreement")
            agreement_text = details.get("text", "")
            agreement_subtype = details.get("subtype", "general")  # ceasefire, peace, trade, alliance
            signatories = details.get("signatories", [sender_country, receiver_country])
            agreement = {
                "id": f"agreement_{len(self.ws.treaties) + 1}",
                "name": agreement_name,
                "subtype": agreement_subtype,
                "text": agreement_text,
                "signatories": signatories,
                "signed_round": self.ws.round_num,
                "active": True,
            }
            self.ws.treaties.append(agreement)
            tx["execution_details"] = {"agreement_id": agreement["id"]}

            # Ceasefire / peace mechanical effect: end active war between signatories
            if agreement_subtype in ("ceasefire", "peace"):
                wars_to_remove = []
                for i, war in enumerate(self.ws.wars):
                    attacker = war.get("attacker")
                    defender = war.get("defender")
                    attacker_allies = war.get("allies", {}).get("attacker", [])
                    defender_allies = war.get("allies", {}).get("defender", [])
                    all_attacker_side = [attacker] + attacker_allies
                    all_defender_side = [defender] + defender_allies
                    # Check if both signatories are on opposing sides of this war
                    s_on_atk = [s for s in signatories if s in all_attacker_side]
                    s_on_def = [s for s in signatories if s in all_defender_side]
                    if s_on_atk and s_on_def:
                        wars_to_remove.append(i)
                # Remove wars in reverse order to preserve indices
                for i in reversed(wars_to_remove):
                    ended_war = self.ws.wars.pop(i)
                    self.ws.log_event({
                        "type": "ceasefire",
                        "agreement_id": agreement["id"],
                        "ended_war": ended_war,
                        "signatories": signatories,
                    })
                tx["execution_details"]["wars_ended"] = len(wars_to_remove)

        elif tx_type == "org_creation":
            org_name = details.get("name", "New Organization")
            members = details.get("members", [sender_country, receiver_country])
            purpose = details.get("purpose", "")
            org = {
                "id": f"org_{org_name.lower().replace(' ', '_')}",
                "sim_name": org_name,
                "parallel": "",
                "decision_rule": details.get("decision_rule", "consensus"),
                "members": members,
                "purpose": purpose,
                "created_round": self.ws.round_num,
            }
            self.ws.organizations.append(org)
            self.ws.org_memberships[org["id"]] = members
            tx["execution_details"] = {"org_id": org["id"]}

        tx["status"] = "executed"
        tx["executed_timestamp"] = time.time()

        # Remove from pending
        if tx in self.pending_transactions:
            self.pending_transactions.remove(tx)

        # Log
        self.transaction_log.append(tx)
        self.ws.log_event({
            "type": "transaction",
            "tx_type": tx_type,
            "sender": sender,
            "receiver": receiver,
            "details": details,
            "tx_id": tx["tx_id"],
        })

        return tx

    def revoke_basing_rights(self, host_country: str, guest_country: str,
                             zone_id: str) -> dict:
        """Host country revokes basing rights. Unilateral."""
        for br in self.ws.basing_rights:
            if (br["host"] == host_country and br["guest"] == guest_country
                    and br["zone"] == zone_id and not br["revoked"]):
                br["revoked"] = True
                br["revoked_round"] = self.ws.round_num
                self.ws.log_event({
                    "type": "basing_rights_revoked",
                    "host": host_country,
                    "guest": guest_country,
                    "zone": zone_id,
                })
                return {"success": True, "revoked": br}
        return {"success": False, "reason": "Basing rights not found"}

    # --- G10: Personal Wallets ---

    def execute_personal_transfer(self, from_entity: str, to_entity: str,
                                   amount: float, from_type: str = 'role',
                                   to_type: str = 'role') -> dict:
        """Transfer coins between individuals, or between individual and country.

        from_type/to_type: 'role' (personal wallet) or 'country' (state treasury)
        """
        # Get source balance
        if from_type == 'role':
            source = self.ws.get_role(from_entity)
            if not source:
                return {"success": False, "reason": f"Role {from_entity} not found"}
            balance = source.get('personal_coins', 0)
            if balance < amount:
                return {"success": False, "reason": "Insufficient personal funds"}
            source['personal_coins'] -= amount
        else:
            source_country = self.ws.countries.get(from_entity)
            if not source_country:
                return {"success": False, "reason": f"Country {from_entity} not found"}
            if source_country['economic']['treasury'] < amount:
                return {"success": False, "reason": "Insufficient treasury"}
            source_country['economic']['treasury'] -= amount

        # Credit destination
        if to_type == 'role':
            dest = self.ws.get_role(to_entity)
            if not dest:
                # Rollback source
                if from_type == 'role':
                    self.ws.get_role(from_entity)['personal_coins'] += amount
                else:
                    self.ws.countries[from_entity]['economic']['treasury'] += amount
                return {"success": False, "reason": f"Role {to_entity} not found"}
            dest['personal_coins'] = dest.get('personal_coins', 0) + amount
        else:
            dest_country = self.ws.countries.get(to_entity)
            if not dest_country:
                # Rollback source
                if from_type == 'role':
                    self.ws.get_role(from_entity)['personal_coins'] += amount
                else:
                    self.ws.countries[from_entity]['economic']['treasury'] += amount
                return {"success": False, "reason": f"Country {to_entity} not found"}
            dest_country['economic']['treasury'] += amount

        result = {
            "success": True,
            "from": from_entity,
            "to": to_entity,
            "amount": amount,
            "from_type": from_type,
            "to_type": to_type,
            "note": f"Personal transfer: {amount} coins from {from_entity} to {to_entity}"
        }

        self.ws.log_event({
            "type": "personal_transfer",
            "from": from_entity,
            "to": to_entity,
            "amount": amount,
            "from_type": from_type,
            "to_type": to_type,
        })

        self.transaction_log.append({
            "tx_id": self._tx_counter + 1,
            "tx_type": "personal_transfer",
            "sender": from_entity,
            "receiver": to_entity,
            "details": {"amount": amount, "from_type": from_type, "to_type": to_type},
            "status": "executed",
            "round": self.ws.round_num,
        })
        self._tx_counter += 1

        return result

    def get_pending_for(self, actor: str) -> List[dict]:
        """Get all pending transactions where actor is the receiver."""
        country_id = self._resolve_country(actor)
        return [
            tx for tx in self.pending_transactions
            if self._resolve_country(tx["receiver"]) == country_id
        ]

    def get_transaction_history(self, country_id: Optional[str] = None) -> List[dict]:
        """Get executed transaction history, optionally filtered by country."""
        if country_id is None:
            return [tx for tx in self.transaction_log if tx["status"] == "executed"]
        return [
            tx for tx in self.transaction_log
            if tx["status"] == "executed" and (
                self._resolve_country(tx["sender"]) == country_id
                or self._resolve_country(tx["receiver"]) == country_id
            )
        ]
