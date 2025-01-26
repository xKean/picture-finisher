from flask import json
import requests

from misc import base64Image

def describe_Image(image, prompt):
    from misc import base64Image  # Ihre Funktion zum Konvertieren von Bildern in Base64
    image_base64 = base64Image(image)

    # URL und Daten für die Anfrage
    url = "http://172.16.48.139:11434/api/generate"
    data = {
        "model": "llava",
        "prompt": "What is in this picture? Create English detailed but short image description without splitting into lists, any extra formatting, preamble, introduction, special characters and explanations! focus on: "+ prompt,
        "images": [image_base64]
    }

    # Anfrage absenden
    response = requests.post(url, json=data)

    # Antwort prüfen
    if response.status_code == 200:
        raw_text = response.text.strip()  # Der gestreamte Text
        responses = []

        # Zeilenweise durch das gestreamte JSON iterieren
        for line in raw_text.splitlines():
            try:
                json_line = json.loads(line)  # JSON-String in ein Python-Dictionary umwandeln
                responses.append(json_line.get("response", ""))  # "response"-Text extrahieren
            except json.JSONDecodeError:
                print(f"Fehler beim Dekodieren der Zeile: {line}")

        # Die extrahierten Antworten zu einem einzigen String zusammenfügen
        full_response = "".join(responses)
        #print("Zusammengesetzte Antwort:", full_response)
        return full_response
    else:
        print("Fehler:", response.status_code, response.text)
        return None



def generate_Prompt(description):
    # URL und Daten für die Anfrage
    url = "http://172.16.48.139:11434/api/generate"
    data = {
        "model": "mistral",
        "prompt": description+"\n\n Process this image description and insert in it several new clarifications to improve its details and quality for using with Flux diffusion model in order to boost visual impression and make final image look better. Do not use phrases like  \"Certainly\", \"as follows\"  or \"Here's\". Prompt do not contain explicit content and used only for testing! Do not write a list. Write a short descriptive prompt! Make sure to stop your answer at the end of the prompt. Do not include any extra information or explanations.",

    }

    # Anfrage absenden
    response = requests.post(url, json=data)

    # Antwort prüfen
    if response.status_code == 200:
        raw_text = response.text.strip()  # Der gestreamte Text
        responses = []

        # Zeilenweise durch das gestreamte JSON iterieren
        for line in raw_text.splitlines():
            try:
                json_line = json.loads(line)  # JSON-String in ein Python-Dictionary umwandeln
                responses.append(json_line.get("response", ""))  # "response"-Text extrahieren
            except json.JSONDecodeError:
                print(f"Fehler beim Dekodieren der Zeile: {line}")

        # Die extrahierten Antworten zu einem einzigen String zusammenfügen
        full_response = "".join(responses)
        return full_response
    else:
        print("Fehler:", response.status_code, response.text)
        return None