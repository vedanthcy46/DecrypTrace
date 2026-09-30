import uvicorn
import sys
from backend.core.dlt.node import create_app

if __name__ == "__main__":
    node_id = sys.argv[1]
    port = int(sys.argv[2])
    app = create_app(node_id, port)
    uvicorn.run(app, host="127.0.0.1", port=port)
