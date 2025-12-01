"""
Analyze training data to understand structure for prompt engineering
"""
import os
import base64
from pathlib import Path
from openai import OpenAI
from dotenv import load_dotenv

load_dotenv()

client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

def analyze_image(image_path: str, filename: str):
    """Analyze an image to understand its structure"""
    print(f"\n{'='*80}")
    print(f"ANALYZING: {filename}")
    print('='*80)
    
    # Read and encode image
    img_bytes = Path(image_path).read_bytes()
    img_base64 = base64.b64encode(img_bytes).decode('utf-8')
    
    # Detailed analysis prompt
    analysis_prompt = """Analyze this architectural drawing in detail:

1. What type of drawing is this? (floor plan, wall section, roof framing, etc.)

2. How many distinct SECTIONS or DETAILS are shown? List each one with its label/number.

3. For EACH section/detail, what ROOF information is visible:
   - Roof framing (trusses, rafters, joists)?
   - Sheathing specifications?
   - Roof slope/pitch?
   - Roof-to-wall connections?
   - Fastening details?
   - Any roof-related notes or callouts?

4. What other building elements are shown (walls, foundations, etc.)?

5. Are there any material specifications, dimensions, or notes visible?

Be specific and thorough. Quote exact text you can read from the drawing."""

    try:
        response = client.chat.completions.create(
            model="gpt-5.1",
            max_completion_tokens=2000,
            messages=[{
                "role": "user",
                "content": [
                    {"type": "text", "text": analysis_prompt},
                    {"type": "image_url", "image_url": {"url": f"data:image/png;base64,{img_base64}"}}
                ]
            }]
        )
        
        analysis = response.choices[0].message.content
        print(analysis)
        print()
        
        return analysis
        
    except Exception as e:
        print(f"ERROR: {e}")
        return None

if __name__ == "__main__":
    training_dir = Path("/Users/durgamaheshboppani/Desktop/MAS/Training Data")
    
    # Analyze sample images
    print("\n" + "█"*80)
    print("TRAINING DATA ANALYSIS - Understanding Structure for Prompt Engineering")
    print("█"*80)
    
    # Analyze sample.png first
    sample_path = training_dir / "sample.png"
    if sample_path.exists():
        analyze_image(str(sample_path), "sample.png")
    
    # Analyze sample1.png
    sample1_path = training_dir / "sample1.png"
    if sample1_path.exists():
        analyze_image(str(sample1_path), "sample1.png")
    
    print("\n" + "█"*80)
    print("ANALYSIS COMPLETE")
    print("█"*80)
