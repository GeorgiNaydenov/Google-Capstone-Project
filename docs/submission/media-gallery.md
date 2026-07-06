# Kaggle Media Gallery Pack

The Kaggle form shows that videos must be hosted on YouTube. Do not upload an `.mp4` directly to Kaggle. Upload the demo video to YouTube first, then add the YouTube URL through the **Media gallery -> Add videos or photos** button.

## Required Basic Details

- Title: `Clinical AI Kit`
- Subtitle: `A Google ADK multi-agent clinical command center that turns fragmented evidence into auditable, clinician-approved decisions.`
- Card and thumbnail image: use `docs/submission/media/card-thumbnail-560x280.png`
- Submission tracks: choose the closest available tracks for Technical Implementation, Deployability, Security, and Agent / Multi-agent Systems. If the selector allows only one, choose Technical Implementation.

## Media Gallery Order

Add the media in this order so the story reads clearly:

1. YouTube demo video, 5 minutes or less.
2. Card/thumbnail: `docs/submission/media/card-thumbnail-560x280.png`.
3. System architecture: `frontend/public/diagrams/01-system-architecture.png`.
4. Agent hierarchy: `frontend/public/diagrams/06-agent-hierarchy.png`.
5. Security pipeline: `frontend/public/diagrams/11-security-pipeline.png`.
6. Human-in-the-loop approval: `frontend/public/diagrams/15-human-in-the-loop-bpmn.png`.
7. Document ingestion flow: `frontend/public/diagrams/16-document-ingestion-flow.png`.
8. Database ERD: `frontend/public/diagrams/23-clinical-database-erd.png`.
9. Deployment topology: `frontend/public/diagrams/04-deployment-topology.png`.
10. Capstone rubric coverage: `frontend/public/diagrams/27-capstone-rubric-coverage.png`.

If you capture fresh product screenshots, add these after the video and before the diagrams:

- Landing page or role selection.
- Clinician dashboard with the diagram atlas visible.
- Extraction review gate after a sample upload.
- Q&A answer with citations open.
- Database intelligence chart after SQL approval.
- Admin system health screen.
- Documentation hub at `/documentation`.

## Video Placement

In the Kaggle form, scroll to **Media gallery**, click **Add videos or photos**, choose the video option, and paste the public or unlisted YouTube URL. The video belongs in the Media Gallery, not in the Project Links attachment list.

## 5-Minute Video Script

Use `docs/submission/demo-script.md` as the shot list. Keep the final YouTube video at or below 5 minutes.

## Public Project Links

Add these under **Attachments -> Project Links**:

- GitHub repository: `https://github.com/GeorgiNaydenov/Google-Capstone-Project`
- Deployed app URL: add the Cloud Run URL after deployment, if available.
- Documentation hub: use the deployed `/documentation` URL if deployed; otherwise mention `http://localhost:8000/documentation` in the README/setup path.

Before final submission, make the GitHub repository public and confirm the Apache-2.0 `LICENSE` is visible from the repo root.
