# KITH — Map of Needs

KITH is a minimal, community-first platform built for local mutual aid. It’s a transparent, open-source “humanity flow” that connects neighbors and makes kindness visible.

> **KITH** means friends, acquaintances, and neighbors—those who make a place feel like home.

<img width="1247" height="574" alt="image" src="https://github.com/user-attachments/assets/234ab723-47a8-419e-a27b-90e6da1dbcbb" />
---

## Core Features

- **Interactive Map:** Live Leaflet/OpenStreetMap view of active community needs.
- **Request Help:** Submit requests with precise location (map picker or geolocation), type, and description.
- **Volunteer:** Neighbors can browse the map and claim tasks to help others.
- **Community Fun:** Post and find local community events, meetups, and volunteering opportunities.
- **Admin Dashboard:** Lightweight moderation for managing users, requests, and community events.

---

## Getting Started
For a basic understanding of how to run KITH, Just clone the repo, statify the dependency stated in requirements.txt, create your secure .env file(Example provided) and run it with docker as a container. 
### 1. Prerequisites
- Python 3.9+
- pip (Python package manager)
- docker (for containerization.)

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
KITH uses environment variables for configuration. You can use a `.env` file.

```bash
# Create your configuration from the examples
cp example.env .env
```

Open `.env` and configure your settings:
- **SECRET_KEY:** Set this to a long, random string.
- **SEED_ADMIN:** Set to `true` if you want to automatically create an admin user on the first run.
- **ADMIN_PASSWORD:** Required if `SEED_ADMIN` is true.

### 4. Run the Application
# docker (RECOMMENDED)
```bash
#simply spin up a docker container by running as admin.
docker compose build 
docker compose up
```
## To run without docker.
```bash
python app.py
```
Open `http://localhost:5000` in your browser.

---

## Administration
Visit the homepage or open `http://localhost:5000/admin` in your browser to acess the admin panel.
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

# This can be done with the docker container as well for example: 
```bash
docker compose exec web flask create-admin kith_admin secretPass123
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
