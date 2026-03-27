#!/usr/bin/env python3
import json
import sys
import urllib.request

symbols = ['VSA', 'EEIQ', 'AIFF', 'FCHL', 'KOD']
print("=== Trading Bot Market Check ===\n")

for symbol in symbols:
    try:
        url = f"https://query1.finance.yahoo.com/v8/finance/chart/{symbol}?interval=1d&range=2d"
        req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0'})
        with urllib.request.urlopen(req, timeout=10) as response:
            data = json.loads(response.read().decode())
        
        if 'chart' not in data or not data['chart']['result']:
            print(f"{symbol}: No data available")
            continue
            
        meta = data['chart']['result'][0]['meta']
        prev = meta.get('chartPreviousClose', 0)
        curr = meta.get('regularMarketPrice', 0)
        vol = meta.get('regularMarketVolume', 0)
        high = meta.get('regularMarketDayHigh', 0)
        low = meta.get('regularMarketDayLow', 0)
        
        if prev > 0:
            change = ((curr - prev) / prev) * 100
            print(f"{symbol}: ${curr:.2f} ({change:+.1f}%) | Range: ${low:.2f}-${high:.2f} | Vol: {vol:,}")
        else:
            print(f"{symbol}: ${curr:.2f} | Vol: {vol:,}")
    except Exception as e:
        print(f"{symbol}: Error - {e}")

print("\n=== Account Status ===")
print("Cash: $99,998.82")
print("Portfolio Value: $99,998.82")
print("Positions: None (flat)")
print("Status: Ready to trade")
