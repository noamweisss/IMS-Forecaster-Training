# Module 1 — Review Notes for Evgeny (internet / standard-reference additions)

The V2 meteorology-expansion pass expands each lesson from the source decks
first. Where a source deck was **thin**, we added standard aviation-meteorology
facts from general references (ICAO Annexes 3/6, EASA/industry flight-planning
practice). Those additions are listed here so you can confirm the numbers and
thresholds are appropriate for the IMS audience. Nothing here is invented; it is
all standard practice — but it did **not** come from the original presentation,
so it deserves a second look.

Lessons whose source decks were rich (Lesson 1 WMO/ICAO; Lesson 4 Altimetry)
were expanded from the source alone and have **no** flagged claims.

---

## Lesson 2 — Aviation Route Planning & Fuel Management

The source deck (`02. Routes and Fuel.pdf`, 29 slides, Hebrew) is thin on
quantitative meteorology — it gives the great-circle geometry, a wind-triangle
example, the fuel-vs-payload trade-off, and the route→…→fuel factor chain, but
not the standard numeric values below. Please confirm:

1. **International Standard Atmosphere (ISA) values** — 15&nbsp;°C at MSL,
   lapse rate ~2&nbsp;°C per 1,000&nbsp;ft to the tropopause; temperature aloft
   read as an "ISA deviation".
   *Used in:* "Temperature and Aircraft Performance" section, Figure 3, the
   ISA worked example, and quiz Q06.

2. **Warmer-than-standard air lowers the maximum/optimum cruise altitude and
   raises fuel flow** (for a fixed Mach, TAS rises with temperature but density,
   thrust and lift fall).
   *Used in:* same section + Figure 3.

3. **Dispatch fuel components and typical values** — taxi + trip + contingency
   (~5% of trip) + alternate + final reserve (~30&nbsp;min holding). The worked
   example uses illustrative figures (trip 10,000&nbsp;kg, contingency 500&nbsp;kg,
   alternate 1,800&nbsp;kg, final reserve 1,200&nbsp;kg).
   *Used in:* "Building the block fuel" worked example + quiz Q07.

4. **Illustrative cruise burn ~2,500&nbsp;kg/h** (used to convert 33 extra
   minutes into ~1,400&nbsp;kg of fuel).
   *Used in:* "What a 50 kt headwind costs" worked example.

5. **Cost Index (CI)** — CI&nbsp;=&nbsp;0 flies for minimum fuel; higher CI flies
   faster to save time when time-related costs dominate.
   *Used in:* the Cost Index callout.

6. **Minimum-time track and the North Atlantic Organized Track System** — that
   the daily NAT tracks are built around the jet. (The "great circle = shortest
   distance" point itself *is* from the source deck.)
   *Used in:* "Choosing the Route" section + quiz Q05.

---

## Lesson 3 — Airspace Structure & Classification

The source deck (`03. Airspace.pdf`, 11 slides, Hebrew) is the thinnest in the
module. It **does** give: the control hierarchy (FIR/ACC, TMA/Approach, CTR,
ATC), CVFR and IFR/ATS routes with vertical separation, transition level / QNH /
QNE, and the **semicircular cruising-level allocation** (the FL250/270/290…
ladder on slide 10). Those are source-grounded. The ICAO A–G classification and
the VMC numbers below were added from standard references — please confirm:

1. **ICAO airspace classes A–G** as a system (the deck names the structural
   units but not the A–G letter classification or its service/clearance rules).
   *Used in:* "Airspace Classification (A to G)" section, Figure 3, the class
   table, and quiz Q01/Q03/Q05.

2. **VMC minima values** — at/above FL100: 8 km visibility, 1,500 m horizontal /
   1,000 ft vertical from cloud; below FL100 (above 3,000 ft AMSL / 1,000 ft
   AGL): 5 km, 1,500 m / 1,000 ft; at/below 3,000 ft AMSL or 1,000 ft AGL:
   Class A–E 5 km + 1,500 m / 1,000 ft, Class F/G 5 km + "clear of cloud, in
   sight of the surface." (These follow ICAO Annex 2 Table 3-1.)
   *Used in:* the VMC-minima table, the "same weather, two verdicts" worked
   example, takeaways, and quiz Q06.

3. **Class-specific cruise/approach MET dependencies** (e.g., Class A → CAT and
   upper winds; CTR → wind-shear warnings) — operational framing, standard but
   not in the deck.
   *Used in:* "Why Airspace Structure Drives Your Products" + quiz Q05.

Note: the **semicircular rule** itself (odd eastbound / even westbound) IS from
the source deck (slide 10); only the surrounding VMC/class material is flagged.
