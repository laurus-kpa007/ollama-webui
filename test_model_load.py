#!/usr/bin/env python3
"""
Model loading test script
"""

def test_model_loading():
    print("Starting model load test...")
    
    try:
        # Test library imports
        print("Checking libraries...")
        import torch
        import diffusers
        import transformers
        
        print(f"PyTorch: {torch.__version__}")
        print(f"Diffusers: {diffusers.__version__}")  
        print(f"Transformers: {transformers.__version__}")
        
        # Check GPU
        if torch.cuda.is_available():
            print(f"GPU available: {torch.cuda.get_device_name(0)}")
            print(f"GPU memory: {torch.cuda.get_device_properties(0).total_memory / 1e9:.1f}GB")
        else:
            print("No GPU - using CPU")
        
        # Test simple models in order
        test_models = [
            "runwayml/stable-diffusion-v1-5",
            "CompVis/stable-diffusion-v1-4"
        ]
        
        from diffusers import DiffusionPipeline
        
        for model_name in test_models:
            print(f"\nTesting: {model_name}")
            try:
                # Load with minimal settings
                pipe = DiffusionPipeline.from_pretrained(
                    model_name,
                    torch_dtype=torch.float16 if torch.cuda.is_available() else torch.float32
                )
                
                if torch.cuda.is_available():
                    pipe = pipe.to("cuda")
                else:
                    pipe = pipe.to("cpu")
                    
                print(f"Success: {model_name}")
                
                # Simple image generation test
                print("Testing image generation...")
                result = pipe(
                    "a beautiful cat", 
                    num_inference_steps=10,  # Low for fast test
                    width=512, 
                    height=512
                )
                print("Image generation successful!")
                
                # Clean up memory
                del pipe
                if torch.cuda.is_available():
                    torch.cuda.empty_cache()
                
                return True, model_name
                
            except Exception as e:
                print(f"Failed: {model_name} - {e}")
                continue
        
        return False, "All models failed to load"
        
    except ImportError as e:
        print(f"Missing library: {e}")
        print("Solution: pip install -r requirements.txt")
        return False, f"Missing library: {e}"
    
    except Exception as e:
        print(f"Unexpected error: {e}")
        return False, f"Unexpected error: {e}"

if __name__ == "__main__":
    success, message = test_model_loading()
    
    print("\n" + "="*50)
    if success:
        print(f"Test SUCCESS! Working model: {message}")
        print("Now try image generation in the web app.")
    else:
        print(f"Test FAILED: {message}")
        print("Solutions:")
        print("   1. pip install -r requirements.txt")
        print("   2. Check internet connection")
        print("   3. Check GPU drivers (NVIDIA GPU)")
        print("   4. Check disk space (for model download)")
    print("="*50)