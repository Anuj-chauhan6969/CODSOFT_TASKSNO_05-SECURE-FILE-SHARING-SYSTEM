from flask import (
    Flask,
    request,
    redirect,
    url_for,
    session,
    render_template,
    send_file,
    abort
)

from flask_bcrypt import Bcrypt
from werkzeug.utils import secure_filename

from database import get_db, init_db
from encryption import encrypt_file, decrypt_file

import os
import uuid
import secrets
from datetime import datetime, timedelta
from io import BytesIO


app = Flask(__name__)

app.secret_key = os.environ.get(
    "FLASK_SECRET_KEY",
    "CHANGE_THIS_SECRET_KEY"
)

bcrypt = Bcrypt(app)

UPLOAD_FOLDER = "storage/encrypted"

os.makedirs(UPLOAD_FOLDER, exist_ok=True)

init_db()


# --------------------------------------------------
# LOGIN REQUIRED
# --------------------------------------------------

def login_required():

    if "user_id" not in session:
        return False

    return True


# --------------------------------------------------
# AUDIT LOG
# --------------------------------------------------

def log_action(user_id, action, file_id=None):

    conn = get_db()

    conn.execute(
        """
        INSERT INTO audit_logs
        (user_id, action, file_id)
        VALUES (?, ?, ?)
        """,
        (user_id, action, file_id)
    )

    conn.commit()
    conn.close()


# --------------------------------------------------
# HOME
# --------------------------------------------------

@app.route("/")
def index():

    if "user_id" in session:
        return redirect(url_for("dashboard"))

    return redirect(url_for("login"))


# --------------------------------------------------
# REGISTER
# --------------------------------------------------

@app.route("/register", methods=["GET", "POST"])
def register():

    if request.method == "POST":

        username = request.form["username"].strip()
        password = request.form["password"]

        if len(password) < 8:
            return "Password must contain at least 8 characters."

        hashed_password = bcrypt.generate_password_hash(
            password
        ).decode("utf-8")

        conn = get_db()

        try:

            conn.execute(
                """
                INSERT INTO users
                (username, password, role)
                VALUES (?, ?, ?)
                """,
                (username, hashed_password, "user")
            )

            conn.commit()

        except Exception:

            conn.close()

            return "Username already exists."

        conn.close()

        return redirect(url_for("login"))

    return render_template("register.html")


# --------------------------------------------------
# LOGIN
# --------------------------------------------------

@app.route("/login", methods=["GET", "POST"])
def login():

    if request.method == "POST":

        username = request.form["username"]
        password = request.form["password"]

        conn = get_db()

        user = conn.execute(
            """
            SELECT *
            FROM users
            WHERE username = ?
            """,
            (username,)
        ).fetchone()

        conn.close()

        if user and bcrypt.check_password_hash(
            user["password"],
            password
        ):

            session.clear()

            session["user_id"] = user["id"]
            session["username"] = user["username"]
            session["role"] = user["role"]

            return redirect(url_for("dashboard"))

        return "Invalid username or password."

    return render_template("login.html")


# --------------------------------------------------
# LOGOUT
# --------------------------------------------------

@app.route("/logout")
def logout():

    session.clear()

    return redirect(url_for("login"))


# --------------------------------------------------
# DASHBOARD
# --------------------------------------------------

@app.route("/dashboard")
def dashboard():

    if not login_required():
        return redirect(url_for("login"))

    conn = get_db()

    if session["role"] == "admin":

        files = conn.execute(
            """
            SELECT files.*, users.username
            FROM files
            JOIN users ON files.owner_id = users.id
            ORDER BY uploaded_at DESC
            """
        ).fetchall()

    else:

        files = conn.execute(
            """
            SELECT *
            FROM files
            WHERE owner_id = ?
            ORDER BY uploaded_at DESC
            """,
            (session["user_id"],)
        ).fetchall()

    conn.close()

    return render_template(
        "dashboard.html",
        files=files
    )


# --------------------------------------------------
# UPLOAD
# --------------------------------------------------

@app.route("/upload", methods=["GET", "POST"])
def upload():

    if not login_required():
        return redirect(url_for("login"))

    if request.method == "POST":

        uploaded_file = request.files.get("file")

        if not uploaded_file:
            return "No file selected."

        if uploaded_file.filename == "":
            return "Invalid filename."

        original_name = secure_filename(
            uploaded_file.filename
        )

        if not original_name:
            return "Invalid filename."

        file_data = uploaded_file.read()

        # Encrypt before storing
        encrypted_data = encrypt_file(file_data)

        stored_name = f"{uuid.uuid4().hex}.enc"

        storage_path = os.path.join(
            UPLOAD_FOLDER,
            stored_name
        )

        with open(storage_path, "wb") as f:
            f.write(encrypted_data)

        conn = get_db()

        conn.execute(
            """
            INSERT INTO files
            (original_name, stored_name, owner_id)
            VALUES (?, ?, ?)
            """,
            (
                original_name,
                stored_name,
                session["user_id"]
            )
        )

        conn.commit()

        file_id = conn.execute(
            "SELECT last_insert_rowid()"
        ).fetchone()[0]

        conn.close()

        log_action(
            session["user_id"],
            "UPLOAD",
            file_id
        )

        return redirect(url_for("dashboard"))

    return render_template("upload.html")


# --------------------------------------------------
# DOWNLOAD
# --------------------------------------------------

@app.route("/download/<int:file_id>")
def download(file_id):

    if not login_required():
        return redirect(url_for("login"))

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

    # RBAC
    if (
        session["role"] != "admin"
        and file["owner_id"] != session["user_id"]
    ):
        abort(403)

    path = os.path.join(
        UPLOAD_FOLDER,
        file["stored_name"]
    )

    if not os.path.exists(path):
        abort(404)

    with open(path, "rb") as f:
        encrypted_data = f.read()

    decrypted_data = decrypt_file(
        encrypted_data
    )

    log_action(
        session["user_id"],
        "DOWNLOAD",
        file_id
    )

    return send_file(
        BytesIO(decrypted_data),
        as_attachment=True,
        download_name=file["original_name"]
    )


# --------------------------------------------------
# GENERATE TEMPORARY LINK
# --------------------------------------------------

@app.route(
    "/share/<int:file_id>",
    methods=["POST"]
)
def create_share_link(file_id):

    if not login_required():
        return redirect(url_for("login"))

    conn = get_db()

    file = conn.execute(
        """
        SELECT *
        FROM files
        WHERE id = ?
        """,
        (file_id,)
    ).fetchone()

    if not file:
        conn.close()
        abort(404)

    # Owner or admin only
    if (
        session["role"] != "admin"
        and file["owner_id"] != session["user_id"]
    ):
        conn.close()
        abort(403)

    token = secrets.token_urlsafe(32)

    expires_at = datetime.utcnow() + timedelta(
        minutes=10
    )

    conn.execute(
        """
        INSERT INTO share_links
        (file_id, token, expires_at, created_by)
        VALUES (?, ?, ?, ?)
        """,
        (
            file_id,
            token,
            expires_at,
            session["user_id"]
        )
    )

    conn.commit()
    conn.close()

    return {
        "message": "Temporary link created",
        "download_url": url_for(
            "temporary_download",
            token=token,
            _external=True
        ),
        "expires_at": expires_at.isoformat()
    }


# --------------------------------------------------
# TEMPORARY DOWNLOAD
# --------------------------------------------------

@app.route("/shared/<token>")
def temporary_download(token):

    conn = get_db()

    share = conn.execute(
        """
        SELECT
            share_links.*,
            files.original_name,
            files.stored_name
        FROM share_links
        JOIN files
        ON share_links.file_id = files.id
        WHERE share_links.token = ?
        """,
        (token,)
    ).fetchone()

    if not share:

        conn.close()

        abort(404)

    expires_at = datetime.fromisoformat(
        share["expires_at"]
    )

    if datetime.utcnow() > expires_at:

        conn.close()

        return "This download link has expired."

    path = os.path.join(
        UPLOAD_FOLDER,
        share["stored_name"]
    )

    if not os.path.exists(path):

        conn.close()

        abort(404)

    with open(path, "rb") as f:
        encrypted_data = f.read()

    decrypted_data = decrypt_file(
        encrypted_data
    )

    conn.close()

    return send_file(
        BytesIO(decrypted_data),
        as_attachment=True,
        download_name=share["original_name"]
    )


# --------------------------------------------------
# ADMIN USERS
# --------------------------------------------------

@app.route("/admin/users")
def admin_users():

    if not login_required():
        return redirect(url_for("login"))

    if session["role"] != "admin":
        abort(403)

    conn = get_db()

    users = conn.execute(
        "SELECT id, username, role FROM users"
    ).fetchall()

    conn.close()

    return {
        "users": [
            dict(user)
            for user in users
        ]
    }


# --------------------------------------------------
# RUN
# --------------------------------------------------

if __name__ == "__main__":

    app.run(
        debug=True
    )
