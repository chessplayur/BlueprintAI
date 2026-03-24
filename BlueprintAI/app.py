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
- For complex flat logos or profiles, use linear_extrude(height = 10) combined with 2D primitives like circle() and square()
- Use module blocks for repeating parts. Use for loops (e.g., for(i=[0:90:270]) rotate([0,0,i])) to arrange repeating components symmetrically around a center point. 
- Use difference() aggressively to create features like eye sockets, bolt holes, or the 'mouth' of a wrench. Ensure the 'subtracted' shape is slightly taller than the main shape to avoid 'ghost' faces. 


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

EXAMPLE OF COMPLEX LOGO LOGIC (Skull & Wrenches):
module wrench() {
    difference() {
        union() {
            cylinder(h=10, r=15, center=true);
            translate([30,0,0]) cube([60, 10, 10], center=true);
        }
        translate([0,0,0]) rotate([0,0,30]) cube([20, 15, 12], center=true);
    }
}
for(i=[45:90:315]) rotate([0,0,i]) translate([40,0,0]) wrench();
// Followed by skull module...
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
        
        # Add image to message
        messages.append({
            "role": "user",
            "content": [
                {"type": "text", "text": user_input},
                {"type": "image_url", "image_url": {"url": "data:image/png;base64," + image_data}}
            ]
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
