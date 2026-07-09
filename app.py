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
# Yardımcılar: toplu fiyat, endeks, karar, yorum, haberler
# ----------------------------------------------------------------
import json
import xml.etree.ElementTree as ET
from email.utils import parsedate_to_datetime
from streamlit.components.v1 import html as st_html

UA = {"User-Agent": "Mozilla/5.0"}

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

@st.cache_data(ttl=600, show_spinner=False)
def endeks_ozet():
    try:
        d = yf.download("XU100.IS", period="7d", interval="1d",
                        auto_adjust=True, progress=False)["Close"].dropna()
        if hasattr(d, "columns"):
            d = d.iloc[:, 0]
        return float(d.iloc[-1]), (float(d.iloc[-1]) / float(d.iloc[-2]) - 1) * 100
    except Exception:
        return None, 0.0

@st.cache_data(ttl=900, show_spinner=False)
def haberler():
    kaynaklar = [
        ("Bloomberg HT", "https://www.bloomberght.com/rss"),
        ("AA Ekonomi", "https://www.aa.com.tr/tr/rss/default?cat=ekonomi"),
        ("Dünya", "https://www.dunya.com/rss"),
    ]
    out = []
    for ad, url in kaynaklar:
        try:
            r = requests.get(url, headers=UA, timeout=10)
            r.raise_for_status()
            root = ET.fromstring(r.content)
            for item in list(root.iter("item"))[:6]:
                baslik = (item.findtext("title") or "").strip()
                link = (item.findtext("link") or "").strip()
                tarih = item.findtext("pubDate") or ""
                try:
                    saat = parsedate_to_datetime(tarih).strftime("%d.%m %H:%M")
                except Exception:
                    saat = ""
                if baslik:
                    out.append({"b": baslik, "l": link, "s": saat, "k": ad})
        except Exception:
            continue
        if len(out) >= 12:
            break
    return out[:12]

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
KATILIM_TR = {"uygun": "◈ Uygun", "disi": "Uygun Değil", "bilinmiyor": "?"}
TF = {"1h": ("3mo", "1h", "1 Saatlik"), "1d": ("1y", "1d", "Günlük"),
      "1wk": ("5y", "1wk", "Haftalık"), "1mo": ("max", "1mo", "Aylık")}

@st.cache_resource
def durum():
    return {"bakiye": 1000.0, "baslangic": 1000.0, "poz": {}, "gunluk": [],
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
# Sayfa + URL eylemleri
# ----------------------------------------------------------------
st.set_page_config(page_title="Vertual Market", page_icon="📈", layout="wide",
                   initial_sidebar_state="collapsed")
st.markdown("<style>#MainMenu,header,footer{visibility:hidden}"
            ".block-container{padding:0.3rem 0.4rem;max-width:100%}</style>",
            unsafe_allow_html=True)

qp = st.query_params
sym = qp.get("sym", "THYAO").upper()
view = qp.get("view", "piyasa")
tf = qp.get("tf", "1d")
if tf not in TF: tf = "1d"
mesaj = ""
if "bot" in qp: G["aktif"] = qp["bot"] == "1"
if "risk" in qp and qp["risk"] in ESIK: G["risk"] = qp["risk"]
if "tutar" in qp:
    try: G["tutar"] = max(50.0, float(qp["tutar"]))
    except ValueError: pass
if "izleme" in qp:
    yeni_iz = [k.strip().upper() for k in qp["izleme"].split(",") if k.strip()][:15]
    if yeni_iz: G["izleme"] = yeni_iz
if qp.get("reset") == "1":
    try: b = max(100.0, float(qp.get("bakiye", "1000")))
    except ValueError: b = 1000.0
    G.update({"bakiye": b, "baslangic": b, "poz": {}, "gunluk": []})
    mesaj = "Sanal portföy sıfırlandı."
if qp.get("tara") == "1" and G["aktif"]:
    with st.spinner("Bot tarıyor, lütfen bekle..."):
        n = bot_tara()
    mesaj = f"Tarama bitti: {n} yeni sanal işlem." if n else "Tarama bitti: eşiği aşan sinyal yok."
if any(k in qp for k in ("bot", "risk", "tutar", "reset", "bakiye", "tara", "izleme")):
    st.query_params.clear()
    st.query_params.update({"sym": sym, "view": view, "tf": tf})
    st.rerun()

# ----------------------------------------------------------------
# Veri
# ----------------------------------------------------------------
tum_kodlar = kap_tum_liste() or sorted(u[0] for u in UNIVERSE)
if sym not in tum_kodlar: sym = "THYAO"
xu, xup = endeks_ozet()

with st.spinner("Piyasa verileri yükleniyor..."):
    fiyatlar = toplu_fiyat(tuple(tum_kodlar))
    per, itv, _ = TF[tf]
    dfp = veri_cek(sym, per, itv)          # piyasa grafiği (seçilen zaman dilimi)
    dfb = veri_cek(sym, "6mo", "1d")       # bot analizi (günlük)
    hbr = haberler()

A = analiz(dfb) if (dfb is not None and len(dfb) >= 30) else None

def bars_json(d, saatlik):
    out = []
    for t, r in d.iterrows():
        out.append({"time": (int(t.timestamp()) if saatlik else t.strftime("%Y-%m-%d")),
                    "open": round(float(r.open), 2), "high": round(float(r.high), 2),
                    "low": round(float(r.low), 2), "close": round(float(r.close), 2),
                    "volume": int(r.volume)})
    return out

def ma_json(d, n, saatlik):
    s = d["close"].rolling(n).mean().dropna()
    return [{"time": (int(t.timestamp()) if saatlik else t.strftime("%Y-%m-%d")),
             "value": round(float(v), 2)} for t, v in s.items()]

saatlik = itv == "1h"
poz_kodlar = tuple(G["poz"].keys())
poz_fiyat = toplu_fiyat(poz_kodlar) if poz_kodlar else {}
pozisyonlar = []
for k, p in G["poz"].items():
    g2 = poz_fiyat.get(k, (p["giris"], 0))[0]
    pozisyonlar.append({"k": k, "a": p["adet"], "giris": round(p["giris"], 2),
                        "guncel": round(g2, 2), "kz": round((g2 - p["giris"]) * p["adet"], 2)})
kapali = [x for x in G["gunluk"] if x["y"] == "SAT"]
karli = sum(1 for x in kapali if (x["kz"] or 0) > 0)
poz_deger = sum(p["a"] * p["guncel"] for p in pozisyonlar)
toplam = G["bakiye"] + poz_deger

son_fiyat = fiyatlar.get(sym, (None, 0))
payload = {
    "sym": sym, "isim": ISIM_SOZLUGU.get(sym, ""), "katd": katilim_etiketi(sym),
    "kat": KATILIM_TR[katilim_etiketi(sym)], "view": view, "tf": tf, "mesaj": mesaj,
    "xu": round(xu, 0) if xu else None, "xup": round(xup, 2),
    "fiyat": son_fiyat[0], "pct": round(son_fiyat[1], 2),
    "yuksek": round(float(dfb["high"].iloc[-1]), 2) if A else None,
    "dusuk": round(float(dfb["low"].iloc[-1]), 2) if A else None,
    "hacim": int(dfb["volume"].iloc[-1]) if A else None,
    "karar": karar_ver(A["skor"]) if A else "VERİ YOK",
    "skor": A["skor"] if A else None,
    "yorum": yorum_yaz(A) if A else "Bu kod için fiyat verisi bulunamadı; hisse olarak işlem görmüyor olabilir.",
    "destek": round(A["support"], 2) if A else None,
    "direnc": round(A["resistance"], 2) if A else None,
    "barsP": bars_json(dfp, saatlik) if (dfp is not None and len(dfp) > 5) else [],
    "maP20": ma_json(dfp, 20, saatlik) if (dfp is not None and len(dfp) > 25) else [],
    "maP50": ma_json(dfp, 50, saatlik) if (dfp is not None and len(dfp) > 55) else [],
    "barsB": bars_json(dfb, False) if A else [],
    "maB20": ma_json(dfb, 20, False) if A else [],
    "maB50": ma_json(dfb, 50, False) if A else [],
    "markers": [{"time": x["iso"], "y": x["y"]} for x in G["gunluk"] if x["k"] == sym],
    "stocks": [{"k": k, "n": ISIM_SOZLUGU.get(k, ""), "katd": katilim_etiketi(k),
                "kat": KATILIM_TR[katilim_etiketi(k)],
                "f": round(fiyatlar[k][0], 2) if k in fiyatlar else None,
                "p": round(fiyatlar[k][1], 2) if k in fiyatlar else None} for k in tum_kodlar],
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
@import url('https://fonts.googleapis.com/css2?family=Cinzel:wght@600;700&family=Inter:wght@400;600;800&display=swap');
:root{--bg:#060D17;--card:#0C1524;--card2:#101B2E;--line:#1B2A3F;--tx:#E7EDF5;--mut:#8496AD;
--grn:#2EBD85;--red:#F6465D;--gold:#E4B95B}
*{box-sizing:border-box;margin:0;font-family:Inter,'Segoe UI',system-ui,sans-serif}
body{background:var(--bg);color:var(--tx)}
.top{display:flex;align-items:center;gap:20px;padding:12px 18px;background:var(--card);
border-bottom:1px solid var(--line);flex-wrap:wrap}
.brand{font-family:Cinzel,serif;font-size:22px;font-weight:700;letter-spacing:3px;
background:linear-gradient(135deg,#F7E2A5,#E4B95B 45%,#B98730);
-webkit-background-clip:text;background-clip:text;-webkit-text-fill-color:transparent;
text-shadow:0 0 24px rgba(228,185,91,.25)}
.big{font-size:26px;font-weight:800;font-family:ui-monospace,monospace}
.mut{color:var(--mut);font-size:13px}
.lbl{color:var(--mut);font-size:12.5px}
.val{font-family:ui-monospace,monospace;font-size:15px}
.wrap{display:flex;min-height:860px}
.nav{width:172px;background:var(--card);border-right:1px solid var(--line);padding:12px 8px;flex-shrink:0}
.nav a{display:flex;gap:10px;align-items:center;padding:12px;border-radius:10px;color:var(--mut);
font-size:14.5px;margin-bottom:4px;cursor:pointer}
.nav a.on{background:var(--card2);color:var(--tx);border-left:3px solid var(--grn)}
.mid{flex:1;padding:14px;min-width:0}
.right{width:322px;padding:14px 14px 14px 0;flex-shrink:0}
.card{background:var(--card);border:1px solid var(--line);border-radius:14px;padding:14px;margin-bottom:14px}
.h{font-size:14px;font-weight:700;margin-bottom:10px;display:flex;align-items:center;gap:8px;flex-wrap:wrap}
table{width:100%;border-collapse:collapse;font-size:13px}
th{color:var(--mut);text-align:left;font-weight:500;padding:6px 8px;border-bottom:1px solid var(--line)}
td{padding:8px;border-bottom:1px solid var(--line)}
tr.sec:hover{background:var(--card2);cursor:pointer}
.grn{color:var(--grn)}.red{color:var(--red)}.gold{color:var(--gold)}
.btn{background:var(--card2);border:1px solid var(--line);color:var(--tx);border-radius:10px;
padding:10px 14px;cursor:pointer;font-size:13px}
.btn.p{background:var(--grn);color:#04110B;border:none;font-weight:700}
.btn.r{border-color:var(--red);color:var(--red)}
.tfb{padding:6px 12px;font-size:12.5px;border-radius:8px}
.tfb.on{background:var(--grn);color:#04110B;border:none;font-weight:700}
.risk{display:flex;gap:6px}.risk .btn{flex:1;text-align:center;padding:8px 4px}
.risk .on{background:var(--grn);color:#04110B;border:none;font-weight:700}
input{background:var(--card2);border:1px solid var(--line);color:var(--tx);
border-radius:10px;padding:10px 12px;font-size:13.5px;width:100%}
.kv{display:flex;justify-content:space-between;padding:8px 0;font-size:13.5px;border-bottom:1px dashed var(--line)}
.verdict{font-size:15px;font-weight:800;padding:6px 14px;border-radius:9px;display:inline-block}
.sw{width:46px;height:25px;border-radius:20px;background:var(--card2);border:1px solid var(--line);
position:relative;cursor:pointer;display:inline-block;vertical-align:middle}
.sw i{position:absolute;top:2px;left:2px;width:19px;height:19px;border-radius:50%;background:var(--mut);transition:.2s}
.sw.on{background:rgba(46,189,133,.25);border-color:var(--grn)}
.sw.on i{left:23px;background:var(--grn)}
.scroll{max-height:400px;overflow-y:auto}
::-webkit-scrollbar{width:8px}::-webkit-scrollbar-thumb{background:var(--line);border-radius:4px}
.hbr{display:flex;gap:10px;padding:9px 4px;border-bottom:1px solid var(--line);align-items:baseline}
.hbr a{color:var(--tx);text-decoration:none;font-size:13.5px;line-height:1.45}
.hbr a:hover{color:var(--gold)}
.msg{background:rgba(46,189,133,.12);border:1px solid var(--grn);border-radius:10px;
padding:10px 12px;font-size:13.5px;margin-bottom:12px}
.warn{color:var(--mut);font-size:11.5px;line-height:1.55;margin-top:8px}
@media(max-width:1000px){.wrap{flex-direction:column}.nav{width:100%;display:flex;overflow-x:auto}
.right{width:100%;padding:0 14px}}
</style></head><body>
<div class="top">
  <div style="display:flex;align-items:center;gap:12px">
    <svg width="40" height="40" viewBox="0 0 44 44" style="filter:drop-shadow(0 0 8px rgba(228,185,91,.45))">
    <defs><linearGradient id="g" x1="0" y1="0" x2="1" y2="1">
    <stop offset="0" stop-color="#F0CE7E"/><stop offset="1" stop-color="#B98A2E"/></linearGradient></defs>
    <rect x="1" y="1" width="42" height="42" rx="11" fill="url(#g)"/>
    <path d="M9 13 L15 31 L20 13 M23 31 L23 13 L29 24 L35 13 L35 31" stroke="#0D1321"
    stroke-width="4.2" fill="none" stroke-linecap="round" stroke-linejoin="round"/></svg>
    <span class="brand">VERTUAL&nbsp;MARKET</span></div>
  <div><span class="big" id="t_fiyat"></span> <span id="t_pct" style="font-size:14px"></span>
  <div class="mut" id="t_ad"></div></div>
  <div><div class="lbl">Günlük Yüksek</div><div class="val" id="t_yuksek"></div></div>
  <div><div class="lbl">Günlük Düşük</div><div class="val" id="t_dusuk"></div></div>
  <div><div class="lbl">Hacim</div><div class="val" id="t_hacim"></div></div>
  <div><div class="lbl">BIST 100</div><div class="val" id="t_xu"></div></div>
  <div style="margin-left:auto;display:flex;align-items:center;gap:10px">
    <span class="mut" id="botlbl"></span><span class="sw" id="botsw" onclick="toggleBot()"><i></i></span></div>
</div>
<div class="wrap">
  <div class="nav">
    <a data-v="piyasa" onclick="nav('piyasa')">📈 Piyasa</a>
    <a data-v="bot" onclick="nav('bot')">🤖 Bot</a>
    <a data-v="portfoy" onclick="nav('portfoy')">💼 Portföy</a>
    <a data-v="islemler" onclick="nav('islemler')">🧾 İşlemler</a>
    <a data-v="ayarlar" onclick="nav('ayarlar')">⚙️ Ayarlar</a>
  </div>
  <div class="mid">
    <div id="mesaj"></div>

    <div id="v_piyasa" style="display:none">
      <div class="card"><div class="h"><span id="pg_baslik"></span>
        <span style="margin-left:auto;display:flex;gap:6px" id="tfbtns"></span></div>
        <div id="chart_p" style="height:410px"></div></div>
      <div class="card"><div class="h">📰 Son Dakika Piyasa Haberleri</div><div id="haberler"></div>
        <div class="warn">Kaynaklar: Bloomberg HT / AA Ekonomi / Dünya (RSS). Başlığa tıklayınca haber sitesinde açılır.</div></div>
      <div class="card"><div class="h">Hisse Listesi
        <input id="ara" placeholder="Hisse ara: kod veya şirket adı..." style="max-width:340px;margin-left:auto">
        <select id="filtre" style="background:var(--card2);border:1px solid var(--line);color:var(--tx);border-radius:10px;padding:10px" onchange="tabloCiz()">
        <option value="t">Tümü</option><option value="u">◈ Katılıma Uygun</option>
        <option value="d">Uygun Değil</option></select></div>
        <div class="scroll"><table><thead><tr><th>Kod</th><th>Şirket</th><th>Katılım</th>
        <th>Fiyat ₺</th><th>Günlük %</th></tr></thead><tbody id="tbl"></tbody></table></div>
        <div class="warn">Satıra tıklayınca o hisse seçilir. Katılım etiketleri örnektir; resmî listeden doğrulayın.</div></div>
    </div>

    <div id="v_bot" style="display:none">
      <div class="card"><div class="h" id="bg_baslik"></div><div id="chart_b" style="height:380px"></div></div>
      <div class="card"><div class="h">🤖 Bot Değerlendirmesi <span id="verdict" class="verdict"></span></div>
        <div id="yorum" style="font-size:14px;line-height:1.7"></div>
        <div class="warn">Kural tabanlı otomatik özet; yatırım tavsiyesi değildir. Veri ~15 dk gecikmelidir.</div></div>
      <div style="display:flex;gap:14px;flex-wrap:wrap">
        <div class="card" style="flex:1;min-width:300px"><div class="h">Açık İşlemler</div>
          <table><thead><tr><th>Hisse</th><th>Adet</th><th>Giriş</th><th>Güncel</th><th>K/Z ₺</th></tr></thead>
          <tbody id="poztbl"></tbody></table></div>
        <div class="card" style="flex:1;min-width:300px"><div class="h">Bot Günlüğü</div>
          <div class="scroll" style="max-height:230px"><table><thead><tr><th>Zaman</th><th>Hisse</th>
          <th>Yön</th><th>Fiyat</th><th>K/Z</th></tr></thead><tbody id="logtbl"></tbody></table></div></div>
      </div>
    </div>

    <div id="v_portfoy" style="display:none">
      <div class="card"><div class="h">💼 Sanal Portföy</div>
        <div class="kv"><span>Nakit</span><span id="pf_nakit"></span></div>
        <div class="kv"><span>Pozisyon Değeri</span><span id="pf_poz"></span></div>
        <div class="kv"><span>Toplam</span><span id="pf_top"></span></div></div>
      <div class="card"><div class="h">Açık Pozisyonlar</div>
        <table><thead><tr><th>Hisse</th><th>Adet</th><th>Giriş</th><th>Güncel</th><th>K/Z ₺</th></tr></thead>
        <tbody id="poztbl2"></tbody></table></div>
    </div>

    <div id="v_islemler" class="card" style="display:none"><div class="h">🧾 Tüm İşlemler</div>
      <div class="scroll"><table><thead><tr><th>Zaman</th><th>Hisse</th><th>Yön</th><th>Adet</th>
      <th>Fiyat</th><th>K/Z ₺</th><th>Gerekçe</th></tr></thead><tbody id="logtbl2"></tbody></table></div></div>

    <div id="v_ayarlar" class="card" style="display:none"><div class="h">⚙️ Ayarlar</div>
      <div class="kv"><span>Sanal başlangıç bakiyesi (₺)</span></div>
      <div style="display:flex;gap:8px;margin:8px 0"><input id="a_bakiye" type="number" min="100">
      <button class="btn r" onclick="resetPort()">Portföyü Sıfırla</button></div>
      <div class="kv"><span>Botun izlediği hisseler (virgülle, en çok 15)</span></div>
      <div style="display:flex;gap:8px;margin:8px 0"><input id="a_izleme">
      <button class="btn" onclick="saveIzleme()">Kaydet</button></div>
      <div class="warn">• Fiyatlar Yahoo Finance kaynaklıdır, ~15 dk gecikmelidir; hisse listesi KAP'tan gelir.<br>
      • Katılım etiketleri örnektir; resmî katılım endeksi listesinden doğrulayın.<br>
      • Bot sanal (kağıt) modda çalışır; hiçbir çıktı yatırım tavsiyesi değildir.</div></div>
  </div>

  <div class="right" id="right" style="display:none">
    <div class="card"><div class="h">🤖 Otomatik Al-Sat Botu <span class="mut">(SANAL)</span></div>
      <div class="kv"><span>Durum</span><span id="b_durum"></span></div>
      <div class="kv"><span>Strateji</span><span>Sinyal Skoru</span></div>
      <div style="margin:10px 0 4px" class="mut">Yatırım Tutarı (sanal ₺)</div>
      <div style="display:flex;gap:8px"><input id="b_tutar" type="number" min="50">
      <button class="btn" onclick="setTutar()">✓</button></div>
      <div style="margin:12px 0 6px" class="mut">Risk Seviyesi</div>
      <div class="risk" id="riskbtns"></div>
      <div style="margin-top:14px">
        <div class="kv"><span>Gerçekleşen K/Z</span><span id="p_kz"></span></div>
        <div class="kv"><span>Kârlı İşlem</span><span id="p_karli"></span></div>
        <div class="kv"><span>Kapanan İşlem</span><span id="p_kapanan"></span></div>
        <div class="kv"><span>Başarı Oranı</span><span id="p_oran" class="grn"></span></div></div>
      <div style="display:flex;gap:8px;margin-top:14px">
        <button class="btn r" style="flex:1" id="b_toggle" onclick="toggleBot()"></button>
        <button class="btn p" style="flex:1" onclick="tara()">🔍 Şimdi Tara</button></div>
      <div class="warn">Bot sanal parayla işlem yapar, gerçek emir göndermez. Sayfa açıkken
      "Şimdi Tara" ile çalışır.</div></div>
  </div>
</div>
<script>
const D = __DATA__;
function go(p){const q=new URLSearchParams();q.set("sym",D.sym);q.set("view",D.view);q.set("tf",D.tf);
for(const k in p){if(p[k]===null)q.delete(k);else q.set(k,p[k]);}
window.parent.location.search=q.toString();}
function show(id,v){document.getElementById(id).style.display=v?"":"none";}
function nav(v){D.view=v;
document.querySelectorAll(".nav a").forEach(a=>a.classList.toggle("on",a.dataset.v===v));
show("v_piyasa",v==="piyasa");show("v_bot",v==="bot");show("v_portfoy",v==="portfoy");
show("v_islemler",v==="islemler");show("v_ayarlar",v==="ayarlar");
show("right",v==="bot");}
function fmt(x){return x==null?"—":x.toLocaleString("tr-TR",{minimumFractionDigits:2,maximumFractionDigits:2});}
function pctHtml(p){if(p==null)return"—";const c=p>=0?"grn":"red";
return `<span class="${c}">${p>=0?"▲":"▼"} %${Math.abs(p).toFixed(2)}</span>`;}
function katHtml(s){return s.katd==="uygun"?`<span class="grn">✔ Uygun</span>`
:s.katd==="disi"?`<span class="red">✖ Uygun Değil</span>`:`<span class="mut">? Doğrulanmadı</span>`;}
// üst şerit
document.getElementById("t_fiyat").textContent=fmt(D.fiyat)+" ₺";
document.getElementById("t_pct").innerHTML=pctHtml(D.pct);
document.getElementById("t_ad").innerHTML=`<b>${D.sym}</b> · ${D.isim||""} · `+katHtml(D);
document.getElementById("t_yuksek").textContent=fmt(D.yuksek);
document.getElementById("t_dusuk").textContent=fmt(D.dusuk);
document.getElementById("t_hacim").textContent=D.hacim==null?"—":D.hacim.toLocaleString("tr-TR");
document.getElementById("t_xu").innerHTML=D.xu?(D.xu.toLocaleString("tr-TR")+" "+pctHtml(D.xup)):"—";
document.getElementById("botlbl").textContent=D.ayar.aktif?"Bot Aktif":"Bot Kapalı";
document.getElementById("botsw").classList.toggle("on",D.ayar.aktif);
if(D.mesaj)document.getElementById("mesaj").innerHTML=`<div class="msg">${D.mesaj}</div>`;
// zaman dilimi düğmeleri
const TFL={"1h":"1S","1d":"1G","1wk":"1H","1mo":"1A"};
const tfb=document.getElementById("tfbtns");
Object.keys(TFL).forEach(k=>{const b=document.createElement("button");
b.className="btn tfb"+(D.tf===k?" on":"");b.textContent=TFL[k];
b.onclick=()=>go({tf:k});tfb.appendChild(b);});
document.getElementById("pg_baslik").textContent=D.sym+" · "+({"1h":"1 Saatlik","1d":"Günlük","1wk":"Haftalık","1mo":"Aylık"})[D.tf]+" Grafik";
document.getElementById("bg_baslik").textContent=D.sym+" · Bot Analiz Grafiği (Günlük) · Destek "
+(D.destek??"—")+" / Direnç "+(D.direnc??"—");
// grafikler
function ciz(el,bars,ma20,ma50,sr){if(!bars.length||!window.LightweightCharts){
document.getElementById(el).innerHTML="<div class='mut' style='padding:40px;text-align:center'>Grafik verisi yok.</div>";return;}
const ch=LightweightCharts.createChart(document.getElementById(el),{
layout:{background:{color:"#0C1524"},textColor:"#8496AD"},
grid:{vertLines:{color:"#101B2E"},horzLines:{color:"#101B2E"}},
height:document.getElementById(el).clientHeight,
timeScale:{borderColor:"#1B2A3F",timeVisible:true},rightPriceScale:{borderColor:"#1B2A3F"}});
const cs=ch.addCandlestickSeries({upColor:"#2EBD85",downColor:"#F6465D",
wickUpColor:"#2EBD85",wickDownColor:"#F6465D",borderVisible:false});
cs.setData(bars);
const vol=ch.addHistogramSeries({priceScaleId:"",priceFormat:{type:"volume"}});
ch.priceScale("").applyOptions({scaleMargins:{top:0.85,bottom:0}});
vol.setData(bars.map(b=>({time:b.time,value:b.volume,
color:b.close>=b.open?"rgba(46,189,133,.45)":"rgba(246,70,93,.45)"})));
if(ma20.length)ch.addLineSeries({color:"#2EBD85",lineWidth:1}).setData(ma20);
if(ma50.length)ch.addLineSeries({color:"#F6465D",lineWidth:1}).setData(ma50);
if(sr){if(D.destek)cs.createPriceLine({price:D.destek,color:"#2EBD85",lineStyle:2,title:"DESTEK"});
if(D.direnc)cs.createPriceLine({price:D.direnc,color:"#F6465D",lineStyle:2,title:"DİRENÇ"});
cs.setMarkers(D.markers.map(m=>({time:m.time,position:m.y==="AL"?"belowBar":"aboveBar",
color:m.y==="AL"?"#2EBD85":"#F6465D",shape:m.y==="AL"?"arrowUp":"arrowDown",text:m.y})));}
ch.timeScale().fitContent();}
ciz("chart_p",D.barsP,D.maP20,D.maP50,false);
ciz("chart_b",D.barsB,D.maB20,D.maB50,true);
// haberler
const hd=document.getElementById("haberler");
if(D.haberler.length)D.haberler.forEach(h=>{hd.innerHTML+=
`<div class="hbr"><span class="mut" style="white-space:nowrap">${h.s||""}</span>
<a href="${h.l}" target="_blank" rel="noopener">${h.b}</a>
<span class="mut" style="margin-left:auto;white-space:nowrap">${h.k}</span></div>`;});
else hd.innerHTML="<div class='mut'>Haber kaynaklarına şu an ulaşılamadı; birazdan sayfayı yenile.</div>";
// hisse tablosu
function tabloCiz(){const a=document.getElementById("ara").value.toUpperCase();
const f=document.getElementById("filtre").value;
const tb=document.getElementById("tbl");tb.innerHTML="";
D.stocks.filter(s=>(f==="t"||(f==="u"&&s.katd==="uygun")||(f==="d"&&s.katd==="disi"))
&&(!a||s.k.includes(a)||s.n.toUpperCase().includes(a))).slice(0,800).forEach(s=>{
const tr=document.createElement("tr");tr.className="sec";
tr.innerHTML=`<td><b>${s.k}</b></td><td class="mut">${s.n}</td><td>${katHtml(s)}</td>
<td>${s.f==null?"—":fmt(s.f)}</td><td>${pctHtml(s.p)}</td>`;
tr.onclick=()=>go({sym:s.k});tb.appendChild(tr);});}
document.getElementById("ara").addEventListener("input",tabloCiz);
tabloCiz();
// karar
const vd=document.getElementById("verdict");vd.textContent=D.karar+(D.skor!=null?` · ${D.skor}/100`:"");
const alci=D.karar.includes("AL")&&!D.karar.includes("SAT");
vd.style.background=alci?"rgba(46,189,133,.15)":D.karar.includes("SAT")?"rgba(246,70,93,.15)":"rgba(132,150,173,.15)";
vd.style.color=alci?"#2EBD85":D.karar.includes("SAT")?"#F6465D":"#8496AD";
document.getElementById("yorum").textContent=D.yorum;
// pozisyonlar + günlük
function pozDoldur(id){const pt=document.getElementById(id);
if(D.poz.length)D.poz.forEach(p=>{pt.innerHTML+=`<tr><td><b>${p.k}</b></td><td>${p.a}</td>
<td>${fmt(p.giris)}</td><td>${fmt(p.guncel)}</td>
<td class="${p.kz>=0?"grn":"red"}">${p.kz>=0?"+":""}${fmt(p.kz)}</td></tr>`;});
else pt.innerHTML=`<tr><td colspan="5" class="mut">Açık pozisyon yok.</td></tr>`;}
pozDoldur("poztbl");pozDoldur("poztbl2");
[["logtbl",false],["logtbl2",true]].forEach(([id,full])=>{const el=document.getElementById(id);
if(!D.gunluk.length){el.innerHTML=`<tr><td colspan="7" class="mut">Henüz işlem yok.</td></tr>`;return;}
D.gunluk.forEach(g=>{const y=`<span class="${g.y==="AL"?"grn":"red"}">${g.y}</span>`;
const kz=g.kz==null?"—":`<span class="${g.kz>=0?"grn":"red"}">${g.kz>=0?"+":""}${fmt(g.kz)}</span>`;
el.innerHTML+=full?`<tr><td>${g.z}</td><td><b>${g.k}</b></td><td>${y}</td><td>${g.a}</td>
<td>${fmt(g.f)}</td><td>${kz}</td><td class="mut">${g.g}</td></tr>`
:`<tr><td>${g.z}</td><td><b>${g.k}</b></td><td>${y}</td><td>${fmt(g.f)}</td><td>${kz}</td></tr>`;});});
// bot paneli
document.getElementById("b_durum").innerHTML=D.ayar.aktif?
'<span class="grn">● Çalışıyor</span>':'<span class="mut">● Kapalı</span>';
document.getElementById("b_tutar").value=D.ayar.tutar;
const rb=document.getElementById("riskbtns");
["Düşük","Orta","Yüksek"].forEach(r=>{const b=document.createElement("button");
b.className="btn"+(D.ayar.risk===r?" on":"");b.textContent=r;
b.onclick=()=>go({risk:r});rb.appendChild(b);});
document.getElementById("p_kz").innerHTML=`<span class="${D.perf.kz>=0?"grn":"red"}">${D.perf.kz>=0?"+":""}${fmt(D.perf.kz)} ₺</span>`;
document.getElementById("p_karli").textContent=D.perf.karli;
document.getElementById("p_kapanan").textContent=D.perf.kapanan;
document.getElementById("p_oran").textContent=D.perf.oran==null?"—":"%"+D.perf.oran;
document.getElementById("b_toggle").textContent=D.ayar.aktif?"Durdur":"Başlat";
document.getElementById("pf_nakit").textContent=fmt(D.ayar.bakiye)+" ₺";
document.getElementById("pf_poz").textContent=fmt(D.ayar.pozdeger)+" ₺";
const tpct=(D.ayar.toplam-D.ayar.baslangic)/D.ayar.baslangic*100;
document.getElementById("pf_top").innerHTML=fmt(D.ayar.toplam)+" ₺ "+pctHtml(tpct);
document.getElementById("a_bakiye").value=D.ayar.baslangic;
document.getElementById("a_izleme").value=D.ayar.izleme.join(", ");
function toggleBot(){go({bot:D.ayar.aktif?"0":"1"});}
function tara(){if(!D.ayar.aktif){alert("Önce botu başlat.");return;}go({tara:"1"});}
function setTutar(){go({tutar:document.getElementById("b_tutar").value});}
function resetPort(){if(confirm("Sanal portföy sıfırlansın mı?"))
go({reset:"1",bakiye:document.getElementById("a_bakiye").value});}
function saveIzleme(){go({izleme:document.getElementById("a_izleme").value});}
window.toggleBot=toggleBot;window.tara=tara;window.setTutar=setTutar;
window.resetPort=resetPort;window.saveIzleme=saveIzleme;window.nav=nav;window.tabloCiz=tabloCiz;
nav(D.view);
</script></body></html>"""

st_html(HTML.replace("__DATA__", json.dumps(payload, ensure_ascii=False)),
        height=1000, scrolling=True)
