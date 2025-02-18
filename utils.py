import base64
from io import BytesIO
from PIL import Image

def base64Image(image):
    """
    Konvertiert ein PIL-Image in einen Base64-kodierten String.
    """
    buffered = BytesIO()
    image.save(buffered, format="PNG")
    return base64.b64encode(buffered.getvalue()).decode("utf-8")
