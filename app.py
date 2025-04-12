from flask import Flask, request, jsonify, render_template, session, redirect, url_for
from flask_cors import CORS
import threading
import time
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
import random
import string
import os

app = Flask(__name__)
app.secret_key = os.urandom(24)
CORS(app)

# Başlangıç değerleri
cikis_data = {
    "vantilator": False,
    "pencere": False,
    "kapi": False,
    "perde": False,
    "ampul": False
}

oto_data = {
    "sicaklik_oto": True,
    "isik_oto": True
}

sicaklik_data = {
    "sicaklik_ilk_esik": 18,
    "sicaklik_ikinci_esik": 22,
    "sicaklik_ucuncu_esik": 26
}

alinan_data = {
    "vantilator_alinan": False,
    "pencere_alinan": False,
    "kapi_alinan": False,
    "perde_alinan": False,
    "ampul_alinan": False,
    "sicaklik": 22,
    "isik_ev": False
}

# Kapı zamanlayıcısı için değişken
kapi_timer = None
kapi_remaining = 0

# Giriş yapmış kullanıcılar için doğrulama kodları
verification_codes = {}

# API Endpoint'leri
@app.route('/api/cikis', methods=['GET', 'POST'])
def cikis():
    global cikis_data
    if request.method == 'POST':
        data = request.get_json()
        if data:
            for key in data:
                if key in cikis_data:
                    cikis_data[key] = bool(data[key])
        return jsonify({"status": "success", "data": cikis_data})
    return jsonify(cikis_data)

@app.route('/api/oto', methods=['GET', 'POST'])
def oto():
    global oto_data
    if request.method == 'POST':
        data = request.get_json()
        if data:
            for key in data:
                if key in oto_data:
                    oto_data[key] = bool(data[key])
        return jsonify({"status": "success", "data": oto_data})
    return jsonify(oto_data)

@app.route('/api/sicaklik', methods=['GET', 'POST'])
def sicaklik():
    global sicaklik_data
    if request.method == 'POST':
        data = request.get_json()
        if data:
            for key in data:
                if key in sicaklik_data:
                    try:
                        sicaklik_data[key] = int(data[key])
                    except:
                        pass
        return jsonify({"status": "success", "data": sicaklik_data})
    return jsonify(sicaklik_data)

@app.route('/api/alinan', methods=['GET', 'POST'])
def alinan():
    global alinan_data
    if request.method == 'POST':
        data = request.get_json()
        if data:
            for key in data:
                if key in alinan_data:
                    if key == "sicaklik":
                        try:
                            alinan_data[key] = int(data[key])
                        except:
                            pass
                    else:
                        alinan_data[key] = bool(data[key])
        return jsonify({"status": "success", "data": alinan_data})
    return jsonify(alinan_data)

# Web sayfaları
@app.route('/')
def index():
    if 'logged_in' in session and session['logged_in']:
        return redirect(url_for('dashboard'))
    return render_template('login.html')

@app.route('/login', methods=['POST'])
def login():
    username = request.form.get('username')
    password = request.form.get('password')
    
    if username == 'herdem' and password == '1940':
        # Doğrulama kodu oluştur ve e-posta gönder
        verification_code = ''.join(random.choices(string.ascii_lowercase + string.digits, k=6))
        verification_codes[username] = verification_code
        
        # E-posta gönderme
        send_verification_email("hidayete369@gmail.com", verification_code)
        
        return render_template('verification.html', username=username)
    else:
        return render_template('login.html', error="Kullanıcı adı veya şifre hatalı!")

@app.route('/verify', methods=['POST'])
def verify():
    username = request.form.get('username')
    code = request.form.get('code')
    
    if username in verification_codes and verification_codes[username] == code:
        session['logged_in'] = True
        return redirect(url_for('dashboard'))
    else:
        return render_template('verification.html', username=username, error="Doğrulama kodu hatalı!")

@app.route('/dashboard')
def dashboard():
    if 'logged_in' not in session or not session['logged_in']:
        return redirect(url_for('index'))
    
    global cikis_data, oto_data, sicaklik_data, alinan_data, kapi_remaining
    
    data = {
        "cikis": cikis_data,
        "oto": oto_data,
        "sicaklik": sicaklik_data,
        "alinan": alinan_data,
        "kapi_remaining": kapi_remaining
    }
    
    return render_template('dashboard.html', data=data)

@app.route('/update_settings', methods=['POST'])
def update_settings():
    if 'logged_in' not in session or not session['logged_in']:
        return jsonify({"status": "error", "message": "Lütfen önce giriş yapın"})
    
    data = request.form
    
    # cikis verilerini güncelle
    if 'vantilator' in data and not oto_data['sicaklik_oto']:
        cikis_data['vantilator'] = data['vantilator'] == 'true'
    
    if 'pencere' in data and not oto_data['sicaklik_oto']:
        cikis_data['pencere'] = data['pencere'] == 'true'
    
    if 'kapi' in data:
        alinan_data['kapi_alinan'] = data['kapi'] == 'true'
    
    if 'perde' in data and not oto_data['isik_oto']:
        cikis_data['perde'] = data['perde'] == 'true'
    
    if 'ampul' in data and not oto_data['isik_oto']:
        cikis_data['ampul'] = data['ampul'] == 'true'
    
    # oto verilerini güncelle
    if 'sicaklik_oto' in data:
        oto_data['sicaklik_oto'] = data['sicaklik_oto'] == 'true'
    
    if 'isik_oto' in data:
        oto_data['isik_oto'] = data['isik_oto'] == 'true'
    
    # sicaklik verilerini güncelle
    if 'sicaklik_ilk_esik' in data:
        try:
            sicaklik_data['sicaklik_ilk_esik'] = int(data['sicaklik_ilk_esik'])
        except:
            pass
    
    if 'sicaklik_ikinci_esik' in data:
        try:
            sicaklik_data['sicaklik_ikinci_esik'] = int(data['sicaklik_ikinci_esik'])
        except:
            pass
    
    if 'sicaklik_ucuncu_esik' in data:
        try:
            sicaklik_data['sicaklik_ucuncu_esik'] = int(data['sicaklik_ucuncu_esik'])
        except:
            pass
    
    return jsonify({"status": "success"})

@app.route('/logout')
def logout():
    session.pop('logged_in', None)
    return redirect(url_for('index'))

# E-posta gönderme fonksiyonu
def send_verification_email(to_email, code):
    from_email = "herdemerasmus@gmail.com"
    password = "kmop hzuo yoqp ztnr"
    
    msg = MIMEMultipart()
    msg['From'] = from_email
    msg['To'] = to_email
    msg['Subject'] = "Ev Otomasyon Sistemi Doğrulama Kodu"
    
    body = f"Doğrulama kodunuz: {code}"
    msg.attach(MIMEText(body, 'plain'))
    
    try:
        server = smtplib.SMTP('smtp.gmail.com', 587)
        server.starttls()
        server.login(from_email, password)
        text = msg.as_string()
        server.sendmail(from_email, to_email, text)
        server.quit()
    except Exception as e:
        print(f"E-posta gönderirken hata oluştu: {e}")

# Otomatik kontrol fonksiyonu
def auto_control():
    global cikis_data, oto_data, sicaklik_data, alinan_data, kapi_timer, kapi_remaining
    
    while True:
        # Kapı kontrolü
        if alinan_data["kapi_alinan"]:
            alinan_data["kapi_alinan"] = False
            cikis_data["kapi"] = True
            kapi_remaining = 10
            
            if kapi_timer:
                kapi_timer.cancel()
            
            def kapi_kapat():
                global cikis_data, kapi_remaining
                cikis_data["kapi"] = False
                kapi_remaining = 0
            
            kapi_timer = threading.Timer(10, kapi_kapat)
            kapi_timer.start()
            
            # Zamanlayıcı sayacı için
            for i in range(10):
                time.sleep(1)
                if kapi_remaining > 0:
                    kapi_remaining -= 1
        
        # Sıcaklık otomatik kontrolü
        if oto_data["sicaklik_oto"]:
            current_temp = alinan_data["sicaklik"]
            
            if current_temp < sicaklik_data["sicaklik_ilk_esik"]:
                cikis_data["vantilator"] = False
                cikis_data["pencere"] = False
            elif sicaklik_data["sicaklik_ilk_esik"] <= current_temp < sicaklik_data["sicaklik_ikinci_esik"]:
                cikis_data["vantilator"] = False
                cikis_data["pencere"] = False
            elif sicaklik_data["sicaklik_ikinci_esik"] <= current_temp < sicaklik_data["sicaklik_ucuncu_esik"]:
                cikis_data["vantilator"] = False
                cikis_data["pencere"] = True
            else:
                cikis_data["vantilator"] = True
                cikis_data["pencere"] = True
        else:
            # Manuel mod
            cikis_data["vantilator"] = alinan_data["vantilator_alinan"]
            cikis_data["pencere"] = alinan_data["pencere_alinan"]
        
        # Işık otomatik kontrolü
        if oto_data["isik_oto"]:
            if alinan_data["isik_ev"]:
                cikis_data["perde"] = True
                cikis_data["ampul"] = True
            else:
                cikis_data["perde"] = False
                cikis_data["ampul"] = False
        else:
            # Manuel mod
            cikis_data["perde"] = alinan_data["perde_alinan"]
            cikis_data["ampul"] = alinan_data["ampul_alinan"]
        
        time.sleep(1)

if __name__ == '__main__':
    # Otomatik kontrol için ayrı bir thread başlat
    control_thread = threading.Thread(target=auto_control, daemon=True)
    control_thread.start()
    
    # Flask uygulamasını başlat
    app.run(host='0.0.0.0', port=int(os.environ.get('PORT', 5000)))
