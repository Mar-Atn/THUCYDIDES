# Information Scoping — What Each Role Can See

**Status:** Draft for Marat alignment
**Principle:** A participant sees what a real person in that role would see. No more, no less.

---

## PUBLIC (visible to ALL participants)

| Information | Detail |
|---|---|
| Map (hex grid, country borders, chokepoints) | Full map always visible |
| Unit positions (all countries, active units) | No fog of war — leaders get military briefings |
| Country names, leaders, regime types | Who's who — public knowledge |
| All countries' official briefings | Published country profiles |
| All roles with short official bio | Public-facing biography (name, title, age, faction — NOT private objectives or ticking clock) |
| All countries' GDP | Published economic statistics |
| All countries' inflation | Published data |
| All countries' stability | Published — political risk assessments are public |
| All countries' political support | Published — polling data is public |
| All countries' economic structure (sectors) | Published data |
| All sanctions (who sanctions whom, level) | Published policy — announced publicly |
| All tariffs (who tariffs whom, level) | Published trade policy |
| Oil price | Published global figure |
| Stock market indexes (3 regional) | Published financial data |
| Debt ratio (all countries) | Published — credit agencies report this |
| All organization memberships | Published — who's in NATO/BRICS/OPEC/EU etc. |
| Nuclear capability tiers (confirmed, all countries) | Public — everyone knows who has nukes |
| Combat results (who attacked, who lost, aftermath) | Public — visible on map + news |
| Public statements | Broadcast to all, attributed |
| Declared wars (combat happening on map) | Visible from unit movements + combat events |
| Active blockades | Visible on map |
| Organization existence + purpose | Known institutions |
| Public agreements | Name + type + signatories + terms |
| All bilateral relationship statuses | Public — diplomatic status is observable (allied/friendly/neutral/tense/hostile/military_conflict/armistice/peace) |
| Election schedules | Known calendar |
| Basing rights (who hosts whom) | Published — military bases are visible |
| Nuclear tests (surface) | Global alert |
| Nuclear missile launch (alert) | Global alert — "launch detected" |
| Nuclear missile launch (detail: launcher + target) | T3 countries only — telemetry from early warning systems |

## COUNTRY-LEVEL (visible to all roles within the same country)

| Information | Detail |
|---|---|
| Own treasury (exact balance) | Internal — not published |
| Own war tiredness | Internal — morale is not published |
| Own military production levels + capacity | Internal military planning |
| Own reserve units (count, types) | Hidden from other countries — only active visible on map |
| Own budget decisions (current + history) | Internal policy record |
| Own nuclear/AI tech level + R&D progress | Tech status |
| Own military: all units (active + reserve + embarked) | Full force picture including reserves |
| Own budget (revenue, spending, deficit) | Financial internals |

## ROLE-SPECIFIC (visible ONLY to the specific role)

| Information | HoS | Military | Economic | Intelligence | Diplomat | Opposition | Tycoon |
|---|---|---|---|---|---|---|---|
| Personal coins balance | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ |
| Own covert op card pool | — | — | — | ✓ | — | — | — |
| Intel reports received | ✓ | — | — | ✓ | — | — | — |
| Covert op results (own operations only) | — | — | — | ✓ | — | — | — |
| Assassination/sabotage cards | — | — | — | ✓ | — | ✓ (some) | — |
| Propaganda/disinfo cards | ✓ | — | — | ✓ | — | ✓ | ✓ |
| Election meddling cards | — | — | — | ✓ | — | ✓ | — |
| Private conversation transcripts | Own only | Own only | Own only | Own only | Own only | Own only | Own only |
| Secret agreements signed | Only signatories see them — not other roles in same country |
| Personal tech investments made | — | — | — | — | — | — | ✓ |
| Own memory (strategic notes) | Own only | Own only | Own only | Own only | Own only | Own only | Own only |
| Own objectives + ticking clock | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ |

**Rule: anything NOT listed in the tiers above is NOT visible.** If it's not PUBLIC, COUNTRY-LEVEL, or ROLE-SPECIFIC — it doesn't exist for that participant.

**Exceptions:** Moderator (facilitator) sees everything. Engine modules see everything (they need full state to calculate). Only PARTICIPANT-FACING interfaces are scoped.

---

## BILATERAL RELATIONSHIP MODEL (auto-updated by engine, public)

| Status | How you get IN | How you get OUT |
|---|---|---|
| **allied** | Agreement signed | Breaks if ally attacked, or agreement dissolved |
| **friendly** | Trade deal, positive interactions | Degrades from sanctions/tariffs |
| **neutral** | Default starting point | — |
| **tense** | Sanctions imposed, military buildup near border | De-escalates if sanctions lifted |
| **hostile** | Heavy sanctions + tariffs | De-escalates slowly if sanctions removed |
| **military_conflict** | **One side attacks the other** | **LOCKED — only exits via signed armistice or peace treaty. No automatic cooling.** |
| **armistice** | Signed agreement | Degrades back to military_conflict if breached (attack after signing) |
| **peace** | Signed peace treaty | Permanent end to that conflict |

Updates automatically at end of each round based on events (combat → military_conflict, agreement signed → armistice/peace, sanctions → tense/hostile). Rule-based, no LLM needed.

---

## HISTORY RULE

**For any information a role can see NOW, the full round-by-round history of that data is also available on request.** Example: if GDP is public, GDP history (R0→R1→R2...) is also public. If treasury is country-level, treasury history is available to all roles in that country. The scoping tier of the data determines the scoping tier of its history.

---

*Decisions (Marat 2026-04-08): GDP, economic structure, sanctions, tariffs, stability, political support, inflation, debt ratio, nuclear tiers, org memberships, combat results — all public. Treasury, war tiredness, R&D progress — internal. Bond yields and gold prices do not exist in the SIM (remove from Observatory).*
