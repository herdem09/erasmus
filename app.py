from flask import Flask, request, jsonify, render_template, redirect, url_for, session
import time
import threading
import random
import string
import hashlib
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
import os
from functools import wraps

app = Flask(__name__)
app.secret_key = os.urandom(24)

# API İçin Basit Şifreleme Anahtarı
API_ANAHTAR = "akilliev2023"

# Kullanıcı bilgileri
KULLANICI_ADI = "herdem"
SIFRE = "1940"

# Mail ayarları
GONDEREN_EMAIL = "herdemerasmus@gmail.com"
ALICI_EMAIL = "hidayete369@gmail.com"
EMAIL_SIFRE = "kmop hzuo yoqp ztnr"

# Tek seferlik şifre
TEK_SEFERLIK_SIFRE = ""

# Veri Modelleri
gelen_veriler = {
    "kapi_gelen": False,
    "isitici_gelen": False,
    "vantilator_gelen": False,
    "pencere_gelen": False,
    "ampul_gelen": False,
    "perde_gelen": False,
    "isik_gelen": 0,
    "sicaklik_gelen": 25,
    "isik_oto_gelen": False,
    "sicaklik_oto_gelen": False,
    "birinci_esik_gelen": 18,
    "ikinci_esik_gelen": 22,
    "ucuncu_esik_gelen": 26
}

olan_veriler = {
    "kapi": False,
    "isitici": False,
    "vantilator": False,
    "pencere": False,
    "ampul": False,
    "perde": False,
    "isik": 0,
    "sicaklik": 25,
    "isik_oto": False,
    "sicaklik_oto": False,
    "birinci_esik": 18,
    "ikinci_esik": 22,
    "ucuncu_esik": 26
}

giden_veriler = {
    "kapi_giden": False,
    "ampul_giden": False,
    "perde_giden": False,
    "isitici_giden": False,
    "vantilator_giden": False,
    "pencere_giden": False
}

# Kilitler
veri_kilidi = threading.Lock()

# Login zorunluluğu decorator'ı
def login_gerekli(f):
    @wraps(f)
    def dekorasyonlu_fonksiyon(*args, **kwargs):
        if 'giris_yapildi' not in session or not session['giris_yapildi']:
            return redirect(url_for('login'))
        return f(*args, **kwargs)
    return dekorasyonlu_fonksiyon

# API anahtarı kontrolü decorator'ı
def api_anahtar_gerekli(f):
    @wraps(f)
    def dekorasyonlu_fonksiyon(*args, **kwargs):
        if request.method == "POST":
            gelen_anahtar = request.headers.get('X-API-Key')
            if not gelen_anahtar or not anahtar_dogrula(gelen_anahtar):
                return jsonify({"hata": "Geçersiz API anahtarı"}), 401
        return f(*args, **kwargs)
    return dekorasyonlu_fonksiyon

def anahtar_dogrula(anahtar):
    beklenen_hash = hashlib.sha256(API_ANAHTAR.encode()).hexdigest()
    return hashlib.sha256(anahtar.encode()).hexdigest() == beklenen_hash

def tek_seferlik_sifre_olustur():
    global TEK_SEFERLIK_SIFRE
    karakterler = string.digits
    TEK_SEFERLIK_SIFRE = ''.join(random.choice(karakterler) for _ in range(8))
    return TEK_SEFERLIK_SIFRE

def mail_gonder(konu, icerik):
    try:
        mesaj = MIMEMultipart()
        mesaj["From"] = GONDEREN_EMAIL
        mesaj["To"] = ALICI_EMAIL
        mesaj["Subject"] = konu
        
        mesaj.attach(MIMEText(icerik, "plain"))
        
        with smtplib.SMTP("smtp.gmail.com", 587) as sunucu:
            sunucu.starttls()
            sunucu.login(GONDEREN_EMAIL, EMAIL_SIFRE)
            sunucu.send_message(mesaj)
        
        return True
    except Exception as e:
        print(f"Mail gönderme hatası: {e}")
        return False

def kapi_otomatik_kapat():
    time.sleep(10)  # 10 saniye bekle
    with veri_kilidi:
        olan_veriler["kapi"] = False
        giden_veriler["kapi_giden"] = False

def otomatik_kontrol():
    while True:
        time.sleep(1)  # Her saniye kontrol et
        with veri_kilidi:
            # Sıcaklık otomatik kontrolü
            if olan_veriler["sicaklik_oto"]:
                sicaklik = olan_veriler["sicaklik"]
                birinci_esik = olan_veriler["birinci_esik"]
                ikinci_esik = olan_veriler["ikinci_esik"]
                ucuncu_esik = olan_veriler["ucuncu_esik"]
                
                if sicaklik < birinci_esik:
                    olan_veriler["pencere"] = False
                    olan_veriler["isitici"] = True
                    olan_veriler["vantilator"] = False
                    
                    giden_veriler["pencere_giden"] = False
                    giden_veriler["isitici_giden"] = True
                    giden_veriler["vantilator_giden"] = False
                    
                elif sicaklik >= birinci_esik and sicaklik < ikinci_esik:
                    olan_veriler["pencere"] = False
                    olan_veriler["isitici"] = False
                    olan_veriler["vantilator"] = False
                    
                    giden_veriler["pencere_giden"] = False
                    giden_veriler["isitici_giden"] = False
                    giden_veriler["vantilator_giden"] = False
                    
                elif sicaklik >= ikinci_esik and sicaklik < ucuncu_esik:
                    olan_veriler["pencere"] = True
                    olan_veriler["isitici"] = False
                    olan_veriler["vantilator"] = False
                    
                    giden_veriler["pencere_giden"] = True
                    giden_veriler["isitici_giden"] = False
                    giden_veriler["vantilator_giden"] = False
                    
                elif sicaklik >= ucuncu_esik:
                    olan_veriler["pencere"] = True
                    olan_veriler["isitici"] = False
                    olan_veriler["vantilator"] = True
                    
                    giden_veriler["pencere_giden"] = True
                    giden_veriler["isitici_giden"] = False
                    giden_veriler["vantilator_giden"] = True
            
            # Işık otomatik kontrolü
            if olan_veriler["isik_oto"]:
                isik = olan_veriler["isik"]
                
                if isik == 1:
                    olan_veriler["ampul"] = True
                    olan_veriler["perde"] = True
                    
                    giden_veriler["ampul_giden"] = True
                    giden_veriler["perde_giden"] = True
                    
                else:  # isik == 0
                    olan_veriler["ampul"] = False
                    olan_veriler["perde"] = False
                    
                    giden_veriler["ampul_giden"] = False
                    giden_veriler["perde_giden"] = False

# API rotaları
@app.route('/api/gelen', methods=['GET', 'POST'])
@api_anahtar_gerekli
def gelen_api():
    global gelen_veriler, olan_veriler, giden_veriler
    
    if request.method == 'GET':
        return jsonify(gelen_veriler)
    
    elif request.method == 'POST':
        yeni_veriler = request.json
        
        with veri_kilidi:
            for anahtar, deger in yeni_veriler.items():
                if anahtar in gelen_veriler:
                    gelen_veriler[anahtar] = deger
                    
                    # Kapı durumu kontrolü
                    if anahtar == "kapi_gelen" and deger:
                        olan_veriler["kapi"] = True
                        giden_veriler["kapi_giden"] = True
                        # 10 saniye sonra kapıyı kapat
                        threading.Thread(target=kapi_otomatik_kapat).start()
                    
                    # Isıtıcı durumu kontrolü
                    elif anahtar == "isitici_gelen":
                        if olan_veriler["sicaklik_oto"]:
                            # Otomatik modda değişiklik yapma, mevcut değer korunsun
                            gelen_veriler["isitici_gelen"] = olan_veriler["isitici"]
                        else:
                            # Manuel mod
                            olan_veriler["isitici"] = deger
                            giden_veriler["isitici_giden"] = deger
                    
                    # Vantilatör durumu kontrolü
                    elif anahtar == "vantilator_gelen":
                        if olan_veriler["sicaklik_oto"]:
                            # Otomatik modda değişiklik yapma
                            gelen_veriler["vantilator_gelen"] = olan_veriler["vantilator"]
                        else:
                            # Manuel mod
                            olan_veriler["vantilator"] = deger
                            giden_veriler["vantilator_giden"] = deger
                    
                    # Pencere durumu kontrolü
                    elif anahtar == "pencere_gelen":
                        if olan_veriler["sicaklik_oto"]:
                            # Otomatik modda değişiklik yapma
                            gelen_veriler["pencere_gelen"] = olan_veriler["pencere"]
                        else:
                            # Manuel mod
                            olan_veriler["pencere"] = deger
                            giden_veriler["pencere_giden"] = deger
                    
                    # Ampul durumu kontrolü
                    elif anahtar == "ampul_gelen":
                        if olan_veriler["isik_oto"]:
                            # Otomatik modda değişiklik yapma
                            gelen_veriler["ampul_gelen"] = olan_veriler["ampul"]
                        else:
                            # Manuel mod
                            olan_veriler["ampul"] = deger
                            giden_veriler["ampul_giden"] = deger
                    
                    # Perde durumu kontrolü
                    elif anahtar == "perde_gelen":
                        if olan_veriler["isik_oto"]:
                            # Otomatik modda değişiklik yapma
                            gelen_veriler["perde_gelen"] = olan_veriler["perde"]
                        else:
                            # Manuel mod
                            olan_veriler["perde"] = deger
                            giden_veriler["perde_giden"] = deger
                    
                    # Diğer parametreler
                    elif anahtar == "sicaklik_gelen":
                        olan_veriler["sicaklik"] = deger
                    elif anahtar == "isik_gelen":
                        olan_veriler["isik"] = deger
                    elif anahtar == "isik_oto_gelen":
                        olan_veriler["isik_oto"] = deger
                    elif anahtar == "sicaklik_oto_gelen":
                        olan_veriler["sicaklik_oto"] = deger
                    elif anahtar == "birinci_esik_gelen":
                        olan_veriler["birinci_esik"] = deger
                    elif anahtar == "ikinci_esik_gelen":
                        olan_veriler["ikinci_esik"] = deger
                    elif anahtar == "ucuncu_esik_gelen":
                        olan_veriler["ucuncu_esik"] = deger
        
        return jsonify({"durum": "başarılı", "mesaj": "Veriler güncellendi"})

@app.route('/api/olan', methods=['GET'])
@api_anahtar_gerekli
def olan_api():
    return jsonify(olan_veriler)

@app.route('/api/giden', methods=['GET'])
@api_anahtar_gerekli
def giden_api():
    return jsonify(giden_veriler)

# Web arayüzü rotaları
@app.route('/')
def ana_sayfa():
    if 'giris_yapildi' in session and session['giris_yapildi']:
        return redirect(url_for('dashboard'))
    return redirect(url_for('login'))

@app.route('/login', methods=['GET', 'POST'])
def login():
    hata = None
    tek_seferlik_sifre_mesaji = None
    
    if request.method == 'POST':
        kullanici_adi = request.form.get('kullanici_adi')
        sifre = request.form.get('sifre')
        
        if kullanici_adi == KULLANICI_ADI and sifre == SIFRE:
            # Kullanıcı bilgileri doğru, tek seferlik şifre oluştur
            tek_seferlik = tek_seferlik_sifre_olustur()
            
            # Mail gönder
            konu = "Giriş Bildirimi ve Tek Seferlik Şifre"
            icerik = f"Hesabınıza bir giriş talebi alındı.\nTek seferlik şifreniz: {tek_seferlik}"
            
            if mail_gonder(konu, icerik):
                tek_seferlik_sifre_mesaji = "Tek seferlik şifreniz e-posta adresinize gönderildi."
                session['kullanici_dogrulandi'] = True
            else:
                hata = "E-posta gönderilemedi, lütfen tekrar deneyin."
        else:
            hata = "Kullanıcı adı veya şifre hatalı!"
    
    return render_template('login.html', hata=hata, tek_seferlik_sifre_mesaji=tek_seferlik_sifre_mesaji)

@app.route('/dogrula', methods=['POST'])
def dogrula():
    if 'kullanici_dogrulandi' not in session or not session['kullanici_dogrulandi']:
        return redirect(url_for('login'))
    
    girilen_kod = request.form.get('tek_seferlik_sifre')
    
    if girilen_kod == TEK_SEFERLIK_SIFRE:
        session['giris_yapildi'] = True
        return redirect(url_for('dashboard'))
    else:
        return render_template('login.html', 
                              kod_hatasi="Tek seferlik şifre hatalı, lütfen tekrar deneyin.",
                              tek_seferlik_sifre_mesaji="Tek seferlik şifrenizi girin.")

@app.route('/cikis')
def cikis():
    session.clear()
    return redirect(url_for('login'))

@app.route('/dashboard')
@login_gerekli
def dashboard():
    return render_template('dashboard.html', olan=olan_veriler, gelen=gelen_veriler, giden=giden_veriler)

@app.route('/gelen_guncelle', methods=['POST'])
@login_gerekli
def gelen_guncelle():
    yeni_veriler = {}
    
    for anahtar in gelen_veriler.keys():
        if anahtar != "isik_gelen":  # isik_gelen hariç
            if anahtar.endswith('_gelen') and anahtar.replace('_gelen', '') in ['kapi', 'isitici', 'vantilator', 'pencere', 'ampul', 'perde', 'isik_oto', 'sicaklik_oto']:
                # Boolean değerler
                deger = anahtar in request.form
                yeni_veriler[anahtar] = deger
            elif anahtar in request.form:
                # Sayısal değerler
                try:
                    deger = int(request.form[anahtar])
                    yeni_veriler[anahtar] = deger
                except ValueError:
                    pass
    
    # API'ye gönder
    with veri_kilidi:
        for anahtar, deger in yeni_veriler.items():
            if anahtar in gelen_veriler:
                gelen_veriler[anahtar] = deger
                
                # Kapı durumu kontrolü
                if anahtar == "kapi_gelen" and deger:
                    olan_veriler["kapi"] = True
                    giden_veriler["kapi_giden"] = True
                    # 10 saniye sonra kapıyı kapat
                    threading.Thread(target=kapi_otomatik_kapat).start()
                
                # Isıtıcı durumu kontrolü
                elif anahtar == "isitici_gelen":
                    if olan_veriler["sicaklik_oto"]:
                        # Otomatik modda değişiklik yapma
                        gelen_veriler["isitici_gelen"] = olan_veriler["isitici"]
                    else:
                        # Manuel mod
                        olan_veriler["isitici"] = deger
                        giden_veriler["isitici_giden"] = deger
                
                # Vantilatör durumu kontrolü
                elif anahtar == "vantilator_gelen":
                    if olan_veriler["sicaklik_oto"]:
                        # Otomatik modda değişiklik yapma
                        gelen_veriler["vantilator_gelen"] = olan_veriler["vantilator"]
                    else:
                        # Manuel mod
                        olan_veriler["vantilator"] = deger
                        giden_veriler["vantilator_giden"] = deger
                
                # Pencere durumu kontrolü
                elif anahtar == "pencere_gelen":
                    if olan_veriler["sicaklik_oto"]:
                        # Otomatik modda değişiklik yapma
                        gelen_veriler["pencere_gelen"] = olan_veriler["pencere"]
                    else:
                        # Manuel mod
                        olan_veriler["pencere"] = deger
                        giden_veriler["pencere_giden"] = deger
                
                # Ampul durumu kontrolü
                elif anahtar == "ampul_gelen":
                    if olan_veriler["isik_oto"]:
                        # Otomatik modda değişiklik yapma
                        gelen_veriler["ampul_gelen"] = olan_veriler["ampul"]
                    else:
                        # Manuel mod
                        olan_veriler["ampul"] = deger
                        giden_veriler["ampul_giden"] = deger
                
                # Perde durumu kontrolü
                elif anahtar == "perde_gelen":
                    if olan_veriler["isik_oto"]:
                        # Otomatik modda değişiklik yapma
                        gelen_veriler["perde_gelen"] = olan_veriler["perde"]
                    else:
                        # Manuel mod
                        olan_veriler["perde"] = deger
                        giden_veriler["perde_giden"] = deger
                
                # Diğer parametreler
                elif anahtar == "sicaklik_gelen":
                    olan_veriler["sicaklik"] = deger
                elif anahtar == "isik_oto_gelen":
                    olan_veriler["isik_oto"] = deger
                elif anahtar == "sicaklik_oto_gelen":
                    olan_veriler["sicaklik_oto"] = deger
                elif anahtar == "birinci_esik_gelen":
                    olan_veriler["birinci_esik"] = deger
                elif anahtar == "ikinci_esik_gelen":
                    olan_veriler["ikinci_esik"] = deger
                elif anahtar == "ucuncu_esik_gelen":
                    olan_veriler["ucuncu_esik"] = deger
    
    return redirect(url_for('dashboard'))

if __name__ == '__main__':
    # Otomatik kontrol thread'ini başlat
    kontrol_thread = threading.Thread(target=otomatik_kontrol, daemon=True)
    kontrol_thread.start()
    
    # Flask uygulamasını başlat
    app.run(host='0.0.0.0', port=int(os.environ.get('PORT', 8080)), debug=False)
