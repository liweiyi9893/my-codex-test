from flask import Flask, render_template, request
import requests
import time
import base64

app = Flask(__name__)

API_URL = "http://127.0.0.1:8188"


def request_comfy(prompt: str):
    """Send prompt to ComfyUI and return an image URL."""
    # Send prompt
    resp = requests.post(f"{API_URL}/prompt", json={"prompt": prompt})
    resp.raise_for_status()
    data = resp.json()
    prompt_id = data.get("prompt_id") or data.get("id")
    if not prompt_id:
        return None

    # Poll history endpoint until we get an image path
    for _ in range(30):
        hist = requests.get(f"{API_URL}/history/{prompt_id}")
        if hist.status_code == 200:
            hdata = hist.json()
            images = hdata.get("images")
            if images:
                img_info = images[0]
                if isinstance(img_info, dict):
                    filename = img_info.get("filename") or img_info.get("path")
                else:
                    filename = img_info
                if filename:
                    img_resp = requests.get(f"{API_URL}/view?filename={filename}")
                    if img_resp.status_code == 200:
                        b64 = base64.b64encode(img_resp.content).decode("utf-8")
                        return f"data:image/png;base64,{b64}"
        time.sleep(1)
    return None


@app.route('/', methods=['GET', 'POST'])
def index():
    image_url = None
    if request.method == 'POST':
        keyword = request.form.get('keyword')
        if keyword:
            try:
                image_url = request_comfy(keyword)
            except Exception as e:
                print(f"Error contacting ComfyUI: {e}")
    return render_template('index.html', image_url=image_url)


if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)
