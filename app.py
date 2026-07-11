# -*- coding: utf-8 -*-
"""
VERTUAL MARKET — BIST Katılım Analiz Terminali (Yerel Sürüm)
------------------------------------------------------------
- Veri: Yahoo Finance (yfinance) — ÜCRETSİZ, ~15 DAKİKA GECİKMELİ
- Matriks mum formasyon kataloğu: 21 boğa + 13 ayı = 34 formasyon
  Teyit / stop seviyeleri ve Onaylanmamış / Onaylanmış /
  Onaylanmış & Başarısız durum döngüsü ile
- RSI, MA20/MA50, destek-direnç, sinyal skoru

Çalıştırmak için:  streamlit run app.py
UYARI: Hiçbir çıktı yatırım tavsiyesi değildir. Veriler gecikmelidir.
"""

import math
import re
import requests
import pandas as pd
import streamlit as st
import yfinance as yf
import plotly.graph_objects as go

# ----------------------------------------------------------------
# Hisse evreni (sembol, isim, katılım_örnek_etiketi, sektör)
# Katılım etiketi ÖRNEKTİR; resmî katılım endeksi listesiyle doğrulayın.
# Yeni hisse eklemek için satır ekleyin: ("KOD", "İsim", True/False, "Sektör")
# ----------------------------------------------------------------
UNIVERSE = [
    ("ASELS", "Aselsan", True, "Savunma"), ("THYAO", "Türk Hava Yolları", True, "Ulaştırma"),
    ("BIMAS", "BİM Mağazalar", True, "Perakende"), ("EREGL", "Ereğli Demir Çelik", True, "Metal"),
    ("SISE", "Şişecam", True, "Cam"), ("FROTO", "Ford Otosan", True, "Otomotiv"),
    ("PGSUS", "Pegasus", True, "Ulaştırma"), ("TCELL", "Turkcell", True, "İletişim"),
    ("TTKOM", "Türk Telekom", True, "İletişim"), ("ARCLK", "Arçelik", True, "Dayanıklı Tük."),
    ("TOASO", "Tofaş", True, "Otomotiv"), ("VESTL", "Vestel", True, "Dayanıklı Tük."),
    ("VESBE", "Vestel Beyaz", True, "Dayanıklı Tük."), ("PETKM", "Petkim", True, "Kimya"),
    ("KOZAL", "Koza Altın", True, "Madencilik"), ("KOZAA", "Koza Madencilik", True, "Madencilik"),
    ("IPEKE", "İpek Doğal Enerji", True, "Enerji"), ("GUBRF", "Gübre Fabrik.", True, "Kimya"),
    ("SASA", "Sasa Polyester", True, "Kimya"), ("HEKTS", "Hektaş", True, "Kimya"),
    ("EKGYO", "Emlak Konut GYO", True, "GYO"), ("ENKAI", "Enka İnşaat", True, "İnşaat"),
    ("TAVHL", "TAV Havalimanları", True, "Ulaştırma"), ("ULKER", "Ülker", True, "Gıda"),
    ("CCOLA", "Coca-Cola İçecek", True, "İçecek"), ("MGROS", "Migros", True, "Perakende"),
    ("SOKM", "Şok Marketler", True, "Perakende"), ("ASTOR", "Astor Enerji", True, "Elektrik Ekip."),
    ("ENJSA", "Enerjisa", True, "Enerji"), ("AKSEN", "Aksa Enerji", True, "Enerji"),
    ("ODAS", "Odaş Elektrik", True, "Enerji"), ("ZOREN", "Zorlu Enerji", True, "Enerji"),
    ("ALARK", "Alarko Holding", True, "Holding"), ("OTKAR", "Otokar", True, "Savunma"),
    ("TTRAK", "Türk Traktör", True, "Makine"), ("KARSN", "Karsan", True, "Otomotiv"),
    ("BRSAN", "Borusan Boru", True, "Metal"), ("ISDMR", "İskenderun Demir", True, "Metal"),
    ("KRDMD", "Kardemir (D)", True, "Metal"), ("OYAKC", "Oyak Çimento", True, "Çimento"),
    ("AKCNS", "Akçansa", True, "Çimento"), ("CIMSA", "Çimsa", True, "Çimento"),
    ("SMRTG", "Smart Güneş", True, "Enerji Tekn."), ("KONTR", "Kontrolmatik", True, "Enerji Tekn."),
    ("GESAN", "Girişim Elektrik", True, "Elektrik Ekip."), ("EUPWR", "Europower Enerji", True, "Elektrik Ekip."),
    ("YEOTK", "Yeo Teknoloji", True, "Enerji Tekn."), ("MIATK", "Mia Teknoloji", True, "Yazılım"),
    ("REEDR", "Reeder Teknoloji", True, "Teknoloji"), ("PENTA", "Penta Teknoloji", True, "Teknoloji"),
    ("LOGO", "Logo Yazılım", True, "Yazılım"), ("KAREL", "Karel Elektronik", True, "Teknoloji"),
    ("INDES", "İndeks Bilgisayar", True, "Teknoloji"), ("ARDYZ", "ARD Grup Bilişim", True, "Yazılım"),
    ("NETAS", "Netaş", True, "Teknoloji"), ("ALFAS", "Alfa Solar", True, "Enerji Tekn."),
    ("CWENE", "CW Enerji", True, "Enerji Tekn."), ("QUAGR", "QUA Granite", True, "Yapı Malz."),
    ("TABGD", "TAB Gıda", True, "Gıda"), ("MAVI", "Mavi Giyim", True, "Giyim"),
    ("SELEC", "Selçuk Ecza", True, "Sağlık"), ("DEVA", "Deva Holding", True, "İlaç"),
    ("ECILC", "Eczacıbaşı İlaç", True, "İlaç"), ("LKMNH", "Lokman Hekim", True, "Sağlık"),
    ("MPARK", "MLP Sağlık", True, "Sağlık"), ("EGEEN", "Ege Endüstri", True, "Otomotiv Yan"),
    ("BFREN", "Bosch Fren", True, "Otomotiv Yan"), ("TMSN", "Tümosan Motor", True, "Makine"),
    ("KCAER", "Kocaer Çelik", True, "Metal"), ("TKFEN", "Tekfen Holding", True, "Holding"),
    ("OBAMS", "Oba Makarna", True, "Gıda"), ("EBEBK", "Ebebek", True, "Perakende"),
    ("TUKAS", "Tukaş Gıda", True, "Gıda"), ("ALBRK", "Albaraka Türk", True, "Katılım Bank."),
    ("DOAS", "Doğuş Otomotiv", True, "Otomotiv"), ("CANTE", "Çan2 Termik", True, "Enerji"),
    # --- katılım dışı (örnek etiket) ---
    ("GARAN", "Garanti BBVA", False, "Bankacılık"), ("AKBNK", "Akbank", False, "Bankacılık"),
    ("ISCTR", "İş Bankası (C)", False, "Bankacılık"), ("YKBNK", "Yapı Kredi", False, "Bankacılık"),
    ("VAKBN", "Vakıfbank", False, "Bankacılık"), ("HALKB", "Halkbank", False, "Bankacılık"),
    ("TSKB", "TSKB", False, "Bankacılık"), ("SKBNK", "Şekerbank", False, "Bankacılık"),
    ("KCHOL", "Koç Holding", False, "Holding"), ("SAHOL", "Sabancı Holding", False, "Holding"),
    ("AGHOL", "AG Anadolu Grubu", False, "Holding"), ("DOHOL", "Doğan Holding", False, "Holding"),
    ("AEFES", "Anadolu Efes", False, "İçecek"), ("TUPRS", "Tüpraş", False, "Enerji"),
    ("AKGRT", "Aksigorta", False, "Sigorta"), ("ANSGR", "Anadolu Sigorta", False, "Sigorta"),
    ("TURSG", "Türkiye Sigorta", False, "Sigorta"), ("ISMEN", "İş Yatırım", False, "Aracı Kurum"),
    ("GLYHO", "Global Yat. Hold.", False, "Holding"), ("ISGYO", "İş GYO", False, "GYO"),
]


# ----------------------------------------------------------------
# TÜM BIST LİSTESİ — KAP'tan otomatik çekilir (24 saat önbellek).
# KAP'a ulaşılamazsa yukarıdaki gömülü UNIVERSE listesi kullanılır.
# ----------------------------------------------------------------
KATILIM_UYGUN_ORNEK = {u[0] for u in UNIVERSE if u[2]}
KATILIM_DISI_ORNEK = {u[0] for u in UNIVERSE if not u[2]}
ISIM_SOZLUGU = {u[0]: u[1] for u in UNIVERSE}

@st.cache_data(ttl=86400, show_spinner=False)
def kap_tum_liste():
    """KAP BIST Şirketleri sayfasından tüm işlem kodlarını çeker."""
    try:
        r = requests.get(
            "https://kap.org.tr/tr/bist-sirketler",
            headers={"User-Agent": "Mozilla/5.0"}, timeout=20)
        r.raise_for_status()
        kodlar = set()
        for m in re.findall(r">([A-Z0-9]{4,6}(?: [A-Z0-9]{3,6})?)</a>", r.text):
            for kod in m.split():
                if 4 <= len(kod) <= 6 and not kod.isdigit():
                    kodlar.add(kod)
        if len(kodlar) > 100:
            return sorted(kodlar)
    except Exception:
        pass
    try:
        r = requests.get("https://finans.mynet.com/borsa/hisseler/",
                         headers={"User-Agent": "Mozilla/5.0"}, timeout=20)
        r.raise_for_status()
        kodlar = {m.upper() for m in re.findall(r"/borsa/hisseler/([a-z0-9]{4,6})-", r.text)}
        if len(kodlar) > 100:
            return sorted(kodlar)
    except Exception:
        pass
    return None

def katilim_etiketi(kod):
    if kod in KATILIM_UYGUN_ORNEK:
        return "uygun"
    if kod in KATILIM_DISI_ORNEK:
        return "disi"
    return "bilinmiyor"

# ----------------------------------------------------------------
# Mum yardımcıları — Matriks kataloğu tespit kuralları için
# ----------------------------------------------------------------
def body(x): return abs(x["c"] - x["o"])
def white(x): return x["c"] > x["o"]
def black(x): return x["c"] < x["o"]
def b_top(x): return max(x["o"], x["c"])
def b_bot(x): return min(x["o"], x["c"])
def up_s(x): return x["h"] - b_top(x)
def lo_s(x): return b_bot(x) - x["l"]
def rng(x): return x["h"] - x["l"]
def is_doji(x): return rng(x) > 0 and body(x) <= 0.12 * rng(x)
def mid(x): return (x["o"] + x["c"]) / 2
def inside(out, inn): return b_top(inn) <= b_top(out) and b_bot(inn) >= b_bot(out)
def engulf(out, inn): return b_top(out) >= b_top(inn) and b_bot(out) <= b_bot(inn) and body(out) > body(inn)
def eq(a, c, ref): return abs(a - c) <= 0.002 * ref

def avg_body(b, i):
    lo = max(1, i - 10)
    vals = [body(b[k]) for k in range(lo, i)]
    return sum(vals) / len(vals) if vals else body(b[i])

def long_b(b, i, x): return body(x) >= 1.15 * avg_body(b, i)
def short_b(b, i, x): return body(x) <= 0.65 * avg_body(b, i)
def maru(b, i, x): return long_b(b, i, x) and up_s(x) <= 0.1 * body(x) and lo_s(x) <= 0.1 * body(x)
def tr_down(b, i): return b[max(0, i - 5)]["c"] > b[max(0, i)]["c"] * 1.005
def tr_up(b, i): return b[max(0, i - 5)]["c"] * 1.005 < b[max(0, i)]["c"]

# ----------------------------------------------------------------
# KATALOG: Matriks "Mum Formasyonlar" — 21 boğa + 13 ayı = 34 tip
# Her giriş: (tr_ad, en_ad, yön(+1/-1), bar_sayısı, test_fonksiyonu)
# test -> None ya da (teyit, stop)
# ----------------------------------------------------------------
def katalog():
    K = []
    def ekle(tr, en, yon, nb, fn): K.append({"tr": tr, "en": en, "yon": yon, "nb": nb, "test": fn})

    # ---------------- BOĞA (21) ----------------
    def f_hammer(b, i):
        x = b[i]
        if tr_down(b, i - 1) and body(x) > 0 and lo_s(x) >= 2 * body(x) and up_s(x) <= 0.3 * rng(x):
            return (b_top(x), x["l"])
    ekle("Çekiç Boğa", "Bullish Hammer", 1, 1, f_hammer)

    def f_belt_b(b, i):
        x = b[i]
        if tr_down(b, i - 1) and white(x) and long_b(b, i, x) and lo_s(x) <= 0.05 * rng(x) and up_s(x) <= 0.25 * rng(x):
            return (x["c"], x["l"])
    ekle("Belden Tutma Boğa", "Bullish Belt Hold", 1, 1, f_belt_b)

    def f_eng_b(b, i):
        p, x = b[i - 1], b[i]
        if tr_down(b, i - 2) and black(p) and white(x) and engulf(x, p):
            return (x["c"], x["l"])
    ekle("Yutan Boğa", "Bullish Engulfing", 1, 2, f_eng_b)

    def f_har_b(b, i):
        p, x = b[i - 1], b[i]
        if tr_down(b, i - 2) and black(p) and long_b(b, i - 1, p) and white(x) and inside(p, x):
            return (max(x["c"], mid(p)), min(p["l"], x["l"]))
    ekle("Hamile Boğa", "Bullish Harami", 1, 2, f_har_b)

    def f_harx_b(b, i):
        p, x = b[i - 1], b[i]
        if tr_down(b, i - 2) and black(p) and is_doji(x) and inside(p, x):
            teyit = b_top(p) if short_b(b, i - 1, p) else max(x["c"], mid(p))
            return (teyit, min(p["l"], x["l"]))
    ekle("Kros Hamile Boğa", "Bullish Harami Cross", 1, 2, f_harx_b)

    def f_invh(b, i):
        p, x = b[i - 1], b[i]
        if tr_down(b, i - 2) and black(p) and body(x) > 0 and up_s(x) >= 2 * body(x) and lo_s(x) <= 0.3 * body(x) + 1e-12:
            return (b_top(x) + up_s(x) / 2, min(p["l"], x["l"]))
    ekle("Ters Çekiç Boğa", "Bullish Inverted Hammer", 1, 2, f_invh)

    def f_pierce(b, i):
        p, x = b[i - 1], b[i]
        if tr_down(b, i - 2) and black(p) and long_b(b, i - 1, p) and white(x) and x["o"] < p["c"] and mid(p) < x["c"] < p["o"]:
            return (x["c"], x["l"])
    ekle("Delen Mumlar Boğa", "Bullish Piercing Line", 1, 2, f_pierce)

    def f_dstar_b(b, i):
        p, x = b[i - 1], b[i]
        if tr_down(b, i - 2) and black(p) and is_doji(x) and b_top(x) < p["c"]:
            return ((p["c"] + b_top(x)) / 2, min(p["l"], x["l"]))
    ekle("Doji Yıldız Boğa", "Bullish Doji Star", 1, 2, f_dstar_b)

    def f_meet_b(b, i):
        p, x = b[i - 1], b[i]
        if tr_down(b, i - 2) and black(p) and white(x) and x["o"] < p["c"] * 0.99 and eq(x["c"], p["c"], p["c"]):
            return (x["c"], x["l"])
    ekle("Değen Mumlar Boğa", "Bullish Meeting Line", 1, 2, f_meet_b)

    def f_pigeon(b, i):
        p, x = b[i - 1], b[i]
        if tr_down(b, i - 2) and black(p) and long_b(b, i - 1, p) and black(x) and inside(p, x):
            return (max(x["c"], mid(p)), min(p["l"], x["l"]))
    ekle("Güvercin Yuvası Boğa", "Bullish Homing Pigeon", 1, 2, f_pigeon)

    def f_mlow(b, i):
        p, x = b[i - 1], b[i]
        if tr_down(b, i - 2) and black(p) and black(x) and eq(p["c"], x["c"], p["c"]):
            return (mid(p), min(p["l"], x["l"]))
    ekle("Çakışan Dip Boğa", "Bullish Matching Low", 1, 2, f_mlow)

    def f_kick_b(b, i):
        p, x = b[i - 1], b[i]
        if black(p) and maru(b, i - 1, p) and white(x) and maru(b, i, x) and x["o"] > p["o"]:
            return (x["c"], x["l"])
    ekle("Tepen Mumlar Boğa", "Bullish Kicking", 1, 2, f_kick_b)

    def f_ows(b, i):
        p, x = b[i - 1], b[i]
        if tr_down(b, i - 2) and black(p) and white(x) and x["o"] > p["c"] and x["c"] > p["o"]:
            return (x["c"], x["l"])
    ekle("Beyaz Asker Boğa", "Bullish One White Soldier", 1, 2, f_ows)

    def f_mstar(b, i):
        q, p, x = b[i - 2], b[i - 1], b[i]
        if (tr_down(b, i - 3) and black(q) and long_b(b, i - 2, q) and short_b(b, i - 1, p)
                and not is_doji(p) and b_top(p) < b_bot(q) and white(x) and x["c"] > mid(q)):
            return (x["c"], min(p["l"], x["l"]))
    ekle("Sabah Yıldızı Boğa", "Bullish Morning Star", 1, 3, f_mstar)

    def f_mdstar(b, i):
        q, p, x = b[i - 2], b[i - 1], b[i]
        if (tr_down(b, i - 3) and black(q) and long_b(b, i - 2, q) and is_doji(p)
                and b_top(p) < b_bot(q) and white(x) and x["c"] > mid(q)):
            return (x["c"], min(p["l"], x["l"]))
    ekle("Doji Sabah Yıldızı Boğa", "Bullish Morning Doji Star", 1, 3, f_mdstar)

    def f_baby_b(b, i):
        q, p, x = b[i - 2], b[i - 1], b[i]
        if (tr_down(b, i - 3) and black(q) and is_doji(p) and p["h"] < q["l"]
                and x["l"] > p["h"] and white(x) and b_bot(q) < x["c"] < b_top(q)):
            return (x["c"], min(p["l"], x["l"]))
    ekle("Terkedilmiş Bebek Boğa", "Bullish Abandoned Baby", 1, 3, f_baby_b)

    def f_tristar(b, i):
        q, p, x = b[i - 2], b[i - 1], b[i]
        if tr_down(b, i - 3) and is_doji(q) and is_doji(p) and is_doji(x):
            return (x["c"], min(p["l"], x["l"]))
    ekle("Üç Yıldız Boğa", "Bullish Tristar", 1, 3, f_tristar)

    def f_rabbits(b, i):
        q, p, x = b[i - 2], b[i - 1], b[i]
        if (tr_down(b, i - 3) and black(q) and white(p) and b_top(p) < b_bot(q)
                and white(x) and x["c"] > p["c"] and b_top(x) < b_bot(q)):
            return (x["c"], x["l"])
    ekle("Aşağı Kopan İki Tavşan Boğa", "Bullish Downside Gap Two Rabbits", 1, 3, f_rabbits)

    def f_river(b, i):
        q, p, x = b[i - 2], b[i - 1], b[i]
        if (tr_down(b, i - 3) and black(q) and long_b(b, i - 2, q) and black(p) and inside(q, p)
                and lo_s(p) >= 1.5 * body(p) and white(x) and short_b(b, i, x) and x["c"] < p["c"]):
            return (x["c"], min(p["l"], x["l"]))
    ekle("Üçlü Vadi Boğa", "Bullish Unique Three River Bottom", 1, 3, f_river)

    def f_tws(b, i):
        q, p, x = b[i - 2], b[i - 1], b[i]
        if (white(q) and white(p) and white(x) and p["c"] > q["c"] and x["c"] > p["c"]
                and b_bot(q) < p["o"] < b_top(q) and b_bot(p) < x["o"] < b_top(p)):
            return (x["c"], x["l"])
    ekle("Üç Beyaz Asker Boğa", "Bullish Three White Soldiers", 1, 3, f_tws)

    def f_block(b, i):
        q, p, x = b[i - 2], b[i - 1], b[i]
        if tr_down(b, i - 3) and black(q) and black(p) and black(x) and p["c"] < q["c"] and x["c"] < p["c"]:
            return (mid(x), min(p["l"], x["l"]))
    ekle("Düşen Blok Boğa", "Bullish Descent Block", 1, 3, f_block)

    # ---------------- AYI (13) ----------------
    def f_hang(b, i):
        x = b[i]
        if tr_up(b, i - 1) and body(x) > 0 and lo_s(x) >= 2 * body(x) and up_s(x) <= 0.3 * rng(x):
            return ((x["l"] + b_bot(x)) / 2, max(b[i - 1]["h"], x["h"]))
    ekle("Asılı Adam Ayı", "Bearish Hanging Man", -1, 1, f_hang)

    def f_belt_a(b, i):
        x = b[i]
        if tr_up(b, i - 1) and black(x) and long_b(b, i, x) and up_s(x) <= 0.05 * rng(x) and lo_s(x) <= 0.25 * rng(x):
            return (x["c"], x["h"])
    ekle("Belden Tutma Ayı", "Bearish Belt Hold", -1, 1, f_belt_a)

    def f_eng_a(b, i):
        p, x = b[i - 1], b[i]
        if tr_up(b, i - 2) and white(p) and black(x) and engulf(x, p):
            return (x["c"], x["h"])
    ekle("Yutan Ayı", "Bearish Engulfing", -1, 2, f_eng_a)

    def f_har_a(b, i):
        p, x = b[i - 1], b[i]
        if tr_up(b, i - 2) and white(p) and long_b(b, i - 1, p) and black(x) and inside(p, x):
            return (min(x["c"], mid(p)), max(p["h"], x["h"]))
    ekle("Hamile Ayı", "Bearish Harami", -1, 2, f_har_a)

    def f_harx_a(b, i):
        p, x = b[i - 1], b[i]
        if tr_up(b, i - 2) and white(p) and is_doji(x) and inside(p, x):
            teyit = b_bot(p) if short_b(b, i - 1, p) else min(x["c"], mid(p))
            return (teyit, max(p["h"], x["h"]))
    ekle("Kros Hamile Ayı", "Bearish Harami Cross", -1, 2, f_harx_a)

    def f_shoot(b, i):
        p, x = b[i - 1], b[i]
        if tr_up(b, i - 2) and white(p) and body(x) > 0 and up_s(x) >= 2 * body(x) and lo_s(x) <= 0.3 * body(x) + 1e-12:
            return (b_bot(x), x["h"])
    ekle("Kayan Yıldız Ayı", "Bearish Shooting Star", -1, 2, f_shoot)

    def f_cloud(b, i):
        p, x = b[i - 1], b[i]
        if (tr_up(b, i - 2) and white(p) and long_b(b, i - 1, p) and black(x)
                and x["o"] > p["h"] * 0.999 and p["o"] < x["c"] < mid(p)):
            return (x["c"], x["h"])
    ekle("Kara Bulut Ayı", "Bearish Dark Cloud Cover", -1, 2, f_cloud)

    def f_dstar_a(b, i):
        p, x = b[i - 1], b[i]
        if tr_up(b, i - 2) and white(p) and is_doji(x) and b_bot(x) > p["c"]:
            return ((p["c"] + b_bot(x)) / 2, max(p["h"], x["h"]))
    ekle("Doji Yıldız Ayı", "Bearish Doji Star", -1, 2, f_dstar_a)

    def f_meet_a(b, i):
        p, x = b[i - 1], b[i]
        if tr_up(b, i - 2) and white(p) and black(x) and x["o"] > p["c"] * 1.01 and eq(x["c"], p["c"], p["c"]):
            return (x["c"], x["h"])
    ekle("Değen Mumlar Ayı", "Bearish Meeting Line", -1, 2, f_meet_a)

    def f_hawk(b, i):
        p, x = b[i - 1], b[i]
        if tr_up(b, i - 2) and white(p) and long_b(b, i - 1, p) and white(x) and inside(p, x):
            return (min(x["c"], mid(p)), max(p["h"], x["h"]))
    ekle("İnen Şahin Ayı", "Bearish Descending Hawk", -1, 2, f_hawk)

    def f_mhigh(b, i):
        p, x = b[i - 1], b[i]
        if tr_up(b, i - 2) and white(p) and white(x) and eq(p["c"], x["c"], p["c"]):
            return (mid(p), max(p["h"], x["h"]))
    ekle("Çakışan Tepe Ayı", "Bearish Matching High", -1, 2, f_mhigh)

    def f_kick_a(b, i):
        p, x = b[i - 1], b[i]
        if white(p) and maru(b, i - 1, p) and black(x) and maru(b, i, x) and x["o"] < p["o"]:
            return (x["c"], x["h"])
    ekle("Tepen Mumlar Ayı", "Bearish Kicking", -1, 2, f_kick_a)

    def f_crow(b, i):
        p, x = b[i - 1], b[i]
        if tr_up(b, i - 2) and white(p) and black(x) and x["o"] < p["c"] and x["c"] < p["o"]:
            return (x["c"], x["h"])
    ekle("Kara Karga Ayı", "Bearish One Black Crow", -1, 2, f_crow)

    return K

KATALOG = katalog()

def formasyon_durumu(bars, i, yon, teyit, stop, cbc=4):
    """Matriks durum döngüsü — seviyeler KAPANIŞ ile aşılmalı."""
    confirmed = False
    for k in range(i + 1, len(bars)):
        c = bars[k]["c"]
        if not confirmed:
            if k > i + cbc:
                break
            if (c > teyit) if yon > 0 else (c < teyit):
                confirmed = True
        else:
            if (c < stop) if yon > 0 else (c > stop):
                return "fail"
    return "ok" if confirmed else "not"

DURUM_TR = {"not": "⏳ Onaylanmamış", "ok": "✅ Onaylanmış", "fail": "❌ Onaylanmış & Başarısız"}

# ----------------------------------------------------------------
# Veri çekme ve analiz
# ----------------------------------------------------------------
@st.cache_data(ttl=300, show_spinner=False)
def veri_cek(sembol, periyot, aralik):
    df = yf.download(f"{sembol}.IS", period=periyot, interval=aralik,
                     auto_adjust=True, progress=False)
    if df is None or df.empty:
        return None
    if isinstance(df.columns, pd.MultiIndex):
        df.columns = df.columns.get_level_values(0)
    df = df.rename(columns=str.lower)
    if "volume" not in df.columns:
        df["volume"] = 0
    df = df[["open", "high", "low", "close", "volume"]].dropna(subset=["close"])
    return df

def analiz(df):
    bars = [{"o": r.open, "h": r.high, "l": r.low, "c": r.close} for r in df.itertuples()]
    n = len(bars)
    close = df["close"]

    delta = close.diff()
    gain = delta.clip(lower=0).rolling(14).mean()
    loss = (-delta.clip(upper=0)).rolling(14).mean()
    rs = gain / loss.replace(0, float("nan"))
    rsi = float((100 - 100 / (1 + rs)).iloc[-1]) if n > 15 else 50.0
    if math.isnan(rsi):
        rsi = 50.0

    ma20 = float(close.rolling(20).mean().iloc[-1]) if n >= 20 else float(close.mean())
    ma50 = float(close.rolling(50).mean().iloc[-1]) if n >= 50 else float(close.mean())
    win = bars[-40:] if n >= 40 else bars
    support = min(x["l"] for x in win)
    resistance = max(x["h"] for x in win)

    bulgular = []
    for i in range(20, n):
        for f in KATALOG:
            if i - f["nb"] < 10:
                continue
            r = f["test"](bars, i)
            if r:
                teyit, stop = r
                bulgular.append({
                    "f": f, "i": i, "teyit": teyit, "stop": stop,
                    "tarih": df.index[i],
                    "durum": formasyon_durumu(bars, i, f["yon"], teyit, stop),
                })

    mum_net = 0
    for bl in bulgular:
        if bl["i"] < n - 10:
            continue
        w = 2 if bl["durum"] == "ok" else (-1 if bl["durum"] == "fail" else 1)
        mum_net += bl["f"]["yon"] * w

    price = bars[-1]["c"]
    skor = 50
    skor += 9 if ma20 > ma50 else -9
    skor += 11 if rsi < 30 else (-11 if rsi > 70 else 0)
    skor += max(-10, min(10, mum_net * 3))
    aralik_g = (resistance - support) or 1
    skor += ((price - support) / aralik_g - 0.5) * -8
    skor = int(max(5, min(95, round(skor))))

    return {"bars": bars, "rsi": rsi, "ma20": ma20, "ma50": ma50,
            "support": support, "resistance": resistance,
            "bulgular": bulgular, "mum_net": mum_net, "skor": skor, "price": price}

# ----------------------------------------------------------------
# Arayüz
# ----------------------------------------------------------------






# ----------------------------------------------------------------
# Yardımcılar
# ----------------------------------------------------------------
import json
import time as _time
import xml.etree.ElementTree as ET
from email.utils import parsedate_to_datetime
from streamlit.components.v1 import html as st_html

UA = {"User-Agent": "Mozilla/5.0"}

@st.cache_data(ttl=1200, show_spinner=False)
def toplu_veri(kodlar):
    """Tüm hisseler için 6 aylık kapanış/hacim: fiyat, %, hacim ve hızlı AI kararı."""
    out = {}
    kodlar = list(kodlar)
    for i in range(0, len(kodlar), 100):
        parca = kodlar[i:i + 100]
        try:
            df = yf.download([k + ".IS" for k in parca], period="6mo", interval="1d",
                             auto_adjust=True, progress=False, group_by="ticker", threads=True)
        except Exception:
            continue
        for k in parca:
            try:
                sub = df[k + ".IS"] if len(parca) > 1 else df
                c = sub["Close"].dropna()
                v = sub["Volume"].reindex(c.index).fillna(0)
                if len(c) < 2:
                    continue
                son, once = float(c.iloc[-1]), float(c.iloc[-2])
                pct = (son - once) / once * 100
                hacim = int(v.iloc[-1])
                sk = 50
                if len(c) >= 55:
                    ma20 = float(c.rolling(20).mean().iloc[-1])
                    ma50 = float(c.rolling(50).mean().iloc[-1])
                    sk += 12 if ma20 > ma50 else -12
                if len(c) >= 16:
                    d = c.diff()
                    g = float(d.clip(lower=0).rolling(14).mean().iloc[-1])
                    l = float((-d.clip(upper=0)).rolling(14).mean().iloc[-1])
                    rsi = 100.0 if l == 0 else 100 - 100 / (1 + (g / l))
                    sk += 10 if rsi < 30 else (-10 if rsi > 70 else 0)
                if len(c) >= 21:
                    sk += 6 if son > float(c.iloc[-21]) else -6
                sk = max(5, min(95, sk))
                out[k] = {"f": round(son, 2), "p": round(pct, 2), "h": hacim,
                          "ai": karar_ver(sk)}
            except Exception:
                continue
    return out

SEKTOR_EN = {"Financial Services": "Finans", "Industrials": "Sanayi",
             "Technology": "Teknoloji", "Consumer Cyclical": "Tüketim",
             "Consumer Defensive": "Temel Tüketim", "Basic Materials": "Hammadde",
             "Energy": "Enerji", "Healthcare": "Sağlık", "Utilities": "Kamu Hizm.",
             "Real Estate": "GYO", "Communication Services": "İletişim"}

@st.cache_resource
def temel_depo():
    return {}

def temel_doldur(kodlar):
    """Her sayfa açılışında ~15 hissenin temel verisini (piy. değ., F/K, sektör,
    isim) doldurur; depo kalıcıdır ve zamanla tüm liste tamamlanır."""
    depo = temel_depo()
    basla = _time.time()
    sayac = 0
    for k in kodlar:
        if k in depo:
            continue
        if sayac >= 15 or _time.time() - basla > 12:
            break
        try:
            info = yf.Ticker(k + ".IS").info
            mc = info.get("marketCap")
            fk = info.get("trailingPE")
            sec = info.get("sector")
            depo[k] = {"mc": round(mc / 1e9, 2) if mc else None,
                       "fk": round(fk, 1) if fk else None,
                       "sec": SEKTOR_EN.get(sec, sec),
                       "n": info.get("longName") or info.get("shortName")}
        except Exception:
            depo[k] = {"mc": None, "fk": None, "sec": None, "n": None}
        sayac += 1
    return depo

@st.cache_data(ttl=600, show_spinner=False)
def endeksler():
    out = []
    for ad, s in [("BIST 100", "XU100.IS"), ("BIST 30", "XU030.IS"),
                  ("KATILIM", "XKTUM.IS")]:
        try:
            d = yf.download(s, period="7d", interval="1d",
                            auto_adjust=True, progress=False)["Close"].dropna()
            if hasattr(d, "columns"):
                d = d.iloc[:, 0]
            if len(d) >= 2:
                out.append({"ad": ad, "v": float(d.iloc[-1]),
                            "p": (float(d.iloc[-1]) / float(d.iloc[-2]) - 1) * 100})
        except Exception:
            continue
    return out

@st.cache_data(ttl=900, show_spinner=False)
def haberler():
    kaynaklar = [("Bloomberg HT", "https://www.bloomberght.com/rss"),
                 ("AA Ekonomi", "https://www.aa.com.tr/tr/rss/default?cat=ekonomi"),
                 ("Dünya", "https://www.dunya.com/rss"),
                 ("Habertürk", "https://www.haberturk.com/rss/ekonomi.xml"),
                 ("Milliyet", "https://www.milliyet.com.tr/rss/rssnew/ekonomi.xml"),
                 ("Sabah", "https://www.sabah.com.tr/rss/ekonomi.xml"),
                 ("NTV", "https://www.ntv.com.tr/ekonomi.rss")]
    out = []
    for ad, url in kaynaklar:
        try:
            r = requests.get(url, headers=UA, timeout=8)
            r.raise_for_status()
            root = ET.fromstring(r.content)
            for item in list(root.iter("item"))[:4]:
                baslik = (item.findtext("title") or "").strip()
                link = (item.findtext("link") or "").strip()
                try:
                    saat = parsedate_to_datetime(item.findtext("pubDate") or "").strftime("%d.%m %H:%M")
                except Exception:
                    saat = ""
                if baslik:
                    out.append({"b": baslik, "l": link, "s": saat, "k": ad})
        except Exception:
            continue
    return out[:20]

def karar_ver(skor):
    if skor >= 70: return "GÜÇLÜ AL"
    if skor >= 57: return "AL"
    if skor > 43:  return "NÖTR"
    if skor > 30:  return "SAT"
    return "GÜÇLÜ SAT"

def yorum_yaz(A):
    p = []
    p.append("Orta vadeli trend yukarı yönlü görünüyor." if A["ma20"] > A["ma50"]
             else "Orta vadeli trend zayıf seyrediyor.")
    if A["rsi"] > 70: p.append("Momentum aşırı ısınmış; kısa vadede kâr satışı gelebilir.")
    elif A["rsi"] < 30: p.append("Hisse aşırı satılmış bölgede; tepki yükselişi ihtimali güçleniyor.")
    else: p.append("Momentum dengeli seyrediyor.")
    if A["mum_net"] >= 2: p.append("Son barlardaki fiyat davranışı alıcıların güçlendiğine işaret ediyor.")
    elif A["mum_net"] <= -2: p.append("Son barlardaki fiyat davranışı satış baskısının arttığına işaret ediyor.")
    else: p.append("Son barlarda fiyat davranışı net bir yön sinyali üretmiyor.")
    yak = (A["price"] - A["support"]) / ((A["resistance"] - A["support"]) or 1)
    if yak > 0.75: p.append(f"Fiyat {A['resistance']:.2f} direncine yakın; kırılım gelmeden yeni alım riskli olabilir.")
    elif yak < 0.25: p.append(f"Fiyat {A['support']:.2f} desteğine yakın; destek korunursa risk/getiri alıcı lehine.")
    else: p.append(f"Fiyat {A['support']:.2f} desteği ile {A['resistance']:.2f} direnci arasında dengeleniyor.")
    return " ".join(p)

ESIK = {"Düşük": (70, 45), "Orta": (62, 43), "Yüksek": (57, 40)}
TFDEF = [("15m", "15 Dk", "1mo", "15m", None), ("1h", "1 Saat", "3mo", "1h", None),
         ("4h", "4 Saat", "6mo", "1h", "4h"), ("1d", "1 Gün", "1y", "1d", None),
         ("1wk", "1 Hafta", "5y", "1wk", None), ("1mo", "1 Ay", "max", "1mo", None),
         ("1y", "1 Yıl", "max", "1mo", "YE")]

def yeniden_ornekle(df, kural):
    return df.resample(kural).agg({"open": "first", "high": "max", "low": "min",
                                   "close": "last", "volume": "sum"}).dropna()

@st.cache_resource
def durum():
    return {"bakiye": 10000.0, "baslangic": 10000.0, "poz": {}, "gunluk": [],
            "izleme": ["ASELS", "THYAO", "BIMAS", "EREGL", "SISE", "FROTO", "TCELL", "TUPRS"],
            "risk": "Orta", "tutar": 250.0, "aktif": False}
G = durum()

def bot_tara():
    esik_al, esik_sat = ESIK[G["risk"]]
    yeni = 0
    for kod in G["izleme"]:
        df = veri_cek(kod, "6mo", "1d")
        if df is None or len(df) < 30:
            continue
        A = analiz(df)
        fiyat = A["price"]
        zn = pd.Timestamp.now()
        if kod in G["poz"] and A["skor"] <= esik_sat:
            p = G["poz"].pop(kod)
            kz = (fiyat - p["giris"]) * p["adet"]
            G["bakiye"] += p["adet"] * fiyat
            G["gunluk"].append({"z": zn.strftime("%d.%m %H:%M"), "iso": zn.strftime("%Y-%m-%d"),
                                "k": kod, "y": "SAT", "a": p["adet"], "f": round(fiyat, 2),
                                "kz": round(kz, 2), "g": f"Skor {A['skor']}"})
            yeni += 1
        elif kod not in G["poz"] and A["skor"] >= esik_al and G["bakiye"] >= G["tutar"]:
            adet = int(G["tutar"] // fiyat)
            if adet >= 1:
                G["bakiye"] -= adet * fiyat
                G["poz"][kod] = {"adet": adet, "giris": fiyat}
                G["gunluk"].append({"z": zn.strftime("%d.%m %H:%M"), "iso": zn.strftime("%Y-%m-%d"),
                                    "k": kod, "y": "AL", "a": adet, "f": round(fiyat, 2),
                                    "kz": None, "g": f"Skor {A['skor']}"})
                yeni += 1
    return yeni

# ----------------------------------------------------------------
# Sayfa: sol menü (yerel) + bağlamsal kontroller + gömülü ekran
# ----------------------------------------------------------------
st.set_page_config(page_title="Vertual Market", page_icon="📈", layout="wide",
                   initial_sidebar_state="collapsed")
st.markdown("""<style>
#MainMenu,header,footer{visibility:hidden}
.block-container{padding:0.3rem 0.6rem;max-width:100%}
div[data-testid="stExpander"]{background:#0C1524;border:1px solid #1B2A3F;border-radius:12px}
div[data-testid="stRadio"] > div{flex-direction:column;gap:6px}
div[data-testid="stRadio"] label{background:#0C1524;border:1px solid #1B2A3F;border-radius:10px;
padding:11px 12px;width:100%;cursor:pointer}
div[data-testid="stRadio"] label:has(input:checked){border-left:3px solid #2EBD85;background:#101B2E}
.vm-brand{font-family:Georgia,serif;font-size:22px;font-weight:700;letter-spacing:3px;
background:linear-gradient(135deg,#F7E2A5,#E4B95B 45%,#B98730);
-webkit-background-clip:text;background-clip:text;-webkit-text-fill-color:transparent}
</style>""", unsafe_allow_html=True)

tum_kodlar = kap_tum_liste() or sorted(u[0] for u in UNIVERSE)

# --- marka + sol menü + içerik düzeni ---
LOGO = """<svg width="58" height="58" viewBox="0 0 60 60" style="filter:drop-shadow(0 2px 10px rgba(228,185,91,.35))">
<defs><linearGradient id="au" x1="0" y1="0" x2="1" y2="1">
<stop offset="0" stop-color="#F7E2A5"/><stop offset=".5" stop-color="#E4B95B"/>
<stop offset="1" stop-color="#B98730"/></linearGradient></defs>
<circle cx="30" cy="30" r="27.5" fill="#0B1322" stroke="url(#au)" stroke-width="1.8"/>
<circle cx="30" cy="30" r="23" fill="none" stroke="url(#au)" stroke-width=".7" opacity=".5"/>
<path d="M17 20 L23.5 40 L30 20" stroke="url(#au)" stroke-width="3.4" fill="none"
 stroke-linecap="round" stroke-linejoin="round"/>
<path d="M30 40 L30 20 L36.5 32 L43 20 L43 40" stroke="url(#au)" stroke-width="3.4" fill="none"
 stroke-linecap="round" stroke-linejoin="round"/>
<circle cx="30" cy="12.5" r="1.4" fill="#E4B95B"/></svg>"""

def pct_span(p):
    renk = "#2EBD85" if p >= 0 else "#F6465D"
    ok = "▲" if p >= 0 else "▼"
    return f"<span style='color:{renk};font-size:12px'>{ok} %{abs(p):.2f}</span>"

edx = endeksler()
edx_html = "".join(
    f"<div style='text-align:right;min-width:96px'>"
    f"<div style='color:#8496AD;font-size:11px;letter-spacing:1px'>{e['ad']}</div>"
    f"<div style='font-family:monospace;font-weight:700;font-size:15px'>"
    f"{e['v']:,.0f}".replace(",", ".") + f"</div>{pct_span(e['p'])}</div>"
    for e in edx)
st.markdown(
    "<div style='display:flex;align-items:center;gap:18px;padding:8px 6px 16px;flex-wrap:wrap'>"
    + LOGO +
    "<div style='line-height:1.25'><div class='vm-brand' style='font-size:26px'>VERTUAL&nbsp;MARKET</div>"
    "<div style='color:#8496AD;font-size:11.5px;letter-spacing:3px'>BIST ANALİZ TERMİNALİ</div></div>"
    f"<div style='margin-left:auto;display:flex;gap:26px;flex-wrap:wrap'>{edx_html}</div></div>",
    unsafe_allow_html=True)
solc, sagc = st.columns([1.15, 5.85])

with solc:
    view = st.radio("Menü", ["📈 Piyasa", "🤖 Bot", "💼 Portföy", "🧾 İşlemler", "⚙️ Ayarlar"],
                    label_visibility="collapsed")
view = {"📈 Piyasa": "piyasa", "🤖 Bot": "bot", "💼 Portföy": "portfoy",
        "🧾 İşlemler": "islemler", "⚙️ Ayarlar": "ayarlar"}[view]

with sagc:
    # ---- bağlamsal kontroller ----
    sym = st.session_state.get("sym", "THYAO")
    if sym not in tum_kodlar:
        sym = tum_kodlar[0]

    if view in ("piyasa", "bot"):
        sym = st.selectbox("Hisse Seç — tüm BIST hisseleri (yazarak arayabilirsin)",
                           tum_kodlar, index=tum_kodlar.index(sym),
                           format_func=lambda k: f"{k} — {ISIM_SOZLUGU.get(k, '')}".rstrip(" —"))
        st.session_state["sym"] = sym

    if view == "bot":
        with st.expander("⚡ Bot Kontrolleri", expanded=True):
            b1, b2, b3 = st.columns([1, 1, 1])
            G["aktif"] = b1.toggle("Bot Aktif (sanal)", value=G["aktif"])
            G["risk"] = b2.radio("Risk", ["Düşük", "Orta", "Yüksek"],
                                 index=["Düşük", "Orta", "Yüksek"].index(G["risk"]),
                                 horizontal=True)
            G["tutar"] = b3.number_input("İşlem tutarı ₺", 50.0, 100000.0, G["tutar"], step=50.0)
            G["izleme"] = st.multiselect("Botun izlediği hisseler (en çok 30)", tum_kodlar,
                                         default=[k for k in G["izleme"] if k in tum_kodlar],
                                         max_selections=30)
            if st.button("🔍 Şimdi Tara ve İşlem Yap", type="primary", use_container_width=True):
                if not G["aktif"]:
                    st.warning("Önce botu aktif et.")
                elif not G["izleme"]:
                    st.warning("İzleme listesi boş.")
                else:
                    try:
                        with st.spinner("Bot tarıyor..."):
                            n = bot_tara()
                        st.success(f"{n} yeni sanal işlem yapıldı." if n else "Eşiği aşan sinyal yok.")
                    except Exception as e:
                        st.error(f"Tarama sırasında hata oluştu: {type(e).__name__}: {e}")

    if view == "ayarlar":
        with st.expander("⚙️ Portföy Ayarları", expanded=True):
            st.write("Her kullanıcı 10.000 ₺ sanal kredi ile başlar.")
            if st.button("♻️ Portföyü Sıfırla (10.000 ₺)", use_container_width=True):
                G.update({"bakiye": 10000.0, "baslangic": 10000.0, "poz": {}, "gunluk": []})
                st.success("Sanal portföy 10.000 ₺ ile sıfırlandı.")

    # ---- veri ----
    def bars_json(d, unix):
        out = []
        for t, r in d.iterrows():
            out.append({"time": (int(t.timestamp()) if unix else t.strftime("%Y-%m-%d")),
                        "open": round(float(r.open), 2), "high": round(float(r.high), 2),
                        "low": round(float(r.low), 2), "close": round(float(r.close), 2),
                        "volume": int(r.volume)})
        return out

    def ma_json(d, n, unix):
        if len(d) <= n + 2:
            return []
        s = d["close"].rolling(n).mean().dropna()
        return [{"time": (int(t.timestamp()) if unix else t.strftime("%Y-%m-%d")),
                 "value": round(float(v), 2)} for t, v in s.items()]

    piyasa = {}
    tfdata, tford = {}, []
    hbr = []
    A = None
    dfb = None
    if view in ("piyasa", "bot", "portfoy"):
        with st.spinner("Veriler yükleniyor (ilk açılış 1-2 dk sürebilir)..."):
            piyasa = toplu_veri(tuple(tum_kodlar))
            dfb = veri_cek(sym, "6mo", "1d")
            if view == "piyasa":
                hbr = haberler()
                for key, ad, per, itv, kural in TFDEF:
                    try:
                        d = veri_cek(sym, per, itv)
                        if d is None or len(d) < 5:
                            continue
                        if kural:
                            d = yeniden_ornekle(d, kural)
                        unix = itv in ("15m", "1h") and kural != "YE"
                        tfdata[key] = {"ad": ad, "bars": bars_json(d, unix),
                                       "ma20": ma_json(d, 20, unix), "ma50": ma_json(d, 50, unix)}
                        tford.append(key)
                    except Exception:
                        continue
        A = analiz(dfb) if (dfb is not None and len(dfb) >= 30) else None

    temel = temel_doldur(list(ISIM_SOZLUGU) + [k for k in tum_kodlar if k not in ISIM_SOZLUGU]) if view == "piyasa" else {}
    SEKTOR = {u[0]: u[3] for u in UNIVERSE}

    liste_kodlar = tum_kodlar

    pozisyonlar = []
    for k, p in G["poz"].items():
        g2 = piyasa.get(k, {}).get("f", p["giris"])
        pozisyonlar.append({"k": k, "a": p["adet"], "giris": round(p["giris"], 2),
                            "guncel": round(g2, 2), "kz": round((g2 - p["giris"]) * p["adet"], 2)})
    kapali = [x for x in G["gunluk"] if x["y"] == "SAT"]
    karli = sum(1 for x in kapali if (x["kz"] or 0) > 0)
    poz_deger = sum(p["a"] * p["guncel"] for p in pozisyonlar)
    toplam = G["bakiye"] + poz_deger
    pv = piyasa.get(sym, {})

    payload = {
        "sym": sym, "isim": ISIM_SOZLUGU.get(sym, ""), "katd": katilim_etiketi(sym),
        "view": view,
        "fiyat": pv.get("f"), "pct": pv.get("p"),
        "karar": karar_ver(A["skor"]) if A else "VERİ YOK",
        "skor": A["skor"] if A else None,
        "yorum": yorum_yaz(A) if A else "Bu kod için fiyat verisi bulunamadı.",
        "destek": round(A["support"], 2) if A else None,
        "direnc": round(A["resistance"], 2) if A else None,
        "tford": tford, "tfdata": tfdata,
        "barsB": bars_json(dfb, False) if A else [],
        "maB20": ma_json(dfb, 20, False) if A else [], "maB50": ma_json(dfb, 50, False) if A else [],
        "markers": [{"time": x["iso"], "y": x["y"]} for x in G["gunluk"] if x["k"] == sym],
        "stocks": [{"k": k,
                    "n": ISIM_SOZLUGU.get(k) or (temel.get(k, {}).get("n") or ""),
                    "katd": katilim_etiketi(k),
                    "f": piyasa.get(k, {}).get("f"), "p": piyasa.get(k, {}).get("p"),
                    "h": piyasa.get(k, {}).get("h"), "ai": piyasa.get(k, {}).get("ai"),
                    "mc": temel.get(k, {}).get("mc"), "fk": temel.get(k, {}).get("fk"),
                    "sec": SEKTOR.get(k) or temel.get(k, {}).get("sec")}
                   for k in liste_kodlar] if view == "piyasa" else [],
        "haberler": hbr,
        "poz": pozisyonlar, "gunluk": list(reversed(G["gunluk"]))[:60],
        "perf": {"kz": round(sum((x["kz"] or 0) for x in kapali), 2), "karli": karli,
                 "kapanan": len(kapali),
                 "oran": round(karli / len(kapali) * 100) if kapali else None},
        "ayar": {"aktif": G["aktif"], "risk": G["risk"], "tutar": G["tutar"],
                 "izleme": G["izleme"], "bakiye": round(G["bakiye"], 2),
                 "baslangic": G["baslangic"], "toplam": round(toplam, 2),
                 "pozdeger": round(poz_deger, 2)},
    }

    HTML = r"""<!DOCTYPE html><html><head><meta charset="utf-8">
<script src="https://unpkg.com/lightweight-charts@4.1.3/dist/lightweight-charts.standalone.production.js"></script>
<style>
:root{--bg:#060D17;--card:#0C1524;--card2:#101B2E;--line:#1B2A3F;--tx:#E7EDF5;--mut:#8496AD;
--grn:#2EBD85;--red:#F6465D;--gold:#E4B95B}
*{box-sizing:border-box;margin:0;font-family:Inter,'Segoe UI',system-ui,sans-serif}
body{background:var(--bg);color:var(--tx);padding:2px}
.mut{color:var(--mut);font-size:13px}
.card{background:var(--card);border:1px solid var(--line);border-radius:14px;padding:14px;margin-bottom:14px}
.h{font-size:14px;font-weight:700;margin-bottom:10px;display:flex;align-items:center;gap:8px;flex-wrap:wrap}
table{width:100%;border-collapse:collapse;font-size:12.5px}
th{color:var(--mut);text-align:left;font-weight:500;padding:6px;border-bottom:1px solid var(--line);white-space:nowrap}
td{padding:7px 6px;border-bottom:1px solid var(--line);white-space:nowrap}
tr.sec:hover{background:var(--card2)}
.grn{color:var(--grn)}.red{color:var(--red)}.gold{color:var(--gold)}
.btn{background:var(--card2);border:1px solid var(--line);color:var(--tx);border-radius:10px;
padding:9px 13px;cursor:pointer;font-size:13px;user-select:none}
.tfb{padding:6px 11px;font-size:12.5px;border-radius:8px}
.tfb.on{background:var(--grn);color:#04110B;border:none;font-weight:700}
input,select{background:var(--card2);border:1px solid var(--line);color:var(--tx);
border-radius:10px;padding:9px 12px;font-size:13.5px}
.kv{display:flex;justify-content:space-between;padding:8px 0;font-size:13.5px;border-bottom:1px dashed var(--line)}
.verdict{font-size:15px;font-weight:800;padding:6px 14px;border-radius:9px;display:inline-block}
.scroll{max-height:420px;overflow:auto}
::-webkit-scrollbar{width:8px;height:8px}::-webkit-scrollbar-thumb{background:var(--line);border-radius:4px}
.hbr{display:flex;gap:10px;padding:9px 4px;border-bottom:1px solid var(--line);align-items:baseline}
.hbr a{color:var(--tx);text-decoration:none;font-size:13.5px;line-height:1.45}
.hbr a:hover{color:var(--gold)}
.err{background:rgba(246,70,93,.12);border:1px solid var(--red);border-radius:10px;
padding:10px 12px;font-size:13px;margin-bottom:12px}
.warn{color:var(--mut);font-size:11.5px;line-height:1.55;margin-top:8px}
.fbig{font-size:20px;font-weight:800;font-family:ui-monospace,monospace}
</style></head><body>
<div id="jshata"></div>

<div id="v_piyasa" style="__D_piyasa__">
  <div class="card">
    <div class="h"><span id="pg_baslik"></span><span id="pg_fiyat" class="fbig" style="margin-left:6px"></span>
      <span id="pg_pct" style="font-size:14px"></span></div>
    <div class="h" style="margin-top:2px">
      <span style="display:flex;gap:5px;flex-wrap:wrap" id="tfbtns"></span>
      <span style="margin-left:auto;display:flex;gap:5px;align-items:center">
        <span class="mut" id="d_info"></span>
        <button class="btn tfb" id="d_trend">✏️ Trend</button>
        <button class="btn tfb" id="d_yatay">─ Yatay</button>
        <button class="btn tfb" id="d_sil">🗑 Temizle</button></span></div>
    <div id="chart_p" style="height:410px"></div>
    <div class="warn">✏️ Trend: grafikte iki noktaya dokun · ─ Yatay: bir noktaya dokun ·
    Zaman dilimi değişince çizimler temizlenir.</div></div>
  <div class="card"><div class="h">📰 Son Dakika Piyasa Haberleri</div><div id="haberler"></div>
    <div class="warn">Kaynaklar: Bloomberg HT · AA Ekonomi · Dünya · Habertürk · Milliyet · Sabah · NTV (RSS).</div></div>
  <div class="card"><div class="h"><span id="liste_baslik">Hisse Listesi</span>
    <input id="ara" placeholder="Hisse ara..." style="max-width:260px;margin-left:auto">
    <select id="filtre"><option value="t">Tümü</option>
    <option value="u">◈ Katılıma Uygun</option><option value="d">Uygun Değil</option></select></div>
    <div class="scroll"><table><thead><tr><th>Kod</th><th>Şirket</th><th>Katılım</th><th>Fiyat ₺</th>
    <th>Piy. Değ. (mlr₺)</th><th>Günlük %</th><th>Hacim</th><th>F/K</th><th>Sektör</th>
    <th>Analist (AI)</th></tr></thead><tbody id="tbl"></tbody></table></div>
    <div class="warn">Hisse açmak için üstteki "Hisse Seç" kutusunu kullan. Analist (AI) kural tabanlı otomatik derecelendirmedir; yatırım tavsiyesi değildir.</div></div>
</div>

<div id="v_bot" style="__D_bot__">
  <div style="display:flex;gap:14px;flex-wrap:wrap">
    <div style="flex:2.2;min-width:340px">
      <div class="card"><div class="h" id="bg_baslik"></div><div id="chart_b" style="height:380px"></div>
        <div class="warn">Destek/direnç, MA çizgileri ve AL/SAT işaretleri botun kendi analizidir.</div></div>
      <div class="card"><div class="h">🤖 Bot Değerlendirmesi <span id="verdict" class="verdict"></span></div>
        <div id="yorum" style="font-size:14px;line-height:1.7"></div>
        <div class="warn">Kural tabanlı otomatik özet; yatırım tavsiyesi değildir. Veri ~15 dk gecikmelidir.</div></div>
      <div style="display:flex;gap:14px;flex-wrap:wrap">
        <div class="card" style="flex:1;min-width:280px"><div class="h">Açık İşlemler</div>
          <table><thead><tr><th>Hisse</th><th>Adet</th><th>Giriş</th><th>Güncel</th><th>K/Z ₺</th></tr></thead>
          <tbody id="poztbl"></tbody></table></div>
        <div class="card" style="flex:1;min-width:280px"><div class="h">Bot Günlüğü</div>
          <div class="scroll" style="max-height:230px"><table><thead><tr><th>Zaman</th><th>Hisse</th>
          <th>Yön</th><th>Fiyat</th><th>K/Z</th></tr></thead><tbody id="logtbl"></tbody></table></div></div>
      </div></div>
    <div style="flex:1;min-width:280px">
      <div class="card"><div class="h">🤖 Otomatik Al-Sat Botu <span class="mut">(SANAL)</span></div>
        <div class="kv"><span>Durum</span><span id="b_durum"></span></div>
        <div class="kv"><span>Strateji</span><span>Sinyal Skoru</span></div>
        <div class="kv"><span>Risk</span><span id="b_risk"></span></div>
        <div class="kv"><span>İşlem Tutarı</span><span id="b_tutar"></span></div>
        <div style="margin-top:12px">
          <div class="kv"><span>Gerçekleşen K/Z</span><span id="p_kz"></span></div>
          <div class="kv"><span>Kârlı İşlem</span><span id="p_karli"></span></div>
          <div class="kv"><span>Kapanan İşlem</span><span id="p_kapanan"></span></div>
          <div class="kv"><span>Başarı Oranı</span><span id="p_oran" class="grn"></span></div></div>
        <div class="warn" style="margin-top:12px">Başlat / Tara / risk / tutar / izleme, yukarıdaki
        <b>⚡ Bot Kontrolleri</b> panelindedir. Bot sanal parayla işlem yapar, gerçek emir göndermez.</div></div>
    </div>
  </div>
</div>

<div id="v_portfoy" style="__D_portfoy__">
  <div class="card"><div class="h">💼 Sanal Portföy</div>
    <div class="kv"><span>Nakit</span><span id="pf_nakit"></span></div>
    <div class="kv"><span>Pozisyon Değeri</span><span id="pf_poz"></span></div>
    <div class="kv"><span>Toplam</span><span id="pf_top"></span></div></div>
  <div class="card"><div class="h">Açık Pozisyonlar</div>
    <table><thead><tr><th>Hisse</th><th>Adet</th><th>Giriş</th><th>Güncel</th><th>K/Z ₺</th></tr></thead>
    <tbody id="poztbl2"></tbody></table></div>
</div>

<div id="v_islemler" class="card" style="__D_islemler__"><div class="h">🧾 Tüm İşlemler</div>
  <div class="scroll"><table><thead><tr><th>Zaman</th><th>Hisse</th><th>Yön</th><th>Adet</th>
  <th>Fiyat</th><th>K/Z ₺</th><th>Gerekçe</th></tr></thead><tbody id="logtbl2"></tbody></table></div></div>

<div id="v_ayarlar" class="card" style="__D_ayarlar__"><div class="h">⚙️ Bilgi</div>
  <div class="kv"><span>Bot durumu</span><span id="a_durum"></span></div>
  <div class="kv"><span>Risk seviyesi</span><span id="a_risk"></span></div>
  <div class="kv"><span>İşlem tutarı</span><span id="a_tutar"></span></div>
  <div class="kv"><span>İzleme listesi</span><span id="a_izleme" style="text-align:right;max-width:60%"></span></div>
  <div class="warn" style="margin-top:12px">
  • Fiyatlar Yahoo Finance kaynaklıdır, ~15 dk gecikmelidir; hisse listesi KAP/Mynet'ten gelir.<br>
  • Katılım etiketleri alım öncesi resmî katılım endeksi listesinden doğrulanmalıdır.<br>
  • Bot sanal (kağıt) modda çalışır; hiçbir çıktı yatırım tavsiyesi değildir.</div></div>

<script>
window.onerror=function(m){var e=document.getElementById("jshata");
if(e)e.innerHTML='<div class="err">Arayüz hatası: '+m+' — bu mesajı geliştiriciye ilet.</div>';};
const D = __DATA__;
function fmt(x){return x==null?"—":x.toLocaleString("tr-TR",{minimumFractionDigits:2,maximumFractionDigits:2});}
function fmtB(x){return x==null?"—":x.toLocaleString("tr-TR");}
function pctHtml(p){if(p==null)return"—";const c=p>=0?"grn":"red";
return '<span class="'+c+'">'+(p>=0?"▲":"▼")+' %'+Math.abs(p).toFixed(2)+'</span>';}
function katHtml(kd){return kd==="uygun"?'<span class="grn">✔ Uygun</span>'
:kd==="disi"?'<span class="red">✖ Değil</span>':'<span class="mut">Belirsiz</span>';}
function aiHtml(a){if(!a)return"—";
const c=a.includes("AL")&&!a.includes("SAT")?"grn":(a.includes("SAT")?"red":"mut");
return '<span class="'+c+'" style="font-weight:700">'+a+'</span>';}
let GP=null;
function grafik(el,veri,sr,ma){const kutu=document.getElementById(el);if(!kutu)return null;kutu.innerHTML="";
if(!veri||!veri.bars||!veri.bars.length){kutu.innerHTML=
"<div class='mut' style='padding:40px;text-align:center'>Veri yok.</div>";return null;}
if(!window.LightweightCharts){kutu.innerHTML=
"<div class='mut' style='padding:40px;text-align:center'>Grafik kütüphanesi yüklenemedi; sayfayı yenile.</div>";return null;}
const ch=LightweightCharts.createChart(kutu,{
layout:{background:{color:"#0C1524"},textColor:"#8496AD"},
grid:{vertLines:{color:"#101B2E"},horzLines:{color:"#101B2E"}},
height:kutu.clientHeight||400,
timeScale:{borderColor:"#1B2A3F",timeVisible:true},rightPriceScale:{borderColor:"#1B2A3F"}});
const cs=ch.addCandlestickSeries({upColor:"#2EBD85",downColor:"#F6465D",
wickUpColor:"#2EBD85",wickDownColor:"#F6465D",borderVisible:false});
cs.setData(veri.bars);
const vol=ch.addHistogramSeries({priceScaleId:"",priceFormat:{type:"volume"}});
ch.priceScale("").applyOptions({scaleMargins:{top:0.85,bottom:0}});
vol.setData(veri.bars.map(b=>({time:b.time,value:b.volume,
color:b.close>=b.open?"rgba(46,189,133,.45)":"rgba(246,70,93,.45)"})));
if(ma&&veri.ma20&&veri.ma20.length)ch.addLineSeries({color:"#2EBD85",lineWidth:1}).setData(veri.ma20);
if(ma&&veri.ma50&&veri.ma50.length)ch.addLineSeries({color:"#F6465D",lineWidth:1}).setData(veri.ma50);
if(sr){if(D.destek)cs.createPriceLine({price:D.destek,color:"#2EBD85",lineStyle:2,title:"DESTEK"});
if(D.direnc)cs.createPriceLine({price:D.direnc,color:"#F6465D",lineStyle:2,title:"DİRENÇ"});
cs.setMarkers(D.markers.map(m=>({time:m.time,position:m.y==="AL"?"belowBar":"aboveBar",
color:m.y==="AL"?"#2EBD85":"#F6465D",shape:m.y==="AL"?"arrowUp":"arrowDown",text:m.y})));}
ch.timeScale().fitContent();return {ch:ch,cs:cs};}
if(D.view==="piyasa"){
let mod=null,ilk=null,cizgiler=[],yataylar=[];
const dInfo=document.getElementById("d_info");
function modAyarla(m){mod=(mod===m)?null:m;ilk=null;
document.getElementById("d_trend").classList.toggle("on",mod==="trend");
document.getElementById("d_yatay").classList.toggle("on",mod==="yatay");
dInfo.textContent=mod==="trend"?"1. noktaya dokun":(mod==="yatay"?"Bir noktaya dokun":"");}
document.getElementById("d_trend").addEventListener("click",()=>modAyarla("trend"));
document.getElementById("d_yatay").addEventListener("click",()=>modAyarla("yatay"));
document.getElementById("d_sil").addEventListener("click",function(){
if(!GP)return;
cizgiler.forEach(s=>{try{GP.ch.removeSeries(s)}catch(e){}});
yataylar.forEach(p=>{try{GP.cs.removePriceLine(p)}catch(e){}});
cizgiler=[];yataylar=[];ilk=null;modAyarla(null);dInfo.textContent="Temizlendi";
setTimeout(()=>{dInfo.textContent=""},1500);});
function cizimBagla(){if(!GP)return;
GP.ch.subscribeClick(function(param){
if(!mod||!param.time||!param.point)return;
const fiyat=GP.cs.coordinateToPrice(param.point.y);
if(fiyat==null)return;
if(mod==="yatay"){
yataylar.push(GP.cs.createPriceLine({price:fiyat,color:"#E4B95B",lineWidth:1,title:fiyat.toFixed(2)}));
modAyarla(null);}
else if(mod==="trend"){
if(!ilk){ilk={time:param.time,value:fiyat};dInfo.textContent="2. noktaya dokun";}
else{let a=ilk,b={time:param.time,value:fiyat};
if(a.time>b.time){const t=a;a=b;b=t;}
if(a.time!==b.time){const ls=GP.ch.addLineSeries({color:"#E4B95B",lineWidth:2,
priceLineVisible:false,lastValueVisible:false});
ls.setData([a,b]);cizgiler.push(ls);}
ilk=null;modAyarla(null);}}});}
let aktifTf=D.tford.includes("1d")?"1d":(D.tford[0]||null);
function cizP(k){if(!k)return;aktifTf=k;cizgiler=[];yataylar=[];ilk=null;
document.querySelectorAll(".tfsec").forEach(b=>b.classList.toggle("on",b.dataset.k===k));
document.getElementById("pg_baslik").textContent=D.sym+" — "+(D.isim||"")+" · "+(D.tfdata[k]?D.tfdata[k].ad:"");
document.getElementById("pg_fiyat").textContent=D.fiyat==null?"":fmt(D.fiyat)+" ₺";
document.getElementById("pg_pct").innerHTML=D.pct==null?"":pctHtml(D.pct);
GP=grafik("chart_p",D.tfdata[k],false,false);cizimBagla();}
const tfb=document.getElementById("tfbtns");
D.tford.forEach(k=>{const b=document.createElement("button");
b.className="btn tfb tfsec";b.dataset.k=k;b.textContent=D.tfdata[k].ad;
b.addEventListener("click",()=>cizP(k));tfb.appendChild(b);});
const hd=document.getElementById("haberler");
if(D.haberler.length)D.haberler.forEach(h=>{hd.innerHTML+=
'<div class="hbr"><span class="mut" style="white-space:nowrap">'+(h.s||"")+'</span>'+
'<a href="'+h.l+'" target="_blank" rel="noopener">'+h.b+'</a>'+
'<span class="mut" style="margin-left:auto;white-space:nowrap">'+h.k+'</span></div>';});
else hd.innerHTML="<div class='mut'>Haber kaynaklarına şu an ulaşılamadı.</div>";
document.getElementById("liste_baslik").textContent="Hisse Listesi ("+D.stocks.length+" hisse)";
function tabloCiz(){const a=document.getElementById("ara").value.toUpperCase();
const f=document.getElementById("filtre").value;
const tb=document.getElementById("tbl");tb.innerHTML="";
D.stocks.filter(s=>(f==="t"||(f==="u"&&s.katd==="uygun")||(f==="d"&&s.katd==="disi"))
&&(!a||s.k.includes(a)||s.n.toUpperCase().includes(a))).slice(0,800).forEach(s=>{
const tr=document.createElement("tr");tr.className="sec";
tr.innerHTML="<td class='gold' style='font-weight:700'>"+s.k+"</td>"+
"<td class='mut'>"+s.n+"</td><td>"+katHtml(s.katd)+"</td>"+
"<td>"+(s.f==null?"—":fmt(s.f))+"</td><td>"+(s.mc==null?"—":fmt(s.mc))+"</td>"+
"<td>"+pctHtml(s.p)+"</td><td>"+(s.h==null?"—":fmtB(s.h))+"</td>"+
"<td>"+(s.fk==null?"—":s.fk)+"</td><td class='mut'>"+(s.sec||"—")+"</td>"+
"<td>"+aiHtml(s.ai)+"</td>";
tb.appendChild(tr);});}
document.getElementById("ara").addEventListener("input",tabloCiz);
document.getElementById("filtre").addEventListener("change",tabloCiz);
tabloCiz();cizP(aktifTf);}
if(D.view==="bot"){
document.getElementById("bg_baslik").textContent=D.sym+" — "+(D.isim||"")+" · Bot Analiz Grafiği (Günlük)";
grafik("chart_b",{bars:D.barsB,ma20:D.maB20,ma50:D.maB50},true,true);
const vd=document.getElementById("verdict");vd.textContent=D.karar+(D.skor!=null?" · "+D.skor+"/100":"");
const alci=D.karar.includes("AL")&&!D.karar.includes("SAT");
vd.style.background=alci?"rgba(46,189,133,.15)":D.karar.includes("SAT")?"rgba(246,70,93,.15)":"rgba(132,150,173,.15)";
vd.style.color=alci?"#2EBD85":D.karar.includes("SAT")?"#F6465D":"#8496AD";
document.getElementById("yorum").textContent=D.yorum;
document.getElementById("b_durum").innerHTML=D.ayar.aktif?
'<span class="grn">● Çalışıyor</span>':'<span class="mut">● Kapalı</span>';
document.getElementById("b_risk").textContent=D.ayar.risk;
document.getElementById("b_tutar").textContent=fmt(D.ayar.tutar)+" ₺";
document.getElementById("p_kz").innerHTML='<span class="'+(D.perf.kz>=0?"grn":"red")+'">'+(D.perf.kz>=0?"+":"")+fmt(D.perf.kz)+' ₺</span>';
document.getElementById("p_karli").textContent=D.perf.karli;
document.getElementById("p_kapanan").textContent=D.perf.kapanan;
document.getElementById("p_oran").textContent=D.perf.oran==null?"—":"%"+D.perf.oran;}
function pozDoldur(id){const pt=document.getElementById(id);if(!pt)return;
if(D.poz.length)D.poz.forEach(p=>{pt.innerHTML+="<tr><td><b>"+p.k+"</b></td><td>"+p.a+"</td>"+
"<td>"+fmt(p.giris)+"</td><td>"+fmt(p.guncel)+"</td>"+
"<td class='"+(p.kz>=0?"grn":"red")+"'>"+(p.kz>=0?"+":"")+fmt(p.kz)+"</td></tr>";});
else pt.innerHTML="<tr><td colspan='5' class='mut'>Açık pozisyon yok.</td></tr>";}
pozDoldur("poztbl");pozDoldur("poztbl2");
[["logtbl",false],["logtbl2",true]].forEach(([id,full])=>{const el=document.getElementById(id);if(!el)return;
if(!D.gunluk.length){el.innerHTML="<tr><td colspan='7' class='mut'>Henüz işlem yok.</td></tr>";return;}
D.gunluk.forEach(g=>{const y="<span class='"+(g.y==="AL"?"grn":"red")+"'>"+g.y+"</span>";
const kz=g.kz==null?"—":"<span class='"+(g.kz>=0?"grn":"red")+"'>"+(g.kz>=0?"+":"")+fmt(g.kz)+"</span>";
el.innerHTML+=full?"<tr><td>"+g.z+"</td><td><b>"+g.k+"</b></td><td>"+y+"</td><td>"+g.a+"</td>"+
"<td>"+fmt(g.f)+"</td><td>"+kz+"</td><td class='mut'>"+g.g+"</td></tr>"
:"<tr><td>"+g.z+"</td><td><b>"+g.k+"</b></td><td>"+y+"</td><td>"+fmt(g.f)+"</td><td>"+kz+"</td></tr>";});});
if(D.view==="portfoy"){
document.getElementById("pf_nakit").textContent=fmt(D.ayar.bakiye)+" ₺";
document.getElementById("pf_poz").textContent=fmt(D.ayar.pozdeger)+" ₺";
const tpct=(D.ayar.toplam-D.ayar.baslangic)/D.ayar.baslangic*100;
document.getElementById("pf_top").innerHTML=fmt(D.ayar.toplam)+" ₺ "+pctHtml(tpct);}
if(D.view==="ayarlar"){
document.getElementById("a_durum").innerHTML=D.ayar.aktif?'<span class="grn">Aktif</span>':'<span class="mut">Kapalı</span>';
document.getElementById("a_risk").textContent=D.ayar.risk;
document.getElementById("a_tutar").textContent=fmt(D.ayar.tutar)+" ₺";
document.getElementById("a_izleme").textContent=D.ayar.izleme.join(", ")||"—";}
</script></body></html>"""

    for v in ("piyasa", "bot", "portfoy", "islemler", "ayarlar"):
        HTML = HTML.replace(f"__D_{v}__", "" if view == v else "display:none")
    yukseklik = {"piyasa": 1500, "bot": 1050, "portfoy": 520, "islemler": 560, "ayarlar": 420}[view]
    st_html(HTML.replace("__DATA__", json.dumps(payload, ensure_ascii=False)),
            height=yukseklik, scrolling=True)
