#!/usr/bin/env python3
"""
Simple Qwen-Image test script
Tests the exact implementation from our app
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

def test_qwen_simple():
    print("Testing Qwen-Image implementation...")
    
    try:
        # Import our QwenImageClient
        from app import QwenImageClient
        
        # Create client
        client = QwenImageClient()
        
        # Check if libraries are available
        if not client.is_available():
            print("Required libraries not available")
            return False
            
        print("Libraries available, attempting to load model...")
        
        # Try to load model
        success = client.load_model()
        if not success:
            print("Model load failed")
            return False
            
        print(f"Model loaded successfully: {client.current_model_path}")
        
        # Test image generation
        print("Testing image generation...")
        prompt = "a beautiful cat sitting on a table"
        
        image, error = client.generate_image(
            prompt=prompt,
            width=512,  # Smaller for faster test
            height=512,
            num_inference_steps=20,  # Fewer steps for faster test
            guidance_scale=4.0
        )
        
        if error:
            print(f"Image generation failed: {error}")
            return False
            
        if image:
            # Save test image
            test_image_path = "test_generated_image.png"
            image.save(test_image_path)
            print(f"SUCCESS! Image saved to {test_image_path}")
            return True
        else:
            print("No image generated")
            return False
            
    except Exception as e:
        print(f"Test failed with error: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    print("="*50)
    print("Qwen-Image Simple Test")
    print("="*50)
    
    success = test_qwen_simple()
    
    print("\n" + "="*50)
    if success:
        print("SUCCESS! Image generation working!")
        print("Check test_generated_image.png")
    else:
        print("TEST FAILED!")
        print("Try installing PyTorch with CUDA:")
        print("   pip install torch torchvision --index-url https://download.pytorch.org/whl/cu124")
        print("   pip install diffusers transformers accelerate")
    print("="*50)