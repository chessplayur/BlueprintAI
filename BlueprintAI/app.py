from flask import Flask, request, jsonify
from flask_cors import CORS
from groq import Groq
import base64
from PIL import Image
import io

app = Flask(__name__)
CORS(app) # This allows your HTML file to talk to this Python script

client = Groq(api_key="Groq API Key Goes Here")

@app.route('/chat', methods=['POST'])
def chat():
    user_input = request.json.get('message')
    image_data = request.json.get('image')
    
    print(f"Image data received: {bool(image_data)}")  # Debug line
    
    system_prompt = """You are an expert OpenSCAD engineer assistant. Your ONLY job is to generate valid OpenSCAD code.

CRITICAL RULES:
- NEVER provide explanations, descriptions, or mathematical calculations
- ONLY return OpenSCAD code
- ALWAYS start with $fn = 60;
- Use proper OpenSCAD syntax with semicolons
- Use translate([x,y,z]) for positioning
- Common shapes: cube([x,y,z]), cylinder(h,r), sphere(r)
- For complex shapes, use difference() and union()

IMAGE ANALYSIS RULES (when user mentions "image" or "reference"):
- If user says "simple cube/box": Generate basic cube([20,20,20])
- If user says "cylinder": Generate cylinder(h=30, r=10)
- If user says "sphere": Generate sphere(r=10)
- If user says "bolt": Generate cylinder head + shaft
- If user says "bracket": Generate L-shaped bracket
- If user says "gear": Generate gear with teeth
- If user says "complex": Use union/difference with multiple shapes
- Default to simple shapes unless specifically asked for complexity

EXAMPLE INPUT/OUTPUT:
Input: "make a sphere"
Output: $fn = 60;
sphere(r=10);

Input: "create a cylinder with radius 2"  
Output: $fn = 60;
cylinder(h=20, r=2);

Input: "make a bolt"
Output: $fn = 60;
cylinder(h=5, r=10, center=true);
translate([0,0,15]) cylinder(h=30, r=5, center=true);

Input: "create this from the image" (assume simple object)
Output: $fn = 60;
cube([20, 20, 20]);

DO NOT EXPLAIN. DO NOT DESCRIBE. ONLY CODE."""

    messages = [{"role": "system", "content": system_prompt}]
    
    # Add image if provided
    if image_data:
        print("Processing image...")  # Debug line
        # Remove data URL prefix and decode
        image_data = image_data.split(',')[1] if ',' in image_data else image_data
        image_bytes = base64.b64decode(image_data)
        
        # Convert to PIL Image and save temporarily
        image = Image.open(io.BytesIO(image_bytes))
        image.save('temp_reference.png')
        
        # Add image to message with smart context
        enhanced_message = f"{user_input}\n\n[Reference image provided - generate appropriate OpenSCAD code. If unsure, default to a simple cube.]"
        messages.append({
            "role": "user",
            "content": enhanced_message
        })
    else:
        messages.append({"role": "user", "content": user_input})

    try:
        completion = client.chat.completions.create(
            model="llama-3.2-11b-vision-preview",  # Try 11b vision model
            messages=messages
        )
        return jsonify({"response": completion.choices[0].message.content})
    except Exception as e:
        print(f"Error: {e}")
        # Fallback to text model if vision fails
        completion = client.chat.completions.create(
            model="llama-3.3-70b-versatile",
            messages=messages
        )
        return jsonify({"response": completion.choices[0].message.content})

if __name__ == '__main__':
    app.run(port=5000)
