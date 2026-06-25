# OpenGotha Comparison

## Purpose

OpenGotha is the operational reference for Stage 6. Its Java implementation
contains mature tournament-director workflows and a weighted pairing engine.
This project will reuse selected product ideas, not port OpenGotha classes or
copy its architecture.

Primary OpenGotha references:

- `opengotha/src/info/vannier/gotha/Tournament.java`
- `opengotha/src/info/vannier/gotha/Pairing.java`
- `opengotha/src/info/vannier/gotha/WeightedMatchLong.java`
- `opengotha/src/info/vannier/gotha/JFrGamesPair.java`
- `opengotha/src/info/vannier/gotha/JFrGamesResults.java`
- `opengotha/src/info/vannier/gotha/JFrPlayersQuickCheck.java`
- `opengotha/src/info/vannier/gotha/JFrGotha.java`
- `opengotha/src/info/vannier/gotha/ExternalDocument.java`

## Pairing Logic

| Area | OpenGotha | Current Python implementation | Assessment |
| --- | --- | --- | --- |
| Optimizer | Complete pairwise cost matrix followed by an Edmonds-style weighted matching solver | Deterministic score-group search with strict no-repeat preference and least-penalty repeat fallback | OpenGotha is more expressive and globally optimized. Python is smaller, easier to test, and gives stronger explicit repeat semantics. |
| Duplicate opponents | Very large soft penalty | Strictly avoided when possible; unavoidable repeats are explicit warnings | Python improves rule visibility and failure behavior. |
| Score proximity | Weighted soft penalty | Score groups and deterministic float/search policy | OpenGotha offers finer global trade-offs. Python is easier to explain but less sophisticated. |
| Draw-up/down balance | Historical DU/DD counts with configurable compensation and group targeting | No explicit DU/DD history | OpenGotha is ahead. This belongs in a later pairing-quality slice. |
| Affiliation avoidance | Country and club preferences with configurable trade-offs | Affiliation fields exist, but pairing does not use them | OpenGotha is ahead. |
| Colour allocation | Weighted balance; deterministic tie resolution; handicap games excluded from balance | Deterministic colour-history balancing | Broadly comparable, but OpenGotha exposes more tuning. |
| Handicap | Rank- or McMahon-score-based with threshold, correction, and ceiling | Reserved only | OpenGotha is ahead. |
| Byes | Separate per-round bye assignment using score, rank, and prior byes | Bye represented as a completed game and selected deterministically | Python's unified game representation improves validation and reporting. |
| McMahon | Configurable bar/floor, score bands, handicap, and tie-breaks | Deliberately simplified one-bar starting score | OpenGotha is substantially richer. |
| Tie-breaks | Large vocabulary including SODOS, direct confrontation, and variants | Score, wins, SOS, SOSOS | OpenGotha is ahead. |
| Explanations | Diagnostic reports after pairing | Pairing reasons and warnings stored with generated rounds | Python better integrates explanations with persisted state, but its explanations are shallow. |

## Tournament Workflow

OpenGotha's strongest operational ideas are:

- separate full player editing from a fast per-round quick-check view;
- model participation independently for each round;
- show participants, assigned players, and entered results in a round dashboard;
- make unpairing, colour exchange, table changes, and bye repair first-class;
- centralize reporting and publishing;
- preserve explicit save copies and a rolling work snapshot.

The ideas worth avoiding are:

- giant mutable `Tournament` and Swing-frame classes;
- UI code mutating tournament state directly;
- implicit workflow states inferred from unrelated counts;
- weak domain enforcement around manual game insertion;
- hidden propagation and configuration behavior;
- broad configuration whose controls are disabled or ineffective;
- snapshot recovery without a durable event journal.

## Improvements Already Achieved

The Python project has improved on OpenGotha in these areas:

- domain, engine, application, storage, CLI, and web dependencies point inward;
- CLI and web use the same application services;
- complete aggregate validation runs before save and after load;
- writes are atomic and preserve the old file on failure;
- correction and regeneration retain audit evidence and superseded round data;
- repeat handling is explicit rather than hidden inside a weight;
- deterministic property and full-event tests protect pairing invariants;
- supported and reserved behavior is documented instead of implied by dormant
  fields.

## Areas Where OpenGotha Remains Ahead

- per-round participation, withdrawal, re-entry, and late entry;
- quick floor-operations views and round completeness warnings;
- manual pairing repair tools;
- configurable special results and richer scoring;
- backup-copy workflow;
- handicap pairing;
- affiliation-aware and DU/DD-aware weighted matching;
- expanded McMahon, SODOS, and direct-confrontation tie-breaks;
- team tournaments and additional tournament formats.

## Stage 6 Direction

Stage 6 starts with director workflow completeness rather than weighted
matching. It will preserve the Python architecture and validation contracts
while adopting OpenGotha's best operational patterns. Weighted matching,
handicap, richer McMahon, team events, and new formats remain separately
designed later slices.
