import os
import requests
from PIL import Image, ImageDraw, ImageFont
import textwrap
import uuid


IMAGE_WIDHT_DEFAULT = 1200 
IMAGE_HEIGTH_DEFAULT = 675 
TEXT_MARGIN_DEFAULT = 60

FONTS = {
    "Poppins": {
        "filename": "Poppins-Bold.ttf",
        "url": "https://raw.githubusercontent.com/google/fonts/main/ofl/poppins/Poppins-Bold.ttf",
        "default_size": 80
    },
    "Lato": {
        "filename": "Lato-Bold.ttf",
        "url": "https://raw.githubusercontent.com/google/fonts/main/ofl/lato/Lato-Bold.ttf",
        "default_size": 85
    }
}




COLOR_PALETTES = {
    "Ocean Deep": {"top": (23, 37, 84), "bottom": (67, 139, 222)},
    "Royal Purple": {"top": (46, 11, 66), "bottom": (3, 166, 166)},
    "Sunset": {"top": (106, 4, 15), "bottom": (242, 126, 3)},
    "Forest": {"top": (10, 48, 6), "bottom": (102, 179, 48)},
    "Graphite": {"top": (15, 15, 15), "bottom": (80, 80, 80)}
}


def donwload_font(font_choice: str) -> str | None: 

    if font_choice not in FONTS:
        return None
    
    font_info = FONTS[font_choice]
    filename = font_info["filename"]
    
    if os.path.exists(filename) and os.path.getsize(filename) > 0:
        return filename

    try:
        #print(f"Downloading font: {font_choice} from {font_info['url']}") 
        r = requests.get(font_info["url"], stream=True, timeout=10)
        r.raise_for_status()
        with open(filename, 'wb') as f:
            for chunk in r.iter_content(chunk_size=8192):
                f.write(chunk)
        print(f"Sucessfully downloaded {filename}")
        return filename
    except requests.exceptions.RequestException as e:
        print(f"could not download font: {e}") 
        return None

def hex_to_Rgb(h: str) -> tuple[int, int, int] | None: 
    """Converts a hex color string to an RGB tuple."""
    h = h.lstrip('#')
    if len(h) == 3:
        h = "".join([c*2 for c in h])

    if len(h) == 6:

        try:
            return (int(h[0:2], 16), int(h[2:4], 16), int(h[4:6], 16))
        except ValueError:
            return None
    return None

def create_gradient_background(w, h, c1, c2, direction):

    base = Image.new('RGB', (w, h), c1)
    top = Image.new('RGB', (w, h), c2)
    
    if direction == 'vertical':
        mask_data = [int(255 * (y / h)) for y in range(h) for _ in range(w)]
    else: 
        mask_data = [int(255 * (x / w)) for _ in range(h) for x in range(w)]
        
    mask = Image.new('L', (w, h))
    mask.putdata(mask_data)
    base.paste(top, (0, 0), mask)
    return base

def create_image(
    text: str,
    font_choice: str,
    pallete_choice: str, 
    v_align: str,
    h_align: str,
    custom_color1: str | None = None,
    custom_color2: str | None = None,
) -> str:

    width, height = IMAGE_WIDHT_DEFAULT, IMAGE_HEIGTH_DEFAULT 

    if custom_color1 and custom_color2:
        c1, c2 = hex_to_Rgb(custom_color1), hex_to_Rgb(custom_color2) 
        if not c1 or not c2:
            return "Error: invalid custom hex color provided." 
    else:
        palette = COLOR_PALETTES.get(pallete_choice)
        if not palette:
            return f"Error: Pallete '{pallete_choice}' not found." 
        c1, c2 = palette["top"], palette["bottom"]

    font_filename = donwload_font(font_choice)
    if not font_filename:
        return "Error: Could not get the specified font." 
    
    font_info = FONTS[font_choice]
    font_size = font_info["default_size"]
    try:
        pil_font = ImageFont.truetype(font_filename, font_size)
    except IOError: 
        return f"Error: Font file '{font_filename}' is bad." 

    img = create_gradient_background(width, height, c1, c2, 'vertical')
    draw = ImageDraw.Draw(img)

    wrap_width = 40 
    lines = textwrap.wrap(text, width=wrap_width)

    line_heights = [draw.textbbox((0, 0), line, font=pil_font)[3] for line in lines]
    spacing = 20
    total_text_height = sum(line_heights) + (spacing * (len(lines) - 1))

    if v_align == 'top':
        y = TEXT_MARGIN_DEFAULT
    elif v_align == 'bottom':
        y = height - total_text_height - TEXT_MARGIN_DEFAULT
    else: 
        y = (height - total_text_height) / 2

    for i, line in enumerate(lines):
        line_width = draw.textbbox((0, 0), line, font=pil_font)[2]
        
        if h_align == 'left':
            x = TEXT_MARGIN_DEFAULT
        elif h_align == 'right':
            x = width - line_width - TEXT_MARGIN_DEFAULT
        else: 
            x = (width - line_width) / 2
        
        draw.text((x, y), line, font=pil_font, fill=(255, 255, 255))
        y += line_heights[i] + spacing

    output_filenme = f"temp_image_{uuid.uuid4()}.png"
    img.save(output_filenme)
    return output_filenme