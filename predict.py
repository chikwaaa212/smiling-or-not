from http.server import BaseHTTPRequestHandler
import json, base64, io, os
import numpy as np
from PIL import Image

_model = None

def get_model():
    global _model
    if _model is None:
        from tensorflow.keras.models import load_model
        model_path = os.path.join(os.path.dirname(__file__), '..', 'smile_model.h5')
        _model = load_model(model_path)
    return _model

class handler(BaseHTTPRequestHandler):
    def _send(self, status, data):
        body = json.dumps(data).encode('utf-8')
        self.send_response(status)
        self.send_header('Content-Type', 'application/json')
        self.send_header('Access-Control-Allow-Origin', '*')
        self.send_header('Access-Control-Allow-Methods', 'POST, OPTIONS')
        self.send_header('Access-Control-Allow-Headers', 'Content-Type')
        self.send_header('Content-Length', str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def do_OPTIONS(self):
        self._send(200, {"ok": True})

    def do_POST(self):
        try:
            length = int(self.headers.get('content-length', 0))
            payload = json.loads(self.rfile.read(length).decode('utf-8'))
            image_data = payload.get('image', '')
            if ',' in image_data:
                image_data = image_data.split(',', 1)[1]

            raw = base64.b64decode(image_data)
            img = Image.open(io.BytesIO(raw)).convert('RGB').resize((224, 224))
            arr = np.asarray(img, dtype=np.float32) / 255.0
            arr = np.expand_dims(arr, axis=0)

            model = get_model()
            pred = model.predict(arr, verbose=0)
            score = float(pred[0][0])
            label = 'SMILE' if score >= 0.5 else 'NON-SMILE'
            self._send(200, {"label": label, "score": score})
        except Exception as e:
            self._send(500, {"error": str(e)})
