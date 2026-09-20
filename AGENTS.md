# Repository instructions

## Authoritative lifecycle

Follow this stage order exactly:

`P0 Environment → P1 Product Design → P2 Technical Design → P3 Scaffolding → P4 Backend → P5 Frontend → P6 Exceptions/Boundaries → P7 Operations → P8 Testing → P9 Documentation → P10 Delivery Acceptance`

- `docs/PROJECT_LIFECYCLE.md` defines each stage and exit gate.
- `PROGRESS.md` is the single status source and must be updated when a gate changes.
- Do not claim a stage is complete until its exit criteria have evidence.
- Product discovery artifacts may be drafted during P0, but P1 cannot pass until the user confirms the positioning.

## Product gate

- Do not implement business UI or business API until the product positioning is confirmed.
- Every feature must map to a user problem, a requirement ID, and an executable acceptance check.
- Prefer one complete vertical slice over several partial modules.

## Scope

- This is an engineering validation and review tool, not a diagnostic medical device.
- Do not add diagnosis, treatment advice, automated segmentation, model training, or real patient integrations.
- Do not introduce microservices, Redis, Celery, Kubernetes, or real-time collaboration for the MVP.

## Privacy

- Use only public, de-identified, or physical-phantom sample data with documented provenance.
- Never log PatientName, PatientID, request bodies, raw DICOM tag collections, or original filenames.
- Display DICOM metadata through an explicit allowlist.
- Keep uploads, databases, logs, generated previews, and secrets out of Git.

## Engineering

- Frontend features live under `apps/web/src/features`; shared code lives under `apps/web/src/shared`.
- API routes translate protocols; business rules belong in services; persistence belongs in repositories.
- API paths use `/api/v1`; IDs use UUID; timestamps use UTC ISO 8601.
- Errors expose a stable code and request ID, never stack traces.
- Add or update tests and documentation with every vertical slice.

## AI-assisted work

- Record material AI assistance in `docs/engineering/ai-usage.md`.
- Verify generated code through documentation, tests, static checks, and manual acceptance paths.
- Record at least one AI suggestion that was modified or rejected and why.
