from flask import Flask, render_template, request, redirect, flash, send_from_directory, session, url_for, g
import json
import os
from werkzeug.utils import secure_filename
from flask_mobility import Mobility

app = Flask(__name__, template_folder='.')
Mobility(app)
app.secret_key = 'секрет'

DATA_FILE = 'price.json'
CRED_FILE = 'cred.json'  # файл з обліковими даними
IMAGES_FOLDER = 'images'  # папка для збереження фото
ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'svg', 'gif'}

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

def load_data():
    if os.path.exists(DATA_FILE):
        with open(DATA_FILE, 'r', encoding='utf-8') as f:
            return json.load(f)
    return {
        "services": [],
        "gallery": []
    }

def save_data(data):
    with open(DATA_FILE, 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=4)

def load_credentials():
    if os.path.exists(CRED_FILE):
        with open(CRED_FILE, 'r', encoding='utf-8') as f:
            return json.load(f)
    return {
        "username": "admin",
        "password": "admin123"
    }

def is_mobile(request):
    user_agent = request.headers.get('User-Agent', '').lower()
    mobile_keywords = ['iphone', 'ipod', 'android', 'blackberry', 'windows phone']
    return any(keyword in user_agent for keyword in mobile_keywords)

@app.route('/images/<path:filename>')
def custom_static_images(filename):
    return send_from_directory(IMAGES_FOLDER, filename)

@app.route('/')
def index():
    data = load_data()
    if is_mobile(request):
        return render_template('mobile.html', services=data['services'], gallery=data.get('gallery', []))
    return render_template('index.html', services=data['services'], gallery=data.get('gallery', []))

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        credentials = load_credentials()
        username = request.form.get('username')
        password = request.form.get('password')

        if username == credentials.get('username') and password == credentials.get('password'):
            session['logged_in'] = True
            return redirect(url_for('admin'))
        else:
            flash('Невірний логін або пароль', 'error')
    
    return render_template('login.html')

@app.route('/logout')
def logout():
    session.pop('logged_in', None)
    return redirect(url_for('login'))

@app.route('/admin', methods=['GET', 'POST'])
def admin():
    if not session.get('logged_in'):
        return redirect(url_for('login'))

    data = load_data()

    if request.method == 'POST':
        # Оновлення ціни послуги
        if 'update_price' in request.form:
            heading = request.form.get('service_heading')
            new_price_raw = request.form.get('new_price')

            if not heading or not new_price_raw:
                flash("Будь ласка, виберіть послугу та введіть нову ціну", 'error')
                return redirect('/admin')

            try:
                new_price = int(new_price_raw)
                if new_price < 0:
                    raise ValueError()
            except ValueError:
                flash("Ціна має бути додатнім числом", 'error')
                return redirect('/admin')

            updated = False
            for service in data['services']:
                if service['heading'] == heading:
                    service['price'] = new_price
                    updated = True
                    break

            if updated:
                save_data(data)
                flash(f"Ціну послуги '{heading}' оновлено", 'success')
            else:
                flash("Послуга не знайдена", 'error')

            return redirect('/admin')

        # Оновлення фото галереї
        if 'update_gallery' in request.form:
            position_raw = request.form.get('position')
            file = request.files.get('new_image')

            if not position_raw or not file or file.filename == '':
                flash('Потрібно вибрати позицію та файл', 'error')
                return redirect('/admin')

            if not allowed_file(file.filename):
                flash('Недопустимий формат файлу', 'error')
                return redirect('/admin')

            try:
                position = int(position_raw)
                if not (1 <= position <= len(data.get('gallery', []))):
                    raise ValueError()
            except ValueError:
                flash('Невірна позиція', 'error')
                return redirect('/admin')

            filename = secure_filename(file.filename)
            filepath = os.path.join(IMAGES_FOLDER, filename)

            os.makedirs(IMAGES_FOLDER, exist_ok=True)
            file.save(filepath)

            # Оновлення назви фото у json за позицією (індексація з 1)
            data['gallery'][position - 1] = filename
            save_data(data)

            flash(f'Фото на позиції {position} оновлено', 'success')
            return redirect('/admin')

    return render_template('admin.html', services=data['services'], gallery=data.get('gallery', []))

if __name__ == '__main__':
    app.run(debug=True, port=9123)