# Action Review Changelog — Master Change List
## All changes agreed during Marat-MARCO action-by-action review (2026-03-30)

---

## REGULAR INPUTS (1-6)

### #1 Budget Allocation
- Maintenance shown as FIXED cost BEFORE discretionary split
- Tech R&D: acceleration options (Normal/x2/x3) with hidden breakthrough threshold
- AI private investment matching (hidden mechanic — doubles AI track progress)
- Revenue display: "Revenue X, Maintenance Y, Discretionary Z — split Z across buckets"

### #2 Oil Production
- 5 levels: Min / Low / Normal / High / Max (was 3)
- Prisoner's dilemma confirmed — restriction can backfire if others produce more
- Demand destruction at high prices limits restriction efficiency

### #3 Tariffs
- Per-sector granularity available: default = one level for all 4 sectors, expandable to set independently (resources/industry/services/technology)
- Engine already has sector weights — accepts per-sector input

### #4 Sanctions
- S-curve effectiveness: coverage 0.3→10%, 0.5→20%, 0.7→60%, 0.9→90%
- Coverage = weighted by GDP share × sanctions level / 3
- Imposer pays cost based on bilateral trade weight
- Coalition matters — West alone = modest. Add swing states = serious. Cathay joins = devastating.

### #5 Mobilization
- FINITE DEPLETABLE POOL per country (not repeatable)
- Partial = half remaining pool. Full = all remaining pool. Never recovers.
- Ruthenia and Sarmatia already partially mobilized at game start
- Stability cost varies by country type (democracy at peace -1.5, democracy at war -0.5, autocracy -0.3, under invasion -0.2)
- Columbia mobilization needs parliament approval (no mechanic — just stated)
- Pool sizes per country defined

### #6 Militia
- Available only when homeland under attack
- 1-3 units, 0.5× combat effectiveness, minor stability cost
- No change from previous

---

## MILITARY (7-13)

### #7 Ground Attack — MAJOR REVISION
- Moderator MUST be present. Both commanders available real-time.
- NO fog of war — all units visible. Modifiers HIDDEN until after roll.
- Real dice or app dice. Both roll, moderator inputs.
- Attacker needs ≥ defender + 1 to win. Ties = defender holds.
- Simplified modifiers (integers only):
  - AI L4: +0 to +1 (random, determined once when L4 reached)
  - Low morale: -1 (stability ≤ 3)
  - Die Hard: +1 defender
  - Amphibious: -1 attacker
  - Air support: +1 defender (yes/no binary)
  - "Fatherland" appeal: +1 one-time card, 60% success, delayed risk 2 rounds later
- REMOVED: naval support modifier, militia modifier, home territory, capital, scaled air support
- Ships carry 1 ground unit + up to 2 air units. Transport between rounds. Attack adjacent land from ship.
- Amphibious: -1 modifier replaces 3:1 ratio requirement

### #8 Blockade — MAJOR REVISION
- GROUND FORCES ONLY can blockade (not naval superiority)
- Chokepoint blockade: ground forces on the shore
- Formosa special: Partial = Strait only. Full = 3+ sea zones around island.
- Partial deblocking of Formosa: 1 friendly ship arriving at any adjacent zone → instant downgrade to partial. Ship doesn't fight — just presence.
- Breaking full blockade: destroy ALL military units at chokepoint, or blocker lifts voluntarily
- Full or Partial levels for all blockades

### #9 Naval Bombardment
- No change — 10% per ship, safe, slow, preparation tool

### #10 Air Strike
- Full system confirmed: AD interception with degrading probability, 15% hit per survivor, air destroyed if intercepted, airfield vulnerability, carrier ops
- No change from earlier revision

### #11 Strategic Missile / Nuclear — MAJOR REVISION
- 5-tier system: subsurface test / open test / conventional missile / single nuclear / massive nuclear
- 10-minute authorization clock (SIM enters special mode)
- 10-minute flight time after launch
- Detection tiers: L3+ for subsurface test, everyone for open test, L2+ for missile launches
- Country-specific authorization: Columbia 3-person, Cathay 3-person, Europe AI gate, Sarmatia 2-person, Choson/Persia/Levantia HoS alone
- Response options during flight: intercept (coalition AD), counter-launch, massive counter-attack, do nothing
- Nuclear unknown until impact — nobody knows if conventional or nuclear during flight

### #12 Nuclear Test — covered in #11

### #13 Troop Deployment — no change

---

## INTELLIGENCE / COVERT (14-18)

### #14 Intelligence — MAJOR REVISION (renamed from Espionage)
- Called "INTELLIGENCE" not espionage
- Per INDIVIDUAL pool (not per country) — varies by role (intel chief 6-8, HoS 3-4, military 2-3, etc.)
- ANY role with intelligence access can use (not just HoS/intel chief)
- Always returns an answer — never "failed, no info"
- Accuracy varies: hard facts 85-90%, diplomatic secrets 70%, intentions 50-60%, aggressive/impractical 40%
- Wrong answers look identical to right ones
- Reports arrive in 5-10 minutes as styled classified artefacts
- Intelligence as tradeable service (no mechanic — participants trade naturally)
- Cross-checking same question from different intelligence services to verify
- Can be sold as a service (pay someone to use their requests)

### #15 Sabotage
- Separate limited pool (2-3 cards per game per eligible role)
- Choose: military target / economic target / technology target
- Success/failure only — probabilistic (40% base + AI + intel chief bonuses)
- Results revealed publicly at Phase B world update (no attribution)
- Attribution hidden unless discovered through intelligence or leak

### #16 Cyber Attack
- Separate pool (2-3 cards)
- Effects simplified: steal coins / reduce military production / undermine GDP (-1%)
- Low impact, scarce cards
- 50% base success, AI tech level critical

### #17 Disinformation
- Separate pool (2-3 cards)
- Target: political support -3%, stability -0.3
- 55% base success (easiest covert op)
- Very hard to trace (~60% attribution accuracy even with investigation)

### #18 Election Meddling
- 1 card per game
- Works with or without election (affects support/attitude if no election)
- Choose country, choose who to support/work against
- 2-5% impact
- Risk of exposure — damages the candidate you tried to help

---

## POLITICAL (19-25)

### #19 Arrest — SIMPLIFIED
- Moderator present. Order in app, moderator executes.
- Target out of play until released.
- Democracy: AI Court between rounds (arguments → verdict)
- Autocracy: indefinite, no court
- NO stability or support cost. Pure player-removal.

### #20 Fire / Reassign
- Moderator present. Immediate loss of role powers. Person stays in play.
- Columbia: Parliament must confirm. Can block. "Acting" status if blocked.
- No stability or support cost.

### #21 Propaganda
- Spend coins for support boost. Diminishing returns like a drug.
- 1 coin: +2-3%, up to cap +10%. AI L3+ gets 50% more effectiveness.
- Oversaturation with repeated use.

### #22 Assassination
- 1 card per game per eligible role
- Domestic: 60% hit. International: 20% default, Levantia 50%, Sarmatia 30%
- Hit = 50/50 kill/survive (injured + martyr effect)
- No AI or intel modifiers. Raw probability.
- International: higher chance of being revealed if failed.

### #23 Coup — SIMPLIFIED
- Any two roles within same country can attempt
- Initiator names co-conspirator. 5-minute window.
- Co-conspirator can: accept, reject silently, or BETRAY (initiator arrested immediately)
- If both accept: probability check (base 15%, + active protest +25%, + low stability, + low support)
- Failed = both exposed. Ruler and world learn.
- Trust mechanic IS the game.

### #24 Protest
- Automatic (engine checks conditions each round) OR stimulated (1-time card, +20% probability next round)
- Support >60%: fizzle. 40-60%: modest (-0.5 stability). <40%: massive (-1.5, +25% coup bonus)
- Public event.

### #25 Impeachment
- Columbia and Ruthenia only
- Columbia: any parliament member initiates → parliament votes (real participants)
- Ruthenia: any team member initiates → 2 real votes needed + AI emulates remaining (loyal to president by default)
- Both sides submit positions. Takes 1 round.
- Removed leader stays in play, loses executive powers.

---

## TRANSACTIONS (26-28)

### #26 Trade
- Country OR individual transactions (participant chooses mode)
- Authorized by: HoS OR PM OR Secretary of State/Foreign Affairs
- Basing rights: yes/no for entire country (not per zone)
- Bilateral, both confirm, instant, irreversible
- Country transactions: COUNTRY visibility. Personal: ROLE-ONLY visibility.

### #27 Agreement
- Types: Armistice (ends war), Peace (ends war), Alliance, Trade Preference, Custom
- Free text. Multiparty possible.
- Public or private (parties choose).
- Only Armistice/Peace have engine effect. Rest = stored, socially enforced.

### #28 New Organization
- 2+ countries found. Name, members, decision rule, purpose.
- Public event. Join/leave/expel mechanics.
- Org = communication channel + meeting structure, not independent power.

---

## COMMUNICATION (29-31)

### #29 Public Statement
- Via moderator ONLY. Physical speech in the room. Transcribed and recorded.

### #30 Call Organization Meeting
- Physical meeting. App handles invitation/notification only.

### #31 Nominate for Election
- 10 minutes before election. Triggered by moderator. Focus: Columbia, some Ruthenia.

---

## SPECIAL MECHANICS

### Columbia Court
- Standard functionality for all democracies
- Complain with arguments → 10 min response → AI clarifying questions → AI verdict → Moderator enforces
- Use cases: arrest challenges, firing challenges, constitutional disputes, contract disputes, impeachment

### Persia Contested Authorization
- Furnace and Anvil both can authorize military independently
- Conflicting orders: CONTESTED, neither executes, stability -0.5, facilitator mediates

### Role-Specific Special Actions (in G spec)
- Endorse successor, delay elections, declare emergency, set military posture, BRICS+ currency support, nuclear initiation, Vision 2030, rare earth restrictions, war posture escalation, kingmaking, IRGC economic intervention, veto implementation, suppress/permit dissent, partial blockade adjustment, Fatherland appeal
