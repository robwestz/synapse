# SEI-X Control Center (WIP)

Static HTML/CSS/JS prototype for the SEI-X control panel. Built in Work-in-progress to keep it lightweight and easy to iterate.

## Run
- Open `index.html` directly for a quick preview.
- If the browser blocks JSON fetch from file://, run a local server:
  - `python -m http.server` (from this directory)

## Svelte-ready notes
- Major sections are structured as candidates for Svelte components.
- `data/mock.json` is a placeholder dataset to replace with live API data.
- `app.js` contains minimal rendering logic that can be migrated into Svelte stores.

## Next options
- Convert each panel into a Svelte component.
- Replace mock data with a typed API layer.
- Add route and workspace management.
