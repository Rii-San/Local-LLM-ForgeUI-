import time
import base64
from pathlib import Path
import requests
import json

forgeUI_address = "http://localhost:7860"

# Fetch available models from ForgeUI
def get_available_models():
    try:
        response = requests.get(f"{forgeUI_address}/sdapi/v1/sd-models")
        response.raise_for_status()
        models = response.json()
        return [model["title"] for model in models]
    except Exception as e:
        print(f"Error fetching models: {e}")
        return []


# Parameters for ForgeUI image generation
params = {
    'model': 'astranime_V6',
    'vae_model': '',
    'clip_skip': 2,
    'prompt_prefix': '(masterpiece:1.1, Best quality:1.2), (Intricate details:1.1, ultra-detailed:1.1), 1girl, solo,  cinematic lighting, dynamic composition, ethereal atmosphere, (artistic shading:1.2), fantasy, storybook illustration style, (Style-Petal:0.8), Perfect proportions, beautiful Japanese woman, pretty face, perfect face,  pointy nose, cute nose',
    'prompt_postfix': '<lora:kittew-artist-richy-v1:0.6>,  lips,kittew artstyle,  <lora:add_detail:0.4>,  <lora:detailed-anime:0.8>, (Ultra detailed eyes, expressive eyes), Perfect proportions,  Expressive brush strokes, Detailed art style, Vibrant colors',
    'negative_prompt': 'EasyNegative, (worst quality:1.5, low quality:1.5, normal quality:1.5), lowres, Style-Petal-neg, (monochrome, grayscale), (bad-hands-5:0.8), (negative_hand-neg:0.8), ng_deepnegative_v1_75t, (bad-artist, bad-artist-anime, bad-image-v2-39000), (BadDream:0.5), (verybadimagenegative_v1.3:0.6)',
    'width': 512,
    'height': 512,
    'steps': 12,
    'sampler': 'Euler a',
    'scheduler': 'Automatic', 
    'high_res_fix': True,
    'hires_steps': 8,
    'upscaler': 'R-ESRGAN 4x+ Anime6B',
    'upscale_factor': 1.5,
    'denoising_strength': 0.45,
    'cfg_scale': 8,
    'hires_cfg_scale':6,
    'batch_size': 1,
    'seed' : -1,
}


def generate_image(description):
    global params
    payload = {
        "prompt": params['prompt_prefix'] + "," + description + "," + params['prompt_postfix'],
        "negative_prompt": params['negative_prompt'],
        "seed": params['seed'],
        "sampler_name": params['sampler'], 
        "scheduler": params['scheduler'], 
        "enable_hr": params['high_res_fix'], 
        "hr_second_pass_steps": params['hires_steps'],  
        "hr_upscaler": params['upscaler'],  
        "hr_scale": params['upscale_factor'],  
        "denoising_strength": params['denoising_strength'],
        "steps": params['steps'],
        "cfg_scale": params['cfg_scale'],
        "hires_cfg_scale": params['hires_cfg_scale'],
        "width": params['width'],
        "height": params['height'],
        "override_settings": {  
            "sd_model_checkpoint": params['model'],
            #"sd_vae": params['vae_model'],
            "CLIP_stop_at_last_layers": params['clip_skip'],
        },
        "batch_size": params['batch_size'],
        "hr_additional_modules": [],
    }
    print(f'\n\n Generating image with prompt: {payload["prompt"]}')

    num_retries = 3
    for attempt in range(num_retries):
        try:
            response = requests.post(url=f'{forgeUI_address}/sdapi/v1/txt2img', json=payload)
            response.raise_for_status()
            result = response.json()
            break
        except Exception as e:
            print(f"Error generating image: {e}")
            if attempt == num_retries - 1:
                return ""
        time.sleep(1)


    if 'images' in result and len(result['images']) > 0:
        img_str = result['images'][0]
        img_dir = Path("img")
        img_dir.mkdir(parents=True, exist_ok=True)
        filename = img_dir / f'{int(time.time())}.png'
        with open(filename.as_posix(), 'wb') as f:
            f.write(base64.b64decode(img_str))
        return filename.as_posix()
    return ""


if __name__ == '__main__':

    models = get_available_models()
    if models:
        print("Available models:", models)
    else:
        print("No models found.")

    # Generate an image
    generate_image("enchanted forest, deep forest, greerny, old farm house, fantasy landscape, halloween, pumpkins")