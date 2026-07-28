import os
import math
import numpy as np
from PIL import Image, ImageEnhance, ImageOps, ImageFilter
from scipy.ndimage import binary_closing, binary_fill_holes, label
from scipy.spatial import cKDTree

def segment_background(img_np, color_thresh=38):
    """
    Segment out background based on color distance from top corners/edges.
    Performs binary closing, fills holes, and keeps largest connected component.
    """
    h, w, _ = img_np.shape
    corner_colors = np.array([
        img_np[0, 0], img_np[0, -1], img_np[5, 5], img_np[5, -5]
    ], dtype=np.float32)
    bg_color = np.median(corner_colors, axis=0)

    dist = np.linalg.norm(img_np.astype(np.float32) - bg_color, axis=2)
    bg_mask = dist < color_thresh
    fg_mask = ~bg_mask

    fg_mask = binary_closing(fg_mask, structure=np.ones((5, 5)))
    fg_mask = binary_fill_holes(fg_mask)

    labeled, num_features = label(fg_mask)
    if num_features > 0:
        sizes = [np.sum(labeled == i) for i in range(1, num_features + 1)]
        largest_idx = np.argmax(sizes) + 1
        fg_mask = (labeled == largest_idx)

    return fg_mask

def process_dither(image_path, target_w=240, target_h=270, dark_mode=True):
    img = Image.open(image_path).convert('RGB')
    w, h = img.size
    
    # Head & shoulders framing
    crop_w = int(w * 0.85)
    crop_h = int(h * 0.90)
    left = (w - crop_w) // 2
    top = int(h * 0.02)
    img_cropped = img.crop((left, top, left + crop_w, top + crop_h))
    img_resized = img_cropped.resize((target_w, target_h), Image.Resampling.LANCZOS)
    
    img_np = np.array(img_resized)
    fg_mask = segment_background(img_np) if dark_mode else np.ones((target_h, target_w), dtype=bool)

    gray = img_resized.convert('L')
    gray = ImageOps.autocontrast(gray, cutoff=1)
    enhancer = ImageEnhance.Contrast(gray)
    gray = enhancer.enhance(1.3)
    gray = gray.filter(ImageFilter.UnsharpMask(radius=3, percent=140))
    
    arr = np.array(gray, dtype=np.float32)
    if dark_mode:
        arr[~fg_mask] = 255.0  # background forced light so dither produces no dots
        
    output = np.zeros((target_h, target_w), dtype=np.uint8)
    
    for y in range(target_h):
        reverse = (y % 2 == 1)
        x_range = range(target_w - 1, -1, -1) if reverse else range(target_w)
        
        for x in x_range:
            old_val = arr[y, x]
            if dark_mode:
                # Subject is lit: darker regions in grayscale map to dither dots for lit portrait
                dot = 1 if (old_val < 138 and fg_mask[y, x]) else 0
                err = old_val - (0.0 if dot else 255.0)
            else:
                dot = 1 if old_val < 120 else 0
                err = old_val - (0.0 if dot else 255.0)
                
            output[y, x] = dot
            
            if reverse:
                if x > 0: arr[y, x - 1] += err * (7.0 / 16.0)
                if y + 1 < target_h:
                    if x < target_w - 1: arr[y + 1, x + 1] += err * (3.0 / 16.0)
                    arr[y + 1, x] += err * (5.0 / 16.0)
                    if x > 0: arr[y + 1, x - 1] += err * (1.0 / 16.0)
            else:
                if x + 1 < target_w: arr[y, x + 1] += err * (7.0 / 16.0)
                if y + 1 < target_h:
                    if x > 0: arr[y + 1, x - 1] += err * (3.0 / 16.0)
                    arr[y + 1, x] += err * (5.0 / 16.0)
                    if x + 1 < target_w: arr[y + 1, x + 1] += err * (1.0 / 16.0)
                    
    if dark_mode:
        output[~fg_mask] = 0

    return output, fg_mask

# Logo shape generators for morphing travellers
def generate_logo_points(logo_type, count=900, center_x=230, center_y=300, radius=85):
    points = []
    if logo_type == 'flutter':
        for i in range(count):
            t = np.random.rand()
            if np.random.rand() > 0.4:
                x = center_x - radius * 0.4 + t * radius * 0.9
                y = center_y - radius * 0.8 + t * radius * 0.9
            else:
                x = center_x - radius * 0.2 + t * radius * 0.6
                y = center_y + radius * 0.1 + (1 - t) * radius * 0.6
            points.append((x + np.random.normal(0, 1.2), y + np.random.normal(0, 1.2)))
    elif logo_type == 'code':
        for i in range(count):
            r = np.random.rand()
            if r < 0.35:
                t = np.random.rand()
                x = center_x - radius * 0.2 - abs(t - 0.5) * radius * 0.8
                y = center_y + (t - 0.5) * radius * 1.2
            elif r < 0.70:
                t = np.random.rand()
                x = center_x + radius * 0.2 + abs(t - 0.5) * radius * 0.8
                y = center_y + (t - 0.5) * radius * 1.2
            else:
                t = np.random.rand()
                x = center_x + (0.5 - t) * radius * 0.6
                y = center_y + (t - 0.5) * radius * 1.4
            points.append((x + np.random.normal(0, 1.2), y + np.random.normal(0, 1.2)))
    elif logo_type == 'vercel':
        for i in range(count):
            u = np.random.rand()
            v = np.random.rand()
            if u + v > 1:
                u, v = 1 - u, 1 - v
            p0 = (center_x, center_y - radius * 0.8)
            p1 = (center_x - radius * 0.8, center_y + radius * 0.7)
            p2 = (center_x + radius * 0.8, center_y + radius * 0.7)
            x = p0[0] + u * (p1[0] - p0[0]) + v * (p2[0] - p0[0])
            y = p0[1] + u * (p1[1] - p0[1]) + v * (p2[1] - p0[1])
            points.append((x, y))
    return np.array(points, dtype=np.float32)

def compute_fast_trajectory_match(src_pts, dst_pts):
    """Fast nearest neighbor trajectory matching via cKDTree."""
    tree = cKDTree(dst_pts)
    _, indices = tree.query(src_pts)
    return dst_pts[indices]

def generate_svg(dark_mode=True):
    palette = {
        'bg': '#0A101F' if dark_mode else '#F8FAFC',
        'panel_bg': '#0D1527' if dark_mode else '#FFFFFF',
        'border': '#1E293B' if dark_mode else '#E2E8F0',
        'portrait': '#A78BFA' if dark_mode else '#7C3AED',
        'ui': '#10B981',
        'accent': '#22D3EE' if dark_mode else '#0891B2',
        'text': '#E2E8F0' if dark_mode else '#0F172A',
        'muted': '#64748B' if dark_mode else '#94A3B8',
        'live': '#EF4444'
    }

    dither_grid, fg_mask = process_dither('Sachinxcode-01.jpg', 240, 270, dark_mode=dark_mode)
    
    dots = []
    grid_h, grid_w = dither_grid.shape
    scale_x = 340.0 / grid_w
    scale_y = 380.0 / grid_h
    offset_x = 60.0
    offset_y = 120.0
    
    for y in range(grid_h):
        for x in range(grid_w):
            if dither_grid[y, x] == 1:
                px = offset_x + x * scale_x
                py = offset_y + y * scale_y
                dots.append((px, py))
                
    dots = np.array(dots, dtype=np.float32)
    total_dots = len(dots)
    print(f"Total portrait dots for {'dark' if dark_mode else 'light'} mode: {total_dots}")

    svg = []
    svg.append(f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 1180 610" width="1180" height="610">')
    svg.append(f'<style>')
    svg.append(f'@import url("https://fonts.googleapis.com/css2?family=Fira+Code:wght@400;500;600;700&amp;display=swap");')
    svg.append(f'text {{ font-family: "Fira Code", monospace; }}')
    svg.append(f'@keyframes pulse {{ 0%, 100% {{ opacity: 1; }} 50% {{ opacity: 0.3; }} }}')
    svg.append(f'.live-dot {{ animation: pulse 1.5s infinite; }}')
    svg.append(f'</style>')

    # Background window
    svg.append(f'<rect width="1180" height="610" rx="12" fill="{palette["bg"]}" stroke="{palette["border"]}" stroke-width="2"/>')
    
    # Header bar
    svg.append(f'<rect width="1180" height="42" rx="12" fill="{palette["panel_bg"]}"/>')
    svg.append(f'<line x1="0" y1="42" x2="1180" y2="42" stroke="{palette["border"]}" stroke-width="1.5"/>')
    
    # Window controls
    svg.append(f'<circle cx="25" cy="21" r="6" fill="#EF4444"/>')
    svg.append(f'<circle cx="45" cy="21" r="6" fill="#F59E0B"/>')
    svg.append(f'<circle cx="65" cy="21" r="6" fill="#10B981"/>')
    
    # Title bar labels
    svg.append(f'<text x="90" y="26" font-size="13" font-weight="600" fill="{palette["muted"]}">profile.sh --live</text>')
    svg.append(f'<text x="1080" y="26" font-size="13" font-weight="600" fill="{palette["ui"]}">VISUAL.MAP</text>')

    # Left Frame (Portrait Zone)
    svg.append(f'<rect x="40" y="65" width="380" height="505" rx="8" fill="{palette["panel_bg"]}" stroke="{palette["border"]}" stroke-width="1.5"/>')
    svg.append(f'<text x="60" y="95" font-size="13" font-weight="700" fill="{palette["ui"]}">SYSTEM.PORTRAIT</text>')

    # Pulse LIVE badge & Pill handle
    svg.append(f'<circle cx="320" cy="91" r="5" fill="{palette["live"]}" class="live-dot"/>')
    svg.append(f'<text x="332" y="95" font-size="12" font-weight="700" fill="{palette["live"]}">LIVE</text>')
    
    # Handle Pill
    svg.append(f'<rect x="60" y="515" width="180" height="32" rx="16" fill="{palette["portrait"]}" opacity="0.15"/>')
    svg.append(f'<text x="75" y="536" font-size="14" font-weight="600" fill="{palette["portrait"]}">@Sachinxcode-01</text>')

    # 1. Base Portrait Layer (Intro Fade-In over 3.2s via 60 scattered random groups)
    num_intro_groups = 60
    indices = np.arange(total_dots)
    np.random.shuffle(indices)
    group_chunks = np.array_split(indices, num_intro_groups)

    svg.append(f'<g fill="{palette["portrait"]}" shape-rendering="crispEdges">')
    for g_idx, chunk in enumerate(group_chunks):
        begin_time = (g_idx / num_intro_groups) * 2.0
        path_data = " ".join([f"M{dots[i, 0]:.1f},{dots[i, 1]:.1f}h1.6v1.6h-1.6z" for i in chunk])
        svg.append(f'<path d="{path_data}" opacity="0">')
        svg.append(f'<animate attributeName="opacity" values="0;1" dur="0.4s" begin="{begin_time:.2f}s" fill="freeze"/>')
        svg.append(f'</path>')
    svg.append(f'</g>')

    # 2. Morph Travellers (~900 dots)
    traveller_indices = np.random.choice(total_dots, size=900, replace=False)
    p0 = dots[traveller_indices] # Portrait initial
    p1 = compute_fast_trajectory_match(p0, generate_logo_points('flutter', 900, center_x=230, center_y=300))
    p2 = compute_fast_trajectory_match(p1, generate_logo_points('code', 900, center_x=230, center_y=300))
    p3 = compute_fast_trajectory_match(p2, generate_logo_points('vercel', 900, center_x=230, center_y=300))
    
    # SMIL Keyframe animation for travellers
    svg.append(f'<g fill="{palette["accent"]}">')
    for i in range(900):
        path_kfs = f"M{p0[i,0]:.1f},{p0[i,1]:.1f}; M{p0[i,0]:.1f},{p0[i,1]:.1f}; M{p1[i,0]:.1f},{p1[i,1]:.1f}; M{p1[i,0]:.1f},{p1[i,1]:.1f}; M{p2[i,0]:.1f},{p2[i,1]:.1f}; M{p2[i,0]:.1f},{p2[i,1]:.1f}; M{p3[i,0]:.1f},{p3[i,1]:.1f}; M{p3[i,0]:.1f},{p3[i,1]:.1f}; M{p0[i,0]:.1f},{p0[i,1]:.1f}"
        op_kfs = "0;0;1;1;1;1;1;1;0"
        svg.append(f'<rect width="2.5" height="2.5" rx="0.5" opacity="0">')
        svg.append(f'<animate attributeName="d" values="{path_kfs}" keyTimes="0;0.21;0.30;0.44;0.53;0.67;0.76;0.90;1" dur="14.2s" begin="3.2s" repeatCount="indefinite"/>')
        svg.append(f'<animate attributeName="opacity" values="{op_kfs}" keyTimes="0;0.21;0.30;0.44;0.53;0.67;0.76;0.90;1" dur="14.2s" begin="3.2s" repeatCount="indefinite"/>')
        svg.append(f'</rect>')
    svg.append(f'</g>')

    # Right Info Panel
    svg.append(f'<rect x="450" y="65" width="690" height="505" rx="8" fill="{palette["panel_bg"]}" stroke="{palette["border"]}" stroke-width="1.5"/>')
    
    rows = [
        ("SECTION", "SYSTEM.INFO", ""),
        ("Subject", "Sachin", palette["text"]),
        ("Role", "Full-Stack & AI Engineer", palette["accent"]),
        ("Origin", "India", palette["text"]),
        ("Education", "B.Tech CSE (Google Student Amb. 2026)", palette["text"]),
        ("Status", "Building + Learning + Shipping", palette["ui"]),
        ("ToolChain", "VS Code, Git, Android Studio, Figma", palette["text"]),
        ("SECTION", "STACK.CORE", ""),
        ("Core.Lang", "Python, JavaScript, TypeScript, Dart, C++", palette["accent"]),
        ("Core.Frontend", "React, Next.js, Flutter, Tailwind", palette["text"]),
        ("Core.Backend", "Node.js, Express, FastAPI", palette["text"]),
        ("Core.Database", "MongoDB, PostgreSQL, SQLite", palette["text"]),
        ("Core.Infra", "Vercel, Firebase, Docker, Git Actions", palette["text"]),
        ("SECTION", "CONNECT.GRID", ""),
        ("Grid.Mail", "kalinganavarsachin@gmail.com", palette["accent"]),
        ("Grid.Portfolio", "github.com/Sachinxcode-01", palette["text"]),
        ("Grid.LinkedIn", "linkedin.com/in/sachin-k-5b6689322", palette["ui"]),
        ("Grid.GitHub", "@Sachinxcode-01", palette["portrait"]),
    ]

    start_y = 100
    y_step = 24
    curr_y = start_y

    for row in rows:
        r_type = row[0]
        if r_type == "SECTION":
            curr_y += 6
            svg.append(f'<text x="470" y="{curr_y}" font-size="13" font-weight="700" fill="{palette["ui"]}">{row[1]}</text>')
            svg.append(f'<line x1="470" y1="{curr_y+5}" x2="1110" y2="{curr_y+5}" stroke="{palette["border"]}" stroke-width="1"/>')
            curr_y += 20
        else:
            label, val, val_color = row
            label_len = len(label)
            val_len = len(val)
            max_chars = 72
            num_dots = max(3, max_chars - label_len - val_len)
            leader_str = "." * num_dots
            
            svg.append(f'<text x="470" y="{curr_y}" font-size="13" font-weight="500" fill="{palette["muted"]}">{label}</text>')
            svg.append(f'<text x="600" y="{curr_y}" font-size="13" fill="{palette["border"]}">{leader_str}</text>')
            val_x = 1110 - (val_len * 7.8)
            svg.append(f'<text x="{val_x:.1f}" y="{curr_y}" font-size="13" font-weight="600" fill="{val_color}">{val}</text>')
            curr_y += y_step

    svg.append('</svg>')
    
    filename = 'banner_dark.svg' if dark_mode else 'banner_light.svg'
    with open(filename, 'w', encoding='utf-8') as f:
        f.write('\n'.join(svg))
    print(f"Generated {filename} successfully!")

if __name__ == '__main__':
    generate_svg(dark_mode=True)
    generate_svg(dark_mode=False)
