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
        return sorted(kodlar) if len(kodlar) > 100 else None
    except Exception:
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
# Toplu fiyat çekimi — 10 dk önbellek
# ----------------------------------------------------------------
@st.cache_data(ttl=600, show_spinner=False)
def toplu_fiyat(kodlar):
    satirlar = {}
    kodlar = list(kodlar)
    for i in range(0, len(kodlar), 100):
        parca = kodlar[i:i + 100]
        try:
            df = yf.download([k + ".IS" for k in parca], period="7d", interval="1d",
                             auto_adjust=True, progress=False, group_by="ticker", threads=True)
        except Exception:
            continue
        for k in parca:
            try:
                seri = (df[k + ".IS"]["Close"] if len(parca) > 1 else df["Close"]).dropna()
                if len(seri) >= 2:
                    son, once = float(seri.iloc[-1]), float(seri.iloc[-2])
                    satirlar[k] = (son, (son - once) / once * 100)
                elif len(seri) == 1:
                    satirlar[k] = (float(seri.iloc[-1]), 0.0)
            except Exception:
                continue
    return satirlar

def karar_ver(skor):
    if skor >= 70: return "GÜÇLÜ AL", "🟢🟢"
    if skor >= 57: return "AL", "🟢"
    if skor > 43:  return "NÖTR / TUT", "⚪"
    if skor > 30:  return "SAT", "🔴"
    return "GÜÇLÜ SAT", "🔴🔴"

KATILIM_TR = {"uygun": "◈ Uygun", "disi": "Dışı", "bilinmiyor": "?"}
ESIK = {"Düşük": (70, 45), "Orta": (62, 43), "Yüksek": (57, 40)}

def yorum_yaz(A):
    p = []
    p.append("Orta vadeli trend yukarı yönlü görünüyor." if A["ma20"] > A["ma50"]
             else "Orta vadeli trend zayıf seyrediyor.")
    if A["rsi"] > 70: p.append("Momentum aşırı ısınmış; kısa vadede kâr satışı gelebilir.")
    elif A["rsi"] < 30: p.append("Hisse aşırı satılmış bölgede; tepki yükselişi ihtimali güçleniyor.")
    else: p.append("Momentum dengeli seyrediyor.")
    if A["mum_net"] >= 2: p.append("Son barlardaki fiyat davranışı alıcıların güçlendiğine işaret eden dönüş sinyalleri üretiyor.")
    elif A["mum_net"] <= -2: p.append("Son barlardaki fiyat davranışı satış baskısının arttığına işaret eden sinyaller üretiyor.")
    else: p.append("Son barlarda fiyat davranışı net bir yön sinyali üretmiyor.")
    yak = (A["price"] - A["support"]) / ((A["resistance"] - A["support"]) or 1)
    if yak > 0.75: p.append(f"Fiyat {A['resistance']:.2f} direncine yakın; kırılım gelmeden yeni alım riskli olabilir.")
    elif yak < 0.25: p.append(f"Fiyat {A['support']:.2f} desteğine yakın; destek korunursa risk/getiri alıcı lehine.")
    else: p.append(f"Fiyat {A['support']:.2f} desteği ile {A['resistance']:.2f} direnci arasında dengeleniyor.")
    return " ".join(p)

# ----------------------------------------------------------------
# Uygulama
# ----------------------------------------------------------------
st.set_page_config(page_title="Vertual Market", page_icon="📈", layout="wide",
                   initial_sidebar_state="expanded")

# --- görsel stil: kart panelleri, altın vurgu, üst şerit ---
st.markdown("""
<style>
:root { --panel:#151D30; --line:#26324F; --gold:#E4B95B; }
.block-container { padding-top: 1.0rem; }
[data-testid="stMetric"] {
  background: var(--panel); border: 1px solid var(--line);
  border-radius: 14px; padding: 14px 16px;
}
[data-testid="stMetricLabel"] { color: #8C97AE; }
[data-testid="stDataFrame"] {
  border: 1px solid var(--line); border-radius: 14px; overflow: hidden;
}
[data-testid="stSidebar"] { background: #0A0F1B; border-right: 1px solid var(--line); }
div.stButton > button, div[data-testid="stFormSubmitButton"] > button {
  border-radius: 10px; border: 1px solid var(--line);
}
div.stButton > button[kind="primary"] {
  background: var(--gold); color: #0D1321; border: none; font-weight: 700;
}
[data-testid="stExpander"] {
  border: 1px solid var(--line); border-radius: 14px; background: var(--panel);
}
.vm-topbar {
  display:flex; align-items:center; gap:18px; flex-wrap:wrap;
  background: var(--panel); border:1px solid var(--line); border-radius:14px;
  padding:10px 16px; margin-bottom:14px;
}
.vm-topbar .ad { font-weight:800; letter-spacing:1px; }
.vm-topbar .deger { font-family: monospace; font-size:18px; font-weight:700; }
.vm-pill {
  margin-left:auto; font-size:12px; padding:4px 12px; border-radius:20px;
  border:1px solid var(--line);
}
</style>""", unsafe_allow_html=True)

@st.cache_data(ttl=600, show_spinner=False)
def endeks_ozet():
    try:
        d = yf.download("XU100.IS", period="7d", interval="1d",
                        auto_adjust=True, progress=False)["Close"].dropna()
        if hasattr(d, "columns"):
            d = d.iloc[:, 0]
        son, once = float(d.iloc[-1]), float(d.iloc[-2])
        return son, (son - once) / once * 100
    except Exception:
        return None, 0.0

# --- durum (sanal portföy) ---
S = st.session_state
S.setdefault("bakiye", 1000.0)
S.setdefault("baslangic", 1000.0)
S.setdefault("poz", {})          # kod -> {adet, giris}
S.setdefault("gunluk", [])       # işlem kayıtları
S.setdefault("izleme", ["ASELS", "THYAO", "BIMAS", "EREGL", "SISE", "FROTO", "TCELL", "TUPRS"])
S.setdefault("risk", "Orta")
S.setdefault("islem_tutari", 250.0)
S.setdefault("bot_aktif", False)

EMBLEM = """<svg width="44" height="44" viewBox="0 0 44 44" xmlns="http://www.w3.org/2000/svg">
<defs><linearGradient id="g" x1="0" y1="0" x2="1" y2="1">
<stop offset="0" stop-color="#F0CE7E"/><stop offset="1" stop-color="#B98A2E"/></linearGradient></defs>
<rect x="1" y="1" width="42" height="42" rx="11" fill="url(#g)"/>
<path d="M9 13 L15 31 L20 13" stroke="#0D1321" stroke-width="4.2" fill="none"
 stroke-linecap="round" stroke-linejoin="round"/>
<path d="M23 31 L23 13 L29 24 L35 13 L35 31" stroke="#0D1321" stroke-width="4.2" fill="none"
 stroke-linecap="round" stroke-linejoin="round"/></svg>"""

with st.sidebar:
    st.markdown(
        f"<div style='display:flex;align-items:center;gap:11px;padding:4px 0 10px'>{EMBLEM}"
        "<div style='line-height:1.15'><span style='font-size:17px;font-weight:800;"
        "letter-spacing:.5px'>VERTUAL<br>MARKET</span></div></div>",
        unsafe_allow_html=True)
    sayfa = st.radio("Menü", ["📈 Piyasa", "🤖 Bot", "💼 Portföy", "🧾 İşlemler", "⚙️ Ayarlar"],
                     label_visibility="collapsed")
    st.divider()
    durum = "🟢 Bot Aktif (sanal)" if S.bot_aktif else "⚫ Bot Kapalı"
    st.caption(durum)
    st.caption("Veri ~15 dk gecikmeli\n\nYatırım tavsiyesi değildir")

# --- üst bilgi şeridi ---
xu, xup = endeks_ozet()
xu_html = (f"<span style='color:#8C97AE;font-size:12px'>BIST 100</span> "
           f"<span class='deger'>{xu:,.0f}</span> "
           f"<span style='color:{'#3ED598' if xup>=0 else '#F4586A'};font-size:13px'>"
           f"{'▲' if xup>=0 else '▼'} %{abs(xup):.2f}</span>") if xu else ""
bot_html = ("<span class='vm-pill' style='color:#3ED598'>● Bot Aktif (sanal)</span>"
            if S.bot_aktif else "<span class='vm-pill' style='color:#8C97AE'>● Bot Kapalı</span>")
st.markdown(f"<div class='vm-topbar'><span class='ad'>VERTUAL MARKET "
            f"<span style='color:#E4B95B'>◈</span></span> {xu_html} {bot_html}</div>",
            unsafe_allow_html=True)

# --- ortak: hisse listesi ---
tum_kodlar = kap_tum_liste() or sorted(u[0] for u in UNIVERSE)

def guncel_fiyat(kod):
    f = toplu_fiyat((kod,))
    return f.get(kod, (None, 0))[0]

def bot_tara():
    """Sanal bot: izleme listesini tarar, sinyale göre kağıt üzerinde alır/satar."""
    esik_al, esik_sat = ESIK[S.risk]
    yeni = 0
    bar = st.progress(0, text="Bot tarıyor...")
    for n, kod in enumerate(S.izleme):
        bar.progress((n + 1) / max(len(S.izleme), 1), text=f"Taranıyor: {kod}")
        df = veri_cek(kod, "6mo", "1d")
        if df is None or len(df) < 30:
            continue
        A = analiz(df)
        fiyat = A["price"]
        zaman = pd.Timestamp.now().strftime("%d.%m %H:%M")
        if kod in S.poz and A["skor"] <= esik_sat:
            p = S.poz.pop(kod)
            tutar = p["adet"] * fiyat
            kz = (fiyat - p["giris"]) * p["adet"]
            S.bakiye += tutar
            S.gunluk.append({"Zaman": zaman, "Hisse": kod, "Yön": "SAT", "Adet": p["adet"],
                             "Fiyat": round(fiyat, 2), "K/Z ₺": round(kz, 2),
                             "Gerekçe": f"Skor {A['skor']} ≤ {esik_sat}"})
            yeni += 1
        elif kod not in S.poz and A["skor"] >= esik_al and S.bakiye >= S.islem_tutari:
            adet = int(S.islem_tutari // fiyat)
            if adet >= 1:
                S.bakiye -= adet * fiyat
                S.poz[kod] = {"adet": adet, "giris": fiyat}
                S.gunluk.append({"Zaman": zaman, "Hisse": kod, "Yön": "AL", "Adet": adet,
                                 "Fiyat": round(fiyat, 2), "K/Z ₺": None,
                                 "Gerekçe": f"Skor {A['skor']} ≥ {esik_al}"})
                yeni += 1
    bar.empty()
    return yeni

# ================= SAYFA: PİYASA =================
if sayfa == "📈 Piyasa":
    u1, u2 = st.columns([2, 1])
    ara = u1.text_input("Ara", placeholder="Hisse kodu veya şirket adı...", label_visibility="collapsed")
    filtre = u2.selectbox("Filtre", ["Tümü", "◈ Katılıma Uygun (örnek)", "Katılım Dışı (örnek)"],
                          label_visibility="collapsed")
    kodlar = tum_kodlar
    if filtre.startswith("◈"): kodlar = [k for k in kodlar if katilim_etiketi(k) == "uygun"]
    elif filtre.startswith("Katılım Dışı"): kodlar = [k for k in kodlar if katilim_etiketi(k) == "disi"]
    if ara:
        a = ara.upper()
        kodlar = [k for k in kodlar if a in k or a in ISIM_SOZLUGU.get(k, "").upper()]
    with st.spinner(f"{len(kodlar)} hissenin fiyatı yükleniyor..."):
        fiyatlar = toplu_fiyat(tuple(kodlar))
    tablo = pd.DataFrame([{
        "Kod": k, "Şirket": ISIM_SOZLUGU.get(k, ""), "Katılım": KATILIM_TR[katilim_etiketi(k)],
        "Fiyat (₺)": round(fiyatlar[k][0], 2) if k in fiyatlar else None,
        "Günlük %": round(fiyatlar[k][1], 2) if k in fiyatlar else None,
    } for k in kodlar])
    st.caption(f"{len(tablo)} hisse · Analiz için satıra tıkla")
    secim = st.dataframe(tablo, use_container_width=True, hide_index=True, height=400,
                         on_select="rerun", selection_mode="single-row")
    if secim.selection.rows:
        sembol = tablo.iloc[secim.selection.rows[0]]["Kod"]
        with st.spinner(f"{sembol} analiz ediliyor..."):
            df = veri_cek(sembol, "6mo", "1d")
        if df is None or len(df) < 30:
            st.error("Bu kod için fiyat verisi yok (hisse olarak işlem görmüyor olabilir).")
        else:
            A = analiz(df)
            karar, ikon = karar_ver(A["skor"])
            onceki = df["close"].iloc[-2]
            st.divider()
            b1, b2, b3 = st.columns([2, 1, 1])
            b1.markdown(f"### {sembol} — {ISIM_SOZLUGU.get(sembol, '')}")
            b1.caption(f"Katılım (örnek): {KATILIM_TR[katilim_etiketi(sembol)]}")
            b2.metric("Son Fiyat", f"{A['price']:.2f} ₺", f"%{(A['price']-onceki)/onceki*100:.2f}")
            b3.metric("Bot Kararı", f"{ikon} {karar}", f"Skor {A['skor']}/100", delta_color="off")
            st.info("🤖 " + yorum_yaz(A))
            st.caption("Kural tabanlı otomatik özet; yatırım tavsiyesi değildir.")
            st.markdown("**Son 5 Gün Özeti**")
            son5 = df.tail(5)
            st.dataframe(pd.DataFrame({
                "Tarih": [t.strftime("%d.%m.%Y") for t in son5.index],
                "Açılış": son5["open"].round(2).values,
                "Kapanış": son5["close"].round(2).values,
                "Değişim %": (son5["close"].pct_change().fillna(0) * 100).round(2).values,
                "Hacim (adet)": son5["volume"].astype(int).values,
            }), use_container_width=True, hide_index=True)
            st.caption("AKD (aracı kurum dağılımı) ücretsiz kaynaklarda yayınlanmadığı için gösterilemiyor.")
            with st.expander("📊 Grafiği göster"):
                fig = go.Figure(go.Candlestick(
                    x=df.index, open=df["open"], high=df["high"], low=df["low"], close=df["close"],
                    increasing_line_color="#3ED598", decreasing_line_color="#F4586A"))
                fig.add_hline(y=A["resistance"], line_dash="dash", line_color="#F4586A",
                              annotation_text=f"DİRENÇ {A['resistance']:.2f}")
                fig.add_hline(y=A["support"], line_dash="dash", line_color="#3ED598",
                              annotation_text=f"DESTEK {A['support']:.2f}")
                fig.update_layout(height=400, xaxis_rangeslider_visible=False,
                                  margin=dict(l=10, r=10, t=10, b=10))
                st.plotly_chart(fig, use_container_width=True)
    else:
        st.info("Analiz için tablodan bir hisseye tıkla.")

# ================= SAYFA: BOT =================
elif sayfa == "🤖 Bot":
    st.markdown("### 🤖 Otomatik Al-Sat Botu — SANAL MOD")
    st.warning("Bot **sanal parayla (kağıt üzerinde)** işlem yapar; gerçek emir göndermez. "
               "Veri ~15 dk gecikmeli olduğundan gerçek otomatik emir güvenli değildir; "
               "strateji burada test edilir, gerçeğe geçiş ileride aracı kurum API'siyle olur.")
    S.bot_aktif = st.toggle("Bot Aktif", value=S.bot_aktif)
    a1, a2 = st.columns(2)
    S.islem_tutari = a1.number_input("İşlem başına tutar (sanal ₺)", 50.0, 100000.0,
                                     S.islem_tutari, step=50.0)
    S.risk = a2.radio("Risk Seviyesi", ["Düşük", "Orta", "Yüksek"],
                      index=["Düşük", "Orta", "Yüksek"].index(S.risk), horizontal=True)
    ea, es = ESIK[S.risk]
    st.caption(f"Strateji: Sinyal Skoru (trend + momentum + fiyat davranışı + destek/direnç) · "
               f"AL: skor ≥ {ea} · SAT: skor ≤ {es}")
    S.izleme = st.multiselect("Botun izleyeceği hisseler (en fazla 15 önerilir)",
                              options=tum_kodlar, default=[k for k in S.izleme if k in tum_kodlar])
    if S.bot_aktif and st.button("🔍 Şimdi Tara ve İşlem Yap", type="primary",
                                 use_container_width=True):
        n = bot_tara()
        st.success(f"Tarama bitti: {n} yeni sanal işlem yapıldı." if n else
                   "Tarama bitti: sinyal eşiğini aşan yeni işlem yok.")
    elif not S.bot_aktif:
        st.info("Taramak için önce botu aktif et.")
    # performans özeti
    kapali = [g for g in S.gunluk if g["Yön"] == "SAT"]
    karli = sum(1 for g in kapali if (g["K/Z ₺"] or 0) > 0)
    toplam_kz = sum((g["K/Z ₺"] or 0) for g in kapali)
    m1, m2, m3, m4 = st.columns(4)
    m1.metric("Gerçekleşen K/Z", f"{toplam_kz:+.2f} ₺")
    m2.metric("Kârlı İşlem", karli)
    m3.metric("Kapanan İşlem", len(kapali))
    m4.metric("Başarı Oranı", f"%{(karli/len(kapali)*100):.0f}" if kapali else "—")
    st.caption("Not: Bulut sürümünde sanal portföy tarayıcı oturumuna bağlıdır; uygulama "
               "yeniden başlarsa sıfırlanabilir. Bot, sayfa açıkken 'Tara' ile çalışır — "
               "7/24 kendi kendine çalışması sunucu kurulumu gerektirir (ileriki aşama).")

# ================= SAYFA: PORTFÖY =================
elif sayfa == "💼 Portföy":
    st.markdown("### 💼 Sanal Portföy")
    poz_fiyat = toplu_fiyat(tuple(S.poz.keys())) if S.poz else {}
    poz_deger = sum(p["adet"] * poz_fiyat.get(k, (p["giris"], 0))[0] for k, p in S.poz.items())
    toplam = S.bakiye + poz_deger
    m1, m2, m3 = st.columns(3)
    m1.metric("Nakit (sanal)", f"{S.bakiye:.2f} ₺")
    m2.metric("Pozisyon Değeri", f"{poz_deger:.2f} ₺")
    m3.metric("Toplam", f"{toplam:.2f} ₺",
              f"%{(toplam - S.baslangic) / S.baslangic * 100:+.2f}")
    if S.poz:
        st.dataframe(pd.DataFrame([{
            "Hisse": k, "Adet": p["adet"], "Giriş": round(p["giris"], 2),
            "Güncel": round(poz_fiyat.get(k, (p["giris"], 0))[0], 2),
            "K/Z ₺": round((poz_fiyat.get(k, (p["giris"], 0))[0] - p["giris"]) * p["adet"], 2),
        } for k, p in S.poz.items()]), use_container_width=True, hide_index=True)
    else:
        st.info("Açık pozisyon yok. Bot sayfasından tarama yaparak sanal işlem başlatabilirsin.")

# ================= SAYFA: İŞLEMLER =================
elif sayfa == "🧾 İşlemler":
    st.markdown("### 🧾 Bot Günlüğü")
    if S.gunluk:
        st.dataframe(pd.DataFrame(list(reversed(S.gunluk))),
                     use_container_width=True, hide_index=True)
    else:
        st.info("Henüz işlem yok. Bot sayfasından botu aktif edip 'Şimdi Tara' de.")

# ================= SAYFA: AYARLAR =================
elif sayfa == "⚙️ Ayarlar":
    st.markdown("### ⚙️ Ayarlar")
    yeni_b = st.number_input("Sanal başlangıç bakiyesi (₺)", 100.0, 10_000_000.0,
                             S.baslangic, step=100.0)
    if st.button("Portföyü sıfırla ve bu bakiyeyle başla"):
        S.bakiye = yeni_b; S.baslangic = yeni_b; S.poz = {}; S.gunluk = []
        st.success(f"Sanal portföy {yeni_b:.0f} ₺ ile sıfırlandı.")
    st.divider()
    st.markdown("**Bilgi**")
    st.caption("- Fiyatlar Yahoo Finance kaynaklı, ~15 dk gecikmelidir; hisse listesi KAP'tan gelir.\n"
               "- Katılım etiketleri örnektir; resmî katılım endeksi listesinden doğrulayın.\n"
               "- AKD (aracı kurum dağılımı) ücretsiz kaynaklarda yoktur.\n"
               "- Bot sanal modda çalışır; hiçbir çıktı yatırım tavsiyesi değildir.")
