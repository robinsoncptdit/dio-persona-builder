# Status

State: paused (dormant since 2025-06-13; reviewed and test crash fixed 2026-10-08)
Last updated: 2026-10-08
Current focus: Python CLI that turns O*NET occupation data into diocesan personas, with OpenAI (gpt-3.5-turbo) filtering technologies and rewriting each one as a UX persona. 117 occupational and 117 user personas sit in output/ from the June 2025 runs. The code has no database connection, but the occupational personas were loaded elsewhere into Supabase project mpkb2personakbv2, table persona_profiles: 120 rows, 118 enriched with user stories, pain points, workarounds and MinistryPlatform modules. That table is the most valuable copy. A verified snapshot is at data/snapshots/persona_profiles_2026-10-08.json (uncommitted). It was made with `supabase db query --linked --project-ref wuwpaemokrczpixkheyw --output-format json "select to_jsonb(t) as r from persona_profiles t order by persona_id" | jq '[.rows[].r]'`. The output/user/ files are mostly blank (107 of 118 have 5 or more empty fields). Local master matches origin as of 2026-10-08.
Next actions:
- Fix the 17 failing tests (29 pass). They look like drift after the "expert review" commit changed the code without updating tests: missing-validation expectations, renamed O*NET model fields, changed error types.
- Replace gpt-3.5-turbo (technology_filter.py:56, cli.py:424) with a current model, and check the O*NET endpoint (services.onetcenter.org/ws) still accepts the stored credentials.
- Handle the 5 roles in logs/unprocessed_roles.log, and consider rebuilding venv from pinned requirements.
Blockers: none. The test segfault was a broken venv: pyvenv.cfg pointed home at a conda 3.11 env, so Homebrew 3.13 loaded C stdlib modules (_asyncio) from miniconda base's 3.13 build. On 2026-10-08, pyvenv.cfg home was repointed to /opt/homebrew/opt/python@3.13/bin. The OpenAI and O*NET credentials in .env were not checked.
