from flask import Flask, request, render_template, jsonify
from PIL import Image
from apiclient import getApiClient
from misc import base64Image

app = Flask(__name__)

# API-Client
api = getApiClient("172.16.48.139")


@app.route("/")
def index():
    return render_template("index.html")


@app.route("/generate", methods=["POST"])
def generate_image():
    # Bild und Prompt aus der Anfrage abrufen
    uploaded_file = request.files["image"]
    prompt = request.form["prompt"]

    # Bild verarbeiten
    image = Image.open(uploaded_file).convert("RGB")

    # Bild mit API generieren
    result = api.img2img(images=[image], prompt=prompt)

    # Das generierte Bild in einen Base64-String umwandeln
    returnImage = base64Image(result.image);

    return jsonify({"image": returnImage})


if __name__ == "__main__":
    app.run(debug=True)
