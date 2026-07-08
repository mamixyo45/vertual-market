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
    df = df.rename(columns=str.lower)[["open", "high", "low", "close"]].dropna()
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
st.set_page_config(page_title="Vertual Market", page_icon="📈", layout="wide")

st.markdown(
    "<h2 style='margin-bottom:0'>VERTUAL MARKET <span style='color:#E4B95B'>◈</span></h2>"
    "<div style='color:#8C97AE'>BIST Katılım Analiz Terminali · Yerel Sürüm · "
    "Veri: Yahoo Finance (~15 dk gecikmeli, ücretsiz)</div>",
    unsafe_allow_html=True,
)
st.warning("Veriler ~15 dakika gecikmelidir ve resmî olmayan bir kaynaktan gelir. "
           "Hiçbir çıktı yatırım tavsiyesi değildir. Katılım etiketleri örnektir; "
           "resmî katılım endeksi listesinden doğrulayın.")

with st.sidebar:
    st.subheader("Filtre ve Ayarlar")
    with st.spinner("BIST hisse listesi KAP'tan alınıyor..."):
        tum_kodlar = kap_tum_liste()
    if tum_kodlar:
        st.caption(f"KAP listesi güncel: {len(tum_kodlar)} kod bulundu.")
    else:
        tum_kodlar = sorted(u[0] for u in UNIVERSE)
        st.caption("KAP'a ulaşılamadı; gömülü liste kullanılıyor.")
    filtre = st.radio("Katılım filtresi (örnek etiket)",
                      ["Tümü", "◈ Uygun (örnek)", "Dışı (örnek)", "Doğrulanmamış"])
    if filtre == "◈ Uygun (örnek)":
        kodlar = [k for k in tum_kodlar if katilim_etiketi(k) == "uygun"]
    elif filtre == "Dışı (örnek)":
        kodlar = [k for k in tum_kodlar if katilim_etiketi(k) == "disi"]
    elif filtre == "Doğrulanmamış":
        kodlar = [k for k in tum_kodlar if katilim_etiketi(k) == "bilinmiyor"]
    else:
        kodlar = tum_kodlar
    st.caption(f"{len(kodlar)} kod listeleniyor. Not: KAP listesinde hisse olarak "
               "işlem görmeyen ihraççılar da bulunur; bunlar seçilirse veri gelmez.")
    isimler = [f"{k} — {ISIM_SOZLUGU.get(k, '')}".rstrip(" —") for k in kodlar]
    secim = st.selectbox("Hisse seç", isimler)
    sembol = kodlar[isimler.index(secim)]
    isim = ISIM_SOZLUGU.get(sembol, sembol)
    katilim = katilim_etiketi(sembol)
    sektor = dict((u[0], u[3]) for u in UNIVERSE).get(sembol, "—")
    periyot = st.selectbox("Dönem", ["3mo", "6mo", "1y", "2y"], index=1)
    aralik = st.selectbox("Bar aralığı", ["1d", "1h", "15m"], index=0,
                          help="Saatlik/15dk barlar için dönem en fazla ~2 ay olabilir (Yahoo sınırı).")
    if aralik != "1d" and periyot in ("1y", "2y"):
        periyot = "1mo"
        st.info("Kısa bar aralığı seçildiği için dönem 1 aya çekildi (Yahoo sınırı).")

with st.spinner(f"{sembol} verisi çekiliyor..."):
    df = veri_cek(sembol, periyot, aralik)

if df is None or len(df) < 30:
    st.error("Veri çekilemedi ya da yetersiz bar var. İnternet bağlantınızı kontrol edin "
             "veya farklı bir dönem/bar aralığı deneyin.")
    st.stop()

A = analiz(df)
onceki = df["close"].iloc[-2]
degisim = (A["price"] - onceki) / onceki * 100

# --- üst şerit ---
c1, c2, c3, c4, c5 = st.columns(5)
c1.metric(f"{sembol} · {sektor}", f"{A['price']:.2f} ₺", f"%{degisim:.2f}")
c2.metric("Katılım (örnek)", {"uygun": "◈ UYGUN", "disi": "DIŞI", "bilinmiyor": "DOĞRULANMADI"}[katilim])
c3.metric("RSI (14)", f"{A['rsi']:.1f}",
          "Aşırı alım" if A["rsi"] > 70 else ("Aşırı satım" if A["rsi"] < 30 else "Nötr"),
          delta_color="off")
c4.metric("MA20 / MA50", "POZİTİF" if A["ma20"] > A["ma50"] else "NEGATİF",
          f"{A['ma20']:.2f} / {A['ma50']:.2f}", delta_color="off")
c5.metric("Bot Sinyal Skoru", f"{A['skor']}/100")

# --- mum grafiği ---
fig = go.Figure(go.Candlestick(
    x=df.index, open=df["open"], high=df["high"], low=df["low"], close=df["close"],
    increasing_line_color="#3ED598", decreasing_line_color="#F4586A", name=sembol,
))
fig.add_hline(y=A["resistance"], line_dash="dash", line_color="#F4586A",
              annotation_text=f"DİRENÇ {A['resistance']:.2f}", annotation_position="top right")
fig.add_hline(y=A["support"], line_dash="dash", line_color="#3ED598",
              annotation_text=f"DESTEK {A['support']:.2f}", annotation_position="bottom right")
for bl in A["bulgular"][-12:]:
    boga = bl["f"]["yon"] > 0
    bar = A["bars"][bl["i"]]
    fig.add_annotation(x=bl["tarih"], y=bar["l"] if boga else bar["h"],
                       text="▲" if boga else "▼", showarrow=False,
                       yshift=-14 if boga else 14,
                       font=dict(color="#E4B95B" if boga else "#F4586A", size=13))
fig.update_layout(height=460, xaxis_rangeslider_visible=False,
                  margin=dict(l=10, r=10, t=10, b=10),
                  paper_bgcolor="#0D1321", plot_bgcolor="#0D1321",
                  font=dict(color="#E9EDF6"))
fig.update_xaxes(gridcolor="#26324F")
fig.update_yaxes(gridcolor="#26324F")
st.plotly_chart(fig, use_container_width=True)

# --- formasyon tablosu ---
st.subheader("Mum Formasyonları — 34 tip aktif (21 boğa + 13 ayı)")
son = list(reversed(A["bulgular"][-10:]))
if not son:
    st.info("Seçili dönemde katalogtaki formasyonlardan tespit edilen oluşum yok.")
else:
    tablo = pd.DataFrame([{
        "Tarih": bl["tarih"].strftime("%d.%m.%Y %H:%M" if aralik != "1d" else "%d.%m.%Y"),
        "Formasyon": bl["f"]["tr"],
        "İngilizce": bl["f"]["en"],
        "Yön": "▲ Boğa" if bl["f"]["yon"] > 0 else "▼ Ayı",
        "Teyit": round(bl["teyit"], 2),
        "Stop": round(bl["stop"], 2),
        "Durum": DURUM_TR[bl["durum"]],
    } for bl in son])
    st.dataframe(tablo, use_container_width=True, hide_index=True)
st.caption("Durum döngüsü Matriks kuralına göre işler: teyit veya stop seviyesi barın "
           "KAPANIŞ değeriyle aşılmalıdır (Confirm Bar Count = 4).")

with st.expander("Formasyon kataloğunun tamamını göster (34 tip)"):
    kc1, kc2 = st.columns(2)
    bogalar = [f for f in KATALOG if f["yon"] > 0]
    ayilar = [f for f in KATALOG if f["yon"] < 0]
    kc1.markdown("**▲ Boğa (21)**\n\n" + "\n".join(f"- {f['tr']} ({f['en']})" for f in bogalar))
    kc2.markdown("**▼ Ayı (13)**\n\n" + "\n".join(f"- {f['tr']} ({f['en']})" for f in ayilar))

# --- bot değerlendirmesi ---
st.subheader("◈ Bot Değerlendirmesi")
p = []
p.append("MA20'nin MA50 üzerinde seyretmesi orta vadeli trendin yukarı yönlü olduğunu gösteriyor."
         if A["ma20"] > A["ma50"] else
         "MA20'nin MA50 altında kalması orta vadeli trendin zayıf olduğuna işaret ediyor.")
if A["rsi"] > 70:
    p.append(f"RSI {A['rsi']:.0f} ile aşırı alım bölgesinde; kısa vadede kâr satışı riski artmış durumda.")
elif A["rsi"] < 30:
    p.append(f"RSI {A['rsi']:.0f} ile aşırı satım bölgesinde; tepki alımı ihtimali teknik olarak güçleniyor.")
else:
    p.append(f"RSI {A['rsi']:.0f} seviyesinde nötr bölgede.")
if son:
    bl = son[0]
    p.append(f"Mum analizinde son olarak {bl['f']['tr']} formasyonu tespit edildi "
             f"({DURUM_TR[bl['durum']]}); teyit {bl['teyit']:.2f}, stop {bl['stop']:.2f} seviyesinde izleniyor.")
yak = (A["price"] - A["support"]) / ((A["resistance"] - A["support"]) or 1)
if yak > 0.75:
    p.append(f"Fiyat {A['resistance']:.2f} direncine yaklaşmış durumda; kırılım teyidi olmadan yeni alım riskli görünüyor.")
elif yak < 0.25:
    p.append(f"Fiyat {A['support']:.2f} desteğine yakın; destek korunursa risk/getiri dengesi alıcı lehine.")
else:
    p.append(f"Fiyat {A['support']:.2f} desteği ile {A['resistance']:.2f} direnci arasındaki bandın ortasında dengeleniyor.")
st.write(" ".join(p))
st.caption("Bu değerlendirme kural tabanlı otomatik bir özettir; yatırım tavsiyesi değildir.")
