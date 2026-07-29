import os
import base64
import math
import html
from io import BytesIO
from PIL import Image, ImageOps, ImageEnhance, ImageFilter

def get_avatar_b64(image_path='Sachinxcode-01.jpg', size=(400, 400), quality=85):
    """Crop, resize and base64 encode the profile photo for crisp SVG embedding."""
    if not os.path.exists(image_path):
        print(f"Warning: {image_path} not found.")
        return ""
    img = Image.open(image_path).convert('RGB')
    w, h = img.size
    min_dim = min(w, h)
    left = (w - min_dim) // 2
    top = (h - min_dim) // 2
    crop = img.crop((left, top, left + min_dim, top + min_dim))
    resized = crop.resize(size, Image.Resampling.LANCZOS)
    
    # Slight contrast enhancement for rich display
    enhancer = ImageEnhance.Contrast(resized)
    resized = enhancer.enhance(1.08)
    
    buf = BytesIO()
    resized.save(buf, format='JPEG', quality=quality, optimize=True)
    b64 = base64.b64encode(buf.getvalue()).decode('utf-8')
    return f"data:image/jpeg;base64,{b64}"

def generate_banner(dark_mode=True):
    avatar_b64 = get_avatar_b64('Sachinxcode-01.jpg')
    
    palette = {
        'bg': '#0A101F' if dark_mode else '#F8FAFC',
        'panel_bg': '#0D1527' if dark_mode else '#FFFFFF',
        'border': '#1E293B' if dark_mode else '#E2E8F0',
        'stroke_glow': 'rgba(34, 211, 238, 0.4)' if dark_mode else 'rgba(8, 145, 178, 0.3)',
        'cyan': '#22D3EE' if dark_mode else '#0891B2',
        'purple': '#A78BFA' if dark_mode else '#7C3AED',
        'emerald': '#10B981' if dark_mode else '#059669',
        'text': '#F8FAFC' if dark_mode else '#0F172A',
        'muted': '#94A3B8' if dark_mode else '#475569',
        'dim': '#475569' if dark_mode else '#94A3B8',
        'live': '#EF4444',
        'leader': '#1E293B' if dark_mode else '#E2E8F0'
    }
    
    gid = "banner_grad_dark" if dark_mode else "banner_grad_light"
    
    svg = []
    svg.append('<svg xmlns="http://www.w3.org/2000/svg" xmlns:xlink="http://www.w3.org/1999/xlink" viewBox="0 0 1180 610" width="1180" height="610">')
    
    # SVG Definitions
    svg.append('<defs>')
    # Fonts & Styles
    svg.append('''<style>
        @import url('https://fonts.googleapis.com/css2?family=Fira+Code:wght@400;500;600;700&amp;display=swap');
        text { font-family: "Fira Code", ui-monospace, monospace; }
        @keyframes pulse { 0%, 100% { opacity: 1; } 50% { opacity: 0.3; } }
        @keyframes scanline { 0% { transform: translateY(0); } 100% { transform: translateY(220px); } }
        .live-dot { animation: pulse 1.5s infinite; }
    </style>''')
    
    # Gradients
    svg.append(f'''
        <linearGradient id="{gid}" x1="0" y1="0" x2="1" y2="0">
            <stop offset="0%" stop-color="{palette['purple']}">
                <animate attributeName="stop-color" values="{palette['purple']};{palette['cyan']};{palette['emerald']};{palette['purple']}" dur="10s" repeatCount="indefinite"/>
            </stop>
            <stop offset="100%" stop-color="{palette['cyan']}">
                <animate attributeName="stop-color" values="{palette['cyan']};{palette['emerald']};{palette['purple']};{palette['cyan']}" dur="10s" repeatCount="indefinite"/>
            </stop>
        </linearGradient>

        <linearGradient id="ringGrad1" x1="0" y1="0" x2="1" y2="1">
            <stop offset="0%" stop-color="{palette['cyan']}"/>
            <stop offset="50%" stop-color="{palette['purple']}"/>
            <stop offset="100%" stop-color="{palette['emerald']}"/>
        </linearGradient>

        <linearGradient id="ringGrad2" x1="1" y1="0" x2="0" y2="1">
            <stop offset="0%" stop-color="{palette['purple']}"/>
            <stop offset="100%" stop-color="{palette['cyan']}"/>
        </linearGradient>

        <linearGradient id="scanGrad" x1="0" y1="0" x2="1" y2="0">
            <stop offset="0%" stop-color="{palette['cyan']}" stop-opacity="0"/>
            <stop offset="20%" stop-color="{palette['cyan']}" stop-opacity="0.9"/>
            <stop offset="50%" stop-color="#FFFFFF" stop-opacity="1"/>
            <stop offset="80%" stop-color="{palette['purple']}" stop-opacity="0.9"/>
            <stop offset="100%" stop-color="{palette['purple']}" stop-opacity="0"/>
        </linearGradient>

        <linearGradient id="scanAura" x1="0" y1="0" x2="0" y2="1">
            <stop offset="0%" stop-color="{palette['cyan']}" stop-opacity="0.35"/>
            <stop offset="100%" stop-color="{palette['cyan']}" stop-opacity="0"/>
        </linearGradient>

        <!-- Avatar Round Clipping Mask -->
        <clipPath id="avatarClip">
            <circle cx="230" cy="265" r="105"/>
        </clipPath>

        <!-- Scanline Rect Clipping -->
        <clipPath id="avatarScanClip">
            <circle cx="230" cy="265" r="104"/>
        </clipPath>
        
        <!-- Glow Filter -->
        <filter id="neonGlow" x="-20%" y="-20%" width="140%" height="140%">
            <feGaussianBlur stdDeviation="3" result="blur"/>
            <feMerge>
                <feMergeNode in="blur"/>
                <feMergeNode in="SourceGraphic"/>
            </feMerge>
        </filter>
    ''')
    svg.append('</defs>')

    # 1. Main Background Window
    svg.append(f'<rect width="1180" height="610" rx="14" fill="{palette["bg"]}" stroke="{palette["border"]}" stroke-width="2"/>')

    # 2. Window Header Bar
    svg.append(f'<rect width="1180" height="42" rx="14" fill="{palette["panel_bg"]}"/>')
    svg.append(f'<rect y="28" width="1180" height="14" fill="{palette["panel_bg"]}"/>')
    svg.append(f'<line x1="0" y1="42" x2="1180" y2="42" stroke="{palette["border"]}" stroke-width="1.5"/>')
    svg.append(f'<line x1="0" y1="42" x2="1180" y2="42" stroke="url(#{gid})" stroke-width="1.5" opacity="0.8"/>')

    # Mac Window Controls
    svg.append('<circle cx="25" cy="21" r="6" fill="#EF4444"/>')
    svg.append('<circle cx="45" cy="21" r="6" fill="#F59E0B"/>')
    svg.append('<circle cx="65" cy="21" r="6" fill="#10B981"/>')

    # Header Bar Titles
    svg.append(f'<text x="90" y="26" font-size="13" font-weight="600" fill="{palette["muted"]}"><tspan fill="{palette["cyan"]}">profile.sh</tspan> --live --interactive</text>')
    svg.append(f'<text x="1060" y="26" font-size="13" font-weight="700" fill="{palette["cyan"]}">VISUAL.HUD</text>')

    # 3. Left Panel (Profile Avatar & Cybernetic HUD)
    svg.append(f'<rect x="40" y="65" width="380" height="505" rx="10" fill="{palette["panel_bg"]}" stroke="{palette["border"]}" stroke-width="1.5"/>')
    
    # Left Header Label & Live Indicator
    svg.append(f'<text x="60" y="95" font-size="13" font-weight="700" fill="{palette["cyan"]}">SYSTEM.PORTRAIT</text>')
    svg.append(f'<circle cx="320" cy="91" r="5" fill="{palette["live"]}" class="live-dot"/>')
    svg.append(f'<text x="332" y="95" font-size="12" font-weight="700" fill="{palette["live"]}">LIVE</text>')
    svg.append(f'<line x1="60" y1="106" x2="400" y2="106" stroke="{palette["border"]}" stroke-width="1"/>')

    # Cyber HUD Decorative Crosshairs & Coordinates
    svg.append(f'<text x="60" y="125" font-size="10" fill="{palette["dim"]}">POS: 23.04N / 77.20E</text>')
    svg.append(f'<text x="325" y="125" font-size="10" fill="{palette["dim"]}">SYS.VER: 4.2</text>')

    # Corner Sci-Fi Target Brackets around avatar box
    # Top-Left
    svg.append(f'<path d="M100 170 h20 v-20" fill="none" stroke="{palette["cyan"]}" stroke-width="2"/>')
    # Top-Right
    svg.append(f'<path d="M360 170 h-20 v-20" fill="none" stroke="{palette["cyan"]}" stroke-width="2"/>')
    # Bottom-Left
    svg.append(f'<path d="M100 360 h20 v20" fill="none" stroke="{palette["cyan"]}" stroke-width="2"/>')
    # Bottom-Right
    svg.append(f'<path d="M360 360 h-20 v20" fill="none" stroke="{palette["cyan"]}" stroke-width="2"/>')

    # Background Ambient Hologram Aura
    svg.append(f'<circle cx="230" cy="265" r="118" fill="{palette["purple"]}" opacity="0.08" filter="url(#neonGlow)"/>')

    # Base Photo Avatar (`Sachinxcode-01.jpg` embedded)
    if avatar_b64:
        svg.append(f'<image href="{avatar_b64}" x="120" y="155" width="220" height="220" preserveAspectRatio="xMidYMid slice" clip-path="url(#avatarClip)"/>')
    else:
        svg.append(f'<circle cx="230" cy="265" r="105" fill="{palette["purple"]}" opacity="0.3"/>')

    # Animated Hologram Scanner Beam
    svg.append(f'<g clip-path="url(#avatarScanClip)">')
    # Aura rectangle trailing behind scan line
    svg.append(f'<rect x="110" y="130" width="240" height="35" fill="url(#scanAura)">')
    svg.append(f'<animate attributeName="y" values="130;340;130" dur="3.8s" repeatCount="indefinite" calcMode="spline" keyTimes="0;0.5;1" keySplines="0.4 0 0.6 1;0.4 0 0.6 1"/>')
    svg.append(f'</rect>')
    # Sharp Laser Line
    svg.append(f'<line x1="110" y1="165" x2="350" y2="165" stroke="url(#scanGrad)" stroke-width="3" filter="url(#neonGlow)">')
    svg.append(f'<animate attributeName="y1" values="165;375;165" dur="3.8s" repeatCount="indefinite" calcMode="spline" keyTimes="0;0.5;1" keySplines="0.4 0 0.6 1;0.4 0 0.6 1"/>')
    svg.append(f'<animate attributeName="y2" values="165;375;165" dur="3.8s" repeatCount="indefinite" calcMode="spline" keyTimes="0;0.5;1" keySplines="0.4 0 0.6 1;0.4 0 0.6 1"/>')
    svg.append(f'</line>')
    svg.append(f'</g>')

    # Concentric Rotating Neon Cyber Rings
    # Outer Ring 1 (Clockwise)
    svg.append(f'<circle cx="230" cy="265" r="112" fill="none" stroke="url(#ringGrad1)" stroke-width="2.5" stroke-dasharray="140 40 70 30" filter="url(#neonGlow)">')
    svg.append(f'<animateTransform attributeName="transform" type="rotate" from="0 230 265" to="360 230 265" dur="14s" repeatCount="indefinite"/>')
    svg.append(f'</circle>')

    # Middle Ring 2 (Counter-Clockwise)
    svg.append(f'<circle cx="230" cy="265" r="120" fill="none" stroke="url(#ringGrad2)" stroke-width="1.8" stroke-dasharray="60 30 180 40">')
    svg.append(f'<animateTransform attributeName="transform" type="rotate" from="360 230 265" to="0 230 265" dur="9s" repeatCount="indefinite"/>')
    svg.append(f'</circle>')

    # Thin Outer Precision Ring 3 (Clockwise)
    svg.append(f'<circle cx="230" cy="265" r="128" fill="none" stroke="{palette["cyan"]}" opacity="0.5" stroke-width="1" stroke-dasharray="2 8 4 8">')
    svg.append(f'<animateTransform attributeName="transform" type="rotate" from="0 230 265" to="360 230 265" dur="24s" repeatCount="indefinite"/>')
    svg.append(f'</circle>')

    # Orbiting Tech Satellites around Avatar
    tech_nodes = [
        ("Flutter", 152, 0, palette["cyan"]),
        ("React", 152, 90, palette["purple"]),
        ("Python", 152, 180, palette["emerald"]),
        ("AI / ML", 152, 270, palette["cyan"])
    ]

    # Rotating Orbit Group
    svg.append(f'<g>')
    svg.append(f'<animateTransform attributeName="transform" type="rotate" from="0 230 265" to="360 230 265" dur="20s" repeatCount="indefinite"/>')
    for label, orbit_r, angle_deg, node_col in tech_nodes:
        rad = math.radians(angle_deg)
        nx = 230 + orbit_r * math.cos(rad)
        ny = 265 + orbit_r * math.sin(rad)
        
        # Satellite Node Circle
        svg.append(f'<circle cx="{nx:.1f}" cy="{ny:.1f}" r="15" fill="{palette["panel_bg"]}" stroke="{node_col}" stroke-width="1.5" filter="url(#neonGlow)"/>')
        
        # Counter-rotate text so labels remain upright while orbiting!
        svg.append(f'<g transform="translate({nx:.1f}, {ny:.1f})">')
        svg.append(f'<g>')
        svg.append(f'<animateTransform attributeName="transform" type="rotate" from="0" to="-360" dur="20s" repeatCount="indefinite"/>')
        svg.append(f'<text x="0" y="3.5" text-anchor="middle" font-size="8" font-weight="700" fill="{node_col}">{label}</text>')
        svg.append(f'</g>')
        svg.append(f'</g>')
    svg.append(f'</g>')

    # Audio / Signal Wave Equalizer Bars under portrait
    svg.append(f'<g transform="translate(130, 422)">')
    svg.append(f'<text x="-70" y="12" font-size="10" font-weight="600" fill="{palette["muted"]}">SIGNAL</text>')
    bar_heights = [14, 22, 10, 28, 18, 32, 12, 24, 16, 26, 8, 20]
    for i, h in enumerate(bar_heights):
        bx = i * 15
        svg.append(f'<rect x="{bx}" y="{35-h}" width="8" height="{h}" rx="3" fill="{palette["cyan"]}" opacity="0.85">')
        # Animate height to mimic live audio equalizer
        h_min = max(4, h // 3)
        h_max = min(36, h + 10)
        dur = 0.8 + (i % 5) * 0.25
        svg.append(f'<animate attributeName="height" values="{h};{h_min};{h_max};{h}" dur="{dur:.2f}s" repeatCount="indefinite"/>')
        svg.append(f'<animate attributeName="y" values="{35-h};{35-h_min};{35-h_max};{35-h}" dur="{dur:.2f}s" repeatCount="indefinite"/>')
        svg.append(f'</rect>')
    svg.append(f'</g>')

    # Handle Tag Badge
    svg.append(f'<rect x="100" y="490" width="260" height="38" rx="19" fill="{palette["purple"]}" opacity="0.12" stroke="{palette["purple"]}" stroke-width="1.5"/>')
    svg.append(f'<text x="230" y="514" text-anchor="middle" font-size="15" font-weight="700" fill="{palette["purple"]}"><tspan fill="{palette["cyan"]}">@</tspan>Sachinxcode-01</text>')


    # 4. Right Panel (Developer System Specs & Tech Stack)
    svg.append(f'<rect x="450" y="65" width="690" height="505" rx="10" fill="{palette["panel_bg"]}" stroke="{palette["border"]}" stroke-width="1.5"/>')

    rows = [
        ("SECTION", "SYSTEM.INFO", ""),
        ("Subject", "Sachin", palette["text"]),
        ("Role", "Full-Stack & AI Engineer", palette["cyan"]),
        ("Origin", "India", palette["text"]),
        ("Education", "B.Tech CSE (Google Student Amb. 2026)", palette["text"]),
        ("Status", "Building + Learning + Shipping", palette["emerald"]),
        ("ToolChain", "VS Code, Git, Android Studio, Figma", palette["text"]),
        ("SECTION", "STACK.CORE", ""),
        ("Core.Lang", "Python, JavaScript, TypeScript, Dart, C++", palette["cyan"]),
        ("Core.Frontend", "React, Next.js, Flutter, Tailwind", palette["text"]),
        ("Core.Backend", "Node.js, Express, FastAPI", palette["text"]),
        ("Core.Database", "MongoDB, PostgreSQL, SQLite", palette["text"]),
        ("Core.Infra", "Vercel, Firebase, Docker, Git Actions", palette["text"]),
        ("SECTION", "CONNECT.GRID", ""),
        ("Grid.Mail", "kalinganavarsachin@gmail.com", palette["cyan"]),
        ("Grid.Portfolio", "github.com/Sachinxcode-01", palette["text"]),
        ("Grid.LinkedIn", "linkedin.com/in/sachin-k-5b6689322", palette["emerald"]),
        ("Grid.GitHub", "@Sachinxcode-01", palette["purple"]),
    ]

    start_y = 100
    y_step = 24
    curr_y = start_y

    for row in rows:
        r_type = row[0]
        if r_type == "SECTION":
            curr_y += 6
            svg.append(f'<text x="470" y="{curr_y}" font-size="13" font-weight="700" fill="{palette["emerald"]}">{row[1]}</text>')
            svg.append(f'<line x1="470" y1="{curr_y+5}" x2="1110" y2="{curr_y+5}" stroke="{palette["border"]}" stroke-width="1"/>')
            curr_y += 20
        else:
            label, val, val_color = row
            label_len = len(label)
            val_len = len(val)
            max_chars = 72
            num_dots = max(3, max_chars - label_len - val_len)
            leader_str = "." * num_dots
            
            val_esc = html.escape(val)
            svg.append(f'<text x="470" y="{curr_y}" font-size="13" font-weight="500" fill="{palette["muted"]}">{html.escape(label)}</text>')
            svg.append(f'<text x="600" y="{curr_y}" font-size="13" fill="{palette["leader"]}">{leader_str}</text>')
            val_x = 1110 - (val_len * 7.8)
            svg.append(f'<text x="{val_x:.1f}" y="{curr_y}" font-size="13" font-weight="600" fill="{val_color}">{val_esc}</text>')
            curr_y += y_step

    # Typing Cursor animation at bottom right
    svg.append(f'<text x="470" y="540" font-size="12" fill="{palette["cyan"]}">user@sachin-dev:~$ <tspan fill="{palette["text"]}">exec --deploy-profile</tspan><tspan fill="{palette["cyan"]}">_</tspan>')
    svg.append(f'<animate attributeName="opacity" values="1;0;1" dur="1s" repeatCount="indefinite"/>')
    svg.append(f'</text>')

    svg.append('</svg>')
    
    filename = 'dark.svg' if dark_mode else 'light.svg'
    svg_str = '\n'.join(svg)
    with open(filename, 'w', encoding='utf-8') as f:
        f.write(svg_str)
        
    alt_filename = 'banner_dark.svg' if dark_mode else 'banner_light.svg'
    with open(alt_filename, 'w', encoding='utf-8') as f:
        f.write(svg_str)
        
    print(f"Generated {filename} ({len(svg_str)//1024} KB) successfully!")

if __name__ == '__main__':
    generate_banner(dark_mode=True)
    generate_banner(dark_mode=False)
