import json
import uuid
import urllib.request
import urllib.parse
import websocket
import time
from io import BytesIO
from PIL import Image, ImageDraw
from utils import base64Image

# Konfiguration
server_address = "172.16.48.139:8188"
save_websocked_id = '53'  # ID des Nodes, der das Bild liefert
client_id = str(uuid.uuid4())

def queue_prompt(prompt):
    """
    Sendet einen Prompt an den ComfyUI-Server und gibt die Antwort (als dict) zurück.
    """
    p = {"prompt": prompt, "client_id": client_id}
    data = json.dumps(p).encode("utf-8")
    req = urllib.request.Request("http://{}/prompt".format(server_address), data=data)
    return json.loads(urllib.request.urlopen(req).read())

def get_images(ws, prompt):
    """
    Liest via Websocket die Bilddaten ab, die vom SaveImageWebsocket-Node kommen.
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

def run_comfyui_workflow(input_image, theme, prompt_text, workflow_file="workflow.json"):
    """
    Lädt den Workflow aus einer JSON-Datei, aktualisiert ihn mit dem Base64-kodierten Bild und
    dem kombinierten Prompt (Theme - Prompt) und führt den Workflow über Websocket aus.
    Gibt das generierte Bild (als PIL-Image) zurück.
    """
    # Workflow laden
    with open(workflow_file, "r") as f:
        workflow = json.load(f)
    
    # Workflow aktualisieren:
    # Setze in Node "29" den Base64-kodierten Inhalt des Bildes.
    workflow["29"]["inputs"]["image"] = base64Image(input_image)
    # Setze in Node "7" den kombinierten Prompt (Theme - Prompt).
    workflow["7"]["inputs"]["text"] = f"{theme} - {prompt_text}"
    
    # Optional: Workflow als String (falls benötigt)
    workflow_str = json.dumps(workflow)
    
    # Verbindung via Websocket herstellen
    ws = websocket.WebSocket()
    ws.connect("ws://{}/ws?clientId={}".format(server_address, client_id))
    
    # Sende den Workflow; get_images nutzt intern queue_prompt, um die Ausführung zu verfolgen.
    images = get_images(ws, workflow)
    ws.close()
    
    # Falls Ergebnisse vom SaveImageWebsocket-Node geliefert wurden, öffne das erste Bild.
    if save_websocked_id in images and images[save_websocked_id]:
        img_data = images[save_websocked_id][0]
        try:
            output_image = Image.open(BytesIO(img_data))
            output_image.load()  # Bild vollständig laden
            return output_image
        except Exception as e:
            print("Fehler beim Öffnen des Bildes:", e)
    # Fallback: Dummy-Bild erstellen, falls kein Ergebnis geliefert wurde.
    dummy = Image.new("RGB", (1024, 1024), color="white")
    draw = ImageDraw.Draw(dummy)
    draw.text((10, 250), "Kein Bild", fill="black")
    print("Kein Bild erhalten")
    return dummy
