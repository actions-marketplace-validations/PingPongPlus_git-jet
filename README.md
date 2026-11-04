# Git Jet

One to three pixel jets launch from a carrier, bank over your real commit calendar,
and destroy each active day's cell. Transparent background, rolling ocean swells,
bow foam and a flowing stern wake, projectiles,
pixel explosions and a spinning radar. Runs with GitHub Actions.

**Lincoln — default carrier**

<picture>
  <source media="(prefers-reduced-motion: reduce)" srcset="examples/demo/git-jet.png?v=graph-theme-20261103">
  <img src="examples/demo/git-jet.gif?v=graph-theme-20261103" width="960" alt="A pixel jet launches from a Lincoln-inspired carrier through rolling ocean water, with an angled runway, detailed island and spinning radar.">
</picture>

**Classic — original carrier with the green graph**

<picture>
  <source media="(prefers-reduced-motion: reduce)" srcset="examples/demo-classic/git-jet.png?v=graph-theme-20261103">
  <img src="examples/demo-classic/git-jet.gif?v=graph-theme-20261103" width="960" alt="The original ivory-island carrier with a spinning radar and flowing ocean wake launches a pixel jet to clear a green commit calendar.">
</picture>

Choose `carrier: 'lincoln'` (default) or `carrier: 'classic'` in your workflow.
For the CLI, use `--carrier classic`. Both designs have the spinning radar.

Choose `water: 'ocean'` (default) for the flowing ocean surface and wake, or
`water: 'original'` for the original small wave patches. This works with either
carrier. For the CLI, use `--water ocean` or `--water original`.

Choose `graph-theme: 'github'` for GitHub green activity cells, as shown
in the Classic demo. The default is `graph-theme: 'blue'`, shown in the Lincoln
demo. Either graph theme works with either carrier and water style.
For the CLI, use `--graph-theme github` or `--graph-theme blue`.

Both demos show **three jets** and **56 synthetic commits across 14 active days**. Live mode uses your
actual data. **One attack clears one day cell**, regardless of that day's count.
The jet returns to land, the calendar rebuilds, and the animation loops.

## Use in your profile

1. Copy [this workflow](examples/profile-workflow.yml) into your profile repository
   as `.github/workflows/git-jet.yml`.
2. Open **Actions → Git Jet → Run workflow**. It publishes images to `output`.
3. Add this to your README, replacing `YOUR_USERNAME` with your GitHub username:

```html
<a href="https://github.com/PingPongPlus/git-jet">
  <picture>
    <source media="(prefers-reduced-motion: no-preference)"
      srcset="https://raw.githubusercontent.com/YOUR_USERNAME/YOUR_USERNAME/output/git-jet.gif">
    <img width="960"
      src="https://raw.githubusercontent.com/YOUR_USERNAME/YOUR_USERNAME/output/git-jet.png"
      alt="My commit history cleared by a pixel jet">
  </picture>
</a>
```

Clicking the animation or its static fallback opens the Git Jet repository.
Existing users can replace their image block with this snippet to add the link.

Updates run **daily**. Set `days: '30'`, `'7'` or `'365'` under the generation
step's `with:` section. The static PNG preserves the full calendar. Flight uses
smooth curves at a steady cruise speed and fires while moving. The default is
20 FPS; `fps: '10'` makes smaller files while preserving flight speed. Set
`scale: '1'` for smaller images.

Set `jets: '2'` or `jets: '3'` to launch multiple jets and clear busy calendars
faster. The default is `jets: '1'`. Jets share the day cells, so each active day
is still attacked exactly once. Jets line up visibly on the runway, launch one
at a time and land in order, returning to their original runway spots. Waiting
jets remain visible before takeoff and after landing. Launch timing keeps the
runway clear for each arrival. The calendar resets after every jet lands.
Small calendars may take a similar time because launch
and return flights still need to finish. For the CLI, use `--jets 3`.

GIFs over **25 MB** are automatically retried at a lower resolution, then lower
FPS if needed. Every day-cell attack is kept. To help keep your requested
resolution, use more jets (`jets: '3'`) to shorten the animation. Disable this
fallback with `auto-compress: 'false'` or CLI `--no-auto-compress`.

Every generation picks a fresh route with varied sweeps, gentle bends and
occasional small loops while shooting. To keep a favorite route, set
`seed: 'my-route'` in the action or use CLI `--seed my-route`. Omit the seed for
new randomness on each run. The generated `report.json` records the chosen seed.

## Run locally

```sh
python3 -m venv .venv
source .venv/bin/activate
python -m pip install -e '.[dev]'
git-jet render --demo --output-dir out/demo
git-jet render --username YOUR_USERNAME --days 365 --carrier lincoln --output-dir out/live
```

For offline real-data rendering, use `--calendar out/live/calendar.json`.
`git-jet collect --username YOUR_USERNAME --output out/calendar.json` saves data
without rendering. `GITHUB_TOKEN` is optional locally; Actions supplies its token.
No server is needed.

## What gets counted

Distinct authored commits in **public, owned, non-fork repositories' default
branches**, including documentation commits. The selected 1–365-day window
includes today and uses UTC. Duplicate SHAs count once. This commit-only graph
excludes issues, PR activity, private repositories and unlinked author identities.
It can differ from GitHub's broader profile contribution calendar.

Each active day gets one visible attack; flight length grows with active days.
No targets are silently sampled or skipped. Empty calendars get a patrol with
no shots. Export is bounded to 3,000 frames and 25 MB per GIF. If even the smallest
render cannot fit, select fewer days. Failed generation preserves previously good assets.

Generation and publication are separate. The publisher updates only `git-jet.gif`
and `git-jet.png` on `output`, preserves other files, uses non-force pushes and
never changes your default branch. Publishing requires `contents: write`.

## Goals

- [x] Approved carrier, parked aircraft, waves, directional jets, grid and effects.
- [x] Real commit collection, transparent GIF/PNG export and a daily Actions template.
- [x] Catapult launch, banked flight, one attack per active day and carrier return.
- [x] Optional 1–3 jets to share targets and shorten busy calendars.
- [ ] Optional **one shot per individual commit** mode.
- [ ] More carrier/jet/runway designs and configurable graph palettes, with artwork approval.

[Artwork approvals](artwork/APPROVAL.md) · [Contributing](CONTRIBUTING.md) · [MIT](LICENSE)
