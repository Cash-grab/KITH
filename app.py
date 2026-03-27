from functools import wraps
from datetime import datetime
from flask import (
    Flask,
    render_template,
    request,
    redirect,
    url_for,
    jsonify,
    flash,
    session,
)
from flask_sqlalchemy import SQLAlchemy
from flask_wtf import CSRFProtect
from flask_wtf.csrf import CSRFError
from werkzeug.security import generate_password_hash, check_password_hash
import os

from config import Config

app = Flask(__name__)
app.config.from_object(Config)

csrf = CSRFProtect(app)
db = SQLAlchemy(app)


# Models
class User(db.Model):
    __tablename__ = "users"
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(150), unique=True, nullable=False)
    password_hash = db.Column(db.String(256), nullable=False)
    role = db.Column(db.String(32), nullable=False, default="user")
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    # List of needs created by this user.
    needs = db.relationship(
        "Need", back_populates="creator", lazy="dynamic", foreign_keys="Need.created_by"
    )
    volunteered_needs = db.relationship(
        "Need",
        back_populates="volunteer_user",
        lazy="dynamic",
        foreign_keys="Need.volunteer_user_id",
    )
    # List of fun events created by this user. This is an easter egg!
    fun_events = db.relationship("FunEvent", back_populates="creator", lazy="dynamic")

    def set_password(self, password):
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)


class Need(db.Model):
    __tablename__ = "needs"
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(255), nullable=False)
    description = db.Column(db.Text, nullable=False)
    contact_info = db.Column(db.String(255), nullable=False)
    latitude = db.Column(db.Float, nullable=False)
    longitude = db.Column(db.Float, nullable=False)
    need_type = db.Column(db.String(64), nullable=False, default="other")
    status = db.Column(db.String(32), nullable=False, default="open")
    emergency = db.Column(db.Boolean, nullable=False, default=False)
    volunteer = db.Column(db.Text, nullable=True)
    volunteer_user_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=True)
    created_by = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    creator = db.relationship("User", foreign_keys=[created_by], back_populates="needs")
    volunteer_user = db.relationship(
        "User", foreign_keys=[volunteer_user_id], back_populates="volunteered_needs"
    )


class FunEvent(db.Model):
    __tablename__ = "fun_events"
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(255), nullable=False)
    description = db.Column(db.Text, nullable=False)
    latitude = db.Column(db.Float, nullable=False)
    longitude = db.Column(db.Float, nullable=False)
    event_type = db.Column(db.String(64), nullable=False, default="community")
    event_date = db.Column(db.String(64), nullable=True)
    created_by = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    creator = db.relationship(
        "User", foreign_keys=[created_by], back_populates="fun_events"
    )


# Utility helpers
def current_user():
    user_id = session.get("user_id")
    if not user_id:
        return None
    return User.query.filter_by(id=user_id).first()


from functools import wraps


def login_required(view):
    @wraps(view)
    def wrapped_view(*args, **kwargs):
        if not session.get("user_id"):
            if (
                request.is_json
                or request.args.get("ajax")
                or request.headers.get("X-Requested-With") == "XMLHttpRequest"
            ):
                return jsonify(
                    {
                        "success": False,
                        "message": "Login required",
                        "login_url": url_for("login"),
                    }
                ), 401
            flash("Please log in to continue.", "error")
            return redirect(url_for("login"))
        return view(*args, **kwargs)

    return wrapped_view


def init_db():
    db.create_all()

    # In production, __do not__ auto-create an admin with fixed credentials.
    # This only executes when `SEED_ADMIN` environment variable is set.

    if os.getenv("SEED_ADMIN", "false").lower() in ("1", "true", "yes"):
        admin_username = os.getenv("ADMIN_USERNAME", "admin")
        admin_password = os.getenv("ADMIN_PASSWORD", None)
        if not admin_password:
            raise RuntimeError("SEED_ADMIN enabled but ADMIN_PASSWORD is not set.")

        admin = User.query.filter_by(username=admin_username).first()
        if not admin:
            admin = User(username=admin_username, role="admin")
            admin.set_password(admin_password)
            db.session.add(admin)
            db.session.commit()


# Flask 3 removed before_first_request; ensure database initializes on app startup
with app.app_context():
    init_db()

app.logger.info(
    "Starting app; SQLALCHEMY_DATABASE_URI=%s",
    app.config.get("SQLALCHEMY_DATABASE_URI"),
)


@app.context_processor
def inject_user():
    return {"current_user": current_user()}


@app.route("/register", methods=["GET", "POST"])
def register():
    if request.method == "POST":
        try:
            username = request.form.get("username", "").strip()
            password = request.form.get("password", "").strip()

            if not username or not password:
                flash("Please provide username and password.", "error")
                return redirect(url_for("register"))

            if User.query.filter_by(username=username).first():
                flash("Username already exists.", "error")
                return redirect(url_for("register"))

            user = User(username=username)
            user.set_password(password)
            db.session.add(user)
            db.session.commit()

            flash("Account created. Please log in.", "success")
            return redirect(url_for("login"))

        except Exception as exc:
            app.logger.exception("Registration failed")
            db.session.rollback()
            flash("Internal error during registration. Please try again.", "error")
            return redirect(url_for("register"))

    return render_template("register.html")


@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        try:
            username = request.form.get("username", "").strip()
            password = request.form.get("password", "").strip()

            user = User.query.filter_by(username=username).first()
            if user is None or not user.check_password(password):
                flash("Invalid username or password.", "error")
                return redirect(url_for("login"))

            session.clear()
            session["user_id"] = user.id
            flash("Logged in successfully.", "success")
            next_url = request.args.get("next") or url_for("index")
            return redirect(next_url)

        except Exception:
            app.logger.exception("Login failed")
            db.session.rollback()
            flash("Internal error during login. Please try again.", "error")
            return redirect(url_for("login"))

    return render_template("login.html")


@app.route("/logout")
def logout():
    session.clear()
    flash("Logged out.", "success")
    return redirect(url_for("index"))


@app.route("/")
def index():
    # A minimal home page; options for map is in template.
    return render_template("index.html")


@app.route("/add", methods=["GET", "POST"])
@login_required
def add_need():
    if request.method == "POST":
        name = request.form.get("name", "").strip()
        description = request.form.get("description", "").strip()
        contact_info = request.form.get("contact_info", "").strip()
        latitude = request.form.get("latitude", "").strip()
        longitude = request.form.get("longitude", "").strip()
        need_type = request.form.get("need_type", "other").strip()
        emergency = True if request.form.get("emergency") == "on" else False

        if not all([name, description, contact_info, latitude, longitude]):
            flash("Please fill all required fields, including contact info.", "error")
            return redirect(url_for("add_need"))

        try:
            latitude = float(latitude)
            longitude = float(longitude)
        except ValueError:
            flash("Latitude and longitude must be numeric.", "error")
            return redirect(url_for("add_need"))

        user = current_user()
        need = Need(
            name=name,
            description=description,
            contact_info=contact_info,
            latitude=latitude,
            longitude=longitude,
            need_type=need_type,
            emergency=emergency,
            created_by=user.id if user else None,
        )
        db.session.add(need)
        db.session.commit()
        flash("Need posted successfully!", "success")
        return redirect(url_for("index"))

    return render_template("add_request.html")


@app.route("/api/needs")
def api_needs():
    need_type = request.args.get("type", "").strip().lower()
    status = request.args.get("status", "").strip().lower()
    page = max(1, int(request.args.get("page", 1)))
    per_page = int(request.args.get("per_page", 20))
    per_page = min(100, max(5, per_page))

    query = Need.query

    if status:
        status_ids = [
            s.strip().lower()
            for s in status.split(",")
            if s.strip().lower() in ["open", "requested", "closed"]
        ]
        if status_ids:
            query = query.filter(Need.status.in_(status_ids))
    else:
        # Default to showing open and requested if no status specified
        query = query.filter(Need.status.in_(["open", "requested"]))

    if need_type:
        query = query.filter(db.func.lower(Need.need_type) == need_type)

    total = query.count()
    needs = (
        query.order_by(Need.created_at.desc())
        .offset((page - 1) * per_page)
        .limit(per_page)
        .all()
    )

    data = []
    for n in needs:
        creator_username = n.creator.username if n.creator else "Unknown"
        data.append(
            {
                "id": n.id,
                "name": n.name,
                "description": n.description,
                "contact_info": n.contact_info,
                "latitude": n.latitude,
                "longitude": n.longitude,
                "need_type": n.need_type,
                "status": n.status,
                "emergency": int(n.emergency),
                "volunteer": n.volunteer,
                "volunteer_user_id": n.volunteer_user_id,
                "created_by": n.created_by,
                "created_at": n.created_at.isoformat(),
                "creator_username": creator_username,
            }
        )

    return jsonify(
        {
            "total": total,
            "page": page,
            "per_page": per_page,
            "data": data,
        }
    )


@app.route("/volunteer/<int:need_id>", methods=["POST"])
@login_required
def volunteer(need_id):
    user = current_user()
    need = Need.query.get(need_id)
    if not need:
        return jsonify({"success": False, "message": "Need not found."}), 404

    if need.status == "closed":
        return jsonify(
            {"success": False, "message": "Need is closed and cannot be volunteered."}
        ), 409

    volunteer_name = request.form.get("volunteer") or user.username
    volunteer_name = volunteer_name.strip() if volunteer_name else "Anonymous"

    volunteers = [v.strip() for v in (need.volunteer or "").split(",") if v.strip()]
    if volunteer_name in volunteers:
        return jsonify(
            {"success": True, "message": "You are already in the volunteer list."}
        ), 200

    volunteers.append(volunteer_name)
    need.volunteer = ", ".join(volunteers)
    need.status = "requested"
    need.volunteer_user_id = need.volunteer_user_id or user.id
    db.session.commit()

    return jsonify({"success": True, "message": "Thanks for volunteering!"}), 200


@app.route("/edit/<int:need_id>", methods=["GET", "POST"])
@login_required
def edit_need(need_id):
    user = current_user()
    need = Need.query.get(need_id)
    if not need:
        flash("Need not found.", "error")
        return redirect(url_for("index"))

    if need.created_by != user.id and user.role != "admin":
        flash("Permission denied.", "error")
        return redirect(url_for("index"))

    if request.method == "POST":
        name = request.form.get("name", "").strip()
        description = request.form.get("description", "").strip()
        contact_info = request.form.get("contact_info", "").strip()
        latitude = request.form.get("latitude", "").strip()
        longitude = request.form.get("longitude", "").strip()
        need_type = request.form.get("need_type", "other").strip()
        emergency = True if request.form.get("emergency") == "on" else False

        if not all([name, description, contact_info, latitude, longitude]):
            flash("Please fill all required fields.", "error")
            return redirect(url_for("edit_need", need_id=need_id))

        try:
            latitude = float(latitude)
            longitude = float(longitude)
        except ValueError:
            flash("Latitude and longitude must be numeric.", "error")
            return redirect(url_for("edit_need", need_id=need_id))

        need.name = name
        need.description = description
        need.contact_info = contact_info
        need.latitude = latitude
        need.longitude = longitude
        need.need_type = need_type
        need.emergency = emergency
        db.session.commit()
        flash("Need updated successfully!", "success")
        return redirect(url_for("index"))

    return render_template("edit_request.html", need=need)


@app.route("/admin")
@login_required
def admin():
    user = current_user()
    if not user or user.role != "admin":
        flash("Admin access required.", "error")
        return redirect(url_for("index"))

    needs = Need.query.order_by(Need.created_at.desc()).all()
    users = User.query.order_by(User.username.asc()).all()
    fun_events = FunEvent.query.order_by(FunEvent.created_at.desc()).all()
    return render_template(
        "admin.html", needs=needs, users=users, fun_events=fun_events
    )


@app.route("/admin/delete_need/<int:need_id>", methods=["POST"])
@login_required
def admin_delete_need(need_id):
    user = current_user()
    if not user or user.role != "admin":
        flash("Admin access required.", "error")
        return redirect(url_for("index"))

    need = Need.query.get(need_id)
    if need:
        db.session.delete(need)
        db.session.commit()
    flash("Need deleted successfully.", "success")
    return redirect(url_for("admin"))


@app.route("/admin/delete_fun/<int:event_id>", methods=["POST"])
@login_required
def admin_delete_fun(event_id):
    user = current_user()
    if not user or user.role != "admin":
        flash("Admin access required.", "error")
        return redirect(url_for("index"))

    event = FunEvent.query.get(event_id)
    if event:
        db.session.delete(event)
        db.session.commit()
    flash("Fun event deleted successfully.", "success")
    return redirect(url_for("admin"))


@app.route("/admin/edit_fun/<int:event_id>", methods=["GET", "POST"])
@login_required
def admin_edit_fun(event_id):
    user = current_user()
    if not user or user.role != "admin":
        flash("Admin access required.", "error")
        return redirect(url_for("index"))

    event = FunEvent.query.get(event_id)
    if not event:
        flash("Event not found.", "error")
        return redirect(url_for("admin"))

    if request.method == "POST":
        title = request.form.get("title", "").strip()
        description = request.form.get("description", "").strip()
        latitude = request.form.get("latitude", "").strip()
        longitude = request.form.get("longitude", "").strip()
        event_type = request.form.get("event_type", "community").strip()
        event_date = request.form.get("event_date", "").strip()

        if not title or not description or not latitude or not longitude:
            flash("Please fill all required fields.", "error")
            return redirect(url_for("admin_edit_fun", event_id=event_id))

        try:
            event.latitude = float(latitude)
            event.longitude = float(longitude)
        except ValueError:
            flash("Latitude and longitude must be numeric.", "error")
            return redirect(url_for("admin_edit_fun", event_id=event_id))

        event.title = title
        event.description = description
        event.event_type = event_type
        event.event_date = event_date
        db.session.commit()
        flash("Fun event updated successfully.", "success")
        return redirect(url_for("admin"))

    return render_template("edit_fun.html", event=event)


@app.route("/admin/users")
@login_required
def admin_users():
    user = current_user()
    if not user or user.role != "admin":
        flash("Admin access required.", "error")
        return redirect(url_for("index"))

    query = request.args.get("q", "").strip()
    if query:
        users = (
            User.query.filter(User.username.ilike(f"%{query}%"))
            .order_by(User.username)
            .all()
        )
    else:
        users = User.query.order_by(User.username).all()
    return render_template("admin_users.html", users=users, query=query)


@app.route("/admin/user/<int:user_id>", methods=["GET", "POST"])
@login_required
def admin_edit_user(user_id):
    user = current_user()
    if not user or user.role != "admin":
        flash("Admin access required.", "error")
        return redirect(url_for("index"))

    target_user = User.query.get(user_id)
    if not target_user:
        flash("User not found.", "error")
        return redirect(url_for("admin_users"))

    if request.method == "POST":
        username = request.form.get("username", "").strip()
        role = request.form.get("role", "user").strip()

        if not username:
            flash("Username is required.", "error")
            return redirect(url_for("admin_edit_user", user_id=user_id))

        existing = User.query.filter(
            User.username == username, User.id != user_id
        ).first()
        if existing:
            flash("Username is already in use.", "error")
            return redirect(url_for("admin_edit_user", user_id=user_id))

        target_user.username = username
        target_user.role = role

        password = request.form.get("password", "").strip()
        if password:
            target_user.set_password(password)

        db.session.commit()
        flash("User updated successfully.", "success")
        return redirect(url_for("admin_users"))

    return render_template("admin_edit_user.html", user=target_user)


@app.route("/admin/delete_user/<int:user_id>", methods=["POST"])
@login_required
def admin_delete_user(user_id):
    user = current_user()
    if not user or user.role != "admin":
        flash("Admin access required.", "error")
        return redirect(url_for("index"))

    if user_id == user.id:
        flash("You cannot delete your own account while logged in.", "error")
        return redirect(url_for("admin_users"))

    target_user = User.query.get(user_id)
    if target_user:
        # orphan needs are kept as unassigned
        Need.query.filter_by(created_by=user_id).update({"created_by": None})
        # orphan fun events as well
        FunEvent.query.filter_by(created_by=user_id).update({"created_by": None})
        db.session.delete(target_user)
        db.session.commit()
    flash("User deleted successfully.", "success")
    return redirect(url_for("admin_users"))


@app.route("/unvolunteer/<int:need_id>", methods=["POST"])
@login_required
def unvolunteer(need_id):
    user = current_user()
    need = Need.query.get(need_id)
    if not need:
        return jsonify({"success": False, "message": "Need not found."}), 404

    if need.volunteer_user_id != user.id:
        return jsonify({"success": False, "message": "Not your volunteer claim."}), 403

    need.status = "open"
    need.volunteer = None
    need.volunteer_user_id = None
    db.session.commit()
    return jsonify({"success": True, "message": "Unvolunteered successfully."}), 200


@app.route("/my_requests")
@login_required
def my_requests():
    user = current_user()
    needs = (
        Need.query.filter_by(created_by=user.id).order_by(Need.created_at.desc()).all()
    )
    return render_template("my_requests.html", needs=needs)


@app.route("/fun")
@login_required
def fun_map():
    return render_template("fun_map.html")


@app.route("/api/fun")
@login_required
def api_fun():
    events = FunEvent.query.order_by(FunEvent.created_at.desc()).all()
    data = []
    for e in events:
        data.append(
            {
                "id": e.id,
                "title": e.title,
                "description": e.description,
                "latitude": e.latitude,
                "longitude": e.longitude,
                "event_type": e.event_type,
                "event_date": e.event_date,
                "created_by": e.created_by,
                "creator_username": e.creator.username if e.creator else "Unknown",
                "created_at": e.created_at.isoformat(),
            }
        )
    return jsonify({"events": data})


@app.route("/add_fun", methods=["GET", "POST"])
@login_required
def add_fun():
    if request.method == "POST":
        title = request.form.get("title", "").strip()
        description = request.form.get("description", "").strip()
        latitude = request.form.get("latitude", "").strip()
        longitude = request.form.get("longitude", "").strip()
        event_type = request.form.get("event_type", "community").strip()
        event_date = request.form.get("event_date", "").strip()

        if not title or not description or not latitude or not longitude:
            flash("Please fill all required fields.", "error")
            return redirect(url_for("add_fun"))

        try:
            latitude = float(latitude)
            longitude = float(longitude)
        except ValueError:
            flash("Latitude and longitude must be numeric.", "error")
            return redirect(url_for("add_fun"))

        user = current_user()
        event = FunEvent(
            title=title,
            description=description,
            latitude=latitude,
            longitude=longitude,
            event_type=event_type,
            event_date=event_date,
            created_by=user.id if user else None,
        )
        db.session.add(event)
        db.session.commit()
        flash("Fun event posted successfully!", "success")
        return redirect(url_for("fun_map"))

    return render_template("add_fun.html")


@app.route("/profile/<string:username>")
@login_required
def profile(username):
    user = User.query.filter_by(username=username).first()
    if not user:
        flash("User not found.", "error")
        return redirect(url_for("index"))

    posted_needs = (
        Need.query.filter_by(created_by=user.id).order_by(Need.created_at.desc()).all()
    )
    volunteered_needs = (
        Need.query.filter(Need.volunteer.ilike(f"%{user.username}%"))
        .order_by(Need.created_at.desc())
        .all()
    )
    return render_template(
        "profile.html",
        user=user,
        posted_needs=posted_needs,
        volunteered_needs=volunteered_needs,
    )


@app.route("/resolve/<int:need_id>", methods=["POST"])
@login_required
def resolve_own_need(need_id):
    user = current_user()
    need = Need.query.get(need_id)
    if not need:
        flash("Need not found.", "error")
        return redirect(url_for("my_requests"))

    if need.created_by != user.id and user.role != "admin":
        flash("Permission denied.", "error")
        return redirect(url_for("my_requests"))

    if need.status == "closed":
        flash("Request is already marked as resolved.", "info")
        return redirect(url_for("my_requests"))

    need.status = "closed"
    need.volunteer = None
    need.volunteer_user_id = None
    db.session.commit()

    flash("Need marked as resolved.", "success")
    return redirect(url_for("my_requests"))


@app.route("/reopen/<int:need_id>", methods=["POST"])
@login_required
def reopen_need(need_id):
    user = current_user()
    need = Need.query.get(need_id)
    if not need:
        flash("Need not found.", "error")
        return redirect(url_for("my_requests"))

    if need.created_by != user.id and user.role != "admin":
        flash("Permission denied.", "error")
        return redirect(url_for("my_requests"))

    if need.status != "closed":
        flash("Only closed requests can be reopened.", "info")
        return redirect(url_for("my_requests"))

    need.status = "open"
    need.volunteer = None
    need.volunteer_user_id = None
    db.session.commit()

    flash("Need has been re-opened for volunteers.", "success")
    return redirect(url_for("my_requests"))


@app.route("/delete/<int:need_id>", methods=["POST"])
@login_required
def delete_need(need_id):
    user = current_user()
    need = Need.query.get(need_id)
    if not need:
        flash("Need not found.", "error")
        return redirect(url_for("my_requests"))

    if need.created_by != user.id and user.role != "admin":
        flash("Permission denied.", "error")
        return redirect(url_for("my_requests"))

    db.session.delete(need)
    db.session.commit()

    flash("Need deleted successfully.", "success")
    return redirect(url_for("my_requests"))


@app.route("/admin/resolve/<int:need_id>", methods=["POST"])
@login_required
def resolve_need(need_id):
    user = current_user()
    if not user or user.role != "admin":
        flash("Admin access required.", "error")
        return redirect(url_for("index"))

    need = Need.query.get(need_id)
    if need:
        need.status = "closed"
        db.session.commit()
    flash("Need marked as resolved.", "success")
    return redirect(url_for("admin"))


@app.errorhandler(CSRFError)
def handle_csrf_error(e):
    app.logger.warning("CSRF failed: %s", e)
    flash("Security token invalid/expired. Please refresh and retry.", "error")
    return redirect(request.path), 400


@app.errorhandler(500)
def internal_server_error(error):
    app.logger.exception("Internal server error: %s", error)
    flash("Internal server error occurred. Please contact support.", "error")
    return "Internal Server Error", 500


# Register custom Flask CLI commands from commands.py
import cli_commands  # noqa: E402

cli_commands.init_app(app)

if __name__ == "__main__":
    app.run(debug=False, host="0.0.0.0", port=5000)
