# KITH — Map of Needs

KITH is a minimal, community-first platform built for local mutual aid. It’s a transparent, open-source “humanity flow” that connects neighbors and makes kindness visible.

> **KITH** means friends, acquaintances, and neighbors—those who make a place feel like home.

---

## Core Features

- **Interactive Map:** Live Leaflet/OpenStreetMap view of active community needs.
- **Request Help:** Submit requests with precise location (map picker or geolocation), type, and description.
- **Volunteer:** Neighbors can browse the map and claim tasks to help others.
- **Community Fun:** Post and find local community events, meetups, and volunteering opportunities.
- **Admin Dashboard:** Lightweight moderation for managing users, requests, and community events.

---

## Getting Started

### 1. Prerequisites
- Python 3.9+
- pip (Python package manager)

### 2. Initial Setup
Clone the repository and set up a virtual environment:

```bash
# Create a virtual environment
python -m venv .venv

# Activate the virtual environment
# On Linux/macOS:
source .venv/bin/activate
# On Windows:
.venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt
```

### 3. Configuration
KITH uses environment variables for configuration. You can use either a `.env` file or a `.config` file.

```bash
# Create your configuration from the examples
cp example.env .env
```

Open `.env` and configure your settings:
- **SECRET_KEY:** Set this to a long, random string.
- **SEED_ADMIN:** Set to `true` if you want to automatically create an admin user on the first run.
- **ADMIN_PASSWORD:** Required if `SEED_ADMIN` is true.

### 4. Run the Application
```bash
python app.py
```
Open `http://localhost:5000` in your browser.

---

## Administration

### Admin Seeding
By setting `SEED_ADMIN=true` in your configuration, the application will create a default admin account on startup using the `ADMIN_USERNAME` and `ADMIN_PASSWORD` you provided.

### CLI Management
You can also manage the application via the command line:

```bash
# Create a new admin user
flask create-admin <username> <password>

# List all users
flask list-users
```

---

## Technical Stack (100% FOSS)

- **Backend:** Python / Flask
- **Database:** SQLite (SQLAlchemy ORM)
- **Frontend:** HTML5, Vanilla CSS, JavaScript
- **Maps:** Leaflet.js / OpenStreetMap

---

## About the Project
KITH was originally built for the FOSS United hackathon, following open-source principles:
- **100% Open Source:** No hidden algorithms or vendor lock-in.
- **Privacy Forward:** Tracks only explicit request state.
- **Lean & Practical:** Low friction for grassroots mutual aid groups.

---

## License
Distributed under the MIT License. See `LICENSE` for more information.
