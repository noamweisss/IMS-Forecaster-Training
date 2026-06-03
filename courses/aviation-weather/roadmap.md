# Aviation Course Roadmap
created: 2026-06-02 13:00
## Upgrading Version 1 to Version 2 (active)

### Meteorology stuff
* Evgeny said that this is largely okay and that he didn't find any obvious mistakes.
* The internal division to lessons between each module is great and does its job
* ⏳ **(in progress)** It needs to go more in depth and give more examples for each lesson. Evegeny says the source material should be sufficient for a more elaborate course but if it isn't we can use material from the internet and he will verify it later.
  * Decided approach: expand from the source presentations first; pull from the internet only where the source is thin, and flag those additions for Evgeny. Done module by module on branch `v2-meteorology-content-expansion` (off `main`, separate from the merged PR #5).
  * ✅ **Module 1 done (2026-06-02)** — all 4 lessons roughly doubled in depth with added worked examples and SVG diagrams; quiz pool grown 15 → 29. Lesson 1 (WMO/ICAO) and Lesson 4 (Altimetry) expanded from source alone; Lessons 2 (Routes & Fuel) and 3 (Airspace) needed standard-reference additions, all flagged for Evgeny in `module-1/REVIEW_NOTES.md`. Optional image requests (with Google/ChatGPT prompts) also listed there.
  * ✅ **Module 2 done (2026-06-03)** — all 5 lessons (turbulence/wind-shear, icing, convection/CB, fog/haze, cloud base/top) deepened from their rich decks; quiz pool grown 25 → 36; new SVG diagrams throughout (incl. gap-wind, microburst, icing decision tree, CB hazard cross-section, visibility instruments, convective-base rule) and decoded real METAR/SPECI examples (LLBG, LLET, LLSD). Mostly source-grounded; one flagged item (carburettor-icing temperature envelope) in `module-2/REVIEW_NOTES.md`. Also fixed an SVG bug (`context-fill`) and aligned the convective-base rule to the source's (T−Td)/3. **Paused here for owner + Evgeny review before Module 3.**
  * ✅ **Module 3 done (2026-06-03)** — the four warning lessons (SIGMET framework/phenomena, SIGMET structure/coordinates/cancellation, AIRMET, aerodrome & wind-shear warnings) were already at full depth, so this was a deliberately **lighter, targeted pass**: added worked compose/decode examples (severity-gate routing, an AIRMET composition, a WS-WRNG for a low-level jet) and grew every quiz to 8 questions (pool 25 → 32). Fully source-grounded; no REVIEW_NOTES needed.
  * ⏳ Module 4 still to do.
### Design/Technical Stuff
* ✅ **(done 2026-06-02)** ~~I don't like that all the lessons are in dark mode; Moodle doesn't have a dark mode so it clashes and make the lesson look a bit out of place~~ — removed the dark-mode block from the design-system CSS and all generated HTML; lessons are always light now.
* ✅ **(done 2026-06-02)** ~~I want every emoji prefixes for activity names to make the easy to distinguish in the Moodle side bar display. We can use 📚 for lessons and ❓ for quizzes.~~ — the `.mbz` builder now prefixes pages with 📚 and quizzes with ❓.
* ✅ **(done 2026-06-02)** ~~we should include a completion standard for the quizzes, so we can verify that the forecasters really did them. we shouldn't grade them with a numerical value (or at least not show them the numerical value) but we do need a way to know who did the course fully and who didn't~~ — quizzes are now completion-tracked (automatic, "make one attempt") with the numeric grade hidden from learners; instructors get a completion report. Rebuild + re-restore the `.mbz` to apply.
* ✅ **(done 2026-06-02)** ~~the Figure 1 SVG diagram in Module 1 Lesson 2 is broken and should be re-written~~ — redrawn as a clean GS = TAS ± wind vector diagram.

## Upgrading Version 2 to Version 3 (future)
* adding more assessment methods rather than relying exclusively on multiple choice quizzes  
* translating the entire course to Hebrew reliably and automatically
