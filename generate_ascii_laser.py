import os
import math
import random
import numpy as np
from PIL import Image, ImageDraw, ImageFont, ImageOps, ImageEnhance, ImageFilter

# ASCII character ramp from lowest to highest luminance
RAMP = " .:-=+*#%@"

def load_font(font_size=16):
    """Attempt to load a crisp monospace TTF font, falling back to default."""
    font_candidates = [
        "consola.ttf", "consolas.ttf", "cour.ttf", "courier.ttf", 
        "lucon.ttf", "DejaVuSansMono.ttf", "FreeMono.ttf"
    ]
    for font_name in font_candidates:
        try:
            return ImageFont.truetype(font_name, font_size), font_size
        except OSError:
            continue
    try:
        # Try system font paths on Windows
        win_fonts = [
            "C:\\Windows\\Fonts\\consola.ttf",
            "C:\\Windows\\Fonts\\cour.ttf",
            "C:\\Windows\\Fonts\\lucon.ttf"
        ]
        for path in win_fonts:
            if os.path.exists(path):
                return ImageFont.truetype(path, font_size), font_size
    except Exception:
        pass
    return ImageFont.load_default(), font_size

def process_image_to_ascii_grid(image_path, cols=84, rows=42):
    """Load photo, crop square, contrast enhance, and convert to 2D ASCII grid."""
    if not os.path.exists(image_path):
        raise FileNotFoundError(f"Source photo {image_path} not found.")

    img = Image.open(image_path).convert('L')
    
    # Square crop center
    w, h = img.size
    min_dim = min(w, h)
    left = (w - min_dim) // 2
    top = (h - min_dim) // 2
    img_cropped = img.crop((left, top, left + min_dim, top + min_dim))
    
    # Resize to target cols x rows
    img_resized = img_cropped.resize((cols, rows), Image.Resampling.LANCZOS)
    
    # Enhance contrast & sharpness for crisp facial features
    img_contrast = ImageOps.autocontrast(img_resized, cutoff=2)
    enhancer = ImageEnhance.Contrast(img_contrast)
    img_enhanced = enhancer.enhance(1.4)
    img_sharp = img_enhanced.filter(ImageFilter.UnsharpMask(radius=1.5, percent=150))
    
    arr = np.array(img_sharp, dtype=np.float32)
    
    # Map pixel brightness (0..255) to ASCII character index
    ramp_len = len(RAMP)
    char_grid = []
    val_grid = []
    
    for r in range(rows):
        char_row = []
        val_row = []
        for c in range(cols):
            val = arr[r, c]
            idx = int((val / 255.0) * (ramp_len - 1))
            idx = max(0, min(ramp_len - 1, idx))
            char_row.append(RAMP[idx])
            val_row.append(val)
        char_grid.append(char_row)
        val_grid.append(val_row)
        
    return char_grid, val_grid, cols, rows

def draw_laser_beam(draw, y_pos, width, color_cyan, color_purple):
    """Draw glowing multi-layer laser scan beam."""
    # Outer bloom aura
    draw.rectangle([20, y_pos - 6, width - 20, y_pos + 6], fill=(34, 211, 238, 40))
    draw.rectangle([30, y_pos - 3, width - 30, y_pos + 3], fill=(167, 139, 250, 90))
    # Core bright beam
    draw.line([(35, y_pos), (width - 35, y_pos)], fill=(255, 255, 255), width=2)

def generate_ascii_laser_gif(
    image_path="Sachinxcode-01.jpg", 
    output_path="assets/ascii-laser-intro.gif", 
    cols=84, 
    rows=42, 
    total_frames=52
):
    """Generate Cyberpunk ASCII-Photo + Laser-Scan animated GIF."""
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    
    char_grid, val_grid, cols, rows = process_image_to_ascii_grid(image_path, cols, rows)
    
    font, font_size = load_font(15)
    
    # Monospace cell measurements
    cell_w = 9
    cell_h = 17
    
    margin_x = 45
    margin_y = 65
    
    canvas_w = margin_x * 2 + cols * cell_w
    canvas_h = margin_y + rows * cell_h + 55
    
    # Color palette
    bg_color = (10, 10, 15)            # #0A0A0F dark cyberpunk bg
    hud_border_color = (30, 41, 59)   # #1E293B border
    text_muted_color = (100, 116, 139) # #64748B
    cyan_accent = (34, 211, 238)       # #22D3EE
    purple_accent = (167, 139, 250)   # #A78BFA
    emerald_accent = (16, 185, 129)    # #10B981
    white_color = (248, 250, 252)
    
    frames = []
    
    ascii_top_y = margin_y
    ascii_bottom_y = margin_y + rows * cell_h
    
    for frame_idx in range(total_frames):
        img = Image.new('RGB', (canvas_w, canvas_h), color=bg_color)
        draw = ImageDraw.Draw(img)
        
        progress = frame_idx / float(total_frames - 1)
        
        # 1. Outer HUD Window Frame & Corner Brackets ┌ ┐ └ ┘
        draw.rectangle([15, 15, canvas_w - 15, canvas_h - 15], outline=hud_border_color, width=1)
        
        # Corner Brackets
        c_len = 16
        # Top-Left ┌
        draw.line([(15, 15), (15 + c_len, 15)], fill=cyan_accent, width=2)
        draw.line([(15, 15), (15, 15 + c_len)], fill=cyan_accent, width=2)
        # Top-Right ┐
        draw.line([(canvas_w - 15, 15), (canvas_w - 15 - c_len, 15)], fill=cyan_accent, width=2)
        draw.line([(canvas_w - 15, 15), (canvas_w - 15, 15 + c_len)], fill=cyan_accent, width=2)
        # Bottom-Left └
        draw.line([(15, canvas_h - 15), (15 + c_len, canvas_h - 15)], fill=cyan_accent, width=2)
        draw.line([(15, canvas_h - 15), (15, canvas_h - 15 - c_len)], fill=cyan_accent, width=2)
        # Bottom-Right ┘
        draw.line([(canvas_w - 15, canvas_h - 15), (canvas_w - 15 - c_len, canvas_h - 15)], fill=cyan_accent, width=2)
        draw.line([(canvas_w - 15, canvas_h - 15), (canvas_w - 15, canvas_h - 15 - c_len)], fill=cyan_accent, width=2)
        
        # Header Info Bar
        draw.text((30, 26), "[ SYS.BOOT_SCAN // @Sachinxcode-01 ]", font=font, fill=cyan_accent)
        draw.text((canvas_w - 160, 26), "GRID: 84x42", font=font, fill=purple_accent)
        draw.line([(30, 48), (canvas_w - 30, 48)], fill=hud_border_color, width=1)
        
        # Determine laser scan position & reveal state
        # Frames 0..6: Dark bootup
        # Frames 6..34: Primary Laser Scan (Top -> Bottom)
        # Frames 34..44: Secondary Verification Laser Pass
        # Frames 44..52: Full Reveal + CRT Flicker + Fade Loop
        
        if frame_idx < 6:
            laser_y = -100
            scan_pct = 0
        elif frame_idx <= 34:
            scan_t = (frame_idx - 6) / 28.0
            laser_y = ascii_top_y + scan_t * (ascii_bottom_y - ascii_top_y)
            scan_pct = int(scan_t * 100)
        elif frame_idx <= 44:
            pass2_t = (frame_idx - 34) / 10.0
            laser_y = ascii_top_y + pass2_t * (ascii_bottom_y - ascii_top_y)
            scan_pct = 100
        else:
            laser_y = -100
            scan_pct = 100

        # Draw ASCII Grid
        for r in range(rows):
            row_y = margin_y + r * cell_h
            
            # Check if row has been passed/revealed by laser
            is_revealed = (laser_y >= row_y) or (frame_idx > 34)
            is_laser_row = abs(laser_y - row_y) < (cell_h * 1.2)
            
            if not is_revealed:
                continue
                
            for c in range(cols):
                char = char_grid[r][c]
                val = val_grid[r][c]
                x_pos = margin_x + c * cell_w
                
                # CRT Character Flicker on idle frames 44..52
                if frame_idx > 44 and random.random() < 0.02:
                    rand_idx = max(0, min(len(RAMP)-1, RAMP.find(char) + random.choice([-1, 1])))
                    char = RAMP[rand_idx]
                
                # Color calculation based on brightness & laser proximity
                if is_laser_row:
                    char_color = white_color
                else:
                    # Gradient palette: high brightness -> Cyan, mid -> Purple, low -> Muted
                    norm = val / 255.0
                    if norm > 0.65:
                        r_c = int(34 + (248 - 34) * (norm - 0.65) / 0.35)
                        g_c = int(211 + (250 - 211) * (norm - 0.65) / 0.35)
                        b_c = int(238 + (252 - 238) * (norm - 0.65) / 0.35)
                        char_color = (r_c, g_c, b_c)
                    elif norm > 0.30:
                        r_c = int(167 * norm)
                        g_c = int(139 * norm)
                        b_c = int(250 * norm)
                        char_color = (max(40, r_c), max(40, g_c), max(50, b_c))
                    else:
                        r_c = int(100 * norm + 20)
                        g_c = int(116 * norm + 20)
                        b_c = int(139 * norm + 30)
                        char_color = (r_c, g_c, b_c)
                        
                # Fade out slightly on last 3 frames to loop back to frame 0 smoothly
                if frame_idx >= total_frames - 3:
                    fade = 1.0 - ((frame_idx - (total_frames - 3)) / 3.0)
                    char_color = (int(char_color[0] * fade), int(char_color[1] * fade), int(char_color[2] * fade))

                draw.text((x_pos, row_y), char, font=font, fill=char_color)
                
        # Draw Laser Scan Line
        if laser_y > 0:
            draw_laser_beam(draw, int(laser_y), canvas_w, cyan_accent, purple_accent)
            
        # Footer Status & Progress Bar
        footer_y = canvas_h - 38
        draw.text((30, footer_y), f"STATUS: SCANNING [{scan_pct:3d}%]", font=font, fill=emerald_accent if scan_pct == 100 else cyan_accent)
        
        # Draw progress bar [██████░░░░]
        bar_x = 240
        bar_w = 200
        bar_h = 10
        draw.rectangle([bar_x, footer_y + 3, bar_x + bar_w, footer_y + 3 + bar_h], outline=hud_border_color)
        fill_w = int(bar_w * (scan_pct / 100.0))
        if fill_w > 0:
            draw.rectangle([bar_x, footer_y + 3, bar_x + fill_w, footer_y + 3 + bar_h], fill=cyan_accent)
            
        draw.text((canvas_w - 180, footer_y), "LOG: VERIFIED_OK", font=font, fill=emerald_accent if scan_pct == 100 else text_muted_color)
        
        frames.append(img)

    # Save animated GIF
    frames[0].save(
        output_path,
        save_all=True,
        append_images=frames[1:],
        duration=65,  # 65ms per frame = ~3.38s loop
        loop=0,
        optimize=True
    )
    
    file_size_mb = os.path.getsize(output_path) / (1024 * 1024)
    print(f"Generated {output_path} ({file_size_mb:.2f} MB, {len(frames)} frames) successfully!")

if __name__ == "__main__":
    generate_ascii_laser_gif()
