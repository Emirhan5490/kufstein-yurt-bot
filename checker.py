import os
import sys
import time
import requests
from bs4 import BeautifulSoup

URL = "https://www.hok.ac.at/en/service/international-student-residence"
SEMESTER_KEYWORD = "SUMMER"

CHECKS_PER_RUN = 5
CHECK_INTERVAL_SECONDS = 60
ALERT_COUNT = 5
ALERT_GAP_SECONDS = 2

TOKEN = os.environ.get("TELEGRAM_TOKEN", "")
CHAT_ID = os.environ.get("TELEGRAM_CHAT_ID", "")
MANUAL = os.environ.get("MANUAL_RUN", "") == "true"


def send_telegram(text):
    r = requests.post(
        f"https://api.telegram.org/bot{TOKEN}/sendMessage",
        data={"chat_id": CHAT_ID, "text": text},
        timeout=30,
    )
    r.raise_for_status()


def send_alarm(keyword):
    for i in range(1, ALERT_COUNT + 1):
        send_telegram(
            f"🚨🚨 ALARM {i}/{ALERT_COUNT} 🚨🚨\n"
            f"FH Kufstein yurt sayfasinda '{keyword}' gorundu!\n"
            f"BASVURU ACILMIS OLABILIR - HEMEN BAK:\n{URL}"
        )
        if i < ALERT_COUNT:
            time.sleep(ALERT_GAP_SECONDS)


def get_page_text():
    headers = {
        "User-Agent": (
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
            "(KHTML, like Gecko) Chrome/124.0 Safari/537.36"
        ),
        "Accept-Language": "en",
    }
    r = requests.get(URL, headers=headers, timeout=30)
    r.raise_for_status()
    soup = BeautifulSoup(r.text, "html.parser")
    for tag in soup(["script", "style", "noscript"]):
        tag.decompose()
    text = soup.get_text(separator=" ")
    return " ".join(text.split()).upper()


def check_once(keyword):
    text = get_page_text()
    if "INTERNATIONAL STUDENT RESIDENCE" not in text:
        raise RuntimeError("Sayfa beklenen icerigi vermedi")
    return keyword in text


def main():
    if not TOKEN or not CHAT_ID:
        print("HATA: TELEGRAM_TOKEN veya TELEGRAM_CHAT_ID bulunamadi (Secrets eksik).")
        sys.exit(1)

    keyword = SEMESTER_KEYWORD.strip().upper()
    checks = 1 if MANUAL else CHECKS_PER_RUN
    errors = 0

    for n in range(1, checks + 1):
        found = False
        try:
            found = check_once(keyword)
            print(f"[{n}/{checks}] Aranan kelime: {keyword} | bulundu: {found}")
        except Exception as e:
            errors += 1
            print(f"[{n}/{checks}] Kontrol hatasi: {e}")

        if found:
            send_alarm(keyword)
            print("Alarm gonderildi.")
            return

        if n < checks:
            time.sleep(CHECK_INTERVAL_SECONDS)

    if errors == checks:
        print("HATA: Hicbir kontrol basarili olmadi.")
        sys.exit(1)

    if MANUAL:
        send_telegram(
            "✅ Test mesaji: bot calisiyor ama aranan kelime henuz sayfada yok.\n"
            f"Aranan kelime: {keyword}"
        )
        print("Elle calistirma: durum mesaji gonderildi.")


if __name__ == "__main__":
    main()
