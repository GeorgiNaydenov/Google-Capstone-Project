# Final Production Push Checklist

Use this as the last gate before submitting the Kaggle writeup and sharing the public project link.

## Kaggle Form

- [ ] Title is `Clinical AI Kit`.
- [ ] Subtitle is under 140 characters.
- [ ] Card image uploaded from `docs/submission/media/card-thumbnail-560x280.png`.
- [ ] Submission track selected.
- [ ] Media Gallery includes the YouTube video.
- [ ] Media Gallery includes at least the architecture, agent hierarchy, security, HITL, document ingestion, database, deployment, and rubric diagrams.
- [ ] Project Description pasted from `docs/submission/kaggle-writeup.md`.
- [ ] Project Links include `https://github.com/GeorgiNaydenov/Google-Capstone-Project` and `https://clinical-ai-kit-330118805806.us-central1.run.app/`.
- [ ] Writeup is saved and submitted, not left as a draft.

## Repository

- [ ] GitHub repository is public: `https://github.com/GeorgiNaydenov/Google-Capstone-Project`.
- [ ] Apache-2.0 `LICENSE` is present in the repo root.
- [ ] `README.md` renders cleanly on GitHub.
- [ ] `.env`, `*.db`, upload folders, local virtual environments, and generated caches are not committed.
- [ ] `deployment/README.md` explains Cloud Run persistence and live-mode constraints.

## Local Verification

Run these from the repo root:

```powershell
npm.cmd --prefix frontend run typecheck
npm.cmd --prefix frontend test
npm.cmd --prefix frontend run build
python scripts/check_harness.py
pytest tests/ -v
```

Then start the product:

```powershell
.run-venv\Scripts\python.exe -m uvicorn clinical_app.app:app --host 127.0.0.1 --port 8000
```

Verify:

- [ ] `http://127.0.0.1:8000/health` returns `{"status":"ok",...}`.
- [ ] `http://127.0.0.1:8000/ready` returns 200.
- [ ] `http://127.0.0.1:8000/` loads the product.
- [ ] `http://127.0.0.1:8000/documentation` loads the documentation hub.

## Cloud Run Verification

If deploying before submission:

```bash
gcloud builds submit --config deployment/cloudbuild.yaml .
```

After deployment:

- [ ] Cloud Run service URL opens the product.
- [ ] `/health` returns 200.
- [ ] `/ready` returns 200.
- [ ] `/documentation` opens.
- [ ] Public service reports deterministic/disabled agent execution and has no paid ADK/Gemini credentials.
- [ ] A separate self-controlled live deployment, if created, uses explicit credentials and the documented service-account roles.
- [ ] Durable storage is externalized before any self-controlled live tenant is expected to survive revisions.
- [ ] Cloud Run max instances remains 1 until shared persistent state is externalized.

## Final Human Step

The only irreversible/human-facing steps are:

- Make the GitHub repo public.
- Upload the YouTube video.
- Paste the YouTube URL into Kaggle Media Gallery.
- Add `https://clinical-ai-kit-330118805806.us-central1.run.app/`.
- Click Submit on Kaggle before the deadline.
