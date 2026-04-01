from flask import Flask, render_template, request, redirect, url_for, flash
import pymysql
import sqlite3
import os
from flask_login import LoginManager, UserMixin, login_user, login_required, logout_user, current_user
from werkzeug.security import check_password_hash, generate_password_hash

app = Flask(__name__)

app.config['SECRET_KEY'] = os.getenv('SECRET_KEY', 'dev-secret-key')

app.config['MYSQL_HOST'] = os.getenv('MYSQL_HOST', 'localhost')
app.config['MYSQL_USER'] = os.getenv('MYSQL_USER', 'root')
app.config['MYSQL_PASSWORD'] = os.getenv('MYSQL_PASSWORD', '')
app.config['MYSQL_DB'] = os.getenv('MYSQL_DB', 'flask_barang')

db_type = 'mysql'
db_connection = None


def init_sqlite_db(connection):
    sqlite_cursor = connection.cursor()
    sqlite_cursor.execute(
        """
        CREATE TABLE IF NOT EXISTS users (
            id_user INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT UNIQUE NOT NULL,
            password TEXT NOT NULL,
            nama TEXT NOT NULL
        )
        """
    )
    sqlite_cursor.execute(
        """
        CREATE TABLE IF NOT EXISTS barangs (
            id_barang INTEGER PRIMARY KEY AUTOINCREMENT,
            nama_barang TEXT NOT NULL,
            merk_barang TEXT NOT NULL,
            stok_barang INTEGER NOT NULL
        )
        """
    )
    sqlite_cursor.execute(
        "INSERT OR IGNORE INTO users(username, password, nama) VALUES(?, ?, ?)",
        ('admin', generate_password_hash('admin'), 'Administrator')
    )
    connection.commit()


try:
    db_connection = pymysql.connect(
        host=app.config['MYSQL_HOST'],
        user=app.config['MYSQL_USER'],
        password=app.config['MYSQL_PASSWORD'],
        database=app.config['MYSQL_DB']
    )
except Exception:
    db_type = 'sqlite'
    os.makedirs('instance', exist_ok=True)
    db_connection = sqlite3.connect('instance/flask_barang.db', check_same_thread=False)
    init_sqlite_db(db_connection)


def db_execute(sql, params=(), fetch='none'):
    if db_type == 'sqlite':
        sql = sql.replace('%s', '?')
    cursor = db_connection.cursor()
    cursor.execute(sql, params)
    if fetch == 'one':
        result = cursor.fetchone()
        cursor.close()
        return result
    if fetch == 'all':
        result = cursor.fetchall()
        cursor.close()
        return result
    cursor.close()
    return None


def db_commit():
    db_connection.commit()


def is_password_hashed(password_value):
    return password_value.startswith('pbkdf2:') or password_value.startswith('scrypt:')


def verify_password(stored_password, provided_password):
    if is_password_hashed(stored_password):
        return check_password_hash(stored_password, provided_password)
    return stored_password == provided_password

app.secret_key = app.config['SECRET_KEY']

login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'login'

class User(UserMixin):
    def __init__(self, id_user, username, password, nama):
        self.id_user = id_user
        self.username = username
        self.password = password
        self.nama = nama
    def get_id(self):
        return self.username


def parse_stok(raw_value):
    try:
        stok = int(raw_value)
        if stok < 0:
            return None
        return stok
    except (TypeError, ValueError):
        return None

@login_manager.user_loader
def load_user(username):
    user_data = db_execute('SELECT * FROM users WHERE username=%s', (username,), fetch='one')
    if user_data:
        return User(user_data[0], user_data[1], user_data[2], user_data[3])
    return None

@app.route('/login', methods=['GET', 'POST'])
def login():
    if current_user.is_authenticated:
        return redirect(url_for('dashboard'))

    if request.method == 'POST':
        username = (request.form.get('username') or '').strip()
        password = request.form.get('password') or ''
        if not username or not password:
            flash('Username dan password wajib diisi.', 'danger')
            return render_template('login.html')

        user_data = db_execute('SELECT * FROM users WHERE username=%s', (username,), fetch='one')
        if user_data and verify_password(user_data[2], password):
            if not is_password_hashed(user_data[2]):
                # Upgrade legacy plaintext passwords transparently after successful login.
                new_hash = generate_password_hash(password)
                db_execute('UPDATE users SET password=%s WHERE id_user=%s', (new_hash, user_data[0]))
                db_commit()
            user = User(user_data[0], user_data[1], user_data[2], user_data[3])

            login_user(user)
            flash('Login successful!', 'success')
            return redirect(url_for('dashboard'))
        else:
            flash('Login failed. Check your username and password.', 'danger')

    return render_template('login.html')

@app.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect(url_for('login'))

@app.route('/')
@login_required
def dashboard():
    datas = []
    try:
        sql = "SELECT * FROM barangs"
        datas = db_execute(sql, fetch='all')
    except Exception as e:
        print(e)
        flash('Gagal mengambil data barang.', 'danger')
    return render_template('index.html', datas=datas)

@app.route('/tambah_barang', methods=['GET', 'POST'])
@login_required
def tambah_barang():
    if request.method == 'POST':
        try:
            nama_barang = (request.form.get('nama_barang') or '').strip()
            merk_barang = (request.form.get('merk_barang') or '').strip()
            stok_barang = parse_stok(request.form.get('stok_barang'))

            if not nama_barang or not merk_barang or stok_barang is None:
                flash('Data barang tidak valid. Periksa kembali input kamu.', 'danger')
                return render_template('tambah_barang.html')

            sql = "INSERT into barangs(nama_barang, merk_barang, stok_barang) VALUES(%s, %s, %s)"
            db_execute(sql, (nama_barang, merk_barang, stok_barang))
            db_commit()
            flash('Add barang successful!', 'success')
            return redirect(url_for('dashboard'))
        except Exception as e:
            print(e)
            flash('Add barang failed.', 'danger')
    return render_template('tambah_barang.html')

@app.route('/edit_barang/<int:id>', methods=['GET'])
@login_required
def edit_barang(id):
    sql = "SELECT * FROM barangs WHERE id_barang = %s"
    datas = db_execute(sql, (id,), fetch='all')
    if not datas:
        flash('Data barang tidak ditemukan.', 'warning')
        return redirect(url_for('dashboard'))
    return render_template('edit_barang.html', datas=datas)

@app.route('/update_barang', methods=['GET', 'POST'])
@login_required
def update_barang():
    if request.method == 'POST':
        try:
            id_barang = request.form.get('id_barang')
            nama_barang = (request.form.get('nama_barang') or '').strip()
            merk_barang = (request.form.get('merk_barang') or '').strip()
            stok_barang = parse_stok(request.form.get('stok_barang'))

            if not id_barang or not nama_barang or not merk_barang or stok_barang is None:
                flash('Update barang failed. Data tidak valid.', 'danger')
                return redirect(url_for('dashboard'))

            sql = "UPDATE barangs SET nama_barang=%s, merk_barang=%s, stok_barang=%s WHERE id_barang=%s"
            db_execute(sql, (nama_barang, merk_barang, stok_barang, id_barang))
            db_commit()
            flash('Update barang successful!', 'success')
            return redirect(url_for('dashboard'))
        except Exception as e:
            print(e)
            flash('Update barang failed.', 'danger')
    return redirect(url_for('dashboard'))

@app.route('/hapus_barang/<int:id>', methods=['GET'])
@login_required
def hapus_barang(id):
    try:
        if id is None:
            flash('Id invalid.', 'danger')
            return redirect(url_for('dashboard'))
        sql = "DELETE FROM barangs WHERE id_barang = %s"
        db_execute(sql, (id,))
        db_commit()
        flash('Barang deleted successfully!', 'success')
    except Exception as e:
        print(e)
        flash('Delete barang failed.', 'danger')
    return redirect(url_for('dashboard'))

if __name__ == '__main__':
    app.run(debug=True)