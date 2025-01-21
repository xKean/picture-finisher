from flask import Flask, request, render_template, jsonify
import requests
import base64
from PIL import Image
import io

app = Flask(__name__)

# Automatic1111 API endpoint
#AUTOMATIC1111_API_URL = "http://localhost:7860/sdapi/v1/txt2img"
AUTOMATIC1111_API_URL = "http://localhost:7860/sdapi/v1/img2img"


@app.route("/")
def index():
    return render_template("index.html")

@app.route("/generate", methods=["POST"])
def generate_image():
    # Get uploaded image and prompt
    uploaded_file = request.files["image"]
    prompt = request.form["prompt"]

    # Preprocess the image
    image = Image.open(uploaded_file).convert("RGB")
    buffered = io.BytesIO()
    image.save(buffered, format="PNG")
    image_base64 = base64.b64encode(buffered.getvalue()).decode("utf-8")

    # Prepare payload for Automatic1111 API
    payload = {
        "prompt": prompt,
        "init_images": [image_base64],
        "steps": 50,
        "width": 512,
        "height": 512,
    }

    # Send request to Automatic1111
    response = requests.post(AUTOMATIC1111_API_URL, json=payload)
    if response.status_code == 200:
        result = response.json()
        generated_image_base64 = result["images"][0]
        return jsonify({"image": generated_image_base64})
    else:
        return jsonify({"error": "Image generation failed"}), 500

if __name__ == "__main__":
    app.run(debug=True)