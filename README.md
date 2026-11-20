# SLAY 2026 vote dashboard

GitHub Pages dashboard for streamer votes. It refreshes `data.json` from the public Telegram channel `@slay_awards` every 15 minutes using GitHub Actions, then redeploys Pages. The page itself refreshes its data every five minutes.

The overall leaderboard sums personal streamer nominations. Couple, project, event, and track choices remain independent options.

## Publish

Enable GitHub Pages with **GitHub Actions** as the publishing source. The included workflow handles polling and deployment.
