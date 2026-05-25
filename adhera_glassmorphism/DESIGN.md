---
name: Adhera Glassmorphism
colors:
  surface: '#111318'
  surface-dim: '#111318'
  surface-bright: '#37393e'
  surface-container-lowest: '#0c0e12'
  surface-container-low: '#1a1c20'
  surface-container: '#1e2024'
  surface-container-high: '#282a2e'
  surface-container-highest: '#333539'
  on-surface: '#e2e2e8'
  on-surface-variant: '#b9cacb'
  inverse-surface: '#e2e2e8'
  inverse-on-surface: '#2f3035'
  outline: '#849495'
  outline-variant: '#3a494b'
  surface-tint: '#00dbe7'
  primary: '#e1fdff'
  on-primary: '#00363a'
  primary-container: '#00f2ff'
  on-primary-container: '#006a71'
  inverse-primary: '#00696f'
  secondary: '#adc6ff'
  on-secondary: '#002e6a'
  secondary-container: '#0566d9'
  on-secondary-container: '#e6ecff'
  tertiary: '#fcf5ff'
  on-tertiary: '#3c0091'
  tertiary-container: '#e2d4ff'
  on-tertiary-container: '#6f3cd8'
  error: '#ffb4ab'
  on-error: '#690005'
  error-container: '#93000a'
  on-error-container: '#ffdad6'
  primary-fixed: '#74f5ff'
  primary-fixed-dim: '#00dbe7'
  on-primary-fixed: '#002022'
  on-primary-fixed-variant: '#004f54'
  secondary-fixed: '#d8e2ff'
  secondary-fixed-dim: '#adc6ff'
  on-secondary-fixed: '#001a42'
  on-secondary-fixed-variant: '#004395'
  tertiary-fixed: '#e9ddff'
  tertiary-fixed-dim: '#d0bcff'
  on-tertiary-fixed: '#23005c'
  on-tertiary-fixed-variant: '#5516be'
  background: '#111318'
  on-background: '#e2e2e8'
  surface-variant: '#333539'
  glass-surface: rgba(255, 255, 255, 0.05)
  glass-border: rgba(255, 255, 255, 0.12)
  status-success: '#10B981'
  status-warning: '#F59E0B'
  status-error: '#EF4444'
typography:
  display-lg:
    fontFamily: Inter
    fontSize: 48px
    fontWeight: '700'
    lineHeight: 56px
    letterSpacing: -0.02em
  display-md:
    fontFamily: Inter
    fontSize: 36px
    fontWeight: '700'
    lineHeight: 44px
    letterSpacing: -0.02em
  headline-lg:
    fontFamily: Inter
    fontSize: 30px
    fontWeight: '600'
    lineHeight: 38px
  headline-md:
    fontFamily: Inter
    fontSize: 24px
    fontWeight: '600'
    lineHeight: 32px
  body-lg:
    fontFamily: Inter
    fontSize: 18px
    fontWeight: '400'
    lineHeight: 28px
  body-md:
    fontFamily: Inter
    fontSize: 16px
    fontWeight: '400'
    lineHeight: 24px
  label-lg:
    fontFamily: Inter
    fontSize: 14px
    fontWeight: '600'
    lineHeight: 20px
    letterSpacing: 0.01em
  label-sm:
    fontFamily: Inter
    fontSize: 12px
    fontWeight: '500'
    lineHeight: 16px
    letterSpacing: 0.02em
  display-md-mobile:
    fontFamily: Inter
    fontSize: 28px
    fontWeight: '700'
    lineHeight: 34px
rounded:
  sm: 0.25rem
  DEFAULT: 0.5rem
  md: 0.75rem
  lg: 1rem
  xl: 1.5rem
  full: 9999px
spacing:
  base: 4px
  xs: 4px
  sm: 8px
  md: 16px
  lg: 24px
  xl: 32px
  2xl: 48px
  3xl: 64px
  container-max: 1280px
  gutter: 24px
---

## Brand & Style

The design system for the platform is rooted in a **Futuristic Minimalist** aesthetic, drawing inspiration from high-end productivity tools and modern operating systems like VisionOS. It balances the high-stakes reliability of healthcare with the sleek, frictionless feel of premium SaaS. 

The core style is **Glassmorphism**, characterized by translucent surfaces, deep layered depth, and vibrant accent glows. This approach creates a "floating" interface that feels light and unobtrusive, yet sophisticated. The UI should evoke an emotional response of **calm authority and technological precision**—reassuring patients while providing providers with a high-density, professional command center.

**Key Visual Principles:**
- **Atmospheric Depth:** Use high-contrast backgrounds to make frosted glass panels pop.
- **Precision Detailing:** Thin, low-opacity borders and subtle noise textures suggest tactile quality.
- **Vibrant Accents:** Use cyan and blue glows to guide the eye toward primary actions and critical data.
- **Ultra-Clean Layouts:** Heavy use of whitespace and structured typography to ensure medical data remains readable under glass effects.

## Colors

The system defaults to a **Dark Mode** to maximize the visual impact of glass effects and luminous accents. 

- **Primary (Vibrant Cyan):** Used for primary actions, focus states, and key adherence metrics. It represents clarity and life.
- **Secondary & Tertiary (Blue/Purple):** Used for gradients, data visualization, and subtle background glows to provide depth and a "pro" aesthetic.
- **Neutral (Deep Navy/Charcoal):** The foundation of the UI. It provides the high-contrast backing necessary for glass transparency to remain accessible.
- **Glass Surfaces:** Defined by low-opacity white backgrounds with a backdrop blur (32px+) and a subtle noise texture to prevent banding and add a tactile feel.

**Accessibility Note:** Despite the glass effects, all text must maintain a contrast ratio of at least 4.5:1 against the background. Background blurs must be strong enough to neutralize any underlying visual noise.

## Typography

The typography system utilizes **Inter** for its exceptional legibility and modern, systematic appearance. The hierarchy is designed to highlight critical medical data (like adherence percentages) while maintaining a clean dashboard structure.

- **Display & Headlines:** Use tighter letter spacing and semi-bold/bold weights to command attention.
- **Body Text:** Optimized for readability with generous line heights to accommodate medical instructions.
- **Labels:** Used for metadata, form headers, and status indicators. Often capitalized or slightly letter-spaced for better differentiation.
- **Mobile Scaling:** Large display sizes scale down significantly on mobile to prevent layout breaking while maintaining visual impact.

## Layout & Spacing

The design system follows a **12-column fluid grid** for desktop dashboards and a single-column layout for mobile. 

**Layout Philosophy:**
- **Floating Panels:** Content is housed in glass panels that float above the base layer.
- **Responsive Margins:** Desktop uses 64px outer margins, scaling down to 16px on mobile.
- **Rhythm:** An 8px-based grid ensures consistent alignment across all components.
- **Touch Targets:** For the patient "One-tap response" feature, all interactive elements maintain a minimum hit area of 48px.

**Breakpoints:**
- **Mobile:** < 640px (Single column, full-width panels)
- **Tablet:** 640px - 1024px (8-column grid, 24px margins)
- **Desktop:** > 1024px (12-column grid, 64px margins)

## Elevation & Depth

Hierarchy is established through **translucency and backdrop filters** rather than traditional opaque shadows.

1.  **Level 0 (Base):** Deep Navy (#0A0C10) with subtle radial gradients of Cyan and Purple to create "glow zones."
2.  **Level 1 (Surface):** Glass panels with `backdrop-filter: blur(24px)` and a 1px white border at 12% opacity.
3.  **Level 2 (Floating/Modals):** Increased blur (40px) and a soft, diffused outer glow (Primary Cyan at 10% opacity) to signify priority.
4.  **Level 3 (Emergency Prompts):** These use a high-contrast treatment with a stronger border and a "pulse" glow effect in the status-error color.

**Shadows:** Use large-radius (32px-64px), low-opacity (10-15%) shadows that inherit the hue of the nearest brand color (Cyan/Blue) to create an "ambient light" effect.

## Shapes

The shape language is defined by **smooth, generous curves** that reflect the friendly yet modern nature of the platform.

- **Panels & Cards:** 24px corner radius (`rounded-xl` / `rounded-2xl` equivalents).
- **Buttons & Inputs:** 12px corner radius for a modern feel.
- **Status Chips:** Full pill-shape for quick recognition.
- **Borders:** Always keep borders thin (1px). Thick borders break the glassmorphism illusion.

## Components

### Buttons
- **Primary:** Solid Cyan background with dark charcoal text. High-contrast for accessibility.
- **Secondary:** Translucent glass background with white text and a 1px Cyan border.
- **Tertiary/Ghost:** No background, Cyan text, clear focus states.

### Cards
- Always glassmorphic. Must include a subtle noise texture overlay (2% opacity) to enhance the tactile feel. 
- Content inside should be padded at `lg` (24px).

### Input Fields
- Glass surfaces with a 1px border that brightens to Primary Cyan on focus.
- Labels must always be visible (never placeholder-only) to meet WCAG AA standards.

### Status Indicators
- **Must use Icon + Text.**
- Use the semantic colors (Success/Warning/Error) as soft glows behind the icon or as text color.
- "Taken" status: Success Green with a check icon.
- "Missed" status: Error Red with an X or Alert icon.

### Charts (Chart.js)
- Line and bar charts should use Cyan and Purple gradients.
- Background grid lines should be extremely low contrast (rgba(255,255,255,0.05)).
- Data points must be large enough to be touch-friendly.

### Modals / Emergency Prompts
- High-priority overlays that dim the background with a 60% black overlay before applying the glass blur.
- Focus is trapped within the modal until an action is taken.