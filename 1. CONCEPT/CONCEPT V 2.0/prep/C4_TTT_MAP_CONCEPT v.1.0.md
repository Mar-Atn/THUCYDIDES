# Thucydides Trap SIM — Map Concept
**Version:** 1.0 | **Date:** 2026-03-19 | **Status:** Conceptual

---

## Core Idea

The Global Map & the local war maps are the focal points of the simulation, it smain **competition field**. These maps, together with some main global dashboards shall be centrally located and permanently publicly visible during the simulation.  

The SIM uses a **two-layer map system**: a permanent global strategic map showing the whole world, and dynamic theater zoom-ins that activate only when military escalation demands tactical resolution. The map is not just a visual aid — it is a gameplay signal. When a new theater map appears, everyone in the room knows the world just got more dangerous.

---

## Layer 1 — Global Strategic Map

**Always visible.** This is the "situation room" view — the big picture that sits on the wall or main screen throughout the entire SIM.

### What it shows

- All countries from the SIM roster, clearly labeled and positioned
- Alliance memberships via color coding or border treatment (NATO, BRICS+, EU, etc.)
- Military force deployment markers — where each country's units are currently positioned
- Maritime chokepoints — critical sea lanes that can be blockaded or contested
- Active conflict zones — highlighted when military action is underway
- Optionally toggled: trade routes, energy flows, sanctions indicators

### Geography

A full world map. Not centered on the Atlantic (which marginalizes Asia) or the Pacific (which marginalizes Europe/Middle East). Ideally centered on the **Indian Ocean / Central Asia region**, placing the two great powers (USA and China) on opposite edges and the contested middle ground — Europe, Middle East, Central Asia, Indian Ocean — prominently in the center. This centering itself tells a story: the world's conflicts cluster in the space between the two poles.

All 15+ Tier 1 countries must be clearly identifiable. Tier 2 countries included as space permits.

### Maritime chokepoints to mark

These are the world's strategic bottlenecks — locations where naval power, trade flows, and military access converge. Control or disruption of any chokepoint has global consequences.

- **Taiwan Strait** — semiconductor supply, China-Pacific access
- **Strait of Hormuz** — Gulf oil exports, Iran's leverage point
- **Bosphorus / Black Sea** — Russia's warm-water access, Turkey's control lever
- **Suez Canal** — Europe-Asia trade shortcut
- **Malacca Strait** — China's energy import vulnerability
- **South China Sea** — contested waters, island claims, massive trade volume
- **GIUK Gap** (Greenland-Iceland-UK) — North Atlantic submarine access, newly relevant with Greenland tensions
- **Caribbean passages** — US near-abroad, Venezuela/Cuba dimension

### What it does in gameplay

The global map makes the **overstretched hegemon problem visible**. Participants can see at a glance that US forces deployed to the Pacific aren't available in Europe, that Russian units are depleting on the Ukrainian front, that China is massing near the strait. It transforms abstract strategic trade-offs into something spatial and intuitive.

It also serves as the display surface for non-military information: which countries are under sanctions, where alliances hold or fracture, where economic pressure is building. The map becomes a shared narrative — the story of the game told visually.

---

## Layer 2 — Theater Zoom-Ins

**Activated dynamically.** Theater maps only appear when military action in a region escalates to the point of needing tactical resolution — unit placement, combat, territorial control.

### Design principles

**Start with two** The game begins with two active theaters (Russia-Ukraine war and Middle Esat/Iran war). All other regions exist only on the global map as political entities and deployment zones.

**Activate on escalation.** When a player or chain of events triggers military confrontation in a new region, the moderator activates that theater's zoom-in map. This is a deliberate, dramatic moment — a new map going up on the wall is a signal to every participant that containment has failed somewhere.

**The number of active theaters at game end is itself a measure of outcome.** If the game ends with one active theater (or zero, if peace is achieved), participants have managed the Trap. If it ends with four active theaters, the world is in freefall. This makes escalation tangible and countable.

**Not all theaters need equal detail.** The granularity of each zoom-in should match the nature of the conflict it models.

### Potential theaters

#### Eastern Europe (active at game start)
The Russia-Ukraine front. Simplified from the Conflict SIM's 22 sectors to approximately **12-20 zones**: western Ukraine, central Ukraine (including capital), eastern front (active combat), southern front / Crimea, Russian border regions, and Belarus corridor. Enough for meaningful maneuver and resource deployment, simple enough to resolve in minutes per round.

Ground forces dominate. Territory changes matter for social score, negotiating leverage, and national morale. The proven dice-combat mechanic from the Conflict SIM applies here.

#### Taiwan Strait / Western Pacific
Activates if China initiates blockade, military exercises-as-pressure, or invasion. A simpler grid — perhaps **3-4 zones**: the strait itself, Taiwan proper, sea/air approaches from the east, and Chinese staging coast. The military question here is more binary than territorial: does China attempt a crossing? Does the US intervene? Does Japan activate?

Naval and air power dominate. Semiconductor facilities on Taiwan are a strategic target / asset to protect. Resolution is fast but consequences are enormous (global economic shock from trade disruption).

#### Middle East
**7-8 zones** covering: Iran (nuclear sites marked), Israel, the Gulf (Hormuz), and proxy territories (Lebanon/Syria, Yemen). 

Air and missile power dominate. The nuclear dimension (Iran's program, Israel's undeclared arsenal) adds escalation risk. Oil infrastructure as strategic target.

#### Caribbean
Activates if the US intervenes militarily in Venezuela/Cuba. **2-3 zones**: naval deployment area, Venezuela/Cuba, proximity to US mainland.

The smallest and simplest theater — but thematically important because it shows the hegemon's own use of force in its sphere.

#### Greenland 
Acyivates if US decides to capture Greenland.  **2-3 zones**

#### Korean Peninsula (optional)
Activates if North Korea provokes beyond the threshold (nuclear test, artillery on Seoul, invasion). **3-4 zones**: North Korea, the DMZ / Seoul corridor, South Korea, and US/Japan basing. 

The terrifying proximity of Seoul to the DMZ makes this theater unique — millions of civilians at immediate risk. Nuclear dimension from North Korea.


---

## Map Style

**Fictional geography with transparent parallels** (like the Conflict SIM). Advantages: psychological safety, creative freedom, avoids political sensitivities with real-world participants, allows geographic simplification. The Conflict SIM's maps proved this works beautifully — everyone knows who "Nordostan" is, but the fictional layer allows players to make choices they might not with real country names.

The map should be **beautifully produced** — the Conflict SIM's fantasy-cartography style (terrain details, sea textures, stylized borders) set a high bar. The map is a physical artifact that draws people in and makes the simulation world feel real. 

### Physical vs. digital implementation

The map is **hybrid**: a large printed global map on the wall for constant reference and physical presence, combined with a digital version on screen that updates in real time (force deployments, sanctions status, alliance indicators). Theater zoom-ins posted when activated (dramatic, tactile) or displayed on screen (more flexible, supports the web platform).

For the web platform version: the global map is the main interface, with clickable regions that expand to theater detail when active. Force deployment is drag-and-drop. The map is the dashboard.

---

## Relationship to Game Domains

The map is not a separate domain — it is the **visual integration layer** where all domains become spatial:

- **Military:** Unit deployment markers, theater combat zones, force projection ranges
- **Economy:** Trade routes, energy flows, sanctions impact (could show as dimmed trade lines), chokepoint control
- **Internal politics:** Territorial losses/gains affect social score, refugee flows have direction and destination
- **Technology:** Semiconductor facilities marked (Taiwan), nuclear sites marked (Iran, N. Korea), missile ranges as overlays

---

## Open Questions for Next Version

1. **Scale of Eastern Europe theater at start:** How detailed? The Conflict SIM's 22 sectors were rich but created moderator burden. What's the minimum that preserves meaningful tactical choice?
2. **Theater activation trigger:** Who decides? The players themselves by choosing to initiate military action?
3. **Naval mechanics:** Several theaters are primarily naval (Taiwan Strait, Hormuz, Caribbean). Do we need a distinct naval mechanic, or is force deployment to sea zones sufficient?

---

## Changelog

- **v1.0 (2026-03-19):** Initial concept. Two-layer map system (global + dynamic theaters). Six potential theater zoom-ins defined. Chokepoints identified. Style and implementation options outlined. Detail levels deferred.
