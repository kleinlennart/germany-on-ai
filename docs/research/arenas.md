# Arenas, levels and venues: what the literature says and how to code them

Research note for the `arenas` attribute (currently `domestic | eu | international` on each Source in the Catalogue). Written 2026-11-17. Works marked **[in Zotero]** are already in the project owner's library. Quotes from an abstract are marked "(abstract)". Other quotes give the page where the passage was read.

## Summary

- **"Arena" mixes four things.** These are the *level* of government, the *venue* where something happens, the *object* a record is about, and the *capacity* in which an actor speaks. The three-value `arenas` tag is fine for describing a Source but too coarse for comparing records.
- **Code a named venue and derive the arena from it.** CAP, IPOD, Council open data and AGORA all record the issuing or deciding body. The owner's "coarse arena plus named forum" fits this, provided `arena` is computed from the venue and never tagged by hand.
- **Describe venues with attributes.** Regime-complex research (Raustiala & Victor 2004; Alter & Raustiala 2018; Geith, Lundgren & Tallberg 2026) shows that "international" lumps together universal IOs, regional bodies, informal clubs and summit series. Venue shopping turns on exactly these differences. A small venue table (`level`, `parent`, `kind`, `membership`, `binding_output`) captures them.
- **Code what a record is about separately from where it happened.** Two-level games (Putnam 1988) and work on parliamentary EU scrutiny (Auel, Rozenberg & Tacea 2015 [in Zotero]) show domestic venues being used to shape international outcomes. Gap analysis needs both fields.
- **Record capacity.** The EU speaks at the UN "to present positions of the European Union and its member States as agreed by them" (A/RES/65/276, annex ¶1). Without a `capacity` field, positions get misattributed to Germany, or lost.
- **Separate actor level from venue level, and build in `subnational` and `local` now.** Research on subnational mobilisation (Hooghe 1995; Jeffery 2000; Tatham 2010) shows Länder acting through a national venue (the Bundesrat) and directly in Brussels. One vocabulary, `local | subnational | national | eu | international`, serves both. `domestic` rolls up the first three, so the current scheme keeps working.
- **A gap between arenas is not proof of a contradiction.** Governments deliberately signal differently to different audiences (Putnam 1988; Hagemann, Hobolt & Wratil 2017). Such gaps are candidates for Judgments.

## Concepts

### Multi-level governance

Hooghe and Marks describe authority being reallocated "upward, downward, and sideways from central states" (2003, abstract). They distinguish two types:

- **Type I** governance disperses authority to "general-purpose, nonintersecting, and durable jurisdictions": municipal, regional, national, EU.
- **Type II** uses "task-specific, intersecting, and flexible jurisdictions" (abstract).

Earlier work on the EU argued that sovereignty is "diluted in the European arena" and that subnational actors deal with Brussels directly (Marks, Hooghe & Blank 1996, abstract; Hooghe 1995).

**For the tracker:** Type I levels form a clean ordered ladder, so a `level` attribute fits them well. Type II bodies, such as the CCW Group of Governmental Experts, GPAI or standards bodies, do not sit on one rung. That is a reason to describe forums by their attributes and not only by their level. The subnational literature asks whether sub-state actors bypass the state or work through it. Jeffery (2000) builds on domestic constitutional context, and Tatham (2010) studies "intra- and extra-state channels" (abstract). This motivates an `actor_level` that is separate from `venue_level`. Germany's Basic Law builds Länder participation into federal EU policy-making through the Bundesrat (Art. 23(2), (4)–(5) GG). Where the Länder's exclusive legislative powers over school education, culture or broadcasting are primarily affected, it transfers the exercise of Germany's rights in the EU to a representative of the Länder nominated by the Bundesrat (Art. 23(6) GG). The paradiplomacy literature covers the foreign relations of subnational governments more generally (Duchacek 1990; Keating 1999; Kuznetsov 2014). The Regional Authority Index codes regions as units, with self-rule and shared-rule scores, across 81 countries (Hooghe et al. 2016). It offers a country-neutral way to define what counts as "subnational".

### Two-level games

Putnam models a negotiator who must win "ratification (formal or informal) from their constituents" at home while bargaining abroad (1988, abstract). Later work adds a third level for the EU (Patterson 1997) and connects national preference formation to interstate bargaining (Moravcsik 1993).

**For the tracker:** the same actor does different things at different levels, and statements made in a domestic venue are often moves in an international game. That supports keeping venue (where it was said) separate from object (which negotiation it is about). It also warns against reading every difference between arenas as a contradiction.

### Europeanisation

Börzel defines Europeanisation as a "two-way process": member states "'upload' their policies to the European level" to minimise the costs of "'downloading'" them (2002, abstract). She classifies their strategies as pace-setting, foot-dragging or fence-sitting. Radaelli (2003) develops the concept for public policy. National parliaments are now "multi-arena players" that act at home, at EU level and jointly with other parliaments (Auel & Neuhold 2017, abstract [in Zotero]).

**For the tracker:** Germany's EU engagement runs in both directions. Uploading happens in the Council and its working parties. Downloading happens in the Bundestag, the Bundesrat and ministries. Records in both directions share an EU object but sit in different venues. Auel, Rozenberg & Tacea (2015, pp. 285–286 [in Zotero]) code four kinds of parliamentary EU activity: European Affairs Committee meetings, plenary debates, mandates or resolutions, and Political Dialogue opinions. They note that parliaments address statements either "to the government" or "to the European Commission". This is a working precedent for coding an addressee.

### Regime complexes

A regime complex is "a collective of partially overlapping and nonhierarchical regimes" (Raustiala & Victor 2004, abstract). Alter and Raustiala (2018, abstract) add that it includes "more than one international agreement or authority" and that its institutions "may be functional or territorial in nature". Keohane and Victor (2011 [in Zotero]) describe climate governance as a "loosely-coupled set of specific regimes" (abstract). Alter and Meunier (2009) set out the mechanisms through which regime complexity shapes later cooperation. Related work on fragmentation includes Biermann et al. (2009) and Orsini, Morin & Young (2013).

**For the tracker:** the "international" arena is a regime complex, not a single place. Forums need stable identities and links between them: parent bodies, nesting and overlapping membership.

### Forum shopping, venue shopping and regime shifting

These three terms describe the same move in different research traditions:

- **Venue shopping (public policy).** Baumgartner and Jones (1991, abstract; 1993) explain policy change through the interaction of a policy image with "the venues of policy action". Pralle defines venue shopping as "finding a decision setting that offers the best prospects for reaching one's policy goals" (2003, abstract), and her case is Canadian forest advocates moving from domestic to international venues. Guiraudon (2000) shows governments moving migration policy "vertically" to EU-level venues to escape domestic constraints.
- **Forum shopping (international relations).** Busch (2007) explains a complainant's choice between overlapping trade forums by membership: who the resulting precedent will bind.
- **Regime shifting (international law).** Helfer (2004; 2009) describes states and NGOs moving lawmaking from one regime to another whose mandate suits them better.

**For the tracker:** to show forum choice, the data needs (1) which forum, (2) when, (3) on what object, and (4) forum attributes such as membership and bindingness that explain why one forum would be chosen over another. Vertical shopping, from national to EU level, uses the `level` ladder. Horizontal shopping, for example from the CCW to the UN General Assembly, uses forum identity and attributes.

### Work specific to AI governance

- **Cihon, Maas & Kemp (2020) [in Zotero]** weigh centralised against fragmented AI governance. They note that a central body "may be able to deter forum shopping", but that "forum shopping can be beneficial" (abstract).
- **Schmitt (2022)** maps AI governance in a two-by-two matrix: the kind of driving actor, and whether action happens inside or outside the existing governance architecture. He finds a "polycentric and fragmented" regime that gravitates around the OECD (abstract).
- **Tallberg et al. (2023)** set out an empirical and normative research agenda on the emerging global AI governance architecture.
- **Veale, Matus & Gorwa (2023) [in Zotero]** catalogue governance *modalities*: ethics councils, industry governance, contracts and licensing, standards, international agreements, and domestic law with extraterritorial reach.
- **Roberts et al. (2024)** call the landscape a "weak 'regime complex'" (abstract) and argue for strengthening it rather than centralising it.
- **Geith, Lundgren & Tallberg (2026)** build a dataset of 119 international institutions involved in AI governance. They code institution type, membership (state, private and civil-society members), a "subentity" link for bodies nested inside other institutions, policy scope, policy domain and bindingness. They find little hierarchy and a dense concentration of governance efforts in Europe.
- **Rosert & Sauer (2021)** analyse the Campaign to Stop Killer Robots. They argue that its strategy of seeking a binding instrument within the CCW is unlikely to work, and recommend adjusting the campaign's "institutional choices" (abstract). This is a direct venue-choice argument for the CCW strand of the tracker.

## Operationalisation options

The owner ranks the purposes as: (1) comparing Germany's positions across arenas as the basis for a gaps-and-contradictions analysis, (2) showing forum choice and venue shopping, (3) advocacy targeting. Navigation comes second. Each option below is judged against those purposes. In the project's layers, venue facts that the source states belong in the **Source record**. Inferred objects (what a record is about) are **Annotations** that name their `method`. A claimed gap or contradiction is a **Judgment**.

### Option A: coarse `arena` only (current)

Three values, multi-valued, set per Source.

- **Supported by:** the classic domestic/international split and the EU's special status in Europeanisation research.
- **Strengths:** easy to apply and easy to explain.
- **Weaknesses:** it describes a Source, not a record. It cannot say which forum, about what, or in what capacity. All three purposes need those facts. Keep it as a Catalogue summary only.

### Option B: a level ladder

`local | subnational | national | eu | international`, single-valued per record. `domestic` is a roll-up of `local`, `subnational` and `national`.

- **Supported by:** Type I multi-level governance (Hooghe & Marks 2003), the Regional Authority Index's region-as-unit approach, and vertical venue shopping (Guiraudon 2000).
- **Strengths:** builds subnational levels in now without breaking the three-value view. The values are country-neutral, as ADR 0006 requires: `subnational`, not "Land". The country-specific unit type (Land, state, province) goes on the venue or actor.
- **Weaknesses:** "international" stays a residual bucket. Type II and club forums do not fit on a rung.

### Option C: coarse arena plus a named venue (the owner's preference)

Each record gets one `venue`, an ID in a venue table, for example `unga`, `council-eu`, `bundestag-digital-committee` or `ccw-gge-laws`. The arena is derived from the venue.

- **Supported by:** every dataset in the table below records the issuing or deciding body. Regime-complex research needs stable forum identities. Venue shopping is defined as a choice between named venues.
- **Strengths:** it is the minimum needed for purposes 2 and 3. It is deterministic: the arena is computed and never typed by hand.
- **Where it falls short:**
  1. **Venue is not the object.** A Bundestag debate about CCW negotiations has the venue `bundestag` and the object `ccw-gge-laws`. Gap analysis compares positions on the same object across different venues, so the object must be recorded (two-level games; Auel et al.'s addressee).
  2. **No capacity.** The EU speaks "on behalf of" member states at the UN, but under A/RES/65/276 it "shall not have the right to vote, to co-sponsor draft resolutions or decisions, or to put forward candidates" (annex ¶3). Germany still votes in its own name. Without `capacity`, positions get misattributed.
  3. **A flat venue list hides structure.** Council configurations sit inside the Council, committees sit inside the Bundestag, and the GGE sits inside the CCW. AGORA solves this with *authority → parent authority → jurisdiction*. Geith et al. use a subentity flag.
  4. **Venue level is not actor level.** The Bundesrat is a federal organ whose members are Länder governments. A Land's office in Brussels is a subnational actor working at EU level.

### Option D (recommended): Option C extended with a venue table and three relational fields

Venue table (reference data, one row per forum):

| field | values | literature or scheme |
|---|---|---|
| `id`, `name`, `name_original` | e.g. `council-eu`, "Council of the European Union" | Council open data, IPOD |
| `level` | `local, subnational, national, eu, international` | Hooghe & Marks 2003; RAI |
| `parent` | venue ID (configuration → Council; committee → Bundestag; GGE → CCW) | AGORA parent authority; Geith et al. subentity |
| `kind` | legislature, executive, court, IO organ, treaty body, informal club, summit series, multistakeholder | Geith et al. institution type; IPOD's exclusion of informal G7/G20 (p. 121) |
| `membership` | universal, regional, plurilateral/club, not applicable | Busch 2007; Alter & Raustiala 2018 |
| `decision_rule`, `binding_output` | e.g. QMV/unanimity, consensus; binding yes/no | Council open data (voting rule); OECD.AI "Legally binding"; Geith et al. |
| `unit_type` | country-specific label (e.g. "Land") | ADR 0006 |

Record-level fields:

- `venue` (single-valued; Source record): where it happened. `arena` is derived from it. In the glossary's terms, `venue` belongs on the **Event** (a Council meeting, a UN session, a debate), and Statements and Votes inherit it through their Event. A **Document** takes its issuing body as its venue, as in AGORA's "authority".
- `actor_level` (on the Actor record): same vocabulary as venue `level`.
- `capacity` (on Statements and Votes): `own | on_behalf | aligned | presidency`, plus `on_behalf_of` (an Actor ID) where relevant. This follows A/RES/65/276 and EU practice at the UN.
- `about` (multi-valued; an Annotation unless the source states it): venue or process IDs the record concerns.

If this option is adopted, `venue`, `level` and `capacity` would be new glossary terms; `arena` would then mean only the derived three-value roll-up.

Trade-offs: more reference data to maintain, and the `about` field calls for judgement, so it needs a documented `method`. A separate `channel` field (legislative, executive, diplomatic) is probably redundant, because venue `kind` combined with actor type already gives it. Auel et al.'s activity types (committee, plenary, resolution, opinion) fit better as a record `type` than as a channel.

How Option D serves each purpose:

- **Gap analysis:** group by `about` and Actor, compare across `venue`, and filter on `capacity` so that own positions are separated from collective ones.
- **Venue shopping:** count records by `about` over time and venue, and explain the pattern with venue attributes.
- **Advocacy targeting:** the venue's `decision_rule`, its `parent` and the actors present show who decides where.

### Edge cases

The cases are stylised, not claims about particular events.

| case | A: `arenas` only | B: level ladder | C: arena + venue | D: full |
|---|---|---|---|---|
| 1. Germany's recorded vote in the Council on an AI legislative act | eu | eu | eu / `council-eu` (configuration unclear) | venue `council-eu-<configuration>` (parent `council-eu`), level eu, capacity own. Stored for all member states (ADR 0006). |
| 2. EU delegation statement at UNGA First Committee "on behalf of the EU and its member States"; Germany does not speak | eu, international (ambiguous) | international (or eu, depending on whether the speaker or the venue is coded) | international / `unga-first-committee`; looks like Germany's position or is missed | venue `unga-first-committee` (international); speaker actor EU (actor_level eu); capacity on_behalf; Germany linked as aligned, not as speaker. |
| 3. Bundestag plenary debate on the CCW talks on autonomous weapons | domestic | national (the CCW link is lost) | domestic / `bundestag` (the CCW link is lost) | venue `bundestag` (national); about `ccw-gge-laws`. The government's line here can be compared with its CCW statements. |
| 4. Bundesrat opinion on an EU AI proposal (Art. 23(4)–(5) GG) | domestic | national (Länder role and EU object both lost) | domestic / `bundesrat` | venue `bundesrat` (national); actor Bundesrat with members at actor_level subnational; about the EU proposal (eu). |
| 5. Länder representative exercising Germany's rights in the Council on AI in schools (Art. 23(6) GG) | eu | eu (or subnational, depending on whether the actor or the venue is coded) | eu / `council-eu` | venue `council-eu-<configuration>`; actor_level subnational; capacity on_behalf, on_behalf_of Germany. |
| 6. Chancellor signs a joint declaration at an AI summit (informal summit series) | international | international | international / `ai-summit-series` | venue kind summit series, membership plurilateral, binding_output no. IPOD would leave it out; Geith et al. include informal institutions. |

## Existing coding schemes

| dataset | unit | how venue or level is coded | source |
|---|---|---|---|
| Comparative Agendas Project, German Policy Agendas | coded item (bill, law, parliamentary question, government statement, manifesto, survey response) | Topic is coded (21 major topics, 220 subtopics). The venue is implicit in which dataset an item belongs to. | [comparativeagendas.net/germany](https://www.comparativeagendas.net/germany); Bevan 2019 |
| UNGA votes (Voeten; UNGA-DM) | country × roll call (`unvotes`); ideal points per country-year (Voeten) | Venue fixed (UNGA). Vote choice per roll call (see codebooks). Roll calls carry resolution, session, amendment/paragraph flags and six issue codes in `unvotes`. UNGA-DM adds votes on paragraphs, amendments and failed resolutions. | [Dataverse LEJUQZ](https://doi.org/10.7910/DVN/LEJUQZ); [UNGA-DM](https://unvotes.unige.ch/); [`unvotes`](https://cran.r-project.org/package=unvotes); Fjelstul, Hug & Kilby 2025 [in Zotero] |
| UN General Debate Corpus | country statement per session | Venue fixed (General Debate). The speaking state is the actor. | Baturo, Dasandi & Mikhaylov 2017 [in Zotero]; Jankin, Baturo & Dasandi 2025 [in Zotero] |
| Council votes on legislative acts | legislative act × member-state vote | Council configuration, session, voting procedure, voting rule (QMV or unanimity), form of adoption, policy area | [data.europa.eu](https://data.europa.eu/data/datasets/council-votes-on-legislative-acts) (marked discontinued); Hagemann, Hobolt & Wratil 2017 |
| DEU III | contested issues within selected EU legislative proposals (see paper for exact unit) | Positions of EU actors on those issues; EU venue fixed | Arregui & Perarnaud 2022 |
| IPOD | policy act of an IO's principal intergovernmental body | IO plus the deciding body (e.g. EU Council, UN Security Council); topic, type, instrument, target; excludes G7/G20 as not IOs | Lundgren et al. 2024 [in Zotero] |
| AI regime-complex dataset | international institution (119) | Institution type, membership, subentity link, scope, domain, bindingness | Geith, Lundgren & Tallberg 2026 |
| OECD.AI policy database | policy initiative | Country/territory *or* international organisation/forum; category separating national from "intergovernmental or supranational"; legally binding yes/no; status | [oecd.ai policy initiatives](https://oecd.ai/en/dashboards/policy-initiatives) |
| AGORA | AI-related legal document | Authority → parent authority (e.g. "State governments") → jurisdiction; status proposed/enacted/defunct | [ETO docs](https://eto.tech/dataset-docs/agora-dataset); [Zenodo](https://doi.org/10.5281/zenodo.21964209) |
| EU activities of national parliaments | parliament-year counts | Activity type (committee meetings, plenary debates, mandates/resolutions, Political Dialogue opinions); addressee (government or Commission) | Auel, Rozenberg & Tacea 2015 [in Zotero] |
| Regional Authority Index | region-year | Self-rule and shared rule per regional tier, 81 countries | Hooghe et al. 2016 |

## References

- Alter, K. J., & Meunier, S. (2009). The politics of international regime complexity. *Perspectives on Politics*, 7(1), 13–24. https://doi.org/10.1017/S1537592709090033
- Alter, K. J., & Raustiala, K. (2018). The rise of international regime complexity. *Annual Review of Law and Social Science*, 14, 329–349. https://doi.org/10.1146/annurev-lawsocsci-101317-030830
- Arnold, Z., Melot, J., Enwereazu, O., Schiff, D. S., et al. (2026). *AGORA Dataset* (v1.32.0). Zenodo. https://doi.org/10.5281/zenodo.21964209
- Arregui, J., & Perarnaud, C. (2022). A new dataset on legislative decision-making in the European Union: The DEU III dataset. *Journal of European Public Policy*, 29(1), 12–22. https://doi.org/10.1080/13501763.2021.1991983
- Auel, K., & Neuhold, C. (2017). Multi-arena players in the making? Conceptualizing the role of national parliaments since the Lisbon Treaty. *Journal of European Public Policy*, 24(10), 1547–1561. https://doi.org/10.1080/13501763.2016.1228694 [in Zotero]
- Auel, K., Rozenberg, O., & Tacea, A. (2015). To scrutinise or not to scrutinise? Explaining variation in EU-related activities in national parliaments. *West European Politics*, 38(2), 282–304. https://doi.org/10.1080/01402382.2014.990695 [in Zotero]
- Bailey, M. A., Strezhnev, A., & Voeten, E. (2017). Estimating dynamic state preferences from United Nations voting data. *Journal of Conflict Resolution*, 61(2), 430–456. https://doi.org/10.1177/0022002715595700
- Baturo, A., Dasandi, N., & Mikhaylov, S. J. (2017). Understanding state preferences with text as data: Introducing the UN General Debate corpus. *Research & Politics*, 4(2). https://doi.org/10.1177/2053168017712821 [in Zotero]
- Baumgartner, F. R., & Jones, B. D. (1991). Agenda dynamics and policy subsystems. *Journal of Politics*, 53(4), 1044–1074. https://doi.org/10.2307/2131866
- Baumgartner, F. R., & Jones, B. D. (1993; 2nd ed. 2009). *Agendas and Instability in American Politics*. University of Chicago Press. ISBN 9780226039497 (2nd ed.)
- Bevan, S. (2019). Gone fishing: The creation of the Comparative Agendas Project master codebook. In F. R. Baumgartner, C. Breunig & E. Grossman (Eds.), *Comparative Policy Agendas* (pp. 17–34). Oxford University Press. https://doi.org/10.1093/oso/9780198835332.003.0002
- Biermann, F., Pattberg, P., van Asselt, H., & Zelli, F. (2009). The fragmentation of global governance architectures: A framework for analysis. *Global Environmental Politics*, 9(4), 14–40. https://doi.org/10.1162/glep.2009.9.4.14
- Börzel, T. A. (2002). Pace-setting, foot-dragging, and fence-sitting: Member state responses to Europeanization. *Journal of Common Market Studies*, 40(2), 193–214. https://doi.org/10.1111/1468-5965.00351
- Busch, M. L. (2007). Overlapping institutions, forum shopping, and dispute settlement in international trade. *International Organization*, 61(4), 735–761. https://doi.org/10.1017/S0020818307070257
- Cihon, P., Maas, M. M., & Kemp, L. (2020). Fragmentation and the future: Investigating architectures for international AI governance. *Global Policy*, 11(5), 545–556. https://doi.org/10.1111/1758-5899.12890 [in Zotero]
- Cihon, P., Maas, M. M., & Kemp, L. (2020). Should artificial intelligence governance be centralised? Design lessons from history. *Proceedings of the AAAI/ACM Conference on AI, Ethics, and Society*, 228–234. https://doi.org/10.1145/3375627.3375857 [in Zotero]
- Duchacek, I. D. (1990). Perforated sovereignties: Towards a typology of new actors in international relations. In H. J. Michelmann & P. Soldatos (Eds.), *Federalism and International Relations* (pp. 1–33). Oxford University Press. https://doi.org/10.1093/oso/9780198274919.003.0001
- Fjelstul, J., Hug, S., & Kilby, C. (2025). Decision-making in the United Nations General Assembly: A comprehensive database of resolution-related decisions. *Review of International Organizations*. https://doi.org/10.1007/s11558-024-09580-1 [in Zotero]
- Geith, J., Lundgren, M., & Tallberg, J. (2026). The emerging regime complex for artificial intelligence. *Global Studies Quarterly*, 6(4). https://doi.org/10.1093/isagsq/ksag145
- Grundgesetz für die Bundesrepublik Deutschland, Art. 23. https://www.gesetze-im-internet.de/gg/art_23.html
- Guiraudon, V. (2000). European integration and migration policy: Vertical policy-making as venue shopping. *Journal of Common Market Studies*, 38(2), 251–271. https://doi.org/10.1111/1468-5965.00219
- Hagemann, S., Hobolt, S. B., & Wratil, C. (2017). Government responsiveness in the European Union: Evidence from Council voting. *Comparative Political Studies*, 50(6), 850–876. https://doi.org/10.1177/0010414015621077
- Helfer, L. R. (2004). Regime shifting: The TRIPs Agreement and new dynamics of international intellectual property lawmaking. *Yale Journal of International Law*, 29, 1–83. https://scholarship.law.duke.edu/faculty_scholarship/2014
- Helfer, L. R. (2009). Regime shifting in the international intellectual property system. *Perspectives on Politics*, 7(1), 39–44. https://doi.org/10.1017/S1537592709090069
- Hooghe, L. (1995). Subnational mobilisation in the European Union. *West European Politics*, 18(3), 175–198. https://doi.org/10.1080/01402389508425097
- Hooghe, L., & Marks, G. (2003). Unraveling the central state, but how? Types of multi-level governance. *American Political Science Review*, 97(2). https://doi.org/10.1017/S0003055403000649
- Hooghe, L., Marks, G., Schakel, A. H., Chapman Osterkatz, S., Niedzwiecki, S., & Shair-Rosenfield, S. (2016). *Measuring Regional Authority: A Postfunctionalist Theory of Governance, Volume I*. Oxford University Press. https://doi.org/10.1093/acprof:oso/9780198728870.001.0001
- Jankin, S., Baturo, A., & Dasandi, N. (2025). Words to unite nations: The complete United Nations General Debate Corpus, 1946–present. *Journal of Peace Research*, 62(4), 1339–1351. https://doi.org/10.1177/00223433241275335 [in Zotero]
- Jeffery, C. (2000). Sub-national mobilization and European integration: Does it make any difference? *Journal of Common Market Studies*, 38(1), 1–23. https://doi.org/10.1111/1468-5965.00206
- Keating, M. (1999). Regions and international affairs: Motives, opportunities and strategies. *Regional & Federal Studies*, 9(1), 1–16. https://doi.org/10.1080/13597569908421068
- Keohane, R. O., & Victor, D. G. (2011). The regime complex for climate change. *Perspectives on Politics*, 9(1), 7–23. https://doi.org/10.1017/S1537592710004068 [in Zotero]
- Kuznetsov, A. S. (2014). *Theory and Practice of Paradiplomacy*. Routledge. https://doi.org/10.4324/9781315817088
- Lundgren, M., Squatrito, T., Sommerer, T., & Tallberg, J. (2024). Introducing the Intergovernmental Policy Output Dataset (IPOD). *Review of International Organizations*, 19(1), 117–146. https://doi.org/10.1007/s11558-023-09492-6 [in Zotero]
- Marks, G., Hooghe, L., & Blank, K. (1996). European integration from the 1980s: State-centric v. multi-level governance. *Journal of Common Market Studies*, 34(3), 341–378. https://doi.org/10.1111/j.1468-5965.1996.tb00577.x
- Marks, G., Nielsen, F., Ray, L., & Salk, J. E. (1996). Competencies, cracks, and conflicts: Regional mobilization in the European Union. *Comparative Political Studies*, 29(2), 164–192. https://doi.org/10.1177/0010414096029002002
- Moravcsik, A. (1993). Preferences and power in the European Community: A liberal intergovernmentalist approach. *Journal of Common Market Studies*, 31(4), 473–524. https://doi.org/10.1111/j.1468-5965.1993.tb00477.x
- OECD.AI. National AI policies & strategies: policy initiatives database. https://oecd.ai/en/dashboards/policy-initiatives (filters read 2026-11-17)
- Orsini, A., Morin, J.-F., & Young, O. (2013). Regime complexes: A buzz, a boom, or a boost for global governance? *Global Governance*, 19(1), 27–39. https://doi.org/10.1163/19426720-01901003
- Patterson, L. A. (1997). Agricultural policy reform in the European Community: A three-level game analysis. *International Organization*, 51(1), 135–165. https://doi.org/10.1162/002081897550320
- Pralle, S. B. (2003). Venue shopping, political strategy, and policy change: The internationalization of Canadian forest advocacy. *Journal of Public Policy*, 23(3), 233–260. https://doi.org/10.1017/S0143814X03003118
- Putnam, R. D. (1988). Diplomacy and domestic politics: The logic of two-level games. *International Organization*, 42(3), 427–460. https://doi.org/10.1017/S0020818300027697
- Radaelli, C. M. (2003). The Europeanization of public policy. In K. Featherstone & C. M. Radaelli (Eds.), *The Politics of Europeanization* (pp. 27–56). Oxford University Press. https://doi.org/10.1093/0199252092.003.0002
- Raustiala, K., & Victor, D. G. (2004). The regime complex for plant genetic resources. *International Organization*, 58(2), 277–309. https://doi.org/10.1017/S0020818304582036
- Roberts, H., Hine, E., Taddeo, M., & Floridi, L. (2024). Global AI governance: Barriers and pathways forward. *International Affairs*, 100(3), 1275–1286. https://doi.org/10.1093/ia/iiae073
- Rosert, E., & Sauer, F. (2021). How (not) to stop the killer robots: A comparative analysis of humanitarian disarmament campaign strategies. *Contemporary Security Policy*, 42(1), 4–29. https://doi.org/10.1080/13523260.2020.1771508
- Schmitt, L. (2022). Mapping global AI governance: A nascent regime in a fragmented landscape. *AI and Ethics*, 2(2), 303–314. https://doi.org/10.1007/s43681-021-00083-y
- Tallberg, J., Erman, E., Furendal, M., Geith, J., Klamberg, M., & Lundgren, M. (2023). The global governance of artificial intelligence: Next steps for empirical and normative research. *International Studies Review*, 25(3). https://doi.org/10.1093/isr/viad040
- Tatham, M. (2010). 'With or without you'? Revisiting territorial state-bypassing in EU interest representation. *Journal of European Public Policy*, 17(1), 76–99. https://doi.org/10.1080/13501760903465082
- United Nations General Assembly (2011). Resolution 65/276, Participation of the European Union in the work of the United Nations (A/RES/65/276, 3 May 2011). https://digitallibrary.un.org/record/702981
- Veale, M., Matus, K., & Gorwa, R. (2023). AI and global governance: Modalities, rationales, tensions. *Annual Review of Law and Social Science*, 19, 255–275. https://doi.org/10.1146/annurev-lawsocsci-020223-040749 [in Zotero]
- Voeten, E. (2013). Data and analyses of voting in the United Nations General Assembly. In B. Reinalda (Ed.), *Routledge Handbook of International Organization* (pp. 80–92). Routledge. https://doi.org/10.4324/9780203405345-14
- Voeten, E. United Nations General Assembly Ideal Points [dataset]. Harvard Dataverse. https://doi.org/10.7910/DVN/LEJUQZ

## Unverified

- **Baumgartner & Jones (1993), definition of "policy venues".** A widely repeated definition, "institutional locations where authoritative decisions are made", is attributed to the book (p. 32 in some secondary sources, which give the 2009 edition). I could not see the book's text, so this note does not quote it. The book's existence and editions were confirmed through publisher and bookseller listings.
- **Hooghe & Marks (2003), page range.** Crossref and OpenAlex give no pages, so none are listed. The Type I/II wording quoted above comes from the abstract.
- **AGORA's academic paper (Arnold et al., AIES 2024).** Search results mention it, but I did not confirm it, so only the Zenodo dataset is cited.
- **Hooghe & Marks (2001), *Multi-Level Governance and European Integration*.** Crossref lists only a 2002 reprint DOI. It is left out and the 2003 APSR article is used instead.
All other references were confirmed through Crossref or OpenAlex DOI metadata, the publisher's page or the official repository.

Further caveats (not unverified references):

- **Council voting data.** The data.europa.eu record is marked discontinued. I could not reach the Council's own open-data page (HTTP 403), so the current successor dataset, if any, is unconfirmed.
- **UNGA-DM and DEU III codebooks.** Neither codebook was read, so their table rows describe them only at the level confirmed by the papers, the `unvotes` README and the Dataverse record.
- **Zotero.** I searched by author surname for most cited works, and by title fragment for a few (Börzel, Schmitt, Roberts et al.). Works not tagged [in Zotero] were not found. Because the search matches substrings, an item stored under a variant spelling could have been missed.
