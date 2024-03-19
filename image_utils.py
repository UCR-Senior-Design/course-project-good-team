from PIL import Image
from io import BytesIO
import requests

def get_dominant_color(image_url):
    response = requests.get(image_url)
    img = Image.open(BytesIO(response.content))
    img = img.resize((150, 150))  # Resize for faster processing
    result = img.convert('P', palette=Image.ADAPTIVE, colors=1)  # Convert to palette mode
    result = result.convert('RGB')
    main_color = result.getcolors(150*150)[0][1]
    return '#%02x%02x%02x' % main_color  # Convert RGB to HEX

def get_contrasting_text_color(hex_color):
    # Convert hex color to RGB
    hex_color = hex_color.lstrip('#')
    r, g, b = tuple(int(hex_color[i:i+2], 16) for i in (0, 2, 4))
    
    # Calculate luminance
    luminance = (0.299 * r + 0.587 * g + 0.114 * b) / 255
    
    # Bright colors - black font, dark colors - white font
    return '#000000' if luminance > 0.5 else '#FFFFFF'