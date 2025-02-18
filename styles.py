# styles.py

style_config = {
    "Zeichnung": {
         "additional_prompt": "sketch, pencil drawing, minimal shading",
         "loras": [
              {"on": True, "lora": "5yocrayon1_cap_d6a3e12.safetensors", "strength": 0.73},
              {"on": True, "lora": "Hand_drawn_pencil_drawing.safetensors", "strength": 0.7}
         ],
         "denoise_strength": 0.85
    },
    "Fantasy": {
         "additional_prompt": "epic fantasy, vivid colors, magical, mythp0rt",
         "loras": [
              {"on": True, "lora": "FluxMythP0rtr4itStyle.safetensors", "strength": 0.9}
         ],
         "denoise_strength": 0.85
    },
    "Sci-Fi": {
         "additional_prompt": "futuristic, high-tech, neon lighting",
         "loras": [
              {"on": True, "lora": "scifi_style.safetensors", "strength": 0.9}
         ],
         "denoise_strength": 0.85
    }
}
