# Product Roadmap

## Milestone A: Repository Rehabilitation

Status: complete after the verification evidence in `MAINTENANCE.md`.

- validated domain and persistence boundaries
- shared application services
- corrected pairing progression and history
- unavoidable-repeat fallback
- auditable correction and regeneration
- truthful simplified McMahon policy
- hardened local web UI and startup
- property, integration, lint, typing, and coverage gates

## Milestone B: Tournament Director Essentials

- withdrawal, late entry, and re-entry
- manual pairing repair with explicit override records
- result correction controls in the UI
- audit-log display and verification status in the UI
- explicitly supported scoring/result policy configuration

## Milestone B1: Local Integrity and Prototyping

Status: first slice complete.

- Windows click-and-go local launcher - complete
- local HMAC-SHA256 audit-log signing and verification - complete
- source-file tamper detection through tournament state hashes - complete
- future key-provider/encryption abstraction - planned
- director-facing audit verification workflow in the web UI - planned
- automatic signing after mutating service operations - planned

## Milestone C: Reports and Tournament Trials

- print-friendly pairing, result, and standings pages - complete
- realistic 32-player fixtures and deterministic five-round Swiss/McMahon simulations - complete
- browser print-layout human trial - pending
- structured tournament-director feedback - pending
- PDF only after the print-layout trial and structured feedback are complete

## Milestone D: Pairing Quality

- affiliation preference
- richer float and colour policy
- expanded McMahon starting-score bands
- SODOS and Go-specific tie-breaks
- optional weighted matching

## Milestone E: Distribution

- one-command packaged local launch
- backup and recovery tools
- desktop packaging evaluation

Multi-user networking remains deferred until the local workflow is proven in
real events.

Next product decision: if field-trial corrections surface, fix those first;
otherwise design Milestone B Tournament Director Essentials before
implementation.
