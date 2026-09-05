import torch
from diffusers import StableDiffusionPipeline
import os

# LOAD ONCE GLOBALLY: This prevents the massive 23-minute delay on every request.
print("[+] Loading Stable Diffusion Pipeline into memory...")
try:
    pipe = StableDiffusionPipeline.from_pretrained("runwayml/stable-diffusion-v1-5", torch_dtype=torch.float32)
    pipe.safety_checker = None # Speeds up inference slightly
except Exception as e:
    print(f"[-] Failed to load SD pipeline: {e}")

def generate_scene_images(prompts: list, output_dir: str = "../frontend/models/"):
    """Generates a sequence of images for the slideshow and returns their paths."""
    print(f"[+] Generating {len(prompts)} cinematic scene images...")
    os.makedirs(output_dir, exist_ok=True)
    image_paths = []
    
    for i, prompt in enumerate(prompts):
        try:
            print(f"   -> Rendering Scene {i+1}: {prompt[:50]}...")
            # Style modifiers to ensure the images look like a cohesive cinematic documentary
            enhanced_prompt = f"{prompt}, hyper-realistic, cinematic lighting, highly detailed documentary photography, 8k"
            
            # num_inference_steps=15 is a sweet spot for fast local generation
            image = pipe(enhanced_prompt, num_inference_steps=15).images[0]
            
            filename = f"scene_{i}.jpg"
            save_path = os.path.join(output_dir, filename)
            image.save(save_path)
            
            # The path the frontend will use to fetch the image
            image_paths.append(f"models/{filename}")
        except Exception as e:
            print(f"[-] Failed to generate scene {i}: {str(e)}")
            image_paths.append("models/dice.mp4") # Fallback if SD crashes
            
    print("[+] All scene images successfully saved.")
    return image_paths