# KITH — Map of Needs (FOSS United)

KITH is a minimal, community-first platform built for local mutual aid. It’s a transparent, open-source “humanity flow” that connects neighbors and makes kindness visible.

> KITH means friends, acquaintances, and neighbors—those who make a place feel like home.

---

## Why KITH exists

- built for FOSS United hackathon energy and ongoing grassroots impact
- maps active local needs and turns them into a living neighborhood feed
- removes friction from help: communities can post, claim, and close requests quickly
- 100% open source stack with no hidden algorithms or closed vendor lock-in

---

## Core user flow

1. User creates need on `/add` (location, type, note)
2. Volunteer clicks `/volunteer/<id>` to take ownership
3. Admin closes request after completion
4. Requests reflect open/claimed/closed status on `/` map view

---

## Key features

- `/` interactive Leaflet map for active requests
- `/add` submit exact lat/lng + description
- `/api/needs` JSON endpoint for mobile or neighborhood clients
- `/volunteer/<id>` to reserve tasks for volunteers
- `/admin` and `/admin_users` for lightweight moderation
- `/my_requests` for request visibility by owner

---

## Strengths & potential

- lean, practical local aid tool with low adoption friction
- runs on SQLite + Flask, no complex infrastructure required
- inspectable behavior makes community trust easier
- extensible for notifications, identity, and partner integrations
- built for community flow, not corporate feature bloat

---

## Technical stack (100% FOSS)

- Python
- Flask
- Jinja2
- Werkzeug
- click
- ItsDangerous
- MarkupSafe
- SQLite (built-in)
- HTML/CSS/JavaScript
- Leaflet
- OpenStreetMap

---

## Install and run

```bash
python -m venv venv
source venv/bin/activate
pip install -r requirements.txt
python app.py
```

Open `http://localhost:5000`

---

## Open-source libraries used

- Flask
- Jinja2
- Werkzeug
- click
- ItsDangerous
- MarkupSafe
- Leaflet
- SQLite (public domain built-in engine)
- OpenStreetMap tile layers

> This is a transparent stack with no proprietary dependencies.

---

## Demo

*(Add screenshots, GIF, or live demo link here)*

---

## Roadmap ideas

- mobile notifications for nearby active needs
- authenticated volunteer channels and local message threads
- category + timing matching for repeat deployments
- nonprofit coordination integrations
- optional community reputation / credit system

---

## Notes

- Best fit for grassroots mutual aid groups, neighborhood teams, and pop-up response.
- Not intended as enterprise infrastructure out of the box; focused on proof-of-concept run-and-grow.
- Privacy-forward: tracks only explicit request state.

---

## About

KITH is designed to be the neighborhood connection layer: rediscovering how local neighbors keep each other resilient, one task at a time.
