import urllib.request
import json

try:
    req = urllib.request.Request('http://127.0.0.1:8001/chain')
    with urllib.request.urlopen(req) as response:
        chain = json.loads(response.read())
        print(f"Total blocks: {len(chain)}")
        for b in chain:
            txs = b.get("transactions", [])
            print(f"Index: {b.get('index')}, tx_count: {len(txs)}")
            if len(txs) > 0:
                print(json.dumps(txs[0], indent=2))
except Exception as e:
    print(e)
