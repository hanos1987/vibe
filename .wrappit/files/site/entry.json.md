---
file: site/entry.json
file-hash: 7605bd9407fdd6bf2365d66c97dc2e20d9e8811b
note-hash: b6488a929f295840
---

# site/entry.json

## What it is
The storefront listing for VIBE on benjiapps.com: name, tagline, description, category, badge, icon, links, price and button text.

## How to navigate it
A single flat JSON object; `url` is the app's page (`/apps/vibe/`), `learnMoreUrl` is GitHub, `icon` names `icon.svg`.

## What it interacts with
- `icon.svg` is the file site/build_page.py writes to site/dist/icon.svg.
- Consumed by the benjiapps.com site (not by anything in this repo).

## Why it exists
Lets the benjiapps.com app catalog show a VIBE card linking to the page.

## Helpful notes
None.
