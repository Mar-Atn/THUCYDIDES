# Thucydides Trap SIM — Roles Architecture
**Version:** 1.0 | **Date:** 2026-03-19 | **Status:** Conceptual

---

## Design Philosophy

**Humans for tension. AI for consistency.** Humans are concentrated in teams where interpersonal dynamics — disagreement, trust, betrayal, negotiation — ARE the learning experience. AI operates solo countries where clear interests, consistent character, and rational decision-making create a responsive, always-available world.

Every human participant is on a team. Nobody sits alone managing a single country's interests — that's what the AI does. The SIM's unique value is the team experience: negotiating with colleagues who disagree, managing internal conflict under external pressure, making collective decisions when the clock is running out.

### Two reasons for multi-role teams

**Designed tension.** For specific countries, team members SHOULD disagree — because the disagreement reproduces a real-world dynamic. Columbia's president vs. Congress. Cathay's chairman vs. the economic pragmatist. The internal politics IS the learning.

**Workload.** Some countries have too many simultaneous decisions for one person — military, economic, diplomatic — across too many counterparts. The team divides the labor so the country can function at the SIM's pace.

### Naming approach

**Country names:** Transparent fiction — invented names on recognizable geography. See SIM_WORLD_BUILDING.md.

**Character names:** Evocative archetypes. Each name captures the character's essence — their method, self-image, or core quality. One word, speakable in fast conversation, culturally neutral, distinct from every other name. The name is the character's first briefing.

---

## Human Teams

### Columbia (USA) — 6-7 players

The deepest team. Full government simulation. The internal tensions — transactional president vs. institutional establishment, executive vs. legislative, political calculation vs. military reality, accountable government vs. unaccountable private power — reproduce the American system's defining dynamics. Decisions are formally divided: the president proposes, Congress controls the budget, the SecDef controls force deployment, the CIA controls information.

| # | Character | Title | Archetype | Core tension |
|---|-----------|-------|-----------|-------------|
| 1 | **Dealer** | President | The transactional leader | Deals vs. commitments. Election vs. strategy. Every move measured against domestic popularity. |
| 2 | **Volt** | Vice President / Special Envoy | The disruptive deputy | Roaming diplomat with presidential authority. Succession question. May interpret the mandate creatively. |
| 3 | **Anchor** | Secretary of State | The institutional stabilizer | Alliances vs. president's transactionalism. Serve loyally or resist quietly? |
| 4 | **Shield** | Secretary of Defense | The strategic realist | Military readiness vs. political demands. Pacific vs. Europe allocation. The one who says "we can't." |
| 5 | **Shadow** | Intelligence Chief | The information controller | Knows things nobody else knows. Selective briefing as power. Covert operations. |
| 6 | **Tribune** | Congressional Leader | The democratic check | Budget veto. Investigation power. Partisan advantage vs. national interest. Becomes dominant after mid-terms if opposition wins. |
| 7 | **Spark** | Tech Mogul | The unaccountable wild card | Personal wealth, media influence, tech capability, back-channel access. No formal authority, no accountability. Can facilitate or destroy. |

**Key mechanic:** Budget requires President + Congress agreement. Military action requires President + SecDef. Nuclear launch requires President + SecDef. Intelligence briefings are selective (Shadow decides what to share). Spark operates independently — nobody controls them. Presidential election at Round 5 determined by political support score.

---

### Cathay (China) — 4 players

Hidden tensions behind a unified facade. All four agree on goals (national rejuvenation, Formosa reunification) but disagree on timing, method, and risk tolerance. Unlike Columbia where disagreements are public, Cathay's debates happen behind closed doors — other players can only guess at what's happening inside. This opacity is itself a mechanic: the outside world can't tell if a military buildup signals strength or desperation.

| # | Character | Title | Archetype | Core tension |
|---|-----------|-------|-----------|-------------|
| 1 | **Helmsman** | Chairman | The supreme navigator | Act on Formosa now or wait? Can't fully trust anyone's advice — each has their own agenda. |
| 2 | **Rampart** | Marshal | The military wall | Readiness honest assessment vs. self-preservation. Report "not ready" (risk purge) or "ready" (risk catastrophe)? |
| 3 | **Abacus** | Premier | The economic calculator | Knows the real numbers on economic vulnerability. Confrontation = sanctions = possible crisis. Pragmatism looks like disloyalty. |
| 4 | **Circuit** | Tech/Industry Chief | The semiconductor strategist | Runs the AI race. Controls rare earth counter-weapon. Formosa invasion could destroy the very fabs Cathay wants. Long game vs. weaponization. |

**Key mechanic:** Chairman has formal authority over everything but depends on the others to execute. Marshal can slow-walk military orders. Abacus controls budget mechanisms. Circuit has independent international tech contacts. Purging is possible but thins the loyalty base. External communications go through Chairman (unified facade) — but cracks may appear.

---

### Nordostan (Russia) — 4 players

Personal, paranoid, brittle. Power concentrated through relationships, not institutions. The president controls everything through a web of mutual dependency and mutual suspicion. Unlike Cathay (where the system would continue differently without the leader), Nordostan without its president is an open question — succession crisis, power vacuum, possible collapse. The coup mechanic is always latent.

| # | Character | Title | Archetype | Core tension |
|---|-----------|-------|-----------|-------------|
| 1 | **Pathfinder** | President | The indispensable balancer | Survival above all. Balance military, economy, and oligarchs. Trust nobody fully. Every subordinate is both essential and a potential threat. |
| 2 | **Ironhand** | General | The military commander | War execution vs. honest assessment. Personal positioning for succession — without appearing to think about it. |
| 3 | **Ledger** | Prime Minister | The economic survivor | Fund the war or save the economy (resources for neither). Most Western-compatible figure — useful and therefore suspected. |
| 4 | **Compass** | Oligarch | The shadow diplomat | Personal wealth (20-30 coins), international connections, back-channel access. Wants sanctions relief for personal reasons that align with national interest. Can be arrested anytime. |

**Key mechanic:** President can arrest anyone on Nordostan soil. Nuclear launch requires President + General. Budget submitted by PM, overridable by President. Oligarch operates independently through personal channels — may or may not inform the president. Coup attempt possible by General + PM (+ Oligarch funding); probability depends on social score, political support, co-conspirators, dice roll.

---

### Europe — 4 players (one per nation)

Not a single country with internal factions — four sovereign nations that must act collectively through the EU but can't agree. Each player simultaneously manages three games: the EU consensus negotiation, the NATO alliance dynamic, and their own national survival. The internal tension IS the inter-state negotiation.

| # | Character | Country | Archetype | Core position |
|---|-----------|---------|-----------|--------------|
| 1 | **Lumière** | Gallia (France) | The autonomy champion | Nuclear power, UNSC veto. Wants European strategic independence. Can go it alone. |
| 2 | **Forge** | Teutonia (Germany) | The torn middle | Economic engine with China trade exposure. Every sanction costs Germany most. Reluctant rearmer. |
| 3 | **Sentinel** | Freeland (Poland) | The frontline hawk | Lives next to the war. Maximum NATO commitment. Closest to Columbia. "We told you so about Russia." |
| 4 | **Mariner** | Albion (UK) | The outside insider | In NATO but not EU. Nuclear, Five Eyes, UNSC veto. Bridge between Columbia and Europe — or the gap. |

**Key mechanic:** EU decisions (sanctions, trade, enlargement) require consensus of EU members (Lumière, Forge, Sentinel) — any one blocks. Albion participates in NATO but not EU decisions. NATO decisions require all four plus Columbia and Phrygia. National decisions (military deployment, bilateral deals, nuclear, basing rights) are sovereign — each decides independently. UNSC vetoes held independently by Lumière and Mariner.

---

### Heartland (Ukraine) — 3 players

Three players, one country, a wartime election that changes everything. All three are active from Round 1 — the President governs, the General advocates from outside command, the Politician explores peace. Foreign leaders can meet all three, pre-negotiating with the potential next president. At a triggered or scheduled round, the AI determines the election result based on actual gameplay (territory, economy, casualties, support). The winner takes the helm. The losers remain active as opposition.

| # | Character | Role | Archetype | What they offer the country |
|---|-----------|------|-----------|---------------------------|
| 1 | **Beacon** | President | The wartime symbol | Resistance, continuity, international legitimacy. But exhausted, constrained by own rhetoric, and the peace deal that saves the country may kill the president's career. |
| 2 | **Bulwark** | The General | The military hero | "Fight harder, fight smarter." Popular with soldiers and Western military. Shadow diplomacy — foreign leaders hedge by talking to the probable next president. |
| 3 | **Broker** | The Politician | The pragmatic dealmaker | "I can negotiate what the current president can't." Controversial but increasingly relevant as war fatigue deepens. Has the contacts, knows the price of everything. |

**Key mechanic:** President holds all formal powers until the election. General has informal military influence and conducts shadow diplomacy. Politician conducts back-channel peace exploration. Election triggered at Round 3-4; AI evaluates social score, military outcomes, economic conditions, Western support to determine vote shares. Winner becomes president for remaining rounds. Losers remain as opposition voices. The peace-deal trap: the leader who signs peace may be the leader the country punishes.

---

## AI-Operated Countries

These are not NPCs — they are full actors with goals, personality, and agency. They pursue interests proactively, negotiate responsively, and can make surprising moves within character. Human players interact with them through the web platform (meetings, messages, deals) and should feel they're engaging a real leader, not a chatbot.

### Requirements for AI characters

**Proactive:** AI countries don't wait to be approached — they initiate negotiations, make announcements, pursue their agenda.

**Responsive:** Every human request for a meeting or negotiation gets a substantive, in-character response.

**Characterful:** Each AI country has distinct personality, not just interests. AI-Choson is erratic. AI-Solaria is transactional. AI-Levantia is decisive and unapologetic.

**Capable of surprise:** Within character, AI countries can make unexpected moves that reshape the game — AI-Levantia strikes Persia's nuclear sites, AI-Choson tests a weapon, AI-Solaria crashes oil prices.

### AI Country Roster

| Character | Country | Key interests | Personality | Consequential moves |
|-----------|---------|--------------|-------------|-------------------|
| **Scales** | Bharata (India) | Non-alignment, court all sides, regional primacy | Patient, calculating, refuses to commit | Sanctions stance determines coalition effectiveness. Nuclear dimension with Indistan. |
| **Bazaar** | Phrygia (Turkey) | Broker everything, NATO + BRICS observer, regional power | Transactional, opportunistic, charmingly unreliable | Controls Bosphorus straits. Can block NATO decisions. Arms dealer to all sides. |
| **Wellspring** | Solaria (Saudi Arabia) | Oil pricing, BRICS+ currency, hedge US-China | Pragmatic, patient, leverage-obsessed | OPEC+ production decisions reshape global economy. Currency union swing vote. |
| **Furnace** | Persia (Iran) | Nuclear program, regional influence, sanctions relief | Intense, patient, ideological but rational | Nuclear threshold crossing triggers UNSC crisis. Proxy network creates Middle East escalation. |
| **Citadel** | Levantia (Israel) | Survival, Iran neutralization, regional dominance | Decisive, unapologetic, independently capable | Unilateral strike on Persia = regional crisis forcing Columbia's hand. |
| **Chip** | Formosa (Taiwan) | Survival, semiconductor leverage, US commitment | Anxious, strategic, globally essential | Semiconductor chokepoint. Blockade or invasion crashes global tech. |
| **Sakura** | Yamato (Japan) | Pacific security, remilitarization, alliance reliability | Cautious but awakening, increasingly assertive | Chip supply chain decisions. Pacific military posture. Could go nuclear. |
| **Pyro** | Choson (N. Korea) | Regime survival, nuclear leverage, extract payments | Erratic, threatening, attention-seeking | Nuclear tests, provocations, troop deployments create crises on demand. |
| **Summit** | Indistan (Pakistan) | India rivalry, China client, nuclear parity | Defensive, proud, seeking respect | India-Pakistan nuclear dimension. China's corridor. Islamic world voice. |
| **Canopy** | Amazonia (Brazil) | Non-alignment, BRICS+, Global South leadership | Independent, principled, frustrated with great powers | BRICS+ currency union voice. Represents 6 billion people outside NATO/SCO. |
| **Spire** | Mirage (UAE) | Financial hub, arms buyer, pragmatic hedger | Sleek, connected, amoral pragmatism | Financial flows, arms deals, Africa interventions. Connects everyone. |
| **Vanguard** | Hanguk (S. Korea) | Security from North, China trade, tech power | Anxious, capable, trapped between patrons | Semiconductor supply chain. Korean peninsula anchor. |
| **Havana** | Caribe (Cuba+Venezuela) | Regime survival, US pressure, Russia/China foothold | Defiant, cornered, willing to provoke | US near-abroad crisis. Triggers Monroe Doctrine dynamic. |
| **Mandela** | Austoria (S. Africa) | BRICS+, Africa voice, moral authority | Principled, post-colonial, under-resourced | ICJ cases, BRICS+ vote, mineral resources, African demographic pressure. |
| **Dove** | UN Secretary General | Peace, rules-based order, mediation | Persistent, morally clear, practically powerless | Convenes emergency sessions. Proposes frameworks. Embarrasses aggressors. |

---

## Structural Roles

| Character | Role | Played by | Function |
|-----------|------|-----------|---------|
| **Veritas** | Global Press | Human (flex) or AI | Investigates, publishes, breaks stories. Shapes narrative. Makes actions public and consequential. Only one press channel — monopoly on public information gives it power. |

---

## Scaling Framework

The design works from 22 to 35+ human participants. The world is always complete — AI fills any role not assigned to a human.

| Priority | Roles filled | Humans | Notes |
|----------|-------------|:------:|-------|
| 1 — Always human | Columbia (6), Cathay (4), Nordostan (4), Europe (4), Heartland (3) | 21 | Core teams. The irreducible minimum. Every human is on a team. |
| 2 — First expansion | +Columbia 7th (Spark), +Press (Veritas) | 23 | Adds the wild card tycoon and human press. |
| 3 — Key solo countries become human | +Bharata, +Phrygia, +Yamato | 26 | The swing states and Pacific anchor most benefit from human unpredictability. |
| 4 — Deepen the world | +Solaria, +Persia, +Levantia, +Formosa | 30 | Major solo actors become human. Middle East and Taiwan gain human agency. |
| 5 — Maximum | +Choson, +Indistan, +Amazonia, extra team roles | 33-35+ | Approaching full-human world. Reserve for large groups. |

**At 25 humans:** 5 teams (21 core) + Spark + Press + Bharata + Phrygia = 25. Every human has a rich team experience or high-agency solo role. AI runs 12 countries competently.

**At 30 humans:** All of the above + Yamato, Solaria, Persia, Levantia, Formosa. AI runs 7 countries. More human unpredictability in the Middle East and Pacific.

**At 35 humans:** Near-complete human coverage. AI runs 3-4 minor countries. Maximum chaos, maximum emergence.

---

## Team Dynamics Comparison

| | Columbia | Cathay | Nordostan | Europe | Heartland |
|--|---------|--------|-----------|--------|-----------|
| **Power structure** | Divided (institutional) | Concentrated (hierarchical) | Personal (paranoid) | Sovereign (collective) | Contested (electoral) |
| **Disagreement style** | Public, institutional | Hidden, behind facade | Whispered, dangerous | Inter-state, procedural | Temporal — three futures competing |
| **What blocks decisions** | Congress veto | Slow-walking, biased advice | Suspicion, fear of purge | Consensus failure | Mandate uncertainty |
| **Succession mechanism** | Election (scheduled) | Purge or quiet displacement | Coup or collapse | National elections (triggered) | Wartime election (AI-judged) |
| **Visibility to outsiders** | Fully transparent | Opaque — world guesses | Partially visible — rumors leak | Messy — EU debates are semi-public | All three candidates visible |
| **Experience for participants** | Democratic dysfunction | Authoritarian opacity | Autocratic paranoia | Collective action failure | Leadership under existential threat |

---

## Open Questions

1. Exact character briefs — interests, relationships, unique information, powers per role
2. Starting resources per country — coins, military units, tech levels, social scores
3. AI character cognitive architecture — extending KING's 4-block model for country-level decision-making
4. Interaction model between human players and AI countries — web platform, moderator-facilitated, or hybrid
5. Whether Columbia needs the 7th role (Spark) in the core 21 or only as expansion
6. Whether Heartland's election is at a fixed round or triggered by conditions
7. Press role: human or AI? Human adds creativity; AI adds consistency and availability
8. Character name final validation — read aloud in fast conversation, test for 12-hour durability

---

## Changelog

- **v1.0 (2026-03-19):** Initial roles architecture. Human-teams-plus-AI-world philosophy. Five team structures (Columbia 6-7, Cathay 4, Nordostan 4, Europe 4, Heartland 3). 15 AI-operated countries with character profiles. Scaling framework from 22 to 35+ participants. Team dynamics comparison. Working character names proposed.
