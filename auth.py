```python
from functools import wraps

from flask import session, redirect, url_for, abort


def login_required(view_function):
    """
    Allow access only to authenticated users.
    """

    @wraps(view_function)
    def wrapped_view(*args, **kwargs):

        if "user_id" not in session:
            return redirect(url_for("login"))

        return view_function(*args, **kwargs)

    return wrapped_view


def role_required(required_role):
    """
    Allow access only to users with the specified role.

    Example:
        @role_required("admin")
    """

    def decorator(view_function):

        @wraps(view_function)
        def wrapped_view(*args, **kwargs):

            if "user_id" not in session:
                return redirect(url_for("login"))

            if session.get("role") != required_role:
                abort(403)

            return view_function(*args, **kwargs)

        return wrapped_view

    return decorator


def owner_or_admin(file_owner_id):
    """
    Check whether the current user owns the file
    or is an administrator.
    """

    if "user_id" not in session:
        return False

    user_id = session.get("user_id")
    role = session.get("role")

    if role == "admin":
        return True

    return user_id == file_owner_id
```

### Use it in `app.py`

Import it:

```python
from auth import login_required, role_required, owner_or_admin
```

Then instead of manually checking every route:

```python
@app.route("/dashboard")
@login_required
def dashboard():

    # dashboard code here

    return render_template(
        "dashboard.html",
        files=files
    )
```

For an admin-only route:

```python
@app.route("/admin/users")
@role_required("admin")
def admin_users():

    conn = get_db()

    users = conn.execute(
        "SELECT id, username, role FROM users"
    ).fetchall()

    conn.close()

    return {
        "users": [dict(user) for user in users]
    }
```

For file access:

```python
@app.route("/download/<int:file_id>")
@login_required
def download(file_id):

    conn = get_db()

    file = conn.execute(
        """
        SELECT *
        FROM files
        WHERE id = ?
        """,
        (file_id,)
    ).fetchone()

    conn.close()

    if not file:
        abort(404)

    if not owner_or_admin(file["owner_id"]):
        abort(403)

    # Continue with secure file decryption/download...
```

### Updated structure

```text
secure_file_sharing/
│
├── app.py
├── auth.py              ← Authentication & authorization
├── database.py          ← SQLite database
├── encryption.py        ← File encryption/decryption
├── requirements.txt
├── .env
├── .gitignore
│
├── storage/
│   └── encrypted/
│
├── templates/
│   ├── login.html
│   ├── register.html
│   ├── dashboard.html
│   └── upload.html
│
└── static/
    └── style.css
```

This separation makes the project cleaner and demonstrates **modular secure coding**, which is useful for a cybersecurity portfolio.
