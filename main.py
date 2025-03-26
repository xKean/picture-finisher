import gradio as gr
import numpy as np
from PIL import Image, ImageDraw
from comfyui_client import run_comfyui_workflow

def update_layout():
    """
    Aktualisiert sofort das Layout:
    - Blendet die Input-Ansicht (Zeichenfläche) aus.
    - Zeigt die Ergebnis-Ansicht mit Ladeplatzhaltern an.
    """
    # Erstelle einen Ladeplatzhalter (graues Bild mit "Lade..."-Text)
    loading_img = Image.new("RGB", (300, 300), color="gray")
    draw = ImageDraw.Draw(loading_img)
    draw.text((75, 140), "Lade...", fill="white")
    # Ergebnisansicht sichtbar; setze beide Bildfelder auf den Ladeplatzhalter;
    # Input-Ansicht wird ausgeblendet.
    return gr.update(visible=True), loading_img, loading_img, gr.update(visible=False)

def process_sketch(input_image, selected_theme, prompt_text):
    """
    Verarbeitet den Input aus dem Zeichenbereich:
    - Konvertiert den Input (aus gr.Paint) in ein PIL-Image.
    - Führt den ComfyUI-Workflow aus und liefert das tatsächliche Vorschau- und Ergebnisbild.
    """
    if isinstance(input_image, dict):
        if "composite" in input_image:
            arr = input_image["composite"]
            input_image_pil = Image.fromarray(arr.astype("uint8"))
        elif "background" in input_image:
            arr = input_image["background"]
            input_image_pil = Image.fromarray(arr.astype("uint8"))
        else:
            return None, None
    elif isinstance(input_image, np.ndarray):
        input_image_pil = Image.fromarray(input_image.astype("uint8"))
    else:
        input_image_pil = input_image

    output_img = run_comfyui_workflow(input_image_pil, selected_theme, prompt_text)
    return input_image_pil, output_img

def reset_view():
    """
    Setzt die Ansicht zurück:
    - Blendet die Ergebnisansicht aus und zeigt wieder die Eingabeansicht an.
    """
    return gr.update(visible=False), gr.update(visible=True)

with gr.Blocks() as demo:
    gr.Markdown("## Exponat Gradio App")
    
    # Obere Steuerelemente (bleiben immer sichtbar)
    with gr.Row():
        theme_dropdown = gr.Dropdown(
            choices=["Zeichnung", "Fantasy", "Sci-Fi"],
            value="Zeichnung",
            label="Setting/Theme"
        )
        prompt_textbox = gr.Textbox(
            lines=2,
            placeholder="What does your picture show?",
            label="Prompt"
        )
        submit_btn = gr.Button("Absenden")
    
    # Hauptcontainer für die Ansichten
    with gr.Column() as main_container:
        # Eingabe-Ansicht: Zeichenbereich (gr.Paint)
        with gr.Column(visible=True) as input_view:
            im_editor = gr.Paint(
                type="numpy",
                canvas_size=(1024, 1024),
                label="Zeichne dein Bild",
                height=700,
                width=600
            )
        # Ergebnis-Ansicht: Zeigt die Vorschau (Input) und das generierte Bild (Output) nebeneinander
        with gr.Column(visible=False) as result_view:
            with gr.Row():
                preview_image = gr.Image(type="numpy", label="Deine Zeichnung")
                output_image = gr.Image(label="Ergebnis")
            reset_btn = gr.Button("Neu zeichnen")
    
    # Beim Klick auf "Absenden" werden zwei Ereignisse an submit_btn gebunden:
    # 1. update_layout: Aktualisiert sofort das Layout (zeigt den Loader, blendet die Zeichenfläche aus).
    submit_btn.click(
        fn=update_layout,
        inputs=[],
        outputs=[result_view, preview_image, output_image, input_view]
    )
    # 2. process_sketch: Führt die rechenintensive Verarbeitung aus und aktualisiert die Bildfelder.
    submit_btn.click(
        fn=process_sketch,
        inputs=[im_editor, theme_dropdown, prompt_textbox],
        outputs=[preview_image, output_image]
    )
    
    # Reset-Button: Setzt die Ansicht zurück, sodass der Zeichenbereich wieder angezeigt wird.
    reset_btn.click(
        fn=reset_view,
        inputs=None,
        outputs=[result_view, input_view]
    )
    
    # Die Queue sorgt dafür, dass während der Verarbeitung ein Spinner angezeigt wird.
    demo.queue()

if __name__ == "__main__":
    demo.launch()
