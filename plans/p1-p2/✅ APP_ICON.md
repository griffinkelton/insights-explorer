# 🎨 App Icon & Favicon — Design & Implementation Plan

> **Status:** ✅ Completed (2026-07-28)
> **Effort:** Small-Medium (2-3 hours) | **Risk:** Low

---

## 🎯 Goal

Replace the generic Streamlit favicon and create a cohesive icon identity for the GA4 Insight Explorer — a custom favicon that appears in browser tabs, bookmarks, mobile home screens, and PWA manifests. The icon should be recognizable at 16×16px and beautiful at 512×512px.

---

## 🧠 Design Concept

### The "Data Lens" Icon

The core concept: a **magnifying glass over a bar chart** — representing "insight exploration" visually.

**Three design directions:**

| Direction | Description | Best for |
|---|---|---|
| **A — Abstract Gradient Gem** | A faceted geometric shape (hexagon or diamond) with a blue-to-purple gradient, evoking the Gemini AI colors. Simple, modern, reads at any size. | Browser tabs, bookmarks |
| **B — Chart + Lens** | A magnifying glass overlaid on a small bar chart. The lens has a subtle highlight to suggest "looking closer." More literal but instantly communicates "analytics exploration." | Marketing, app stores |
| **C — Letterform "IE"** | The letters "I" and "E" (Insight Explorer) merged into a single glyph, with the "E" forming bar chart lines. Clean, typographic, distinctive. | Brand identity |

**Recommended:** Direction A for the favicon (reads at small sizes), Direction B for the Open Graph / social share image. Direction C for the sidebar logo if we want to move away from emoji.

### Color Palette

```
Primary gradient: #6366f1 → #8b5cf6 (Indigo → Purple — matches the app theme)
Accent: #818cf8 (Lighter indigo for highlights)
Dark bg: #0a0a0f (App background)
Light bg: #ffffff (For light theme variant)
```

### Sizes Needed

| Size | Use Case |
|---|---|
| 16×16 | Browser favicon (tab icon) |
| 32×32 | Browser favicon (retina) |
| 48×48 | Windows taskbar, browser bookmarks bar |
| 64×64 | Site icon in bookmarks |
| 128×128 | Chrome Web Store, high-res favicon |
| 180×180 | Apple Touch Icon (iOS home screen) |
| 192×192 | Android PWA icon, Chrome splash screen |
| 512×512 | PWA manifest, macOS dock, largest context |

---

## 🛠️ Implementation

### Step 1: Generate the SVG source

Create a single SVG file that serves as the master source:

```svg
<!-- assets/icon.svg — master source for all icon sizes -->
<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 512 512" width="512" height="512">
  <defs>
    <linearGradient id="gemGradient" x1="0%" y1="0%" x2="100%" y2="100%">
      <stop offset="0%" style="stop-color:#6366f1"/>
      <stop offset="100%" style="stop-color:#8b5cf6"/>
    </linearGradient>
    <linearGradient id="glossGradient" x1="0%" y1="0%" x2="0%" y2="100%">
      <stop offset="0%" style="stop-color:rgba(255,255,255,0.25)"/>
      <stop offset="50%" style="stop-color:rgba(255,255,255,0)"/>
    </linearGradient>
  </defs>

  <!-- Background rounded square -->
  <rect x="32" y="32" width="448" height="448" rx="112" ry="112" fill="url(#gemGradient)"/>

  <!-- Gloss overlay -->
  <rect x="32" y="32" width="448" height="224" rx="112" ry="112" fill="url(#glossGradient)"/>

  <!-- Abstract "exploration" lines — suggest data + lens -->
  <circle cx="256" cy="256" r="140" fill="none" stroke="rgba(255,255,255,0.3)" stroke-width="12"/>
  <line x1="360" y1="360" x2="430" y2="430" stroke="rgba(255,255,255,0.5)" stroke-width="16" stroke-linecap="round"/>

  <!-- Three bars inside the lens (simplified bar chart) -->
  <rect x="180" y="300" width="36" height="80" rx="8" fill="rgba(255,255,255,0.7)"/>
  <rect x="238" y="240" width="36" height="140" rx="8" fill="rgba(255,255,255,0.85)"/>
  <rect x="296" y="280" width="36" height="100" rx="8" fill="rgba(255,255,255,0.7)"/>
</svg>
```

### Step 2: Convert to PNG sizes

Use `cairosvg` or `pillow` to rasterize the SVG at each required size:

```python
# scripts/generate_icons.py — one-time script to generate all icon sizes
import cairosvg

SIZES = [16, 32, 48, 64, 128, 180, 192, 512]
SVG_SOURCE = "assets/icon.svg"
OUTPUT_DIR = "assets/icons/"

for size in SIZES:
    cairosvg.svg2png(
        url=SVG_SOURCE,
        write_to=f"{OUTPUT_DIR}icon-{size}x{size}.png",
        output_width=size,
        output_height=size,
    )
```

Add `cairosvg` and `pillow` to `requirements.txt` (used only by the one-time icon generation script, not at runtime).

### Step 3: Convert to ICO (Windows)

Use `pillow` to create a multi-resolution `.ico` file:

```python
from PIL import Image

img = Image.open("assets/icons/icon-32x32.png")
img.save("assets/favicon.ico", format="ICO", sizes=[(16, 16), (32, 32), (48, 48)])
```

### Step 4: Configure Streamlit page config

Update `app.py`:

```python
st.set_page_config(
    page_title="GA4 Insight Explorer",
    page_icon="assets/favicon.ico",  # ← was "📊", now a real file
    layout="wide",
    initial_sidebar_state="expanded",
)
```

And `pages/learn.py`:

```python
st.set_page_config(
    page_title="Learn · GA4 Insight Explorer",
    page_icon="assets/favicon.ico",  # ← was "📚", now a real file
)
```

### Step 5: Add HTML meta tags for full favicon coverage

Inject into the `<head>` via `st.markdown(unsafe_allow_html=True)`:

```python
def inject_favicon_meta() -> None:
    """Inject favicon and Apple Touch Icon meta tags into the page head."""
    st.markdown("""
    <!-- Favicon (standard) -->
    <link rel="icon" type="image/png" sizes="32x32" href="/assets/icons/icon-32x32.png">
    <link rel="icon" type="image/png" sizes="16x16" href="/assets/icons/icon-16x16.png">
    <link rel="shortcut icon" href="/assets/favicon.ico">

    <!-- Apple Touch Icon (iOS home screen) -->
    <link rel="apple-touch-icon" sizes="180x180" href="/assets/icons/icon-180x180.png">

    <!-- Android / PWA -->
    <link rel="manifest" href="/assets/site.webmanifest">
    <meta name="theme-color" content="#0a0a0f">
    """, unsafe_allow_html=True)
```

### Step 6: PWA manifest

Create `assets/site.webmanifest`:

```json
{
    "name": "GA4 Insight Explorer",
    "short_name": "Insight Explorer",
    "description": "Analyze GA4 data with natural language — powered by Gemini AI",
    "start_url": "/",
    "display": "standalone",
    "background_color": "#0a0a0f",
    "theme_color": "#6366f1",
    "icons": [
        {
            "src": "/assets/icons/icon-192x192.png",
            "sizes": "192x192",
            "type": "image/png"
        },
        {
            "src": "/assets/icons/icon-512x512.png",
            "sizes": "512x512",
            "type": "image/png"
        }
    ]
}
```

### Step 7: Open Graph / Social Share Image

Create a 1200×630px PNG for social sharing (Twitter, Slack, LinkedIn, Discord unfurls):

```python
# scripts/generate_og_image.py
from PIL import Image, ImageDraw, ImageFont

img = Image.new("RGB", (1200, 630), "#0a0a0f")
draw = ImageDraw.Draw(img)

# Paste the icon at center
icon = Image.open("assets/icons/icon-512x512.png").resize((200, 200))
img.paste(icon, (500, 100), icon if icon.mode == "RGBA" else None)

# Add text
draw.text((600, 380), "GA4 Insight Explorer", fill="#f0f0f5", anchor="mm")
draw.text((600, 460), "Analyze GA4 data with natural language", fill="#9898b0", anchor="mm")

img.save("assets/og-image.png")
```

Add Open Graph meta tags:

```html
<meta property="og:title" content="GA4 Insight Explorer">
<meta property="og:description" content="Analyze GA4 data with natural language — powered by Gemini AI">
<meta property="og:image" content="/assets/og-image.png">
<meta property="og:image:width" content="1200">
<meta property="og:image:height" content="630">
<meta name="twitter:card" content="summary_large_image">
```

---

## 🗂️ File Changes Summary

| File | Change |
|---|---|
| `assets/icon.svg` | New — master SVG source |
| `assets/icons/icon-{16,32,48,64,128,180,192,512}x{size}.png` | New — 8 PNG sizes |
| `assets/favicon.ico` | New — multi-res ICO for Windows |
| `assets/site.webmanifest` | New — PWA manifest |
| `assets/og-image.png` | New — 1200×630 social preview |
| `app.py` | Update `page_icon` from emoji to file path |
| `pages/learn.py` | Update `page_icon` from emoji to file path |
| `utils/styles.py` | Add `inject_favicon_meta()` function |
| `scripts/generate_icons.py` | New — one-time icon generation script |
| `requirements.txt` | Add `cairosvg>=2.7.0`, `Pillow>=10.0.0` |
| `.gitignore` | Keep `assets/` (these are committed — they're generated once) |

---

## 🔍 Edge Cases

| Edge Case | Handling |
|---|---|
| **Streamlit doesn't serve static files by default** | Streamlit serves files in `assets/` automatically when referenced with relative paths. Confirmed working with `page_icon="assets/favicon.ico"`. |
| **Browser caches old favicon** | Adding `?v=2` cache-busting to HTML links. The `page_icon` in `st.set_page_config` can't take query params, so the favicon.ico file itself is the cache key. Acceptable — browsers refresh favicons on hard reload. |
| **`cairosvg` installation fails** | It requires `libcairo2` system library. Fallback: use `rsvg-convert` CLI tool, or generate PNGs manually via an online SVG→PNG converter. The `generate_icons.py` script is a one-time tool, not a runtime dependency. |
| **Dark mode vs light mode icon** | Provide two favicons and use `prefers-color-scheme` media query in the HTML: `<link rel="icon" media="(prefers-color-scheme: dark)" ...>` and `<link rel="icon" media="(prefers-color-scheme: light)" ...>`. |
| **PWA install on mobile** | The webmanifest enables "Add to Home Screen" on Android. iOS uses the Apple Touch Icon + meta tags. Both are covered. |

---

## 🧪 Test Impact

- **Smoke test:** Verify the favicon appears in the browser tab after running `streamlit run app.py`
- **Unit test:** No unit test for visual assets (they're binary files)
- **Structural test:** Verify `app.py` and `pages/learn.py` have `page_icon` set to `"assets/favicon.ico"` (update `test_learn_page.py`; `test_app.py` is planned as [IMPL #13](../IMPLEMENTATION_PLAN.md) — add the assertion there once it exists)

---

## 📐 Implementation Order

1. Create `assets/icon.svg` — design the icon (this is the creative step)
2. Write `scripts/generate_icons.py` — rasterizer script
3. Run the script once → generate all PNGs + ICO + OG image
4. Create `assets/site.webmanifest` — PWA manifest
5. Update `app.py` and `pages/learn.py` — swap emoji for file path
6. Add `inject_favicon_meta()` to `utils/styles.py`
7. Call `inject_favicon_meta()` from `app.py` and `pages/learn.py`
8. Smoke test in browser → verify favicon, Apple Touch Icon, PWA manifest

---

## 💭 Why This Matters

A custom favicon is the smallest change with the largest branding impact. It's the difference between "a Streamlit app" and "a product." Browser tabs, bookmarks, and mobile home screens all show the icon. The Open Graph image means sharing a link in Slack or Twitter shows a polished preview instead of a blank card.

Currently, the app uses emoji (`📊` and `📚`) for page icons. Emoji render inconsistently across platforms — the chart emoji on Windows looks different from macOS. A custom SVG-based icon is pixel-perfect everywhere.

---

*Plan created to match the app's existing indigo-to-purple gradient theme and dark aesthetic.*
