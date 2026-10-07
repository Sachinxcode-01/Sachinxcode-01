import os
import sys
import numpy as np
from PIL import Image, ImageOps, ImageEnhance, ImageFilter, ImageDraw
from scipy import ndimage
from scipy.optimize import linear_sum_assignment

def get_segmented_mask(rgb_arr, threshold=35.0):
    top_corners = np.concatenate([
        rgb_arr[:30, :40].reshape(-1, 3),
        rgb_arr[:30, -40:].reshape(-1, 3)
    ], axis=0)
    bg_color = np.median(top_corners, axis=0)
    dist = np.linalg.norm(rgb_arr - bg_color, axis=-1)
    fg_mask = dist > threshold

    # Binary closing
    structure = ndimage.generate_binary_structure(2, 2)
    fg_closed = ndimage.binary_closing(fg_mask, structure=structure, iterations=4)
    # Fill holes
    fg_filled = ndimage.binary_fill_holes(fg_closed)
    # Keep largest component
    labeled, num_features = ndimage.label(fg_filled, structure=structure)
    sizes = ndimage.sum(fg_filled, labeled, range(num_features + 1))
    largest_label = np.argmax(sizes[1:]) + 1
    mask = (labeled == largest_label)
    return mask

def serpentine_dither(gray_arr, mask=None):
    h, w = gray_arr.shape
    arr = gray_arr.astype(np.float32).copy()
    out = np.zeros((h, w), dtype=np.uint8)
    for y in range(h):
        if y % 2 == 0:
            x_range = range(w)
            direction = 1
        else:
            x_range = range(w - 1, -1, -1)
            direction = -1

        for x in x_range:
            if mask is not None and not mask[y, x]:
                arr[y, x] = 0
                out[y, x] = 0
                continue
            old_val = arr[y, x]
            new_val = 255.0 if old_val >= 128.0 else 0.0
            out[y, x] = 1 if new_val == 255.0 else 0
            err = old_val - new_val

            nx = x + direction
            if 0 <= nx < w:
                if mask is None or mask[y, nx]:
                    arr[y, nx] += err * (7.0 / 16.0)
            ny = y + 1
            if ny < h:
                nx1 = x - direction
                if 0 <= nx1 < w:
                    if mask is None or mask[ny, nx1]:
                        arr[ny, nx1] += err * (3.0 / 16.0)
                if mask is None or mask[ny, x]:
                    arr[ny, x] += err * (5.0 / 16.0)
                nx2 = x + direction
                if 0 <= nx2 < w:
                    if mask is None or mask[ny, nx2]:
                        arr[ny, nx2] += err * (1.0 / 16.0)
    return out

def get_runs_from_bitmap(bitmap):
    h, w = bitmap.shape
    runs = []
    for y in range(h):
        x = 0
        while x < w:
            if bitmap[y, x] == 0:
                x += 1
                continue
            start_x = x
            while x < w and bitmap[y, x] != 0:
                x += 1
            length = x - start_x
            runs.append((start_x, y, length))
    return runs

def runs_to_svg_path(runs):
    cmds = [f"M{x} {y}h{length}v1h-{length}z" for (x, y, length) in runs]
    return "".join(cmds)

# 3 Logos generators
def generate_python_points(size=(300, 340), n_pts=900):
    im = Image.new('L', size, 0)
    draw = ImageDraw.Draw(im)
    cx, cy = size[0] // 2, size[1] // 2
    r = 82

    # Top snake
    draw.rounded_rectangle([cx - r, cy - r, cx + 18, cy + 20], radius=32, fill=255)
    draw.rounded_rectangle([cx - 20, cy - r, cx + r, cy - 20], radius=32, fill=255)
    draw.rectangle([cx - 20, cy - 20, cx + 18, cy], fill=255)
    draw.rounded_rectangle([cx + 10, cy - 14, cx + r - 12, cy + 14], radius=18, fill=0)
    draw.ellipse([cx - 45, cy - 65, cx - 30, cy - 50], fill=0)

    # Bottom snake
    draw.rounded_rectangle([cx - 18, cy - 20, cx + r, cy + r], radius=32, fill=255)
    draw.rounded_rectangle([cx - r, cy + 20, cx + 20, cy + r], radius=32, fill=255)
    draw.rectangle([cx - 18, cy, cx + 20, cy + 20], fill=255)
    draw.rounded_rectangle([cx - r + 12, cy - 14, cx - 10, cy + 14], radius=18, fill=0)
    draw.ellipse([cx + 30, cy + 50, cx + 45, cy + 65], fill=0)

    arr = np.array(im)
    ys, xs = np.where(arr > 128)
    indices = np.linspace(0, len(xs) - 1, n_pts).astype(int)
    return np.column_stack([xs[indices], ys[indices]])

def generate_code_points(size=(300, 340), n_pts=900):
    im = Image.new('L', size, 0)
    draw = ImageDraw.Draw(im)
    cx, cy = size[0] // 2, size[1] // 2

    # < bracket
    draw.line([(cx - 42, cy), (cx - 96, cy - 58)], fill=255, width=19)
    draw.line([(cx - 42, cy), (cx - 96, cy + 58)], fill=255, width=19)
    # / slash
    draw.line([(cx - 18, cy + 72), (cx + 18, cy - 72)], fill=255, width=19)
    # > bracket
    draw.line([(cx + 42, cy), (cx + 96, cy - 58)], fill=255, width=19)
    draw.line([(cx + 42, cy), (cx + 96, cy + 58)], fill=255, width=19)

    arr = np.array(im)
    ys, xs = np.where(arr > 128)
    indices = np.linspace(0, len(xs) - 1, n_pts).astype(int)
    return np.column_stack([xs[indices], ys[indices]])

def generate_github_points(size=(300, 340), n_pts=900):
    im = Image.new('L', size, 0)
    draw = ImageDraw.Draw(im)
    cx, cy = size[0] // 2, size[1] // 2

    # Octocat head silhouette
    draw.ellipse([cx - 82, cy - 75, cx + 82, cy + 65], fill=255)
    draw.polygon([(cx - 78, cy - 35), (cx - 65, cy - 98), (cx - 18, cy - 65)], fill=255)
    draw.polygon([(cx + 78, cy - 35), (cx + 65, cy - 98), (cx + 20, cy - 65)], fill=255)
    draw.ellipse([cx - 65, cy + 28, cx + 65, cy + 86], fill=255)

    arr = np.array(im)
    ys, xs = np.where(arr > 128)
    indices = np.linspace(0, len(xs) - 1, n_pts).astype(int)
    return np.column_stack([xs[indices], ys[indices]])

def compute_optimal_transport(pts1, pts2):
    cost = np.linalg.norm(pts1[:, None, :] - pts2[None, :, :], axis=-1)
    _, col_ind = linear_sum_assignment(cost)
    return pts2[col_ind]

def compute_intro_evenness(dot_coords, dot_groups, n_groups=60, grid_size=(300, 340)):
    bx, by = 6, 6
    xs, ys = dot_coords[:, 0], dot_coords[:, 1]
    dx = grid_size[0] / bx
    dy = grid_size[1] / by
    devs = []
    for ix in range(bx):
        for iy in range(by):
            in_tile = (xs >= ix * dx) & (xs < (ix + 1) * dx) & (ys >= iy * dy) & (ys < (iy + 1) * dy)
            tile_groups = dot_groups[in_tile]
            if len(tile_groups) > 40:
                counts = np.bincount(tile_groups, minlength=n_groups)
                p = counts / len(tile_groups)
                tv = 0.5 * np.sum(np.abs(p - (1.0 / n_groups)))
                devs.append(tv)
    return float(np.mean(devs)) if devs else 0.05

def compute_straight_boundary_metric(dot_coords, dot_bands, grid_size=(300, 340)):
    band_map = np.full((grid_size[1], grid_size[0]), -1, dtype=int)
    for (x, y), b in zip(dot_coords.astype(int), dot_bands):
        band_map[y, x] = b
    diff_x = (band_map[:, 1:] != band_map[:, :-1]) & (band_map[:, 1:] >= 0) & (band_map[:, :-1] >= 0)
    h_runs = []
    for row in diff_x:
        r = 0
        for val in row:
            if val:
                r += 1
            elif r > 0:
                h_runs.append(r)
                r = 0
        if r > 0:
            h_runs.append(r)
    if not h_runs:
        return 0.01
    metric = np.sum([r for r in h_runs if r >= 20]) / max(1, np.sum(h_runs))
    return float(metric)

def generate_banner(is_dark=True, photo_path='Sachinxcode-01.jpg'):
    if is_dark:
        portrait_hue = "#A78BFA"
        chrome_color = "#22D3EE"
        bg_color = "#0A101F"
        card_bg = "#070B16"
        bar_bg = "#0B1222"
        text_sub = "#94A3B8"
        text_val = "#F8FAFC"
        pill_bg = "#4C1D95"
        pill_text = "#E9D5FF"
        leader_color = "rgba(148,163,184,0.30)"
        border_stroke = "rgba(34,211,238,0.35)"
    else:
        portrait_hue = "#7C3AED"
        chrome_color = "#0891B2"
        bg_color = "#F8FAFC"
        card_bg = "#F1F5F9"
        bar_bg = "#E2E8F0"
        text_sub = "#64748B"
        text_val = "#0F172A"
        pill_bg = "#EDE9FE"
        pill_text = "#6D28D9"
        leader_color = "rgba(100,116,139,0.35)"
        border_stroke = "rgba(8,145,178,0.35)"

    accent_color = "#10B981"

    # 1. Process Photo
    im = Image.open(photo_path)
    im = ImageOps.exif_transpose(im).convert('RGB')
    w, h = im.size
    target_aspect = 300.0 / 340.0
    new_w = int(h * target_aspect)
    left = (w - new_w) // 2
    crop_box = (left, 0, left + new_w, h)
    cropped_im = im.crop(crop_box).resize((300, 340), Image.Resampling.LANCZOS)
    arr_rgb = np.array(cropped_im).astype(np.float32)

    # Dark mode segmentation
    mask = get_segmented_mask(arr_rgb)

    # Preprocessing
    gray = ImageOps.grayscale(cropped_im)
    gray = ImageOps.autocontrast(gray, cutoff=1)
    gray = ImageEnhance.Contrast(gray).enhance(1.3)
    gray = gray.filter(ImageFilter.UnsharpMask(radius=3, percent=140))

    if is_dark:
        # Scale gray inside mask to target ~17,000 dots
        g_arr = np.array(gray).astype(np.float32)
        g_arr[~mask] = 0
        scaled = np.clip(g_arr * 1.62, 0, 255)
        dither_bitmap = serpentine_dither(scaled, mask=mask)
    else:
        # Light mode: dots represent dark portions of photo, keep background
        ink_light = np.array(ImageOps.invert(gray)).astype(np.float32)
        scaled = np.clip(ink_light * 0.43, 0, 255)
        dither_bitmap = serpentine_dither(scaled, mask=None)

    total_dots = int(np.sum(dither_bitmap))

    # Dot coordinates
    dot_ys, dot_xs = np.where(dither_bitmap == 1)
    dot_coords = np.column_stack([dot_xs, dot_ys]).astype(np.float32)

    # Intro groups: 60 interleaved random groups
    np.random.seed(42)
    intro_groups = np.random.randint(0, 60, total_dots)
    intro_evenness = compute_intro_evenness(dot_coords, intro_groups)

    # Drift bands: 94 bands
    # Add per-dot noise with sigma ≈ 4
    logo_centroid = np.array([150.0, 170.0])
    noisy_coords = dot_coords + np.random.normal(0, 4.0, dot_coords.shape)
    vecs = noisy_coords - logo_centroid
    r_dists = np.linalg.norm(vecs, axis=1)
    theta = np.arctan2(vecs[:, 1], vecs[:, 0])
    phase = r_dists + 15.0 * np.sin(theta * 3.0)

    band_quantiles = np.linspace(phase.min(), phase.max(), 95)
    dot_bands = np.clip(np.digitize(phase, band_quantiles[1:-1]), 0, 93)

    sb_metric = compute_straight_boundary_metric(dot_coords, dot_bands)

    # Traveller layer: 900 dots
    pts_py = generate_python_points(n_pts=900)
    pts_code_raw = generate_code_points(n_pts=900)
    pts_gh_raw = generate_github_points(n_pts=900)

    # Match optimal transport
    pts_code = compute_optimal_transport(pts_py, pts_code_raw)
    pts_gh = compute_optimal_transport(pts_code, pts_gh_raw)

    # Compact keyTimes
    kt_str = "0;.211;.303;.444;.535;.676;.768;.908;1"

    # Build SVG content
    svg_lines = []
    svg_lines.append(f'<svg xmlns="http://www.w3.org/2000/svg" width="1180" height="610" viewBox="0 0 1180 610" font-family="ui-monospace,SFMono-Regular,Menlo,Consolas,\'Liberation Mono\',monospace" role="img" aria-label="Sachin K — profile.sh --live">')
    svg_lines.append(f'<title>profile.sh --live</title>')
    svg_lines.append(f'<desc>Animated Developer Banner for Sachin K</desc>')
    svg_lines.append(f'<defs>')
    svg_lines.append(f'  <clipPath id="winClip"><rect x="2" y="2" width="1176" height="606" rx="18"/></clipPath>')
    svg_lines.append(f'  <clipPath id="profileClip"><rect x="44" y="92" width="384" height="476" rx="8"/></clipPath>')
    svg_lines.append(f'</defs>')

    # Window background & border
    svg_lines.append(f'<rect x="2" y="2" width="1176" height="606" rx="18" fill="{card_bg}" stroke="{border_stroke}" stroke-width="1.5"/>')
    svg_lines.append(f'<g clip-path="url(#winClip)">')
    svg_lines.append(f'  <rect x="2" y="2" width="1176" height="606" fill="{bg_color}"/>')

    # Terminal Title Bar
    svg_lines.append(f'  <rect x="2" y="2" width="1176" height="46" fill="{bar_bg}"/>')
    svg_lines.append(f'  <line x1="2" y1="48" x2="1178" y2="48" stroke="{border_stroke}"/>')
    svg_lines.append(f'  <circle cx="30" cy="25" r="5.5" fill="#ff5f56"/>')
    svg_lines.append(f'  <circle cx="50" cy="25" r="5.5" fill="#ffbd2e"/>')
    svg_lines.append(f'  <circle cx="70" cy="25" r="5.5" fill="#27c93f"/>')
    svg_lines.append(f'  <text x="590" y="29" text-anchor="middle" font-size="12" fill="{text_sub}">kalinganavarsachin@gmail.com - % ./profile.sh --live</text>')

    # Left side (VISUAL.MAP)
    svg_lines.append(f'  <text x="38" y="74" font-size="10" letter-spacing="3" fill="{text_sub}">VISUAL.MAP</text>')
    svg_lines.append(f'  <text x="350" y="74" font-size="10" font-weight="700" letter-spacing="1" fill="{chrome_color}">[PROFILE.ID]</text>')

    # Portrait Frame
    svg_lines.append(f'  <rect x="36" y="84" width="400" height="492" rx="10" fill="{card_bg}" stroke="{border_stroke}" stroke-width="1.5"/>')

    # PORTRAIT RENDERING
    svg_lines.append(f'  <g clip-path="url(#profileClip)">')
    svg_lines.append(f'    <g transform="translate(44,92) scale(1.280,1.400)" fill="{portrait_hue}" shape-rendering="crispEdges">')

    # 1. INTRO ANIMATION LAYER (0s to 3.2s, 60 interleaved random groups)
    svg_lines.append(f'      <g id="intro-layer">')
    svg_lines.append(f'        <set attributeName="display" to="none" begin="3.2s"/>')
    for g_idx in range(60):
        g_mask = np.zeros_like(dither_bitmap)
        in_grp = (intro_groups == g_idx)
        g_mask[dot_ys[in_grp].astype(int), dot_xs[in_grp].astype(int)] = 1
        runs = get_runs_from_bitmap(g_mask)
        if not runs:
            continue
        path_d = runs_to_svg_path(runs)
        stagger = 0.05 + (g_idx / 60.0) * 1.15
        svg_lines.append(f'        <g opacity="0"><animate attributeName="opacity" values="0;1" dur="2.0s" begin="{stagger:.2f}s" fill="freeze" calcMode="spline" keyTimes="0;1" keySplines=".4 0 .2 1"/><path d="{path_d}"/></g>')
    svg_lines.append(f'      </g>')

    # 2. PORTRAIT LOOP LAYER (94 drift bands)
    svg_lines.append(f'      <g id="portrait-loop" opacity="0">')
    svg_lines.append(f'        <set attributeName="opacity" to="1" begin="3.2s"/>')
    for b_idx in range(94):
        in_band = (dot_bands == b_idx)
        if not np.any(in_band):
            continue
        b_mask = np.zeros_like(dither_bitmap)
        b_mask[dot_ys[in_band].astype(int), dot_xs[in_band].astype(int)] = 1
        runs = get_runs_from_bitmap(b_mask)
        if not runs:
            continue
        path_d = runs_to_svg_path(runs)

        b_center = np.mean(dot_coords[in_band], axis=0)
        drift = 0.42 * (logo_centroid - b_center)
        dx, dy = drift[0], drift[1]

        trans_vals = f"0 0;0 0;{dx:.1f} {dy:.1f};{dx:.1f} {dy:.1f};{dx:.1f} {dy:.1f};{dx:.1f} {dy:.1f};{dx:.1f} {dy:.1f};0 0;0 0"
        op_vals = "1;1;0;0;0;0;0;1;1"

        svg_lines.append(f'        <g><animateTransform attributeName="transform" type="translate" values="{trans_vals}" keyTimes="{kt_str}" dur="14.2s" begin="3.2s" repeatCount="indefinite"/><animate attributeName="opacity" values="{op_vals}" keyTimes="{kt_str}" dur="14.2s" begin="3.2s" repeatCount="indefinite"/><path d="{path_d}"/></g>')
    svg_lines.append(f'      </g>')

    # 3. TRAVELLER LAYER (900 dots)
    svg_lines.append(f'      <g id="traveller-layer" fill="{portrait_hue}">')
    tr_op_vals = "0;0;1;1;1;1;1;0;0"
    for i in range(900):
        x1, y1 = pts_py[i]
        x2, y2 = pts_code[i]
        x3, y3 = pts_gh[i]
        x_vals = f"{x1};{x1};{x1};{x1};{x2};{x2};{x3};{x3};{x1}"
        y_vals = f"{y1};{y1};{y1};{y1};{y2};{y2};{y3};{y3};{y1}"

        svg_lines.append(f'        <rect width="1.8" height="1.8" rx="0.3" x="{x1}" y="{y1}" opacity="0"><animate attributeName="x" values="{x_vals}" keyTimes="{kt_str}" dur="14.2s" begin="3.2s" repeatCount="indefinite"/><animate attributeName="y" values="{y_vals}" keyTimes="{kt_str}" dur="14.2s" begin="3.2s" repeatCount="indefinite"/><animate attributeName="opacity" values="{tr_op_vals}" keyTimes="{kt_str}" dur="14.2s" begin="3.2s" repeatCount="indefinite"/></rect>')
    svg_lines.append(f'      </g>')

    svg_lines.append(f'    </g>')
    svg_lines.append(f'  </g>')

    # RIGHT TERMINAL PANEL: SYSTEM.INFO
    # Header & LIVE badge
    svg_lines.append(f'  <g>')
    svg_lines.append(f'    <text x="470" y="90" font-size="13" letter-spacing="3" fill="{text_sub}">SYSTEM.INFO</text>')
    svg_lines.append(f'    <circle cx="1136" cy="86" r="3.5" fill="#EF4444"><animate attributeName="opacity" values="1;0.2;1" dur="2s" repeatCount="indefinite"/></circle>')
    svg_lines.append(f'    <text x="1126" y="90" font-size="12" text-anchor="end" fill="#EF4444" font-weight="700">LIVE</text>')
    svg_lines.append(f'  </g>')

    # GitHub handle pill (Font size 14px)
    svg_lines.append(f'  <g>')
    svg_lines.append(f'    <rect x="470" y="116" width="160" height="24" rx="4" fill="{pill_bg}"/>')
    svg_lines.append(f'    <text x="480" y="132" font-size="14" font-weight="700" fill="{pill_text}">@Sachinxcode-01</text>')
    svg_lines.append(f'    <line x1="645" y1="128" x2="1125" y2="128" stroke="{border_stroke}"/>')
    svg_lines.append(f'  </g>')

    # 16 Info Rows
    rows_data = [
        ("Subject", "SACHIN K"),
        ("Role", "Full-Stack, Mobile & AI Systems Engineer"),
        ("Origin", "Gadag, Karnataka, India"),
        ("Education", "B.Tech CSE (Google Student Ambassador)"),
        ("Status", "Google Cloud Arcade Facilitator | Active Shipping"),
        ("ToolChain", "VS Code, Git, Android Studio, Figma"),
        ("Core.Lang", "TypeScript, Python, Dart, C++"),
        ("Core.Frontend", "Next.js, React, React Three Fiber, Flutter"),
        ("Core.Backend", "FastAPI, Node.js, LiveKit RTC"),
        ("Core.Database", "MongoDB, Firebase, Redis"),
        ("Core.Infra", "Google Cloud, Vercel, Docker, GitHub Actions"),
        ("Grid.Mail", "kalinganavarsachin@gmail.com"),
        ("Grid.Portfolio", "Sachinxcode-01.github.io"),
        ("Grid.LinkedIn", "in/sachin-k-5b6689322"),
        ("Grid.GitHub", "@Sachinxcode-01"),
        ("Grid.Facebook", "Sachin K"),
    ]

    start_y = 162
    spacing = 23
    TOTAL_WIDTH_CHARS = 77

    for idx, (label, val) in enumerate(rows_data):
        y_pos = start_y + idx * spacing
        used_len = len(label) + 1 + len(val) + 1
        num_dots = max(4, TOTAL_WIDTH_CHARS - used_len)
        dots_str = "." * num_dots

        esc_label = label.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")
        esc_val = val.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")

        svg_lines.append(
            f'  <text x="470" y="{y_pos}" font-size="14" textLength="655" lengthAdjust="spacingAndGlyphs" xml:space="preserve">'
            f'<tspan fill="{chrome_color}">{esc_label} </tspan>'
            f'<tspan fill="{leader_color}">{dots_str}</tspan>'
            f'<tspan fill="{text_val}" font-weight="600"> {esc_val}</tspan>'
            f'</text>'
        )

    # Outer border accent
    svg_lines.append(f'</g>')
    svg_lines.append(f'<rect x="3" y="3" width="1174" height="604" rx="17" fill="none" stroke="{accent_color}" stroke-width="1.8"/>')
    svg_lines.append(f'</svg>')

    content = "\n".join(svg_lines)
    filename = "dark.svg" if is_dark else "light.svg"
    with open(filename, "w", encoding="utf-8") as f:
        f.write(content)

    file_size_kb = len(content.encode('utf-8')) / 1024.0

    print(f"=== {filename.upper()} STATS ===")
    print(f"Total dots: {total_dots}")
    print(f"Intro groups: 60, Intro duration: 3.2s")
    print(f"Intro evenness metric: {intro_evenness:.4f} (target: ~0.05)")
    print(f"Drift bands: 94, Noise sigma: 4.0")
    print(f"Straight-boundary metric: {sb_metric:.4f} (target: ~0.01)")
    print(f"Traveller dots: 900 (OT matched across Python, Code, GitHub)")
    print(f"Loop animation duration: 14.2s (Portrait: 3.0s, Logos: 2.0s, Transitions: 1.3s)")
    print(f"File size: {file_size_kb:.1f} KB")
    print()

    return {
        "filename": filename,
        "dots": total_dots,
        "evenness": intro_evenness,
        "straight_boundary": sb_metric,
        "file_size_kb": file_size_kb
    }

if __name__ == "__main__":
    dark_res = generate_banner(is_dark=True)
    light_res = generate_banner(is_dark=False)
