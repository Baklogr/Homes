from flask import Flask, render_template, request, redirect, flash, send_from_directory
import json
import os
from werkzeug.utils import secure_filename

app = Flask(__name__, template_folder='.')
app.secret_key = 'секрет'

DATA_FILE = 'price.json'
IMAGES_FOLDER = 'images'  # папка для збереження фото
ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif'}

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

@app.route('/images/<path:filename>')
def custom_static_images(filename):
    return send_from_directory(IMAGES_FOLDER, filename)

@app.route('/')
def index():
    data = load_data()
    return render_template('index.html', services=data['services'], gallery=data.get('gallery', []))

@app.route('/admin', methods=['GET', 'POST'])
def admin():
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
