import os
import sys
import requests
from bs4 import BeautifulSoup

URL = "https://www.hok.ac.at/en/service/international-student-residence"
SEMESTER_KEYWORD = "WINTER"

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


def main():
    if not TOKEN or not CHAT_ID:
        print("HATA: TELEGRAM_TOKEN veya TELEGRAM_CHAT_ID bulunamadi (Secrets eksik).")
        sys.exit(1)

    text = get_page_text()

    if "INTERNATIONAL STUDENT RESIDENCE" not in text:
        print("HATA: Sayfa beklenen icerigi vermedi, kontrol atlandi.")
        sys.exit(1)

    keyword = SEMESTER_KEYWORD.strip().upper()
    found = keyword in text

    print(f"Aranan kelime: {keyword} | sayfada bulundu: {found}")

    if found:
        send_telegram(
            f"🚨 FH Kufstein yurt sayfasinda '{keyword}' kelimesi gorundu!\n\n"
            f"Hemen kontrol et: {URL}"
        )
        print("Telegram bildirimi gonderildi.")
    elif MANUAL:
        send_telegram(
            "✅ Test mesaji: bot calisiyor ama aranan kelime henuz sayfada yok.\n"
            f"Aranan kelime: {keyword}"
        )
        print("Elle calistirma: durum mesaji gonderildi.")
    else:
        print("Degisiklik yok, mesaj atilmadi.")


if __name__ == "__main__":
    main()
