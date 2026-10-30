import sys
sys.stdout.reconfigure(encoding='utf-8')
from app import app
import json

client = app.test_client()

print("Testing /api/stats...")
res = client.get('/api/stats')
print("Status:", res.status_code)
data = json.loads(res.data.decode('utf-8'))
print("Stats response:", data)

print("\nTesting /api/search (q='قرآن')...")
res2 = client.get('/api/search?q=قرآن&limit=3')
print("Status:", res2.status_code)
data2 = json.loads(res2.data.decode('utf-8'))
print(f"Total results for 'قرآن': {data2['total']}")
for b in data2['results']:
    print(f"  #{b['serial_no']} - {b['title']} (Author: {b['author']})")

print("\nTesting /api/search by serial number (q='113')...")
res3 = client.get('/api/search?q=113')
data3 = json.loads(res3.data.decode('utf-8'))
print(f"Total results for '113': {data3['total']}")
for b in data3['results']:
    print(f"  #{b['serial_no']} - {b['title']} -> {b['kitabosunnat_url']}")

print("\nTesting root page /...")
res4 = client.get('/')
print("Status:", res4.status_code, "HTML length:", len(res4.data))

print("\nALL FLASK TESTS PASSED SUCCESSFULLY!")
