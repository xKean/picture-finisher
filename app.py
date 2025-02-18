import gradio as gr
import json
from PIL import Image, ImageDraw
import os
import time
import numpy as np
import io
import websocket
import uuid
import urllib.request
import urllib.parse
import base64
from io import BytesIO

# Konfiguration
server_address = "172.16.48.139:8188"
save_websocked_id = '53'
client_id = str(uuid.uuid4())

# Hilfsfunktion: Konvertiert ein PIL Image in einen Base64-String
def base64Image(image):
    buffered = BytesIO()
    image.save(buffered, format="PNG")
    return base64.b64encode(buffered.getvalue()).decode("utf-8")

# Sendet einen Prompt an den ComfyUI-Server und liefert die Antwort (als dict)
def queue_prompt(prompt):
    p = {"prompt": prompt, "client_id": client_id}
    data = json.dumps(p).encode("utf-8")
    req = urllib.request.Request("http://{}/prompt".format(server_address), data=data)
    return json.loads(urllib.request.urlopen(req).read())

# Liest via Websocket die ausgegebenen Bilddaten ab (hier für den SaveImageWebsocket-Node)
def get_images(ws, prompt):
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

# Hauptfunktion, die den ComfyUI-Workflow via Websocket ausführt
def run_comfyui_workflow(input_image, theme, prompt_text):
    # Lade den existierenden Workflow aus der Datei newWorkflow.json
    with open("newWorkflow.json", "r") as f:
        workflow = json.load(f)
    
    # Aktualisiere den Workflow:
    # In Node "29" wird der Base64-kodierte Inhalt des gezeichneten Bildes gesetzt
    workflow["29"]["inputs"]["image"] = base64Image(input_image)
    # In Node "7" wird der kombinierte Prompt (Theme - Prompt) gesetzt
    workflow["7"]["inputs"]["text"] = f"{theme} - {prompt_text}"
    
    # Konvertiere den aktualisierten Workflow in einen JSON-String
    workflow_str = json.dumps(workflow)
    
    # Verbinde via Websocket mit dem ComfyUI-Server
    ws = websocket.WebSocket()
    ws.connect("ws://{}/ws?clientId={}".format(server_address, client_id))
    
    # Sende den Workflow über den Websocket (queue_prompt wird intern genutzt)
    images = get_images(ws, workflow)
    ws.close()
    
    # Falls der SaveImageWebsocket-Node Ergebnisse geliefert hat, öffne das erste Bild
    if save_websocked_id in images and images[save_websocked_id]:
        img_data = images[save_websocked_id][0]
        try:
            output_image = Image.open(BytesIO(img_data))
            output_image.load()  # Bild vollständig laden
            return output_image
        except Exception as e:
            print("Fehler beim Öffnen des Bildes:", e)
    # Fallback: Erstelle ein Dummy-Bild, falls kein Ergebnis geliefert wurde
    dummy = Image.new("RGB", (1024, 1024), color="white")
    draw = ImageDraw.Draw(dummy)
    draw.text((10, 250), "Kein Bild", fill="white")
    print("Kein bild erhalten")
    return dummy

# Callback für die Gradio-App: Extrahiert den "composite"-Layer aus dem Paint-Editor
def process_sketch(input_image, selected_theme, prompt_text):
    # Falls der Paint-Editor ein dict zurückliefert, versuche den "composite"-Layer zu nutzen
    if isinstance(input_image, dict):
        if "composite" in input_image:
            arr = input_image["composite"]
            input_image_pil = Image.fromarray(arr.astype("uint8"))
        elif "background" in input_image:
            arr = input_image["background"]
            input_image_pil = Image.fromarray(arr.astype("uint8"))
        else:
            return gr.update(visible=False), None, None
    elif isinstance(input_image, np.ndarray):
        input_image_pil = Image.fromarray(input_image.astype("uint8"))
    else:
        input_image_pil = input_image

    # Führe den ComfyUI-Workflow aus und erhalte das generierte Bild
    output_img = run_comfyui_workflow(input_image_pil, selected_theme, prompt_text)
    # Gib als Vorschau nun das konvertierte PIL-Bild zurück (nicht das originale dict)
    return gr.update(visible=True), input_image_pil, output_img

# Gradio-App
with gr.Blocks() as demo:
    gr.Markdown("## Exponat Gradio App")
    
    # Initiale Ansicht: Großer Zeichenbereich (Paint) und Formularfelder
    with gr.Column() as initial_view:
        im_editor = gr.Paint(
            type="numpy",
            canvas_size=(1024,1024),  # Größe des Zeichenbereichs
            label="Zeichne dein Bild",
            height=600,
            width=600
        )
        theme_dropdown = gr.Dropdown(
            choices=["Zeichnung", "Fantasy", "Sci-Fi"],
            value="Zeichnung",
            label="Setting/Theme"
        )
        prompt_textbox = gr.Textbox(
            lines=2,
            placeholder="Was wurde gemalt?",
            label="Prompt"
        )
        submit_btn = gr.Button("Absenden")
    
    # Ergebnis-Ansicht: 50/50-Layout mit Originalzeichnung und Ergebnisbild; anfänglich unsichtbar
    with gr.Column(visible=False) as result_view:
        with gr.Row():
            preview_image = gr.Image(
                type="numpy",
                label="Deine Zeichnung"
            )
            output_image = gr.Image(
                label="Ergebnis"
            )
    
    # Beim Klick auf "Absenden" wird process_sketch aufgerufen; show_progress sorgt für einen Loader
    submit_btn.click(
        fn=process_sketch,
        inputs=[im_editor, theme_dropdown, prompt_textbox],
        outputs=[result_view, preview_image, output_image],
        show_progress=True
    )
    
    # Nutze die Queue, damit der Nutzer einen Spinner sieht
    demo.queue()

if __name__ == "__main__":
    demo.launch()
