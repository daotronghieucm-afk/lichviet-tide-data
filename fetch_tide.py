# -*- coding: utf-8 -*-
"""Lay du lieu thuy trieu cho cac cang Viet Nam, xuat ra tide.json.
Chay tu dong moi ngay bang GitHub Actions."""
import os, json, requests
from datetime import datetime, timedelta, timezone

KEY = os.environ['TIDE_API_KEY']
VN = timezone(timedelta(hours=7))

# 6 cang - them/bot tuy han muc goi API
PORTS = [
    {"id": "honDau",   "name": "Hải Phòng (Hòn Dấu)", "lat": 20.67, "lng": 106.80},
    {"id": "cuaLo",    "name": "Cửa Lò – Nghệ An",    "lat": 18.80, "lng": 105.72},
    {"id": "daNang",   "name": "Đà Nẵng",             "lat": 16.10, "lng": 108.25},
    {"id": "nhaTrang", "name": "Nha Trang",           "lat": 12.24, "lng": 109.20},
    {"id": "vungTau",  "name": "Vũng Tàu",            "lat": 10.34, "lng": 107.08},
    {"id": "rachGia",  "name": "Rạch Giá – Kiên Giang","lat": 10.01, "lng": 105.08},
]

def lay_muc_nuoc(lat, lng, start, end):
    r = requests.get(
        'https://api.stormglass.io/v2/tide/sea-level/point',
        params={'lat': lat, 'lng': lng,
                'start': start.isoformat(), 'end': end.isoformat()},
        headers={'Authorization': KEY}, timeout=30)
    r.raise_for_status()
    return r.json().get('data', [])

def tim_dinh_day(gio, muc):
    """Tu tim gio nuoc lon / nuoc rong tu chuoi muc nuoc.
    Lam o day de KHOI ton them 1 luot goi API cho moi cang."""
    out = []
    for i in range(1, len(muc) - 1):
        if muc[i] > muc[i-1] and muc[i] >= muc[i+1]:
            out.append({"t": gio[i], "type": "high", "h": round(muc[i], 2)})
        elif muc[i] < muc[i-1] and muc[i] <= muc[i+1]:
            out.append({"t": gio[i], "type": "low", "h": round(muc[i], 2)})
    return out

def main():
    hom_nay = datetime.now(VN).replace(hour=0, minute=0, second=0, microsecond=0)
    ket_thuc = hom_nay + timedelta(days=7)
    ports_out = []

    for p in PORTS:
        try:
            data = lay_muc_nuoc(p['lat'], p['lng'], hom_nay, ket_thuc)
        except Exception as e:
            print(f"  [LOI] {p['name']}: {e}")
            continue

        theo_ngay = {}
        for d in data:
            t = datetime.fromisoformat(d['time'].replace('Z', '+00:00')).astimezone(VN)
            if t.minute != 0:
                continue
            theo_ngay.setdefault(t.strftime('%Y-%m-%d'), {})[t.hour] = round(d['sg'], 2)

        days = []
        for ngay in sorted(theo_ngay)[:7]:
            gio_map = theo_ngay[ngay]
            if len(gio_map) < 20:
                continue
            heights = [gio_map.get(h, gio_map.get(h-1, 0)) for h in range(24)]
            nhan_gio = [f"{h:02d}:00" for h in range(24)]
            days.append({
                "date": ngay,
                "heights": heights,
                "extremes": tim_dinh_day(nhan_gio, heights),
            })

        if days:
            ports_out.append({"id": p['id'], "name": p['name'],
                              "station": p['name'], "days": days})
            print(f"  [OK] {p['name']}: {len(days)} ngay")

    if not ports_out:
        raise SystemExit("Khong lay duoc cang nao - DUNG, khong ghi de file cu")

    out = {
        "updated": datetime.now(VN).isoformat(),
        "source": "Stormglass",
        "ports": ports_out,
    }
    with open('tide.json', 'w', encoding='utf-8') as f:
        json.dump(out, f, ensure_ascii=False, separators=(',', ':'))
    print(f"Xong: {len(ports_out)} cang")

main()
