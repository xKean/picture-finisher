
import base64
import io


def base64Image (image):
    """Converts an image to a base64 string."""

    buffered = io.BytesIO()
    image.save(buffered, format="PNG")  # Ergebnis-Bild im PNG-Format speichern
    buffered.seek(0)
    image_base64 = base64.b64encode(buffered.getvalue()).decode("utf-8")
    return image_base64