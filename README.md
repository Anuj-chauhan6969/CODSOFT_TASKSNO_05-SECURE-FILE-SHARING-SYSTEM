# 🔐 Secure File-Sharing Application

A secure web-based file-sharing application built with **Python and Flask** that allows authenticated users to upload, store, share, and download files securely.

The application encrypts files before storing them on the server and uses **role-based access control (RBAC)** to restrict unauthorized file access. It also supports **temporary download links with expiration times** for secure file sharing.

---

## 🚀 Features

### 🔑 User Authentication

* User registration and login
* Secure password hashing using **bcrypt**
* Session-based authentication
* Logout functionality
* Prevents unauthenticated users from accessing protected resources

### 📁 Secure File Upload

* Authenticated users can upload files
* Uploaded files are encrypted before storage
* Original filenames are safely sanitized
* Random UUID filenames are used for stored files
* Encrypted files use the `.enc` extension

### 🔒 File Encryption

Files are encrypted using the **Fernet symmetric encryption** mechanism provided by the Python `cryptography` library.

```text
Original File
     ↓
Fernet Encryption
     ↓
Encrypted File
     ↓
Server Storage
```

The server never stores the uploaded file in its original plaintext form.

### 👥 Role-Based Access Control

The application supports different user roles:

| Role  | Permissions                                                         |
| ----- | ------------------------------------------------------------------- |
| User  | Upload and download own files                                       |
| Admin | Access files belonging to users and manage administrative functions |

Users cannot download files belonging to another user unless they have the required privileges.

### 🔗 Temporary Download Links

Users can generate temporary download links for their files.

Example:

```text
/shared/<secure-token>
```

The generated link:

* Uses a cryptographically secure random token
* Has an expiration time
* Cannot be used after expiration
* Does not expose the physical storage filename

Default expiration:

```text
10 minutes
```

### 📋 Audit Logging

Important file operations are recorded in the database.

Examples:

```text
UPLOAD
DOWNLOAD
```

Audit records contain:

* User ID
* Action
* File ID
* Timestamp

---

## 🛡️ Security Features

This project demonstrates several important secure-development practices:

* 🔐 bcrypt password hashing
* 🔒 Fernet file encryption
* 👥 Role-Based Access Control
* 🎲 Cryptographically secure temporary tokens
* ⏱️ Expiring download links
* 🧹 Secure filename sanitization
* 🆔 UUID-based stored filenames
* 🚫 Unauthorized file-access prevention
* 🗃️ Parameterized SQL queries
* 📋 Audit logging
* 🔑 Encryption key separation from source code

---

## 🏗️ Project Architecture

```text
User
 │
 ▼
Authentication
 │
 ▼
Flask Application
 │
 ├───────────────┐
 │               │
 ▼               ▼
RBAC          File Upload
 │               │
 │               ▼
 │         Fernet Encryption
 │               │
 │               ▼
 │       Encrypted Storage
 │
 ▼
File Authorization
 │
 ├── Owner
 │
 └── Admin
 │
 ▼
Decryption
 │
 ▼
Secure Download
```

---

## 📂 Project Structure

```text
secure-file-sharing/
│
├── app.py
├── database.py
├── encryption.py
├── requirements.txt
├── .env
├── .gitignore
├── secret.key
│
├── secure_files.db
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

> ⚠️ `secret.key`, `.env`, `secure_files.db`, and uploaded encrypted files should **not** be committed to GitHub.

---

## 🧰 Technologies Used

### Backend

* Python
* Flask
* SQLite

### Security

* Flask-Bcrypt
* Cryptography / Fernet
* Secure random tokens
* Role-Based Access Control

### Frontend

* HTML5
* CSS3
* Jinja2 Templates

---

## ⚙️ Installation

### 1. Clone the repository

```bash
git clone https://github.com/YOUR-USERNAME/secure-file-sharing.git
```

### 2. Open the project

```bash
cd secure-file-sharing
```

### 3. Create a virtual environment

Windows:

```bash
python -m venv venv
```

Activate it:

```bash
venv\Scripts\activate
```

Linux/macOS:

```bash
python3 -m venv venv
source venv/bin/activate
```

### 4. Install dependencies

```bash
pip install -r requirements.txt
```

### 5. Generate the encryption key

Run the application once, or generate a key using:

```python
from cryptography.fernet import Fernet

key = Fernet.generate_key()

with open("secret.key", "wb") as f:
    f.write(key)
```

Keep `secret.key` secure.

### 6. Run the application

```bash
python app.py
```

The application will be available at:

```text
http://127.0.0.1:5000
```

---

## 👤 User Workflow

### Registration

```text
Register
   ↓
Username + Password
   ↓
bcrypt Password Hash
   ↓
SQLite Database
```

### Upload

```text
Select File
    ↓
Validate Filename
    ↓
Read File
    ↓
Encrypt File
    ↓
Generate UUID
    ↓
Store Encrypted File
    ↓
Save Metadata
```

### Download

```text
Request Download
       ↓
Authentication Check
       ↓
Authorization / RBAC
       ↓
Read Encrypted File
       ↓
Decrypt in Memory
       ↓
Download Original File
```

---

## 🔗 Temporary File Sharing

A file owner can generate a temporary download link.

Example:

```text
http://127.0.0.1:5000/shared/AbCdEf123456...
```

The server verifies:

```text
Token exists?
     │
     ├── No → 404
     │
     ▼
Token expired?
     │
     ├── Yes → Access Denied
     │
     ▼
Decrypt File
     │
     ▼
Download
```

---

## 🗄️ Database Design

### Users

```text
users
├── id
├── username
├── password
└── role
```

### Files

```text
files
├── id
├── original_name
├── stored_name
├── owner_id
└── uploaded_at
```

### Share Links

```text
share_links
├── id
├── file_id
├── token
├── expires_at
└── created_by
```

### Audit Logs

```text
audit_logs
├── id
├── user_id
├── action
├── file_id
└── timestamp
```

---

## 🧪 Security Testing

The application can be tested against common security scenarios.

### Test 1 — Unauthorized Download

Attempt to access another user's file.

Expected result:

```text
403 Forbidden
```

### Test 2 — Expired Link

Access a temporary link after its expiration time.

Expected result:

```text
This download link has expired.
```

### Test 3 — Invalid Token

Use a random token.

Expected result:

```text
404 Not Found
```

### Test 4 — Password Security

Passwords should never be stored as plaintext.

Database should contain a bcrypt hash similar to:

```text
$2b$12$................................
```

### Test 5 — Stored File

Inspect the encrypted storage directory.

The stored file should not be readable as the original uploaded document/image.

---

## 📊 Security Model

```text
                    SECURE FILE SHARING
                           │
          ┌────────────────┼────────────────┐
          │                │                │
          ▼                ▼                ▼
    Authentication      Encryption        RBAC
          │                │                │
        bcrypt          Fernet         Access Control
          │                │                │
          └────────────────┼────────────────┘
                           │
                           ▼
                    Secure Storage
                           │
                           ▼
                  Temporary Sharing
                           │
                           ▼
                    Audit Logging
```

---

## 🔮 Future Enhancements

The following features can be added to make the project more advanced:

* [ ] CSRF protection
* [ ] HTTPS deployment
* [ ] File-size restrictions
* [ ] MIME-type validation
* [ ] Virus/malware scanning
* [ ] File integrity verification using SHA-256
* [ ] Multiple encryption keys
* [ ] Key rotation
* [ ] Password reset
* [ ] Email verification
* [ ] Two-factor authentication (2FA)
* [ ] Admin user-management dashboard
* [ ] File deletion and recovery
* [ ] Share-link revocation
* [ ] Download limits
* [ ] Advanced audit dashboard
* [ ] Rate limiting
* [ ] Secure HTTP headers
* [ ] Docker deployment
* [ ] Cloud storage integration

---

## 🎯 Learning Objectives

This project demonstrates practical knowledge of:

* Python web development
* Flask
* Authentication
* Authorization
* Password security
* File encryption
* Secure file handling
* RBAC
* Secure token generation
* Temporary access control
* SQLite database management
* Security logging
* Secure coding practices

---

## ⚠️ Security Disclaimer

This project is developed for **educational and cybersecurity learning purposes**.

For production deployment, additional security controls should be implemented, including HTTPS/TLS, CSRF protection, strict upload validation, rate limiting, secure cookie configuration, key management, malware scanning, and hardened server configuration.

---

## 👨‍💻 Author

**Anuj Chauhan**

Cybersecurity / Python Project

---

## ⭐ Project Highlights

```text
🔐 Secure Authentication
🔒 File Encryption
👥 Role-Based Access Control
📁 Secure File Storage
🔗 Temporary Download Links
⏱️ Expiration-Based Access
📋 Audit Logging
🛡️ Secure Coding Practices
```

If you found this project useful, consider giving the repository a ⭐.
