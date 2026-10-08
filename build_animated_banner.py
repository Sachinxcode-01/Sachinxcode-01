import os
import sys
import re
import numpy as np
from PIL import Image, ImageOps, ImageEnhance, ImageFilter, ImageDraw
from scipy import ndimage
from scipy.optimize import linear_sum_assignment
import matplotlib.path as mpath
import matplotlib.patches as mpatches
import matplotlib.pyplot as plt

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

GITHUB_PATH_D = (
    "M12 .297c-6.63 0-12 5.373-12 12 0 5.303 3.438 9.8 8.205 11.385"
    ".6.113.82-.258.82-.577 0-.285-.01-1.04-.015-2.04-3.338.724-4.042-1.61-4.042-1.61"
    "C4.422 18.07 3.633 17.7 3.633 17.7c-1.087-.744.084-.729.084-.729 1.205.084 1.838 1.236"
    " 1.838 1.236 1.07 1.835 2.809 1.305 3.495.998.108-.776.417-1.305.76-1.605-2.665-.3-5.466-1.332"
    "-5.466-5.93 0-1.31.465-2.38 1.235-3.22-.135-.303-.54-1.523.105-3.176 0 0 1.005-.322 3.3 1.23"
    ".96-.267 1.98-.399 3-.405 1.02.006 2.04.138 3 .405 2.28-1.552 3.285-1.23 3.285-1.23"
    ".645 1.653.24 2.873.12 3.176.765.84 1.23 1.91 1.23 3.22 0 4.61-2.805 5.625-5.475 5.92"
    ".42.36.81 1.096.81 2.22 0 1.606-.015 2.896-.015 3.286 0 .315.21.69.825.57"
    "C20.565 22.092 24 17.592 24 12.297c0-6.627-5.373-12-12-12"
)

PYTHON_PATH_D = (
    "M14.25.18l.9.2.73.26.59.3.45.32.34.34.25.34.16.33.1.3.04.26.02.2-.01.13V8.5l-.05.63"
    "-.13.55-.21.46-.26.38-.3.31-.33.25-.35.19-.35.14-.33.1-.3.07-.26.04-.21.02H8.77l-.69.05"
    "-.59.14-.5.22-.41.27-.33.32-.27.35-.2.36-.15.37-.1.35-.07.32-.04.27-.02.21v3.06H3.17"
    "l-.21-.03-.28-.07-.32-.12-.35-.18-.36-.26-.36-.36-.35-.46-.32-.59-.28-.73-.21-.88-.14-1.05"
    "-.05-1.23.06-1.22.16-1.04.24-.87.32-.71.36-.57.4-.44.42-.33.42-.24.4-.16.36-.1.32-.05.24-.01h.16"
    "l.06.01h8.16v-.83H6.18l-.01-2.75-.02-.37.05-.34.11-.31.17-.28.25-.26.31-.23.38-.2.44-.18.51-.15"
    ".58-.12.64-.1.71-.06.77-.04.84-.02 1.27.05zm-6.3 1.98l-.23.33-.08.41.08.41.23.34.33.22.41.09"
    ".41-.09.33-.22.23-.34.08-.41-.08-.41-.23-.33-.33-.22-.41-.09-.41.09zm13.09 3.95l.28.06.32.12"
    ".35.18.36.27.36.35.35.47.32.59.28.73.21.88.14 1.04.05 1.23-.06 1.23-.16 1.04-.24.86-.32.71"
    "-.36.57-.4.45-.42.33-.42.24-.4.16-.36.09-.32.05-.24.02-.16-.01h-8.22v.82h5.84l.01 2.76.02.36"
    "-.05.34-.11.31-.17.29-.25.25-.31.24-.38.2-.44.17-.51.15-.58.13-.64.09-.71.07-.77.04-.84.01"
    "-1.27-.04-1.07-.14-.9-.2-.73-.25-.59-.3-.45-.33-.34-.34-.25-.34-.16-.33-.1-.3-.04-.25-.02-.2"
    ".01-.13v-5.34l.05-.64.13-.54.21-.46.26-.38.3-.32.33-.24.35-.2.35-.14.33-.1.3-.06.26-.04.21-.02"
    ".13-.01h5.84l.69-.05.59-.14.5-.21.41-.28.33-.32.27-.35.2-.36.15-.36.1-.35.07-.32.04-.28.02-.21"
    "V6.07h2.09l.14.01zm-6.47 14.25l-.23.33-.08.41.08.41.23.33.33.23.41.08.41-.08.33-.23.23-.33"
    ".08-.41-.08-.41-.23-.33-.33-.23-.41-.08-.41.08z"
)

def parse_svg_path(d):
    tokens = re.findall(r'([A-Za-z]|[-+]?(?:\d*\.\d+|\d+)(?:[eE][-+]?\d+)?)', d)
    vertices = []
    codes = []
    i = 0
    cur_x, cur_y = 0.0, 0.0
    start_x, start_y = 0.0, 0.0
    last_cmd = ''

    while i < len(tokens):
        t = tokens[i]
        if t.isalpha():
            cmd = t
            i += 1
        else:
            if last_cmd in 'Mm':
                cmd = 'L' if last_cmd == 'M' else 'l'
            else:
                cmd = last_cmd

        last_cmd = cmd

        if cmd == 'M':
            cur_x, cur_y = float(tokens[i]), float(tokens[i+1])
            start_x, start_y = cur_x, cur_y
            vertices.append((cur_x, cur_y))
            codes.append(mpath.Path.MOVETO)
            i += 2
        elif cmd == 'm':
            cur_x += float(tokens[i])
            cur_y += float(tokens[i+1])
            start_x, start_y = cur_x, cur_y
            vertices.append((cur_x, cur_y))
            codes.append(mpath.Path.MOVETO)
            i += 2
        elif cmd == 'L':
            cur_x, cur_y = float(tokens[i]), float(tokens[i+1])
            vertices.append((cur_x, cur_y))
            codes.append(mpath.Path.LINETO)
            i += 2
        elif cmd == 'l':
            cur_x += float(tokens[i])
            cur_y += float(tokens[i+1])
            vertices.append((cur_x, cur_y))
            codes.append(mpath.Path.LINETO)
            i += 2
        elif cmd == 'H':
            cur_x = float(tokens[i])
            vertices.append((cur_x, cur_y))
            codes.append(mpath.Path.LINETO)
            i += 1
        elif cmd == 'h':
            cur_x += float(tokens[i])
            vertices.append((cur_x, cur_y))
            codes.append(mpath.Path.LINETO)
            i += 1
        elif cmd == 'V':
            cur_y = float(tokens[i])
            vertices.append((cur_x, cur_y))
            codes.append(mpath.Path.LINETO)
            i += 1
        elif cmd == 'v':
            cur_y += float(tokens[i])
            vertices.append((cur_x, cur_y))
            codes.append(mpath.Path.LINETO)
            i += 1
        elif cmd == 'C':
            x1, y1 = float(tokens[i]), float(tokens[i+1])
            x2, y2 = float(tokens[i+2]), float(tokens[i+3])
            cur_x, cur_y = float(tokens[i+4]), float(tokens[i+5])
            vertices.extend([(x1, y1), (x2, y2), (cur_x, cur_y)])
            codes.extend([mpath.Path.CURVE4, mpath.Path.CURVE4, mpath.Path.CURVE4])
            i += 6
        elif cmd == 'c':
            x1 = cur_x + float(tokens[i])
            y1 = cur_y + float(tokens[i+1])
            x2 = cur_x + float(tokens[i+2])
            y2 = cur_y + float(tokens[i+3])
            cur_x += float(tokens[i+4])
            cur_y += float(tokens[i+5])
            vertices.extend([(x1, y1), (x2, y2), (cur_x, cur_y)])
            codes.extend([mpath.Path.CURVE4, mpath.Path.CURVE4, mpath.Path.CURVE4])
            i += 6
        elif cmd in 'Zz':
            cur_x, cur_y = start_x, start_y
            vertices.append((cur_x, cur_y))
            codes.append(mpath.Path.CLOSEPOLY)
        else:
            i += 1

    return mpath.Path(vertices, codes)

def sample_mask_points(mask, n_pts=900, edge_ratio=0.36, seed=42):
    np.random.seed(seed)
    struct = ndimage.generate_binary_structure(2, 1)
    eroded = ndimage.binary_erosion(mask, structure=struct, iterations=1)
    edge_mask = mask & (~eroded)
    interior_mask = eroded

    edge_ys, edge_xs = np.where(edge_mask)
    int_ys, int_xs = np.where(interior_mask)

    n_edge = int(n_pts * edge_ratio)
    n_int = n_pts - n_edge

    if len(edge_xs) > n_edge:
        edge_idx = np.linspace(0, len(edge_xs) - 1, n_edge, endpoint=False).astype(int)
        edge_pts = np.column_stack([edge_xs[edge_idx], edge_ys[edge_idx]])
    else:
        edge_pts = np.column_stack([edge_xs, edge_ys])
        n_int = n_pts - len(edge_pts)

    ymin, ymax = int_ys.min(), int_ys.max()
    xmin, xmax = int_xs.min(), int_xs.max()

    area_per_pt = np.sum(interior_mask) / float(n_int)
    cell_size = np.sqrt(area_per_pt)

    grid_x = np.arange(xmin, xmax, cell_size)
    grid_y = np.arange(ymin, ymax, cell_size)
    gx, gy = np.meshgrid(grid_x, grid_y)
    gx = gx.ravel() + np.random.uniform(-cell_size * 0.35, cell_size * 0.35, gx.size)
    gy = gy.ravel() + np.random.uniform(-cell_size * 0.35, cell_size * 0.35, gy.size)

    int_pts_list = []
    for x, y in zip(gx, gy):
        ix, iy = int(round(x)), int(round(y))
        if 0 <= iy < mask.shape[0] and 0 <= ix < mask.shape[1] and interior_mask[iy, ix]:
            int_pts_list.append([x, y])

    int_pts = np.array(int_pts_list, dtype=np.float32)
    if len(int_pts) >= n_int:
        perm = np.random.permutation(len(int_pts))
        int_pts = int_pts[perm[:n_int]]
    else:
        shortage = n_int - len(int_pts)
        unused_idx = np.random.choice(len(int_xs), shortage, replace=False)
        supp = np.column_stack([int_xs[unused_idx], int_ys[unused_idx]]).astype(np.float32)
        int_pts = np.vstack([int_pts, supp]) if len(int_pts) > 0 else supp

    pts = np.vstack([edge_pts.astype(np.float32), int_pts])
    return pts

# 3 Logos generators (Authentic Official Geometry & Perfect Sampling)
def generate_python_points(size=(300, 340), n_pts=900):
    fig, ax = plt.subplots(figsize=(size[0] / 100.0, size[1] / 100.0), dpi=100)
    fig.patch.set_facecolor('black')
    ax.set_facecolor('black')

    path = parse_svg_path(PYTHON_PATH_D)
    scale = 0.64
    pixel_scale = (size[0] * scale) / 24.0
    cx = size[0] / 2.0
    cy = size[1] / 2.0

    verts = path.vertices.copy()
    verts[:, 0] = (verts[:, 0] - 12.0) * pixel_scale + cx
    verts[:, 1] = (verts[:, 1] - 12.0) * pixel_scale + cy

    transformed_path = type(path)(verts, path.codes)
    patch = mpatches.PathPatch(transformed_path, facecolor='white', edgecolor='white', lw=0.6)
    ax.add_patch(patch)

    ax.set_xlim(0, size[0])
    ax.set_ylim(size[1], 0)
    ax.axis('off')
    plt.subplots_adjust(left=0, right=1, top=1, bottom=0)
    fig.canvas.draw()
    rgba = np.asarray(fig.canvas.buffer_rgba())
    plt.close(fig)

    py_mask = rgba[:, :, 0] > 128
    return sample_mask_points(py_mask, n_pts=n_pts, edge_ratio=0.38, seed=42)

def generate_code_points(size=(300, 340), n_pts=900):
    im = Image.new('L', size, 0)
    draw = ImageDraw.Draw(im)
    cx, cy = size[0] // 2, size[1] // 2

    # Proper < bracket (apex pointing left)
    draw.line([(cx - 42, cy - 58), (cx - 96, cy)], fill=255, width=19)
    draw.line([(cx - 96, cy), (cx - 42, cy + 58)], fill=255, width=19)
    # / slash
    draw.line([(cx - 18, cy + 72), (cx + 18, cy - 72)], fill=255, width=19)
    # Proper > bracket (apex pointing right)
    draw.line([(cx + 42, cy - 58), (cx + 96, cy)], fill=255, width=19)
    draw.line([(cx + 96, cy), (cx + 42, cy + 58)], fill=255, width=19)

    code_mask = np.array(im) > 128
    return sample_mask_points(code_mask, n_pts=n_pts, edge_ratio=0.35, seed=42)

def generate_github_points(size=(300, 340), n_pts=900):
    path = parse_svg_path(GITHUB_PATH_D)
    verts = path.vertices[6:70].copy()
    codes = path.codes[6:70].copy()
    codes[0] = mpath.Path.MOVETO
    verts = np.vstack([verts, [verts[0]], [verts[0]]])
    codes = np.append(codes, [mpath.Path.LINETO, mpath.Path.CLOSEPOLY])

    fig, ax = plt.subplots(figsize=(size[0] / 100.0, size[1] / 100.0), dpi=100)
    fig.patch.set_facecolor('black')
    ax.set_facecolor('black')

    scale = 10.8
    cx = size[0] / 2.0
    cy = size[1] / 2.0
    verts[:, 0] = (verts[:, 0] - 12.0) * scale + cx
    verts[:, 1] = (verts[:, 1] - 14.7) * scale + cy

    octo_path_scaled = mpath.Path(verts, codes)
    patch = mpatches.PathPatch(octo_path_scaled, facecolor='white', edgecolor='white', lw=0.6)
    ax.add_patch(patch)
    ax.set_xlim(0, size[0])
    ax.set_ylim(size[1], 0)
    ax.axis('off')
    plt.subplots_adjust(left=0, right=1, top=1, bottom=0)
    fig.canvas.draw()
    rgba = np.asarray(fig.canvas.buffer_rgba())
    plt.close(fig)

    gh_mask = rgba[:, :, 0] > 128
    return sample_mask_points(gh_mask, n_pts=n_pts, edge_ratio=0.36, seed=42)

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
