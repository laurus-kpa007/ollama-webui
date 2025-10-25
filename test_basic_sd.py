#!/usr/bin/env python3
"""
Basic Stable Diffusion test - minimal dependencies
"""

def test_basic_sd():
    print("Testing basic Stable Diffusion...")
    
    try:
        # Test basic imports first
        print("1. Testing imports...")
        import torch
        print(f"   PyTorch: {torch.__version__}")
        
        # Check if we can import the minimal parts we need
        try:
            from diffusers import StableDiffusionPipeline
            print("   StableDiffusionPipeline: OK")
        except Exception as e:
            print(f"   StableDiffusionPipeline: FAILED - {e}")
            return False
            
        print("2. Testing model load...")
        # Try the smallest, most compatible model
        model_id = "runwayml/stable-diffusion-v1-5"
        
        # Load with minimal settings for compatibility
        pipe = StableDiffusionPipeline.from_pretrained(
            model_id,
            torch_dtype=torch.float32,  # Use float32 for CPU compatibility
            safety_checker=None,        # Disable safety checker to reduce dependencies
            requires_safety_checker=False
        )
        
        # Move to CPU (most compatible)
        device = "cpu"
        pipe = pipe.to(device)
        
        print(f"   Model loaded on: {device}")
        
        print("3. Testing image generation...")
        # Generate a simple image
        prompt = "a red apple on a table"
        
        # Use minimal settings for fast test
        image = pipe(
            prompt=prompt,
            num_inference_steps=10,  # Very low for fast test
            width=256,              # Small size for speed
            height=256,
            guidance_scale=7.5
        ).images[0]
        
        # Save the result
        output_path = "test_basic_sd_output.png"
        image.save(output_path)
        
        print(f"   Image saved to: {output_path}")
        print("SUCCESS! Basic Stable Diffusion is working!")
        return True
        
    except Exception as e:
        print(f"FAILED: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    print("="*50)
    print("Basic Stable Diffusion Test")
    print("="*50)
    
    success = test_basic_sd()
    
    print("\n" + "="*50)
    if success:
        print("✓ BASIC TEST PASSED!")
        print("Now we can proceed with Qwen-Image")
    else:
        print("✗ BASIC TEST FAILED!")
        print("Need to fix basic dependencies first")
    print("="*50)