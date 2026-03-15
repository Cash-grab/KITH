from flask import Flask, render_template, request, redirect, url_for, jsonify, flash, session
from flask_wtf import CSRFProtect
from werkzeug.security import generate_password_hash, check_password_hash
import sqlite3
import os

BASE_DIR = os.path.abspath(os.path.dirname(__file__))
DB_PATH = os.path.join(BASE_DIR, 'data.db')

app = Flask(__name__)
app.secret_key = 'change-this-secret-for-production'
app.config['WTF_CSRF_ENABLED'] = True
app.config['WTF_CSRF_CHECK_DEFAULT'] = True
csrf = CSRFProtect(app)


def get_db_connection():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn

def current_user():
    user_id = session.get('user_id')
    if not user_id:
        return None
    conn = get_db_connection()
    user = conn.execute('SELECT id, username, role FROM users WHERE id = ?', (user_id,)).fetchone()
    conn.close()
    return user

from functools import wraps

def login_required(view):
    @wraps(view)
    def wrapped_view(*args, **kwargs):
        if not session.get('user_id'):
            if request.is_json or request.args.get('ajax') or request.headers.get('X-Requested-With') == 'XMLHttpRequest':
                return jsonify({'success': False, 'message': 'Login required', 'login_url': url_for('login')}), 401
            flash('Please log in to continue.', 'error')
            return redirect(url_for('login'))
        return view(*args, **kwargs)
    return wrapped_view

def init_db():
    conn = get_db_connection()
    conn.execute('''
        CREATE TABLE IF NOT EXISTS needs (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            description TEXT NOT NULL,
            latitude REAL NOT NULL,
            longitude REAL NOT NULL,
            need_type TEXT NOT NULL,
            status TEXT NOT NULL DEFAULT 'open',
            emergency INTEGER NOT NULL DEFAULT 0,
            volunteer TEXT DEFAULT NULL,
            volunteer_user_id INTEGER DEFAULT NULL,
            created_by INTEGER,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    exists = [r['name'] for r in conn.execute("PRAGMA table_info('needs')").fetchall()]
    if 'created_by' not in exists:
        conn.execute('ALTER TABLE needs ADD COLUMN created_by INTEGER')
    if 'emergency' not in exists:
        conn.execute('ALTER TABLE needs ADD COLUMN emergency INTEGER NOT NULL DEFAULT 0')
    if 'volunteer_user_id' not in exists:
        conn.execute('ALTER TABLE needs ADD COLUMN volunteer_user_id INTEGER DEFAULT NULL')
    if 'contact_info' not in exists:
        conn.execute('ALTER TABLE needs ADD COLUMN contact_info TEXT DEFAULT NULL')
    if 'volunteer' not in exists:
        conn.execute('ALTER TABLE needs ADD COLUMN volunteer TEXT DEFAULT NULL')

    conn.execute('''
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT NOT NULL UNIQUE,
            password_hash TEXT NOT NULL,
            role TEXT NOT NULL DEFAULT 'user',
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')

    conn.execute('''
        CREATE TABLE IF NOT EXISTS fun_events (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            title TEXT NOT NULL,
            description TEXT NOT NULL,
            latitude REAL NOT NULL,
            longitude REAL NOT NULL,
            event_type TEXT NOT NULL DEFAULT 'community',
            event_date TEXT,
            created_by INTEGER,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')

    # create default admin user if none exists
    user_row = conn.execute('SELECT id FROM users WHERE username = ?', ('admin',)).fetchone()
    if not user_row:
        conn.execute('INSERT INTO users (username, password_hash, role) VALUES (?, ?, ?)',
                     ('admin', generate_password_hash('admin123'), 'admin'))
    conn.commit()
    conn.close()

def setup():
    init_db()

setup()

@app.context_processor
def inject_user():
    return {'current_user': current_user()}

@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        username = request.form.get('username', '').strip()
        password = request.form.get('password', '').strip()

        if not username or not password:
            flash('Please provide username and password.', 'error')
            return redirect(url_for('register'))

        conn = get_db_connection()
        if conn.execute('SELECT id FROM users WHERE username = ?', (username,)).fetchone():
            conn.close()
            flash('Username already exists.', 'error')
            return redirect(url_for('register'))

        conn.execute('INSERT INTO users (username, password_hash) VALUES (?, ?)',
                     (username, generate_password_hash(password)))
        conn.commit()
        conn.close()
        flash('Account created. Please log in.', 'success')
        return redirect(url_for('login'))

    return render_template('register.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form.get('username', '').strip()
        password = request.form.get('password', '').strip()

        conn = get_db_connection()
        user = conn.execute('SELECT * FROM users WHERE username = ?', (username,)).fetchone()
        conn.close()

        if user is None or not check_password_hash(user['password_hash'], password):
            flash('Invalid username or password.', 'error')
            return redirect(url_for('login'))

        session.clear()
        session['user_id'] = user['id']
        flash('Logged in successfully.', 'success')
        next_url = request.args.get('next') or url_for('index')
        return redirect(next_url)

    return render_template('login.html')

@app.route('/logout')
def logout():
    session.clear()
    flash('Logged out.', 'success')
    return redirect(url_for('index'))

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/add', methods=['GET', 'POST'])
@login_required
def add_need():
    if request.method == 'POST':
        name = request.form.get('name', '').strip()
        description = request.form.get('description', '').strip()
        contact_info = request.form.get('contact_info', '').strip()
        latitude = request.form.get('latitude', '').strip()
        longitude = request.form.get('longitude', '').strip()
        need_type = request.form.get('need_type', 'other').strip()
        emergency = 1 if request.form.get('emergency') == 'on' else 0

        if not name or not description or not latitude or not longitude or not contact_info:
            flash('Please fill all required fields, including contact info.', 'error')
            return redirect(url_for('add_need'))

        try:
            latitude = float(latitude)
            longitude = float(longitude)
        except ValueError:
            flash('Latitude and longitude must be numeric.', 'error')
            return redirect(url_for('add_need'))

        conn = get_db_connection()
        user = current_user()
        created_by = user['id'] if user else None
        conn.execute(
            'INSERT INTO needs (name, description, contact_info, latitude, longitude, need_type, emergency, created_by) VALUES (?, ?, ?, ?, ?, ?, ?, ?)',
            (name, description, contact_info, latitude, longitude, need_type, emergency, created_by)
        )
        conn.commit()
        conn.close()
        flash('Need posted successfully!', 'success')
        return redirect(url_for('index'))

    return render_template('add_request.html')

@app.route('/api/needs')
def api_needs():
    need_type = request.args.get('type', '').strip().lower()
    status = request.args.get('status', '').strip().lower()
    page = max(1, int(request.args.get('page', 1)))
    per_page = int(request.args.get('per_page', 20))
    per_page = min(100, max(5, per_page))

    allowed_status = {'open', 'requested', 'closed'}
    where = ['status IN ("open", "requested")']
    params = []

    if status:
        status_ids = [s.strip().lower() for s in status.split(',') if s.strip().lower() in allowed_status]
        if status_ids:
            placeholder = ','.join('?' for _ in status_ids)
            where.append(f'status IN ({placeholder})')
            params.extend(status_ids)

    if need_type:
        where.append('LOWER(need_type) = ?')
        params.append(need_type)

    count_query = 'SELECT COUNT(*) FROM needs WHERE ' + ' AND '.join(where)
    conn = get_db_connection()
    total = conn.execute(count_query, params).fetchone()[0]

    data_query = 'SELECT needs.*, users.username as creator_username FROM needs LEFT JOIN users ON needs.created_by = users.id WHERE ' + ' AND '.join(where) + ' ORDER BY created_at DESC LIMIT ? OFFSET ?'
    params_for_data = params + [per_page, (page - 1) * per_page]
    rows = conn.execute(data_query, params_for_data).fetchall()
    conn.close()

    needs = []
    for row in rows:
        row_dict = dict(row)
        row_dict['creator_username'] = row_dict.get('creator_username') or 'Unknown'
        needs.append(row_dict)
    return jsonify({
        'total': total,
        'page': page,
        'per_page': per_page,
        'data': needs,
    })

@app.route('/volunteer/<int:need_id>', methods=['POST'])
@login_required
def volunteer(need_id):
    data = request.get_json(silent=True) or request.form
    volunteer_name = (data.get('volunteer') or current_user()['username'] or 'Anonymous').strip()
    if not volunteer_name:
        volunteer_name = 'Anonymous'

    conn = get_db_connection()
    cur = conn.execute('SELECT status, volunteer, volunteer_user_id FROM needs WHERE id = ?', (need_id,))
    row = cur.fetchone()

    if not row:
        conn.close()
        return jsonify({'success': False, 'message': 'Need not found.'}), 404

    if row['status'] == 'closed':
        conn.close()
        return jsonify({'success': False, 'message': 'Need is closed and cannot be volunteered.'}), 409

    user = current_user()
    volunteers = []
    volunteer_raw = (row['volunteer'] or '').strip()
    if volunteer_raw:
        volunteers = [v.strip() for v in volunteer_raw.split(',') if v.strip()]

    if volunteer_name in volunteers:
        conn.close()
        return jsonify({'success': True, 'message': 'You are already in the volunteer list.'}), 200

    volunteers.append(volunteer_name)
    merged = ', '.join(sorted(set(volunteers), key=lambda x: volunteers.index(x)))
    new_status = 'requested'

    # Always keep admin-created or first volunteer id to keep traceability, but prefer first volunteer id if not set.
    volunteer_user_id = row['volunteer_user_id'] or user['id']

    conn.execute('UPDATE needs SET status = ?, volunteer = ?, volunteer_user_id = ? WHERE id = ?',
                 (new_status, merged, volunteer_user_id, need_id))

    conn.commit()
    conn.close()

    return jsonify({'success': True, 'message': 'Thanks for volunteering!'}), 200

@app.route('/edit/<int:need_id>', methods=['GET', 'POST'])
@login_required
def edit_need(need_id):
    user = current_user()
    conn = get_db_connection()
    need = conn.execute('SELECT * FROM needs WHERE id = ?', (need_id,)).fetchone()

    if not need:
        conn.close()
        flash('Need not found.', 'error')
        return redirect(url_for('index'))

    if need['created_by'] != user['id'] and user['role'] != 'admin':
        conn.close()
        flash('Permission denied.', 'error')
        return redirect(url_for('index'))

    if request.method == 'POST':
        name = request.form.get('name', '').strip()
        description = request.form.get('description', '').strip()
        latitude = request.form.get('latitude', '').strip()
        longitude = request.form.get('longitude', '').strip()
        need_type = request.form.get('need_type', 'other').strip()
        emergency = 1 if request.form.get('emergency') == 'on' else 0

        if not name or not description or not latitude or not longitude:
            flash('Please fill all required fields.', 'error')
            return redirect(url_for('edit_need', need_id=need_id))

        try:
            latitude = float(latitude)
            longitude = float(longitude)
        except ValueError:
            flash('Latitude and longitude must be numeric.', 'error')
            return redirect(url_for('edit_need', need_id=need_id))

        contact_info = request.form.get('contact_info', '').strip()

        if not contact_info:
            flash('Please provide contact information.', 'error')
            return redirect(url_for('edit_need', need_id=need_id))

        conn.execute(
            'UPDATE needs SET name = ?, description = ?, contact_info = ?, latitude = ?, longitude = ?, need_type = ?, emergency = ? WHERE id = ?',
            (name, description, contact_info, latitude, longitude, need_type, emergency, need_id)
        )
        conn.commit()
        conn.close()
        flash('Need updated successfully!', 'success')
        return redirect(url_for('index'))

    conn.close()
    return render_template('edit_request.html', need=need)

@app.route('/admin')
@login_required
def admin():
    user = current_user()
    if not user or user['role'] != 'admin':
        flash('Admin access required.', 'error')
        return redirect(url_for('index'))
    conn = get_db_connection()
    needs = conn.execute('SELECT needs.*, users.username as creator_username FROM needs LEFT JOIN users ON needs.created_by = users.id ORDER BY needs.created_at DESC').fetchall()
    users = conn.execute('SELECT id, username, role, created_at FROM users ORDER BY username ASC').fetchall()
    conn.close()
    return render_template('admin.html', needs=needs, users=users)

@app.route('/admin/delete_need/<int:need_id>', methods=['POST'])
@login_required
def admin_delete_need(need_id):
    user = current_user()
    if not user or user['role'] != 'admin':
        flash('Admin access required.', 'error')
        return redirect(url_for('index'))
    conn = get_db_connection()
    conn.execute('DELETE FROM needs WHERE id = ?', (need_id,))
    conn.commit()
    conn.close()
    flash('Need deleted successfully.', 'success')
    return redirect(url_for('admin'))

@app.route('/admin/users')
@login_required
def admin_users():
    user = current_user()
    if not user or user['role'] != 'admin':
        flash('Admin access required.', 'error')
        return redirect(url_for('index'))
    query = request.args.get('q', '').strip()
    conn = get_db_connection()
    if query:
        users = conn.execute('SELECT id, username, role, created_at FROM users WHERE username LIKE ? ORDER BY username ASC', ('%' + query + '%',)).fetchall()
    else:
        users = conn.execute('SELECT id, username, role, created_at FROM users ORDER BY username ASC').fetchall()
    conn.close()
    return render_template('admin_users.html', users=users, query=query)

@app.route('/admin/user/<int:user_id>', methods=['GET', 'POST'])
@login_required
def admin_edit_user(user_id):
    user = current_user()
    if not user or user['role'] != 'admin':
        flash('Admin access required.', 'error')
        return redirect(url_for('index'))
    conn = get_db_connection()
    target_user = conn.execute('SELECT id, username, role FROM users WHERE id = ?', (user_id,)).fetchone()
    if not target_user:
        conn.close()
        flash('User not found.', 'error')
        return redirect(url_for('admin_users'))

    if request.method == 'POST':
        username = request.form.get('username', '').strip()
        role = request.form.get('role', 'user').strip()
        if not username:
            flash('Username is required.', 'error')
            return redirect(url_for('admin_edit_user', user_id=user_id))
        # prevent duplicate usernames
        existing = conn.execute('SELECT id FROM users WHERE username = ? AND id != ?', (username, user_id)).fetchone()
        if existing:
            conn.close()
            flash('Username is already in use.', 'error')
            return redirect(url_for('admin_edit_user', user_id=user_id))
        conn.execute('UPDATE users SET username = ?, role = ? WHERE id = ?', (username, role, user_id))
        conn.commit()
        conn.close()
        flash('User updated successfully.', 'success')
        return redirect(url_for('admin_users'))

    conn.close()
    return render_template('admin_edit_user.html', target_user=target_user)

@app.route('/admin/delete_user/<int:user_id>', methods=['POST'])
@login_required
def admin_delete_user(user_id):
    user = current_user()
    if not user or user['role'] != 'admin':
        flash('Admin access required.', 'error')
        return redirect(url_for('index'))
    if user_id == user['id']:
        flash('You cannot delete your own account while logged in.', 'error')
        return redirect(url_for('admin_users'))
    conn = get_db_connection()
    conn.execute('DELETE FROM users WHERE id = ?', (user_id,))
    conn.execute('UPDATE needs SET created_by = NULL WHERE created_by = ?', (user_id,))
    conn.commit()
    conn.close()
    flash('User deleted successfully.', 'success')
    return redirect(url_for('admin_users'))

@app.route('/unvolunteer/<int:need_id>', methods=['POST'])
@login_required
def unvolunteer(need_id):
    user = current_user()
    conn = get_db_connection()
    need = conn.execute('SELECT volunteer_user_id, status FROM needs WHERE id = ?', (need_id,)).fetchone()
    if not need:
        conn.close()
        return jsonify({'success': False, 'message': 'Need not found.'}), 404
    if need['volunteer_user_id'] != user['id']:
        conn.close()
        return jsonify({'success': False, 'message': 'Not your volunteer claim.'}), 403
    conn.execute('UPDATE needs SET status = ?, volunteer = NULL, volunteer_user_id = NULL WHERE id = ?', ('open', need_id))
    conn.commit()
    conn.close()
    return jsonify({'success': True, 'message': 'Unvolunteered successfully.'}), 200
@app.route('/my_requests')
@login_required
def my_requests():
    user = current_user()
    conn = get_db_connection()
    needs = conn.execute('SELECT * FROM needs WHERE created_by = ? ORDER BY created_at DESC', (user['id'],)).fetchall()
    conn.close()
    return render_template('my_requests.html', needs=needs)

@app.route('/fun')
@login_required
def fun_map():
    return render_template('fun_map.html')

@app.route('/api/fun')
@login_required
def api_fun():
    conn = get_db_connection()
    rows = conn.execute('SELECT fun_events.*, users.username as creator_username FROM fun_events LEFT JOIN users ON fun_events.created_by = users.id ORDER BY created_at DESC').fetchall()
    conn.close()
    events = [dict(row) for row in rows]
    return jsonify({'events': events})

@app.route('/add_fun', methods=['GET', 'POST'])
@login_required
def add_fun():
    if request.method == 'POST':
        title = request.form.get('title', '').strip()
        description = request.form.get('description', '').strip()
        latitude = request.form.get('latitude', '').strip()
        longitude = request.form.get('longitude', '').strip()
        event_type = request.form.get('event_type', 'community').strip()
        event_date = request.form.get('event_date', '').strip()

        if not title or not description or not latitude or not longitude:
            flash('Please fill all required fields.', 'error')
            return redirect(url_for('add_fun'))

        try:
            latitude = float(latitude)
            longitude = float(longitude)
        except ValueError:
            flash('Latitude and longitude must be numeric.', 'error')
            return redirect(url_for('add_fun'))

        user = current_user()
        conn = get_db_connection()
        conn.execute('INSERT INTO fun_events (title, description, latitude, longitude, event_type, event_date, created_by) VALUES (?, ?, ?, ?, ?, ?, ?)',
                     (title, description, latitude, longitude, event_type, event_date, user['id']))
        conn.commit()
        conn.close()
        flash('Fun event posted successfully!', 'success')
        return redirect(url_for('fun_map'))

    return render_template('add_fun.html')

@app.route('/profile/<string:username>')
@login_required
def profile(username):
    conn = get_db_connection()
    user = conn.execute('SELECT id, username, role, created_at FROM users WHERE username = ?', (username,)).fetchone()
    if not user:
        conn.close()
        flash('User not found.', 'error')
        return redirect(url_for('index'))

    posted_needs = conn.execute('SELECT * FROM needs WHERE created_by = ? ORDER BY created_at DESC', (user['id'],)).fetchall()
    volunteered_needs = conn.execute('SELECT * FROM needs WHERE volunteer LIKE ? ORDER BY created_at DESC', (f'%{user["username"]}%',)).fetchall()
    conn.close()
    return render_template('profile.html', user=user, posted_needs=posted_needs, volunteered_needs=volunteered_needs)
@app.route('/resolve/<int:need_id>', methods=['POST'])
@login_required
def resolve_own_need(need_id):
    user = current_user()
    conn = get_db_connection()
    need = conn.execute('SELECT created_by, status FROM needs WHERE id = ?', (need_id,)).fetchone()
    if not need:
        conn.close()
        flash('Need not found.', 'error')
        return redirect(url_for('my_requests'))

    if need['created_by'] != user['id'] and user['role'] != 'admin':
        conn.close()
        flash('Permission denied.', 'error')
        return redirect(url_for('my_requests'))

    if need['status'] == 'closed':
        conn.close()
        flash('Request is already marked as resolved.', 'info')
        return redirect(url_for('my_requests'))

    conn.execute('UPDATE needs SET status = ?, volunteer = NULL, volunteer_user_id = NULL WHERE id = ?', ('closed', need_id))
    conn.commit()
    conn.close()
    flash('Need marked as resolved.', 'success')
    return redirect(url_for('my_requests'))


@app.route('/reopen/<int:need_id>', methods=['POST'])
@login_required
def reopen_need(need_id):
    user = current_user()
    conn = get_db_connection()
    need = conn.execute('SELECT created_by, status FROM needs WHERE id = ?', (need_id,)).fetchone()
    if not need:
        conn.close()
        flash('Need not found.', 'error')
        return redirect(url_for('my_requests'))

    if need['created_by'] != user['id'] and user['role'] != 'admin':
        conn.close()
        flash('Permission denied.', 'error')
        return redirect(url_for('my_requests'))

    if need['status'] != 'closed':
        conn.close()
        flash('Only closed requests can be reopened.', 'info')
        return redirect(url_for('my_requests'))

    conn.execute('UPDATE needs SET status = ?, volunteer = NULL, volunteer_user_id = NULL WHERE id = ?', ('open', need_id))
    conn.commit()
    conn.close()
    flash('Need has been re-opened for volunteers.', 'success')
    return redirect(url_for('my_requests'))


@app.route('/delete/<int:need_id>', methods=['POST'])
@login_required
def delete_need(need_id):
    user = current_user()
    conn = get_db_connection()
    need = conn.execute('SELECT created_by FROM needs WHERE id = ?', (need_id,)).fetchone()
    if not need:
        conn.close()
        flash('Need not found.', 'error')
        return redirect(url_for('my_requests'))

    if need['created_by'] != user['id'] and user['role'] != 'admin':
        conn.close()
        flash('Permission denied.', 'error')
        return redirect(url_for('my_requests'))

    conn.execute('DELETE FROM needs WHERE id = ?', (need_id,))
    conn.commit()
    conn.close()
    flash('Need deleted successfully.', 'success')
    return redirect(url_for('my_requests'))


@app.route('/admin/resolve/<int:need_id>', methods=['POST'])
@login_required
def resolve_need(need_id):
    user = current_user()
    if not user or user['role'] != 'admin':
        flash('Admin access required.', 'error')
        return redirect(url_for('index'))

    conn = get_db_connection()
    conn.execute('UPDATE needs SET status = ? WHERE id = ?', ('closed', need_id))
    conn.commit()
    conn.close()
    flash('Need marked as resolved.', 'success')
    return redirect(url_for('admin'))

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5000)
