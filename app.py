from flask import Flask, render_template, request, redirect, url_for, flash
import pymysql
import sqlite3
import os
from flask_login import LoginManager, UserMixin, login_user, login_required, logout_user, current_user

app = Flask(__name__)

app.config['SECRET_KEY'] = os.getenv('SECRET_KEY', 'dev-secret-key')

app.config['MYSQL_HOST'] = os.getenv('MYSQL_HOST', 'localhost')
app.config['MYSQL_USER'] = os.getenv('MYSQL_USER', 'root')
app.config['MYSQL_PASSWORD'] = os.getenv('MYSQL_PASSWORD', '')
app.config['MYSQL_DB'] = os.getenv('MYSQL_DB', 'flask_barang')

db_type = 'mysql'


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
        ('admin', 'admin', 'Administrator')
    )
    connection.commit()


try:
    mysql = pymysql.connect(
        host=app.config['MYSQL_HOST'],
        user=app.config['MYSQL_USER'],
        password=app.config['MYSQL_PASSWORD'],
        database=app.config['MYSQL_DB']
    )
    cursor = mysql.cursor()
except Exception:
    db_type = 'sqlite'
    os.makedirs('instance', exist_ok=True)
    mysql = sqlite3.connect('instance/flask_barang.db', check_same_thread=False)
    cursor = mysql.cursor()
    init_sqlite_db(mysql)


def db_execute(sql, params=()):
    if db_type == 'sqlite':
        sql = sql.replace('%s', '?')
    cursor.execute(sql, params)

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
           return (self.username)

@login_manager.user_loader
def load_user(username):
    db_execute('SELECT * FROM users WHERE username=%s', (username,))
    user_data = cursor.fetchone()
    if user_data:
        return User(user_data[0], user_data[1], user_data[2],user_data[3] )
    return None

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        db_execute('SELECT * FROM users WHERE username=%s AND password=%s', (username, password))
        user_data = cursor.fetchone()
        if user_data:
            user = User(user_data[0], user_data[1], user_data[2],user_data[3])

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
    try:
        sql = "select * from barangs"
        db_execute(sql)
        datas = cursor.fetchall()
        print(datas)
    except Exception as e:
        print(e)
    return render_template('index.html', datas=datas)

@app.route('/tambah_barang', methods=['GET', 'POST'])
def tambah_barang():
    if request.method == 'POST':
        try:
            nama_barang = request.form.get('nama_barang')
            merk_barang = request.form.get('merk_barang')
            stok_barang = request.form.get('stok_barang')
            sql = "INSERT into barangs(nama_barang, merk_barang, stok_barang) VALUES(%s, %s, %s)"
            db_execute(sql, (nama_barang, merk_barang, stok_barang))
            mysql.commit()
            flash('Add barang successful!', 'success')
            return redirect(url_for('dashboard'))
        except Exception as e:
            print(e)
            flash('Add barang failed.', 'danger')
    return render_template('tambah_barang.html')

@app.route('/edit_barang/<int:id>', methods=['GET'])
def edit_barang(id):
    sql = "select * from barangs where id_barang = %s"
    db_execute(sql, (id,))
    datas = cursor.fetchall()
    return render_template('edit_barang.html', datas=datas)

@app.route('/update_barang', methods=['GET', 'POST'])
def update_barang():
    if request.method == 'POST':
        try:
            id_barang = request.form.get('id_barang')
            nama_barang = request.form.get('nama_barang')
            merk_barang = request.form.get('merk_barang')
            stok_barang = request.form.get('stok_barang')
            sql = "UPDATE barangs SET nama_barang=%s, merk_barang=%s, stok_barang=%s WHERE id_barang=%s"
            db_execute(sql, (nama_barang, merk_barang, stok_barang, id_barang))
            mysql.commit()
            flash('Update barang successful!', 'success')
            return redirect(url_for('dashboard'))
        except Exception as e:
            print(e)
            flash('Update barang failed.', 'danger')
    return render_template('tambah_barang.html')

@app.route('/hapus_barang/<int:id>', methods=['GET'])
def hapus_barang(id):
    try:
        if id == None:
            flash('Id invalid.', 'danger')
            return redirect(url_for('dashboard'))
        sql = "delete from barangs where id_barang = %s"
        db_execute(sql, (id,))
        mysql.commit()
        flash('User deleted successfully!')
    except Exception as e:
        print(e)
        flash('Add barang failed.', 'danger')
    return redirect(url_for('dashboard'))

if __name__ == '__main__':
    app.run(debug=True)