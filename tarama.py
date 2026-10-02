"""ABD borsasındaki büyük şirketleri tarayıp temel metrik tablosu üretir.

Kaynak: Yahoo Finance (yfinance). Çıktı: sirketler.csv ve sirketler.md
Kullanım: pip install yfinance pandas && python tarama.py
"""
import time
from datetime import date

import pandas as pd
import yfinance as yf

# Piyasa değerine göre ABD'nin en büyük ~100 şirketi (ABD borsalarında işlem gören)
TICKERS = [
    "NVDA", "AAPL", "MSFT", "GOOGL", "AMZN", "META", "AVGO", "TSLA", "BRK-B", "ORCL",
    "JPM", "WMT", "LLY", "V", "MA", "NFLX", "XOM", "COST", "JNJ", "PLTR",
    "HD", "ABBV", "BAC", "PG", "AMD", "UNH", "GE", "CVX", "KO", "CSCO",
    "WFC", "IBM", "TMUS", "MS", "PM", "GS", "CRM", "ABT", "AXP", "LIN",
    "MCD", "INTU", "MRK", "RTX", "DIS", "T", "PEP", "UBER", "CAT", "NOW",
    "TMO", "VZ", "BKNG", "C", "SCHW", "BLK", "MU", "ANET", "QCOM", "ISRG",
    "GEV", "BA", "AMGN", "TXN", "SPGI", "ACN", "ADBE", "NEE", "LRCX", "SYK",
    "BSX", "AMAT", "PGR", "DHR", "HON", "PFE", "GILD", "UNP", "KLAC", "APH",
    "INTC", "LOW", "COF", "PANW", "DE", "ETN", "CMCSA", "ADP", "CRWD", "MDT",
    "APP", "COP", "SBUX", "LMT", "CB", "MRSH", "PLD", "VRTX", "ICE", "SHOP",
]

FIELDS = {
    "marketCap": "Market Cap",
    "currentPrice": "Fiyat",
    "trailingPE": "P/E",
    "forwardPE": "Forward P/E",
    "revenueGrowth": "Gelir Büyümesi",
    "earningsGrowth": "Kâr Büyümesi",
    "fiftyTwoWeekHigh": "52H Zirve",
}


def fetch(ticker: str) -> dict:
    for attempt in range(3):
        try:
            info = yf.Ticker(ticker).info
            row = {"Ticker": ticker, "Şirket": info.get("shortName") or ticker}
            for key, col in FIELDS.items():
                row[col] = info.get(key)
            if row["Fiyat"] is None:
                row["Fiyat"] = info.get("regularMarketPrice")
            return row
        except Exception as exc:  # ağ / rate-limit hataları
            print(f"{ticker}: deneme {attempt + 1} başarısız ({exc})")
            time.sleep(2 ** (attempt + 1))
    return {"Ticker": ticker, "Şirket": ticker}


def fmt_cap(v):
    if pd.isna(v):
        return "–"
    return f"${v / 1e12:.2f}T" if v >= 1e12 else f"${v / 1e9:.0f}B"


def fmt_num(v):
    return "–" if pd.isna(v) else f"{v:.1f}"


def fmt_pct(v):
    return "–" if pd.isna(v) else f"{v * 100:+.1f}%"


def main():
    rows = []
    for i, t in enumerate(TICKERS, 1):
        rows.append(fetch(t))
        print(f"[{i}/{len(TICKERS)}] {t}")
        time.sleep(0.3)

    df = pd.DataFrame(rows)
    df["52H Düşüş"] = df["Fiyat"] / df["52H Zirve"] - 1
    df = df.sort_values("Market Cap", ascending=False).reset_index(drop=True)
    df.index += 1

    df.to_csv("sirketler.csv", index_label="#")

    out = pd.DataFrame({
        "Ticker": df["Ticker"],
        "Şirket": df["Şirket"],
        "Market Cap": df["Market Cap"].map(fmt_cap),
        "Fiyat": df["Fiyat"].map(lambda v: "–" if pd.isna(v) else f"${v:,.2f}"),
        "P/E": df["P/E"].map(fmt_num),
        "Forward P/E": df["Forward P/E"].map(fmt_num),
        "Gelir Büyümesi": df["Gelir Büyümesi"].map(fmt_pct),
        "Kâr Büyümesi": df["Kâr Büyümesi"].map(fmt_pct),
        "52H Düşüş": df["52H Düşüş"].map(fmt_pct),
    }, index=df.index)

    with open("sirketler.md", "w", encoding="utf-8") as f:
        f.write(f"# ABD Büyük Şirketler Taraması ({date.today().isoformat()})\n\n")
        f.write("Kaynak: Yahoo Finance. Gelir/Kâr büyümesi: son çeyrek, yıllık bazda (YoY). "
                "52H Düşüş: güncel fiyatın 52 haftalık zirveye uzaklığı. "
                "P/E: son 12 ay; negatif kârda boş (–).\n\n")
        f.write(out.rename_axis("#").to_markdown())
        f.write("\n")
    print(out.to_string())


if __name__ == "__main__":
    main()
