import requests
import json
import datetime
import csv
import io
import sys

# Google Sheets CSV URL - ISG_PANEL_VERI sayfası
SHEETS_CSV_URL = "https://docs.google.com/spreadsheets/d/e/2PACX-1vSBFr-6T9tNYsyQVqSq9HqcKEi7Hbn72rR3D3Lfuaa24K6lChv8QDcNoW1pY_P-pdhJINqHu0jpkW4E/pub?gid=594059710&single=true&output=csv"

def fmt_date(v):
    if not v:
        return ''
    s = str(v).strip()
    for fmt in ['%d.%m.%Y', '%Y-%m-%d', '%m/%d/%Y', '%d/%m/%Y']:
        try:
            return datetime.datetime.strptime(s, fmt).strftime('%d.%m.%Y')
        except:
            pass
    return s

def normalize(h):
    return h.lower().replace('i̇','i').strip()

def parse_csv(csv_text):
    # Python'un csv modülü satır-içi newline'ları doğru handle eder
    reader = csv.reader(io.StringIO(csv_text))
    rows = list(reader)
    if len(rows) < 2:
        return []

    headers = [normalize(h) for h in rows[0]]

    header_map = {
        'isim': 'ad_soyad',
        'ad soyad': 'ad_soyad',
        'tarih': 'bildirim_tarihi',
        'süreç durumu': 'durum',
        'tespit edilen durum': 'tespit',
        'öneri': 'oneri',
        'yapılan işlem / durum': 'alinanan_aksiyon',
    }
    mapped = [header_map.get(h, h) for h in headers]

    records = []
    for row in rows[1:]:
        obj = {}
        for i, key in enumerate(mapped):
            obj[key] = row[i].strip() if i < len(row) else ''
        isim = obj.get('ad_soyad', '').strip()
        if not isim or isim in ('0', 'None', ''):
            continue
        records.append({
            'ad_soyad': isim,
            'bildirim_tarihi': fmt_date(obj.get('bildirim_tarihi', '')),
            'durum': obj.get('durum', '').strip(),
            'tespit': obj.get('tespit', '').strip(),
            'oneri': obj.get('oneri', '').strip(),
            'alinanan_aksiyon': obj.get('alinanan_aksiyon', '').strip(),
        })
    return records

def main():
    csv_url = sys.argv[1] if len(sys.argv) > 1 else SHEETS_CSV_URL
    print(f"CSV çekiliyor...")

    resp = requests.get(csv_url, timeout=30)
    resp.encoding = 'utf-8'
    records = parse_csv(resp.text)
    print(f"Kayıt sayısı: {len(records)}")

    if len(records) == 0:
        print("UYARI: Hiç kayıt bulunamadı! Mevcut veri korunuyor, güncelleme yapılmadı.")
        sys.exit(0)

    with open('index.html', 'r', encoding='utf-8') as f:
        content = f.read()

    start = content.find('const DEMO_DATA = ')
    end = content.find('\n\n// ═══════════════════════', start)

    if start == -1 or end == -1:
        print("HATA: DEMO_DATA bloğu bulunamadı!")
        sys.exit(1)

    new_block = f'const DEMO_DATA = {json.dumps(records, ensure_ascii=False, indent=2)};'
    content = content[:start] + new_block + content[end:]

    with open('index.html', 'w', encoding='utf-8') as f:
        f.write(content)

    print(f"index.html güncellendi ({len(content)//1024}KB)")

if __name__ == '__main__':
    main()
