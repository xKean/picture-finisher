import json
import uuid
import urllib.request
import urllib.parse
import websocket
import time
import random
from io import BytesIO
from PIL import Image, ImageDraw
from utils import base64Image
from styles import style_config

# Konfiguration
server_address = "127.0.0.1:8188"
save_websocked_id = '53'  # ID des Nodes, der das Bild liefert
client_id = str(uuid.uuid4())

def queue_prompt(prompt):
    """
    Sendet einen Prompt an den ComfyUI-Server und gibt die Antwort als dict zurück.
    """
    p = {"prompt": prompt, "client_id": client_id}
    data = json.dumps(p).encode("utf-8")
    req = urllib.request.Request("http://{}/prompt".format(server_address), data=data)
    return json.loads(urllib.request.urlopen(req).read())

def get_images(ws, prompt):
    """
    Liest über den Websocket die vom SaveImageWebsocket-Node ausgegebenen Bilddaten aus.
    """
    prompt_id = queue_prompt(prompt)['prompt_id']
    output_images = {}
    current_node = ""
    while True:
        out = ws.recv()
        if isinstance(out, str):
            message = json.loads(out)
            if message['type'] == 'executing':
                data = message['data']
                if data['prompt_id'] == prompt_id:
                    if data['node'] is None:
                        break  # Ausführung abgeschlossen
                    else:
                        current_node = data['node']
        else:
            if current_node == save_websocked_id:
                images_output = output_images.get(current_node, [])
                # Entferne die ersten 8 Bytes (Header) – wie im Beispiel
                images_output.append(out[8:])
                output_images[current_node] = images_output
    return output_images

def run_comfyui_workflow(input_image, selected_style, prompt_text, workflow_file="workflow.json"):
    """
    Lädt den Workflow aus der JSON-Datei, aktualisiert ihn basierend auf dem gewählten Zeichenstil
    und führt den Workflow über Websocket aus. Gibt das generierte Bild (als PIL-Image) zurück.
    """
    # Workflow laden
    with open(workflow_file, "r") as f:
        workflow = json.load(f)
    
    # Hole die Style-Konfiguration (falls vorhanden)
    config = style_config.get(selected_style, {})

    # Workflow aktualisieren:
    # - Node "29": Bild-Input (als Base64)
    workflow["29"]["inputs"]["image"] = base64Image(input_image)
    # - Node "7": Text-Prompt: Kombination aus gewähltem Stil, eingegebenem Prompt und zusätzlichen Wörtern
    base_prompt = f"{selected_style} - {prompt_text}"
    if "additional_prompt" in config:
        base_prompt += " " + config["additional_prompt"]
    workflow["7"]["inputs"]["text"] = base_prompt

    # - Lora-Konfigurationen: Überschreibe komplett die Werte in Node "52"
    if "loras" in config and "52" in workflow and "inputs" in workflow["52"]:
        for i, lora_entry in enumerate(config["loras"]):
            key = f"lora_{i+1}"
            if key in workflow["52"]["inputs"]:
                workflow["52"]["inputs"][key]["on"] = lora_entry.get("on", True)
                workflow["52"]["inputs"][key]["lora"] = lora_entry["lora"]
                workflow["52"]["inputs"][key]["strength"] = lora_entry["strength"]

    # - Denoise-Strength: Aktualisiere ggf. Node "26"
    if "denoise_strength" in config:
        if "26" in workflow and "inputs" in workflow["26"]:
            workflow["26"]["inputs"]["denoise"] = config["denoise_strength"]

    # - Random Seed: Setze in Node "23" einen zufälligen Seed
    if "23" in workflow and "inputs" in workflow["23"]:
        workflow["23"]["inputs"]["noise_seed"] = random.randint(0, 10**18)

    # Optional: Workflow in einen String umwandeln, falls benötigt
    workflow_str = json.dumps(workflow)
    
    # Verbindung via Websocket herstellen
    ws = websocket.WebSocket()
    ws.connect("ws://{}/ws?clientId={}".format(server_address, client_id))
    
    # Sende den Workflow über den Websocket; get_images nutzt intern queue_prompt, um den Fortschritt zu verfolgen.
    images = get_images(ws, workflow)
    ws.close()
    
    # Falls der SaveImageWebsocket-Node Ergebnisse liefert, öffne das erste Bild
    if save_websocked_id in images and images[save_websocked_id]:
        img_data = images[save_websocked_id][0]
        try:
            output_image = Image.open(BytesIO(img_data))
            output_image.load()  # Bild vollständig laden
            return output_image
        except Exception as e:
            print("Fehler beim Öffnen des Bildes:", e)
    # Fallback: Dummy-Bild erzeugen, falls kein Ergebnis geliefert wurde
    dummy = Image.new("RGB", (1024, 1024), color="white")
    draw = ImageDraw.Draw(dummy)
    draw.text((10, 250), "Kein Bild", fill="black")
    print("Kein Bild erhalten")
    return dummy
