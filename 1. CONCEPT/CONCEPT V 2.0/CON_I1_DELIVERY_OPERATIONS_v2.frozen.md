# Thucydides Trap SIM — Delivery & Operations
**Code:** I1 | **Version:** 1.0 | **Date:** 2026-03-25 | **Status:** Conceptual framework — details to be developed after first delivery

---

## Purpose

This document defines the complete delivery package for TTT: everything needed to prepare, run, and follow up a SIM event. TTT is not just software — it is a delivered experience. The web app is the platform; this document covers everything around it: the people, the space, the materials, the schedule, the marketing, the debrief, and the post-event outputs.

The goal is to capture all delivery elements now at the concept level, with enough structure that nothing is forgotten during the first delivery and enough flexibility that each element can be refined based on real experience.

Most sections below describe WHAT must exist and in WHAT FORMAT. The detailed content will be developed during Seed Design and refined after each delivery.

---

## 1. Facilitator Model

### Team Composition (3–5 people)

| Role | Count | Responsibilities |
|------|:-----:|-----------------|
| **Lead Facilitator** | 1 | Runs the SIM. Opens and closes each round. Manages the dramatic arc. Makes judgment calls (extend a round, inject an event, call a vote). Reviews and approves World Model Engine output. The public face of the experience. Must deeply understand the scenario, every role, and every mechanic. |
| **Engine Operator** | 1 | Manages the web app during the SIM. Triggers engine processing. Monitors real-time events. Manages AI participants (adjusts activity, pauses if needed, handles errors). Troubleshoots technical issues. Works alongside Lead Facilitator during Phase B (world update). Requires technical comfort with the platform. |
| **Assistant Facilitator(s)** | 1–2 | On the floor during Phase A. Answers participant questions. Helps with interface issues. Guides confused participants to Navigator. Monitors room energy — reports to Lead Facilitator if a country is disengaged or overwhelmed. Manages physical logistics (breaks, rooms, food). At least one should be able to substitute for Lead Facilitator if needed. |
| **Debrief Coach(es)** | 0–1 | Leads the reflection process (outro circles, structured debrief). Can be the Lead Facilitator in a small team, but a dedicated coach is better for groups above 30. Ideally someone with facilitation or coaching background — the debrief is where learning solidifies. |

**Minimum viable team:** 3 (Lead Facilitator + Engine Operator + 1 Assistant). The Lead Facilitator doubles as Debrief Coach. This is tight but workable for groups up to 30.

**Recommended team:** 4–5 for groups of 30+. Adding a second Assistant Facilitator and a dedicated Debrief Coach significantly improves participant experience.

**External facilitator model (future).** TTT should be deliverable by trained external facilitators, not only by MetaGames. This means all facilitator materials must be self-contained and comprehensive enough for a competent facilitator to run the SIM after a training program. The training program itself is a future deliverable (see section 11).

### Facilitator Qualities

The Lead Facilitator needs three things: deep knowledge of the scenario (geopolitical context, every role's position, the mechanics), theatrical presence (they set the tone — gravitas without pomposity, seriousness without boredom), and improvisational judgment (knowing when to intervene and when to let the participants' story play out). This person is not a lecturer — they are a director of a live experience.

---

## 2. Customisation and Setup Process

The process from "client books TTT" to "day one, participants walk in."

### Phase 1: Scoping (4–8 weeks before event)

- Confirm participant count and composition (seniority, background, language, experience with SIMs)
- Select format: two-day (recommended) or single-day
- Select scenario template from the template library (Scenario Configurator)
- Decide on customization: standard template or AI-assisted context refresh to current events
- Decide on expansion roles: which optional roles are active
- Confirm which solo countries are human-played vs. AI
- Confirm learning objectives with the organizing institution (what should participants walk away with?)
- Agree on language (English primary; TTT can be adapted to other languages for character names and briefing materials)

### Phase 2: Configuration (2–4 weeks before event)

- Facilitator runs AI-assisted context refresh on the scenario template (if updating to current events)
- Facilitator reviews and adjusts scenario parameters in the Scenario Configurator (Block B and C from D0)
- Participant roster loaded — role assignments made (or left for day-of assignment based on facilitator preference)
- Brief generation triggered — role briefs, world briefing, AI country postures produced
- Navigator prompts reviewed and adjusted if needed (tone, emphasis, learning objectives)
- AI participant profiles reviewed — character personalities and initial postures checked
- Printed materials ordered (see section 5)
- Technical infrastructure tested (see section 4)

### Phase 3: Final Preparation (1 week before event)

- Participant pre-work distributed (see section 3)
- Physical space confirmed and setup planned (see section 4)
- Full technical dry run: Scenario Configurator → web app loaded with scenario → all roles accessible → engines process test round → AI participants active → Navigator sessions tested → public display working
- Facilitator team briefing: review scenario, walk through schedule, assign floor responsibilities, rehearse key moments (election, UNGA, possible military escalation)
- Contingency plans reviewed (see section 12)

### Phase 4: Day-Of Setup (morning of event, 2–3 hours before start)

- Physical space arranged (see section 4 checklist)
- Tech check: WiFi, devices, screens, voice terminals, web app accessible for all roles
- AI participants initialized — all 4 blocks generated, status confirmed
- Public display live with starting world state
- Printed materials at stations
- Facilitator team final sync

---

## 3. Participant Pre-Work and Onboarding

What participants receive before the event. The goal is to get them curious and oriented — not to teach them the entire game.

### Before arrival (sent 3–7 days prior)

| Material | Format | Purpose |
|----------|--------|---------|
| **Welcome message** | Email / message | Sets tone. Explains what TTT is (1 paragraph). Tells them what to expect. Gives logistics. |
| **Role assignment notification** | Email / message | "You are playing [Character Name], [Title] of [Country]." Brief teaser of the role — 2–3 sentences, enough to spark curiosity. Does NOT include the full brief (that's for day-of). |
| **World briefing summary** | PDF or web page, 1–2 pages | The fictional world at a glance: country names, major tensions, key organizations. Enough to orient, not enough to strategize. |
| **Login credentials** | Email | Access to the web app. The participant can log in and see their role's home screen (limited — no game data yet, just the interface). This lets them familiarize with the tool before pressure starts. |
| **Optional: Context video** | 3–5 minute video | Lead Facilitator or narrator introduces the world, the central tension, and what's at stake. Sets mood. |

### On arrival (check-in period, 30–45 minutes)

| Activity | Duration | Owner |
|----------|----------|-------|
| Registration and badge collection | 10 min | Assistant Facilitator |
| Welcome and world briefing presentation | 15–20 min | Lead Facilitator |
| Role briefs distributed (printed + digital) | — | During briefing |
| Read brief, explore interface, set up device | 10–15 min | Self-directed |
| **Navigator intro session** (essential) | 10–15 min | Each participant talks to Navigator: sets personal learning goals, gets rules clarification, discusses initial strategy |

The Navigator intro is the critical onboarding moment. It ensures every participant — from the experienced executive to the reluctant attendee — understands their role, has personal goals, and feels prepared to start. Completion tracked on Facilitator Dashboard.

---

## 4. Physical Location Requirements and Setup Checklist

### Space Requirements

**Main hall.** One large room where all participants can gather. Used for: opening briefing, world updates (Phase B announcements), public speeches, election events, debrief. Needs a stage or focal point, a large screen for the public display, and good acoustics. Capacity: all participants + facilitator team + observers.

**Meeting spaces.** 3–5 smaller rooms or defined areas for bilateral and multilateral meetings. Can be breakout rooms, corners of a large space, or separate rooms nearby. Each needs: table, chairs, power outlets. Privacy matters — Cathay's internal meetings shouldn't be overheard by Columbia.

**Country stations.** Each multi-role country team needs a "home base" — a table or area with chairs, power, and visibility to the public display. Solo country AI terminals (screens/devices representing AI-operated countries) placed in the main hall or along a "diplomatic corridor." These are where human participants go to talk to AI countries.

**Facilitator station.** A dedicated table or area (can be slightly elevated or behind the main space) with: large screen for Facilitator Dashboard, Engine Operator's workstation, communication equipment (walkie-talkies or messaging channel with Assistant Facilitators).

**Dining area.** In the two-day format, lunch and dinner areas are game venues. Ideally the dining space is near the main hall so movement is natural.

### Setup Checklist

**Technology:**
- [ ] WiFi tested with 50+ simultaneous devices (participants + AI + facilitator + displays)
- [ ] Backup internet (mobile hotspot) available
- [ ] Public display screen(s) operational — large, visible from all areas
- [ ] AI country voice terminals set up and tested (10 stations)
- [ ] Facilitator workstations connected and dashboard accessible
- [ ] Power outlets / extension cords at all country stations and meeting rooms
- [ ] Audio system for main hall (facilitator announcements, world updates)
- [ ] Web app accessible on all test devices, all roles logging in correctly
- [ ] All AI participants initialized and responding
- [ ] Navigator voice sessions tested (at least 2 simultaneous sessions confirmed working)

**Physical:**
- [ ] Country stations set up with country flags/signs and printed materials
- [ ] Meeting rooms labeled and accessible
- [ ] Signage: schedule posted, room map visible, WiFi credentials displayed
- [ ] Name badges prepared with character name, country, and role
- [ ] Facilitator walkies/communication channel tested
- [ ] Catering arranged (in-role meals for two-day format)
- [ ] Breakout timing materials (timer visible or projected)

**Printed materials at each station:**
- [ ] Role brief (country-specific, classified)
- [ ] Quick-reference card (key mechanics, action types, authorization chain for this role)
- [ ] World map (physical A3 or larger — participants will mark it up during play)
- [ ] Organization membership card (which orgs this country belongs to, voting rules)
- [ ] Schedule card (round timing, key events, deadlines)

---

## 5. Printed SIM Materials and Artefacts

Physical materials enhance immersion and serve as reference during fast-paced play when looking at screens isn't practical.

### Essential Printed Materials

| Material | Format | Quantity | Notes |
|----------|--------|----------|-------|
| **Role brief** | A4 booklet, 4–8 pages | 1 per participant | Classified. Contains: character background, country situation, role powers, team structure, personal motivations, secret information, starting strategic position. The most important physical artefact. |
| **Quick-reference card** | A5 laminated card | 1 per participant | Double-sided. Front: available actions with timing (real-time vs. submitted). Back: authorization chain for this role + key mechanics relevant to this role. Participants keep this on the table all SIM. |
| **World map** | A3 poster or larger | 1 per country station + 2 spares | Starting world state: theaters, military deployments (public), organizational memberships, chokepoints. Participants will draw on it during play — provide markers. |
| **Organization cards** | A5 cards | 1 set per country | One card per organization the country belongs to: members, decision rules, core dilemma, meeting protocol. Participants bring the right card to each meeting. |
| **Schedule card** | A5 card | 1 per participant | Day schedule with round times, key events, deadlines. Updated for each format (two-day / single-day). |
| **Name badge** | Badge with lanyard | 1 per participant + facilitators | Character name (large, readable at 3m), real name (smaller), country, role title. Color-coded by country. |

### Optional / Premium Materials

| Material | Format | Notes |
|----------|--------|-------|
| **Country dossier** | A4 booklet, 8–12 pages | Extended intelligence briefing per country: full economic data, military assessment, diplomatic relationships, strategic options. For groups that want deeper prep. |
| **Physical coins** | Metal tokens or chips | Physical currency for visible, tangible transactions. High immersion value. Participants push coins across the table during deals. The web app tracks the official balance; physical coins are theatrical. |
| **Sealed intelligence envelopes** | A5 sealed envelopes | Pre-prepared intelligence revelations that the facilitator distributes at specific moments. "Open when instructed." Creates drama. |
| **Treaty templates** | A5 pad of blank treaty forms | Pre-formatted forms participants fill in by hand and sign. Both parties get a copy; facilitator gets one. Physical signature = commitment weight. Digital version also submitted to the web app. |
| **Country flags** | Small desktop flags | One per country station. Visual territory markers. |

### Production Notes

All printed materials are generated from the Scenario Configurator's brief generation system. The facilitator triggers generation → system produces formatted documents → exported as PDF → sent to print. For quick iterations (last-minute role changes), the system should be able to regenerate a single role brief in under a minute.

---

## 6. Intro Slides or Interactive Briefing

The opening presentation that brings participants into the world. This is the first impression — it sets energy, seriousness, and engagement for everything that follows.

### Format Options

**Option A: Slide deck (PowerPoint/Keynote).** Traditional presentation delivered by the Lead Facilitator. Works for any venue. 15–20 minutes.

**Option B: Interactive HTML briefing.** A web-based presentation participants follow on their own devices while the facilitator narrates. Can include embedded maps, clickable country profiles, short video clips, and interactive quizzes ("which country is this?"). More engaging but requires reliable WiFi from the start.

**Option C: Video + live narration.** A pre-produced 5-minute cinematic introduction (dramatic narration over maps and imagery, setting the geopolitical context) followed by live facilitator Q&A and rules walkthrough. Highest production value; the video can be reused across deliveries.

### Content Structure

Regardless of format:

1. **Welcome and framing** (2 min) — what this experience is, what it's not, what to expect. "This is not a lecture. You are about to lead countries through a crisis. Everything you do has consequences."
2. **The world** (5 min) — the geopolitical map, the key countries, the central tension (rising power vs. established power), the major flashpoints. Use the fictional names. Show the map.
3. **The mechanics** (5 min) — how rounds work (negotiate → submit → world updates → deploy). How to use the interface. What kinds of actions exist. Where to find help (Navigator, facilitators). Keep this high-level — Navigator handles individual rules questions during the intro session.
4. **The schedule** (2 min) — what happens today (or over two days). Key scheduled events. When lunch is. When it ends.
5. **The invitation** (1 min) — "Read your brief. Set your goals with Navigator. When Round 1 starts, you are your character. Go."

### Deliverable

A template slide deck or HTML package included in the delivery package. Customizable: facilitator can adjust country names, scenario details, images, branding. Stored in the Scenario Configurator alongside the scenario template.

---

## 7. Event Schedule

The full timeline for participants, covering everything from arrival to departure. Based on C3_TTT_TIME_STRUCTURE but extended to include all non-SIM activities.

### Two-Day Format (reference — detailed timing in C3)

**Day 0 (evening before, optional):** Welcome dinner. Participants meet informally. Role assignments may or may not be revealed. Facilitator sets context conversationally. No game mechanics — just human connection and anticipation.

**Day 1:**

| Time | Activity |
|------|----------|
| 08:30–09:00 | Arrival, registration, badges, tech check (log into app) |
| 09:00–09:45 | Intro briefing (slides/video + rules overview) |
| 09:45–10:15 | Read briefs + Navigator intro sessions (personal goals, rules, strategy) |
| 10:15–11:45 | **Round 1** (Phase A: 80 min + submission) |
| 11:45–12:00 | World update R1 |
| 12:00–13:25 | **Round 2** (Phase A: 75 min + submission) |
| 13:25–13:40 | World update R2 (mid-term election results) |
| 13:40–14:30 | Lunch (in role — dining is a negotiation venue) |
| 14:30–15:50 | **Round 3** (Phase A: 65 min + UNGA vote + submission) |
| 15:50–16:05 | World update R3 |
| 16:05–16:20 | Break |
| 16:20–17:35 | **Round 4** (Phase A: 60 min + submission) |
| 17:35–17:50 | Extended world update R4 — "state of the world at the halfway point" |
| 17:50–18:00 | Facilitator recap / set up overnight dynamics |
| 18:00+ | SIM pauses — stay in role. Dinner, informal negotiations, overnight scheming |

**Day 2:**

| Time | Activity |
|------|----------|
| 09:00–09:15 | Check-in, overnight events announced |
| 09:15–10:25 | **Round 5** (Phase A: 55 min + presidential election + submission) |
| 10:25–10:40 | Extended world update R5 (election results) |
| 10:40–11:35 | **Round 6** (Phase A: 45 min + submission) |
| 11:35–11:50 | World update R6 |
| 11:50–12:00 | Moderator decision: end or continue to R7–8 |
| 12:00–12:15 | Final state of the world. **SIM ENDS.** |
| 12:15–12:30 | Step out of role. Decompress. |
| 12:30–13:00 | **Navigator outro sessions** (individual reflection, self-assessment, peer nominations) |
| 13:00–13:45 | **Reflection circles** (small groups with coach — see section 8) |
| 13:45–14:30 | Lunch |
| 14:30–15:15 | **Structured debrief** (plenary — see section 9) |
| 15:15–15:30 | Closing, awards, farewell |

### Single-Day Format

Same structure compressed. See C3 for round timing. Key difference: Navigator outro and reflection circles happen in a tighter window (45 min total instead of 75 min). The structured debrief is shorter (30 min instead of 45 min). No overnight. No Day 0 dinner.

### Schedule Deliverable

A formatted schedule document (PDF, one page) included in the delivery package. Two versions: participant-facing (simple, round times + key events + logistics) and facilitator-facing (detailed, including Phase B processing time, tech checkpoints, contingency windows).

---

## 8. Outro: Reflection Circles

Small-group reflection immediately after the SIM ends and after individual Navigator outro sessions. This is where participants process the experience together — not as countries but as people.

### Format

Groups of 4–6 participants. Mixed countries (not your own team). Seated in circles. Led by a Debrief Coach or Assistant Facilitator. Duration: 30–45 minutes.

### Structure

The coach asks 2–3 simple, open questions. Participants respond in rounds (each person speaks, no interruptions). The questions are designed to surface personal reflection, not game analysis.

**Question 1 (always):** "What surprised you most about yourself during this experience?"

This is the most important question. It moves participants from "what happened in the game" to "what happened inside me." It surfaces: unexpected reactions under pressure, decisions they didn't expect to make, moments where they discovered something about their leadership style.

**Question 2 (choose one depending on group):**
- "Was there a moment where you had to choose between what was right and what was effective? What did you do?"
- "Who on the other side earned your respect — and why?"
- "What would you do differently if you could replay the last 24 hours?"

**Question 3 (if time allows):**
- "What will you take from this experience into your real work?"
- "Is there something you want to say to someone from another country — now that we're out of role?"

### Coach's Role

Listen more than speak. Ensure everyone gets time. Don't analyze or explain — let participants find their own meaning. Gently redirect if someone stays in game-analysis mode ("the economy crashed because...") toward personal reflection ("how did that make you feel as a leader?").

### Data Capture

The coach takes brief notes (not full transcripts). Key themes, standout reflections, and any powerful quotes. These feed into the post-event report. With consent, audio recording is an option for deeper analysis.

---

## 9. Structured Debrief (Plenary)

The full-group debrief after reflection circles. Led by the Lead Facilitator. This is the intellectual and emotional closing of the experience.

### Format

All participants together in the main hall. Slide deck on the public display. Duration: 30–45 minutes. Interactive — not a lecture.

### Content Structure

**Part 1: What happened (10 min)**

The Lead Facilitator tells the story of the SIM — the key decisions, the turning points, the surprises. Uses data from the web app: maps showing how theaters evolved, charts showing GDP trajectories, key transaction flows. This is the "documentary recap" — participants see the big picture they couldn't see while playing.

Slides: before/after maps, key indicator timelines, major event timeline.

**Part 2: The Thucydides Trap — did it spring? (10 min)**

The conceptual debrief. Connect what happened in the SIM to the real-world phenomenon. Did the participants fall into the Trap? Did they avoid it? What structural forces pushed them toward conflict? What personal decisions could have changed the trajectory?

This is where the three-layer model (structural / situational / personal) from A1 becomes vivid — participants just lived through it. The facilitator doesn't lecture about theory; they ask: "You were there. What drove the escalation? Was it the structural pressure, the situation in Round 3, or someone's personal decision?"

Slides: the three-layer model, real-world parallels, key takeaways.

**Part 3: Recognition and awards (10 min)**

Data from Navigator outro sessions (peer nominations) combined with facilitator observations.

**Awards categories (flexible — facilitator selects 3–5):**
- **Best Diplomat** — who built the most effective alliances, brokered the best deals
- **Best Strategist** — who played the long game most effectively
- **Most Impactful Decision** — the single action that changed the course of the SIM most
- **Best Under Pressure** — who performed best in the crisis moments
- **Best Team** — which country team functioned most effectively together
- **Best Actor** — who embodied their character most convincingly (audience vote or facilitator pick)
- **People's Choice** — most impressive participant as voted by peers (from Navigator outro data)

The awards should feel fun, not competitive. Brief justifications. Light humor. The goal is to close with positive energy and recognition.

**Part 4: Closing (5 min)**

The facilitator makes the connection to real leadership: "Every one of you just made decisions under uncertainty, with incomplete information, under time pressure, with people who disagreed with you. That's leadership. The question isn't whether you got it right — it's what you learned about how you lead."

Final slide: learning objectives achieved. Invitation to continue reflecting. Information about post-event deliverables.

### Debrief Slides Deliverable

A template slide deck included in the delivery package. Customizable sections: the "what happened" recap is generated per SIM run (data-driven, from the web app). The conceptual debrief and awards sections are templated with facilitator notes. The closing is standard with space for personalization.

---

## 10. Post-Event Deliverables

What participants and the organizing institution receive after the SIM.

### For Each Participant

| Deliverable | Format | Source | Timeline |
|-------------|--------|--------|----------|
| **Individual reflection summary** | PDF, 1–2 pages | Navigator outro data: goals set, self-assessment, key learnings, what they'd do differently | Within 1 week |
| **Personal development insights** | Section in above PDF | Navigator analysis: engagement trajectory (Prisoner → Tourist → Partner), strategic patterns, communication style observations | Within 1 week |
| **SIM highlights reel** | Email with key moments | Auto-generated from events log: this participant's most significant actions, deals, and outcomes | Within 1 week |
| **Certificate of participation** | PDF (printable) | Character name, role, SIM date, organization. Signed by Lead Facilitator. Optional: with a brief narrative of what this character accomplished. | Same day or within 3 days |

### For the Organizing Institution

| Deliverable | Format | Source | Timeline |
|-------------|--------|--------|----------|
| **Group report** | PDF, 10–20 pages | Aggregate analysis: what happened (narrative), key decision points, group dynamics patterns, learning outcomes achieved, peer recognition patterns, recommendations | Within 2 weeks |
| **Leadership analytics** | Section in group report or separate dashboard | Behavioral patterns: who led, who followed, who disrupted, who built coalitions. Communication patterns. Decision-making styles. Engagement quality distribution. | Within 2 weeks |
| **Raw data export** | CSV/JSON (optional) | Full events log, transaction records, Navigator transcripts (anonymized if required), world state history. For institutions with their own research/analytics capability. | On request |
| **Facilitator debrief notes** | Internal document | Facilitator team's assessment: what worked, what didn't, recommendations for next run. Not shared with participants. | Within 1 week |

### Production Notes

Individual reflection summaries are generated automatically from Navigator data (structured extractions from outro conversations) with light AI formatting. The group report requires facilitator input (narrative, recommendations) combined with auto-generated analytics. This is a semi-automated pipeline: AI produces the draft, facilitator reviews and edits, final version distributed.

---

## 11. Moderator Instructions and Training

### Moderator Instructions (included in delivery package)

A comprehensive document that tells the facilitator team everything they need to run the SIM. Not a rulebook (that's in the scenario template) — this is operational guidance: what to do, when, and why.

**Contents:**

**Before the SIM:** Scoping checklist, configuration walkthrough, technical setup guide, briefing preparation, team role assignments, contingency planning.

**During the SIM — Round-by-Round Guide:** What to watch for in each round, where the scenario pressure builds, when scheduled events fire, what AI participants are likely to do, when to intervene (and when not to), common participant confusion points and how to resolve them.

**Key Judgment Calls:** When to extend a round (negotiations reaching breakthrough). When to inject an event (energy flagging, or a country is too passive). When to let a crisis escalate (learning is happening) vs. when to moderate (someone is genuinely distressed, or the game is spiraling unproductively). How to handle participant conflicts that cross from in-character to personal.

**Phase B Processing Guide:** Step-by-step: trigger engine, review AI output, adjust values if needed, approve, announce. What to look for in the AI calculations (sanity checks). How to present the world update compellingly (it's a performance, not a data dump).

**Debrief Facilitation Guide:** Reflection circle facilitation tips, structured debrief presentation guide, award selection process, closing remarks guidance.

**Troubleshooting:** Web app issues, AI participant malfunctions, participant dropouts, time overruns, WiFi failures. Quick-reference troubleshooting for common problems.

### Moderator Training (future deliverable)

For the external facilitator model (non-MetaGames delivery), a training program:

**Format option A: In-person workshop (1–2 days).** Walk through the entire SIM as a facilitator. Run a mini-session (3–4 rounds with training participants). Practice Phase B processing, event injection, and debrief facilitation. Receive certification.

**Format option B: Asynchronous training package.** Video modules (facilitator commentary over recorded SIM footage), written guides, practice exercises (process a sample Round's data, write a world update narrative, facilitate a practice debrief). Final assessment: run a mock session evaluated by MetaGames.

**Format option C: Apprenticeship.** Attend a MetaGames-led delivery as an observer/assistant. Then co-facilitate the next delivery. Then lead with MetaGames observer. Graduated independence.

The right format depends on the licensing model and how TTT scales. For early deliveries, MetaGames runs everything. Training materials are built from real delivery experience — not written in advance and hoped to work.

---

## 12. Contingency and Emergency Procedures

What happens when things go wrong during a live SIM.

### Technical Failures

| Issue | Immediate response | Recovery |
|-------|-------------------|----------|
| **WiFi drops** | Announce: "Technical pause — 5 minutes." Participants stay in role, continue face-to-face negotiations. | Switch to backup internet. If unrecoverable: paper mode for action submissions (facilitator enters manually after reconnection). |
| **Web app crashes** | Engine Operator diagnoses. Lead Facilitator extends current phase. | Restart app. Client state recovers from database (local cache + reconnection sync). If server-side: Supabase status check, restart Edge Functions. |
| **AI participant stuck** | Engine Operator pauses the affected AI. | Restart cognitive loop. If persistent: that AI country operates in "quiet mode" (responds to incoming only, no proactive actions) for the remainder of the round. |
| **Voice terminal failure** | Redirect participants to text chat with that AI country. | Restart voice session. If ElevenLabs outage: all AI interactions switch to text mode. |
| **World Model Engine error** | Lead Facilitator extends the break. "The world takes a moment to process..." | Engine Operator debugs. Moderator can manually adjust values and force-publish if automated processing fails. |

### Participant Issues

| Issue | Response |
|-------|----------|
| **Participant drops out** | Their role defaults to AI. Engine Operator activates AI participant with the dropped player's most recent game state. Announce in-game: "[Character] has been recalled to the capital." |
| **Participant confused / overwhelmed** | Assistant Facilitator guides them to Navigator. Navigator provides rules help and emotional support. If persistent: facilitator has a brief private conversation, helps simplify their focus to 1–2 priorities. |
| **In-character conflict becomes personal** | Facilitator intervenes immediately. Private conversation with both parties. Remind them they are playing characters, not themselves. If needed: 10-minute break. In extreme cases: reassign one participant to a different role. |
| **Participant actively disruptive** | Lead Facilitator has authority to: restrict a participant's actions (in-game justification: "your character has been placed under house arrest"), remove from a meeting, or in extreme cases ask them to observe rather than participate. |

### Timing Issues

| Issue | Response |
|-------|----------|
| **Running behind schedule** | Compress remaining rounds (reduce Phase A by 10–15 min each). Skip one round if necessary — jump the scenario forward 6 months, briefly narrate what happened. |
| **Running ahead of schedule** | Extend Phase A in remaining rounds. Add a mid-SIM "press conference" event. Deepen the debrief. |
| **Specific round dragging** | Lead Facilitator announces: "15 minutes remaining. All submissions must be final." Creates urgency. |

---

## 13. Marketing and Registration

### Landing Page

A web page (or section of the MetaGames website) for each scheduled TTT event. Purpose: inform potential participants, generate interest, collect registrations.

**Content:**
- What TTT is (1 paragraph, compelling: "Lead a country through a geopolitical crisis. Make decisions that reshape the world. Discover how you lead under pressure.")
- Who it's for (target audience: executives, MBA students, government officials, military leaders, diplomats — depending on the specific event)
- What you'll experience (brief description of the format, without spoiling the scenario)
- Date, location, duration
- Testimonials (after first delivery — placeholder until then)
- Registration form (name, email, organization, brief background, dietary/accessibility needs)
- FAQ (is this a game? how many people? do I need to prepare? what do I wear?)

**Design:** Professional, serious, slightly dramatic. Not corporate-boring, not game-flashy. The aesthetic should signal: "this is an experience that will challenge you intellectually and develop you as a leader."

### Invitation Materials

For events where an organization invites its own participants (not open registration):

| Material | Format | Purpose |
|----------|--------|---------|
| **Invitation email template** | HTML email | Sent by the organizing institution to participants. Customizable with organization branding. Includes: what, when, where, why this matters, registration link. |
| **One-pager** | PDF, A4, single page | For organizations deciding whether to book TTT. What it is, learning outcomes, format options, participant count, logistics, testimonials. |
| **Briefing for sponsors** | PDF, 2–3 pages | For the executive sponsor at the organization: what their people will experience, what data/insights they'll receive back (group report), how it connects to their development program. |

### Registration System

Part of the web app (or a simple external form feeding into it). Collects: participant information, consent forms (GDPR), dietary/accessibility needs, pre-event questionnaire (optional: role preferences, experience level, learning interests). The facilitator sees all registrations in the Scenario Configurator and uses them for role assignment.

---

## 14. Feedback Collection

### Participant Feedback

**During:** Navigator conversations are inherently a feedback channel — participants tell Navigator what confuses them, what frustrates them, what delights them. This is the richest feedback source.

**After:** A brief survey (5–10 questions, 3 minutes) sent within 24 hours. Questions: overall experience rating, most valuable moment, what could be improved, would you recommend this to a colleague, NPS score. Keep it short — participants have already given deep reflection through Navigator and reflection circles.

### Organizing Institution Feedback

A structured debrief call with the organizing sponsor within 1 week. What they observed, how participants responded afterward, whether learning objectives were met, what they'd change for next time.

### Facilitator Team Feedback

Internal debrief within 48 hours. What worked, what broke, what surprised, what to change. Documented in the facilitator debrief notes. This feeds directly into improving the delivery package for the next run.

### Feedback Loop

All feedback feeds into three outputs: (1) immediate fixes for the next delivery, (2) product improvements for the web app and scenario design, (3) updates to the Knowledge Base (08_BEST_PRACTICES.md).

---

## 15. Licensing and Delivery Model (Future Consideration)

Even at concept level, worth noting the spectrum of delivery models:

**MetaGames-delivered (current model).** MetaGames team facilitates everything. Highest quality control. Limited scalability.

**Certified facilitator model.** External facilitators trained and certified by MetaGames. They license the scenario, use the platform, and deliver independently. MetaGames provides: platform access, scenario templates, training, quality assurance (spot-check recordings, feedback review). Revenue model: platform license + per-event fee.

**White-label model.** An organization licenses the platform and scenarios under their own brand. They train their own facilitators. MetaGames provides: technology platform, scenario library, training-the-trainer program, ongoing support. Revenue model: annual license + usage fees.

The delivery package must be designed with the certified facilitator model in mind from the start — this means all materials must be self-contained, clearly documented, and usable without MetaGames presence.

---

## Master Delivery Checklist

A single consolidated checklist for the facilitator team. Everything that must be done, in order.

### 8–4 Weeks Before
- [ ] Participant count and composition confirmed
- [ ] Format selected (two-day / single-day)
- [ ] Scenario template selected and customized (AI-assisted context refresh if needed)
- [ ] Learning objectives agreed with organizing institution
- [ ] Physical venue confirmed and inspected
- [ ] Facilitator team assembled and roles assigned

### 4–2 Weeks Before
- [ ] Scenario configured in the Scenario Configurator (all parameters set)
- [ ] Participant roster loaded, role assignments made
- [ ] Role briefs and world briefing generated and reviewed
- [ ] Printed materials ordered
- [ ] Technical infrastructure tested (full dry run)
- [ ] Facilitator team briefing completed
- [ ] Marketing/invitation materials sent (if open registration)

### 1 Week Before
- [ ] Participant pre-work distributed (welcome email, role teaser, world summary, login credentials)
- [ ] Optional context video sent
- [ ] Final technical test (all AI participants initialized, Navigator sessions working, public display tested)
- [ ] Contingency plans reviewed with team
- [ ] Catering and logistics confirmed

### Day-Of Setup (2–3 hours before)
- [ ] Physical space arranged per layout plan
- [ ] Tech check complete (WiFi, devices, screens, voice, web app)
- [ ] AI participants initialized and status confirmed
- [ ] Public display live with starting world state
- [ ] Printed materials distributed to stations
- [ ] Badges and registration materials ready
- [ ] Facilitator team final sync (15 min)

### During the SIM
- [ ] Navigator intro sessions tracked — all participants completed before Round 1
- [ ] Round progression managed per schedule
- [ ] World updates processed and reviewed per Phase B guide
- [ ] AI participants monitored — no stuck agents
- [ ] Issues logged for post-event debrief

### After the SIM
- [ ] Navigator outro sessions completed for all participants
- [ ] Reflection circles facilitated
- [ ] Structured debrief delivered
- [ ] Participant feedback survey sent (within 24 hours)
- [ ] Individual reflection summaries generated and distributed (within 1 week)
- [ ] Group report drafted and reviewed (within 2 weeks)
- [ ] Facilitator team debrief completed (within 48 hours)
- [ ] Knowledge Base updated with lessons learned

---

## Relationship to Other Documents

| This document's section | Related concept documents |
|------------------------|--------------------------|
| Event schedule | C3_TTT_TIME_STRUCTURE_v2.md (round timing, formats, dramatic arc) |
| Facilitator Dashboard references | G1_TTT_WEB_APP_ARCHITECTURE_v2.md, Module 14 |
| Scenario configuration process | G1_TTT_WEB_APP_ARCHITECTURE_v2.md, Module 12 |
| Navigator intro/outro | F2_TTT_AI_ASSISTANT_MODULE_v2.md (three-phase conversation lifecycle) |
| AI participant management | F1_TTT_AI_PARTICIPANT_MODULE_v2.md (moderator visibility and controls) |
| Physical map | C4_TTT_MAP_CONCEPT_v2.md |
| Role briefs content | B2_TTT_ROLES_ARCHITECTURE_v2.md + D4 (private role brief seeds — future) |
| Learning objectives | A1_TTT_THUCYDIDES_TRAP_REFERENCE_v2.md (three-layer model) |
| Parameter configuration | D0_TTT_PARAMETER_STRUCTURE_v2.md (Block B and C parameters) |

---

## Open Questions

1. **Physical coins** — high immersion value but logistics complexity (counting, tracking, loss). Worth the effort? Could start without them and add based on feedback.
2. **Day 0 dinner** — included as optional. For corporate events, this is often expected. For educational settings, may not be feasible. Should it be a standard recommendation?
3. **Participant devices** — BYOD (bring your own device) or provided tablets? BYOD is simpler logistically but creates variance in screen size and capability. Tablets ensure consistency but add cost and setup time.
4. **Language** — TTT is designed in English. For non-English-speaking groups: translate materials and briefs, or keep English as the SIM language (many leadership programs operate in English regardless of location)?
5. **Photography and video** — record the SIM for promotional material and participant memories? Requires additional consent. A dedicated photographer adds to the experience but also to cost and logistics.
6. **Accessibility** — how to accommodate participants with visual impairment (interface), hearing impairment (voice-based AI interactions), or mobility limitations (moving between meeting rooms)? Must be addressed before first delivery.

---

## Changelog

- **v1.0 (2026-03-25):** Initial concept. 15 sections covering: facilitator team model (3–5 people), customization/setup process (4 phases), participant pre-work and onboarding, physical location requirements with setup checklist, printed materials and artefacts, intro briefing (3 format options), event schedule (two-day and single-day), reflection circles (2–3 questions format), structured debrief with awards, post-event deliverables (individual + institutional), moderator instructions and training (3 training models), contingency procedures, marketing and registration, feedback collection, licensing model considerations. Master delivery checklist consolidated.
