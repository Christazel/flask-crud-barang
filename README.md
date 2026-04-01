# flask-crud-barang

A simple CRUD web app built with Flask for inventory management.

## Features

- Login authentication
- CRUD data barang
- Bootstrap-based UI
- MySQL as primary database
- Automatic SQLite fallback if MySQL is unavailable

## Tech Stack

- Python 3.10+
- Flask
- Flask-Login
- PyMySQL
- Bootstrap + jQuery

## Project Setup

1. Clone repository:

```bash
git clone https://github.com/Christazel/flask-crud-barang.git
cd flask-crud-barang
```

2. Create and activate virtual environment:

```bash
python -m venv .venv
```

Windows PowerShell:

```powershell
.\.venv\Scripts\Activate.ps1
```

3. Install dependencies:

```bash
pip install -r requirements.txt
```

4. Copy environment config:

```bash
copy .env.example .env
```

## Database Setup (XAMPP)

1. Start MySQL from XAMPP Control Panel.
2. Create database named flask_barang.
3. Import SQL file from database/flask_barang.sql using phpMyAdmin.

Default local values are already listed in .env.example:

- MYSQL_HOST=localhost
- MYSQL_USER=root
- MYSQL_PASSWORD=
- MYSQL_DB=flask_barang

## Run App

```bash
python app.py
```

Open:

http://127.0.0.1:5000

## Default Login

- Username: user1
- Password: 123

## Notes

- If MySQL is off or unavailable, the app will fallback to SQLite in instance/flask_barang.db.
- File .env is ignored by Git and should not be committed.

## Git Workflow Suggestion

Use these branches:

- main: stable code
- development: active integration branch
- feature/*: per-feature work

Example flow:

1. Create feature branch from development.
2. Commit work to feature branch.
3. Merge feature branch into development.
4. Merge development into main when ready for release.
