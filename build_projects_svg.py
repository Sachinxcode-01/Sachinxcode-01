import json
import os

projects_data = [
  {
    "name": "Aurevia Premium Rentals",
    "repo": "Sachinxcode-01/aurevia-premium-rentals",
    "logo": "camera",
    "description": "Luxury 3D camera rental platform with Next.js, React Three Fiber & Anime.js featuring interactive booking & admin analytics.",
    "tags": ["NextJS", "TypeScript", "Tailwind", "Three.js"]
  },
  {
    "name": "MediConnect",
    "repo": "Sachinxcode-01/MediConnect",
    "logo": "health",
    "description": "Smart healthcare platform bridging patients and doctors via AI tools, appointment scheduling & electronic health records.",
    "tags": ["JavaScript", "React", "NodeJS", "AI"]
  },
  {
    "name": "Nexa Voice Assistant",
    "repo": "Sachinxcode-01/NexaVoiceAssistant",
    "logo": "mic",
    "description": "Python AI assistant featuring LiveKit integration, voice interaction, web search, WhatsApp messaging & desktop automation.",
    "tags": ["Python", "AI", "LiveKit", "Automation"]
  },
  {
    "name": "Digital Grievance System",
    "repo": "Sachinxcode-01/digitalgrievanceredressalsystem",
    "logo": "shield",
    "description": "Modern web platform streamlining grievance submission, live tracking, authority routing, and transparent resolutions.",
    "tags": ["JavaScript", "Express", "NodeJS", "Web"]
  },
  {
    "name": "KrishiAI",
    "repo": "Sachinxcode-01/KrishiAI",
    "logo": "leaf",
    "description": "AI-powered smart farming platform delivering real-time crop disease diagnosis, yield insights, and weather advisory.",
    "tags": ["JavaScript", "Python", "AI", "AgriTech"]
  },
  {
    "name": "REC Hackathon 1.0",
    "repo": "Sachinxcode-01/rec-hackathon",
    "logo": "trophy",
    "description": "Official hackathon portal featuring team registrations, live leaderboards, team matching, and event schedule management.",
    "tags": ["HTML", "CSS", "JavaScript", "Web"]
  }
]

# Write updated projects.json
with open("projects.json", "w", encoding="utf-8") as f:
    json.dump(projects_data, f, indent=2)

print("projects.json updated successfully.")

def get_svg_icon(logo_type, is_dark=True):
    # Embedded clean SVG vector icons (40x40 canvas)
    if logo_type == "camera":
        # 3D Camera / Aperture icon
        bg_col = "#1E1B4B" if is_dark else "#EEF2FF"
        main_col = "#818CF8" if is_dark else "#4F46E5"
        accent_col = "#22D3EE" if is_dark else "#0891B2"
        return f'''<g transform="translate(16, 44)">
          <rect width="40" height="40" rx="10" fill="{bg_col}"/>
          <path d="M12 15C12 13.8954 12.8954 13 14 13H17L18.5 11H21.5L23 13H26C27.1046 13 28 13.8954 28 15V25C28 26.1046 27.1046 27 26 27H14C12.8954 27 12 26.1046 12 25V15Z" stroke="{main_col}" stroke-width="2" fill="none"/>
          <circle cx="20" cy="20" r="4" stroke="{accent_col}" stroke-width="2" fill="none"/>
        </g>'''
    elif logo_type == "health":
        # Medical Cross + Heartbeat icon
        bg_col = "#064E3B" if is_dark else "#ECFDF5"
        main_col = "#34D399" if is_dark else "#059669"
        accent_col = "#A78BFA" if is_dark else "#7C3AED"
        return f'''<g transform="translate(16, 44)">
          <rect width="40" height="40" rx="10" fill="{bg_col}"/>
          <path d="M14 20H17L19 15L21 24L23 18L24.5 20H26" stroke="{main_col}" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" fill="none"/>
          <path d="M20 11V13M20 27V29M11 20H13M27 20H29" stroke="{accent_col}" stroke-width="1.5" stroke-linecap="round"/>
        </g>'''
    elif logo_type == "mic":
        # AI Mic / Audio wave icon
        bg_col = "#311042" if is_dark else "#F5F3FF"
        main_col = "#C084FC" if is_dark else "#7C3AED"
        accent_col = "#38BDF8" if is_dark else "#0284C7"
        return f'''<g transform="translate(16, 44)">
          <rect width="40" height="40" rx="10" fill="{bg_col}"/>
          <rect x="16" y="11" width="8" height="13" rx="4" stroke="{main_col}" stroke-width="2" fill="none"/>
          <path d="M12 20C12 24.4183 15.5817 28 20 28C24.4183 28 28 24.4183 28 20" stroke="{accent_col}" stroke-width="2" stroke-linecap="round" fill="none"/>
          <path d="M20 28V31" stroke="{accent_col}" stroke-width="2" stroke-linecap="round"/>
        </g>'''
    elif logo_type == "shield":
        # Digital Shield / Security icon
        bg_col = "#1E293B" if is_dark else "#F1F5F9"
        main_col = "#38BDF8" if is_dark else "#0284C7"
        accent_col = "#F43F5E" if is_dark else "#E11D48"
        return f'''<g transform="translate(16, 44)">
          <rect width="40" height="40" rx="10" fill="{bg_col}"/>
          <path d="M20 11L12 14V20C12 24.5 15.5 27.8 20 29C24.5 27.8 28 24.5 28 20V14L20 11Z" stroke="{main_col}" stroke-width="2" stroke-linejoin="round" fill="none"/>
          <path d="M17 20L19.5 22.5L23.5 17.5" stroke="{accent_col}" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" fill="none"/>
        </g>'''
    elif logo_type == "leaf":
        # KrishiAI / Leaf Sprout icon
        bg_col = "#14532D" if is_dark else "#F0FDF4"
        main_col = "#4ADE80" if is_dark else "#16A34A"
        accent_col = "#FACC15" if is_dark else "#CA8A04"
        return f'''<g transform="translate(16, 44)">
          <rect width="40" height="40" rx="10" fill="{bg_col}"/>
          <path d="M13 27C13 27 15 16 27 13C27 13 25 24 13 27Z" stroke="{main_col}" stroke-width="2" stroke-linejoin="round" fill="none"/>
          <path d="M13 27L21 19" stroke="{main_col}" stroke-width="2" stroke-linecap="round"/>
          <circle cx="25" cy="15" r="2" fill="{accent_col}"/>
        </g>'''
    else:
        # Trophy / Code icon
        bg_col = "#451A03" if is_dark else "#FFFBEB"
        main_col = "#FBBF24" if is_dark else "#D97706"
        accent_col = "#A78BFA" if is_dark else "#7C3AED"
        return f'''<g transform="translate(16, 44)">
          <rect width="40" height="40" rx="10" fill="{bg_col}"/>
          <path d="M14 12H26V18C26 21.3137 23.3137 24 20 24C16.6863 24 14 21.3137 14 18V12Z" stroke="{main_col}" stroke-width="2" fill="none"/>
          <path d="M20 24V28M16 28H24" stroke="{main_col}" stroke-width="2" stroke-linecap="round"/>
          <path d="M11 14H14M26 14H29" stroke="{accent_col}" stroke-width="2" stroke-linecap="round"/>
        </g>'''

def generate_svg(is_dark=True):
    bg_color = "#0A101F" if is_dark else "#F8FAFC"
    acc_id = "acc_dark" if is_dark else "acc_light"
    text_hdr = "#22D3EE" if is_dark else "#0891B2"
    text_sub = "#475569" if is_dark else "#94A3B8"
    
    card_bg = "#0C1426" if is_dark else "#FFFFFF"
    card_hdr = "#0B1222" if is_dark else "#F1F5F9"
    card_stroke_start = "rgba(34,211,238,0.22)" if is_dark else "rgba(8,145,178,0.20)"
    card_stroke_mid = "rgba(34,211,238,0.55)" if is_dark else "rgba(8,145,178,0.55)"
    
    repo_text_col = "#94A3B8" if is_dark else "#475569"
    repo_bullet_col = "#22D3EE" if is_dark else "#0891B2"
    title_col = "#F8FAFC" if is_dark else "#0F172A"
    desc_col = "#94A3B8" if is_dark else "#475569"
    
    tag_bg = "rgba(30,41,59,0.7)" if is_dark else "#F1F5F9"
    tag_border = "rgba(148,163,184,0.2)" if is_dark else "rgba(71,85,105,0.2)"
    tag_text = "#22D3EE" if is_dark else "#0891B2"
    
    gradient_stops = '''
    <stop offset="0" stop-color="#7C3AED"><animate attributeName="stop-color" values="#7C3AED;#22D3EE;#10B981;#7C3AED" dur="10s" repeatCount="indefinite"/></stop>
    <stop offset="1" stop-color="#10B981"><animate attributeName="stop-color" values="#10B981;#7C3AED;#22D3EE;#10B981" dur="10s" repeatCount="indefinite"/></stop>
    ''' if is_dark else '''
    <stop offset="0" stop-color="#7C3AED"><animate attributeName="stop-color" values="#7C3AED;#0891B2;#059669;#7C3AED" dur="10s" repeatCount="indefinite"/></stop>
    <stop offset="1" stop-color="#059669"><animate attributeName="stop-color" values="#059669;#7C3AED;#0891B2;#059669" dur="10s" repeatCount="indefinite"/></stop>
    '''

    cards_markup = []
    
    for i, proj in enumerate(projects_data):
        col = i % 2
        row = i // 2
        
        x = 5 if col == 0 else 597
        y = 42 + row * 184
        
        anim_begin = f"{0.25 + i * 0.15:.2f}s"
        
        # Word wrap description into 2 lines max
        desc = proj["description"]
        words = desc.split(" ")
        line1, line2 = "", ""
        for w in words:
            if len(line1 + " " + w) < 58:
                line1 = (line1 + " " + w).strip()
            else:
                line2 = (line2 + " " + w).strip()
                
        # Generate tags markup
        tags_markup = []
        tx_offset = 68
        for tag in proj["tags"]:
            tag_w = len(tag) * 6 + 16
            tags_markup.append(f'''
              <rect x="{tx_offset}" y="124" width="{tag_w}" height="20" rx="10" fill="{tag_bg}" stroke="{tag_border}" stroke-width="1"/>
              <text x="{tx_offset + tag_w//2}" y="137" font-size="9.5" fill="{tag_text}" text-anchor="middle" font-weight="600">{tag}</text>
            ''')
            tx_offset += tag_w + 8

        tags_str = "".join(tags_markup)
        icon_str = get_svg_icon(proj["logo"], is_dark)

        card_xml = f'''<a href="https://github.com/{proj['repo']}" target="_blank">
  <g opacity="0" transform="translate({x},{y})">
    <animate attributeName="opacity" from="0" to="1" dur="0.5s" begin="{anim_begin}" fill="freeze"/>
    <rect width="578" height="168" rx="12" fill="{card_bg}" stroke="{card_stroke_start}">
      <animate attributeName="stroke" values="{card_stroke_start};{card_stroke_mid};{card_stroke_start}" dur="4.5s" begin="{anim_begin}" repeatCount="indefinite"/>
    </rect>
    <rect width="578" height="30" rx="12" fill="{card_hdr}"/>
    <rect y="18" width="578" height="12" fill="{card_hdr}"/>
    <line x1="0" y1="30" x2="578" y2="30" stroke="rgba(255,255,255,0.08)"/>
    <text x="16" y="19" font-size="10" fill="{repo_text_col}"><tspan fill="{repo_bullet_col}">•</tspan> {proj['repo']}</text>
    <circle cx="562" cy="15" r="3.5" fill="{text_sub}"/>
    <g>
      <animateTransform attributeName="transform" type="translate" values="0 0; 0 -2.5; 0 0" dur="5s" begin="{anim_begin}" repeatCount="indefinite" calcMode="spline" keyTimes="0;0.5;1" keySplines="0.4 0 0.6 1;0.4 0 0.6 1"/>
      {icon_str}
      <text x="68" y="58" font-size="15" font-weight="700" fill="{title_col}">{proj['name']}</text>
      <text x="68" y="78" font-size="11" fill="{desc_col}">{line1}</text>
      <text x="68" y="94" font-size="11" fill="{desc_col}">{line2}</text>
      {tags_str}
    </g>
  </g>
</a>'''
        cards_markup.append(card_xml)

    cards_str = "\n".join(cards_markup)

    svg_content = f'''<svg xmlns="http://www.w3.org/2000/svg" width="1180" height="607" viewBox="0 0 1180 607" font-family="ui-monospace,SFMono-Regular,Menlo,Consolas,'Liberation Mono',monospace" role="img" aria-label="Projects">
  <rect width="1180" height="607" fill="{bg_color}"/>
  <defs>
    <linearGradient id="{acc_id}" x1="0" y1="0" x2="1" y2="0">
      {gradient_stops}
    </linearGradient>
  </defs>
  <text x="7" y="18" font-size="11" letter-spacing="2" fill="{text_hdr}">PROJECTS.LIST</text>
  <text x="135" y="18" font-size="10" fill="{text_sub}">./projects.sh --all</text>
  <line x1="5" y1="28" x2="1175" y2="28" stroke="url(#{acc_id})" stroke-width="1.5" opacity="0.7"/>
{cards_str}
</svg>'''
    return svg_content

# Generate both SVG files
dark_svg = generate_svg(is_dark=True)
with open("projects.svg", "w", encoding="utf-8") as f:
    f.write(dark_svg)

light_svg = generate_svg(is_dark=False)
with open("projects-light.svg", "w", encoding="utf-8") as f:
    f.write(light_svg)

print("projects.svg and projects-light.svg successfully generated!")
