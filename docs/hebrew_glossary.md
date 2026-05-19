# Hebrew Glossary — Aviation Weather Terms

Bilingual reference for the Hebrew translation pipeline. Both the
translator agent and the editor agent consult this file as the single
source of truth for term renderings.

**Status: seed list, v0.1. The owner / SME (Evgeny) should review and
lock these before the first production translation run.** Anywhere the
agents need a term not listed here, they propose a Hebrew rendering and
record it in `_translation_manifest.json` under `new_glossary_proposals`
for later review.

Rules:
- Group 1 acronyms stay in Latin script in the translated output. Israeli
  aviation/meteorology practice is to use the English acronym
  untransliterated.
- Group 2 terms are translated using the Hebrew rendering listed. If a
  term has two acceptable renderings, the "preferred" column is the one
  the translator uses; the "alternative" column documents what to flag
  as a `glossary_consistency / warning` if the editor sees it instead.
- Notes column captures rationale or edge cases.

---

## Group 1 — Acronyms preserved in Latin script

| Acronym | Expansion | Notes |
|---------|-----------|-------|
| ICAO | International Civil Aviation Organization | Universal. Never transliterate. |
| WMO | World Meteorological Organization | Universal. Never transliterate. |
| METAR | Meteorological Aerodrome Report | Code-name; always English. |
| TAF | Terminal Aerodrome Forecast | Code-name; always English. |
| SIGMET | Significant Meteorological Information | Code-name; always English. |
| AIRMET | Airmen's Meteorological Information | Code-name; always English. |
| AIP | Aeronautical Information Publication | |
| SARPs | Standards and Recommended Practices | ICAO terminology; English. |
| NMHS | National Meteorological and Hydrological Service | English in ICAO/WMO context. |
| MWO | Meteorological Watch Office | English. |
| FIR | Flight Information Region | English. |
| IFR | Instrument Flight Rules | English. |
| VFR | Visual Flight Rules | English. |
| ITCZ | Inter-Tropical Convergence Zone | Scientific; English. |
| CAT | Clear-Air Turbulence | English. |
| TCU | Towering Cumulus | Cloud code; English. |
| CB | Cumulonimbus | Cloud code; English. |
| MSLP | Mean Sea Level Pressure | English in operational use. |
| hPa | hectopascals | Unit; English. |
| QNH | Altimeter setting (sea-level reference) | Q-code; English. |
| QFE | Altimeter setting (field elevation reference) | Q-code; English. |
| QNE | Altimeter setting (standard pressure) | Q-code; English. |
| FL | Flight Level | Used with number, e.g. "FL350"; English. |
| AGL | Above Ground Level | English. |
| AMSL | Above Mean Sea Level | English. |
| UTC | Coordinated Universal Time | English. |

---

## Group 2 — Translated technical terms

| English | Hebrew (preferred) | Alternative (flag if used) | Notes |
|---------|---------------------|----------------------------|-------|
| aviation weather | מזג אוויר תעופתי | מזג אוויר אווירי | "תעופתי" matches IMS operational usage. |
| meteorologist | מטאורולוג | חזאי (forecaster) | Distinguish: a meteorologist is a scientist; a forecaster operates. |
| forecaster | חזאי | — | Operational role. Plural: חזאים. |
| forecast (noun) | תחזית | חיזוי | תחזית is the standard product name. |
| observation | תצפית | — | |
| runway | מסלול המראה ונחיתה | מסלול | Long form on first mention; "מסלול" acceptable thereafter. |
| aerodrome | שדה תעופה | נמל תעופה (airport) | "שדה תעופה" is the regulatory term; "נמל תעופה" implies commercial. |
| cloud base | בסיס עננים | — | |
| cloud top | ראש עננים | פסגת עננים | |
| ceiling | תקרה | — | Operational meaning: cloud ceiling. |
| visibility | ראות | — | |
| turbulence | טלטולים | מערבולות אוויר | "טלטולים" is IMS operational; "מערבולות אוויר" is more technical. |
| icing | היווצרות קרח | קרח | Long form preferred on first mention. |
| wind shear | גזירת רוח | — | |
| fog | ערפל | — | |
| haze | אובך | — | |
| mist | אד | — | |
| squall | סופת רוח פתאומית | משב פתאומי | |
| gust | משב | — | |
| convection | הסעה | קונבקציה | Both are used in IMS; "הסעה" is preferred Hebrew. |
| advection | הסעה אופקית | — | Distinguished from vertical convection. |
| jet stream | זרם סילון | — | |
| pressure setting | כיוון לחץ | — | |
| altimeter | מד גובה | אלטימטר | "מד גובה" preferred. |
| altitude | גובה | — | |
| flight level | רום טיסה | — | Used with the FL code, e.g. "רום טיסה FL350". |
| transition altitude | גובה מעבר | — | |
| transition level | רום מעבר | — | |
| standard (n.) | תקן | תקנה | "תקן" matches ICAO Annex usage. |
| recommended practice | המלצה לפעולה | המלצה | Long form on first mention. |
| regulation | תקנה | — | |
| amendment | תיקון | — | |
| compliance | עמידה בתקן | — | |
| difference (ICAO) | "Difference" (סטייה) | סטייה | Keep English term in parens — it's an ICAO formal term. |
| annex | נספח | — | E.g. "ICAO Annex 3" → "נספח 3 של ICAO". |
| airspace | מרחב אווירי | — | |
| airspace class | מחלקת מרחב אווירי | — | E.g. "Class A" → "מחלקה A" (the letter stays Latin). |
| controlled airspace | מרחב אווירי מבוקר | — | |
| uncontrolled airspace | מרחב אווירי לא מבוקר | — | |
| airway | נתיב אווירי | — | |
| precipitation | משקעים | — | |
| temperature | טמפרטורה | חום | "טמפרטורה" in scientific context. |
| dew point | נקודת טל | — | |
| relative humidity | לחות יחסית | — | |
| pressure | לחץ | — | |
| isobar | קו לחץ שווה | איזובר | "קו לחץ שווה" on first mention. |
| front (weather) | חזית | — | E.g. "cold front" → "חזית קרה". |
| trough | אפיק | — | |
| ridge | רכס | — | |
| cyclone | ציקלון | סופה | |
| anticyclone | אנטי-ציקלון | — | |
| cumulonimbus (full word) | ענן קומולונימבוס | — | When spelled out; use "CB" otherwise. |
| stratus | סטרטוס | — | Cloud type names are transliterated. |
| cumulus | קומולוס | — | |
| cirrus | צירוס | — | |
| satellite | לוויין | — | |
| radar | מכ"ם | רדאר | "מכ"ם" is the Hebrew technical term. |
| sounding | מדידה אנכית | סאונדינג | |

---

## How to add to this glossary

When the translator agent encounters an unlisted technical term:

1. Render a best-guess Hebrew.
2. Append `(English term)` on the first occurrence in each lesson.
3. Record the proposal in `_translation_manifest.json` under
   `new_glossary_proposals` with the fields `english`, `hebrew_proposal`,
   and `notes`.

After the run, review the manifest's proposals. If a rendering is good,
move it into Group 2 above with the owner / SME's sign-off and commit
the glossary update separately. If a rendering needs change, edit it in
the glossary first, then re-run the translator agent — the next run
will pick up the new entry.
