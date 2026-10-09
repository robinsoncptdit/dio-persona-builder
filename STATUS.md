# Status

State: active
Last updated: 2026-10-08
Date source: commit 39956af, 2026-10-08 ("Add persona_profiles snapshot and project status")
Current focus: Bringing the project back into active work after a dormant stretch (2025-06-13 to 2026-10-08). First steps are getting the test suite green and the generation pipeline running again on current models and credentials.
Next actions:
- Fix the 17 failing tests (29 pass). They look like drift from the "expert review" commit, which changed code without updating tests: missing-validation expectations, renamed O*NET model fields, changed error types.
- Replace gpt-3.5-turbo (technology_filter.py:56, cli.py:424) with a current model. Check that the O*NET endpoint (services.onetcenter.org/ws) still accepts the stored credentials, and that the OpenAI key in .env still works.
- Handle the 5 roles in logs/unprocessed_roles.log, and consider rebuilding the venv from pinned requirements.
Blockers: none

Notes:
- What it is: a Python CLI that turns O*NET occupation data into diocesan personas. OpenAI (gpt-3.5-turbo) filters technologies and rewrites each persona as a UX persona. output/ holds 117 occupational and 117 user personas from the June 2025 runs.
- Canonical data: the code has no database connection, but the occupational personas were loaded separately into Supabase project mpkb2personakbv2, table persona_profiles. It has 120 rows, and 118 of them are enriched with user stories, pain points, workarounds and MinistryPlatform modules. That table is the most valuable copy. The output/user/ files are mostly blank (107 of 118 have 5 or more empty fields).
- Snapshot: data/snapshots/persona_profiles_2026-10-08.json (commit 39956af), made with `supabase db query --linked --project-ref wuwpaemokrczpixkheyw --output-format json "select to_jsonb(t) as r from persona_profiles t order by persona_id" | jq '[.rows[].r]'`.
- Supabase lockdown, 2026-10-08: run through the SQL Editor and verified the same day. All 62 public tables have RLS. 35 of them have no policies, so only the service role can reach them. The 3 views use security_invoker. The 2 materialized views and user_has_diocese_access are closed to anon.
- Venv fix, 2026-10-08: the test segfault came from a broken venv. pyvenv.cfg pointed home at a conda 3.11 env, so Homebrew 3.13 loaded C stdlib modules (_asyncio) from miniconda base's 3.13 build. pyvenv.cfg home now points to /opt/homebrew/opt/python@3.13/bin.
- Local master matched origin as of 2026-10-08.
