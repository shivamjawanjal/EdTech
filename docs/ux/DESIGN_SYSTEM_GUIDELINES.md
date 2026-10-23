# Design System & Mobile UX Guidelines

## 1. Visual Design Philosophy: Focused & Inspiring

The visual identity is designed to eliminate cognitive fatigue for long study sessions while giving both students and the teacher a state-of-the-art, premium feel. It avoids juvenile gamification cartoons or sterile enterprise grey tables in favor of a clean, high-contrast, modern aesthetic.

---

## 2. Color Palette & Semantic Tokens

### 2.1 Brand Palette (Curated HSL)
- **Primary / Brand Indigo**:
  - `brand-50`: `#EEF2FF` (Subtle active backgrounds)
  - `brand-100`: `#E0E7FF` (Card borders / hover states)
  - `brand-500`: `#6366F1` (Action buttons, active tabs)
  - `brand-600`: `#4F46E5` (Primary CTA, focus rings)
  - `brand-700`: `#4338CA` (Pressed states)
- **Secondary / Slate Neutral**:
  - `slate-50`: `#F8FAFC` (App background light mode)
  - `slate-100`: `#F1F5F9` (Card background light mode)
  - `slate-200`: `#E2E8F0` (Borders, dividers)
  - `slate-700`: `#334155` (Secondary text)
  - `slate-900`: `#0F172A` (Primary text, dark surface)

### 2.2 Pedagogical Health Badges (High Visibility)
- 🟢 **`On Track`**:
  - Background: `bg-emerald-50`, Text: `text-emerald-700`, Border: `border-emerald-200`
- 🟡 **`Needs Attention`**:
  - Background: `bg-amber-50`, Text: `text-amber-700`, Border: `border-amber-200`
- 🔴 **`At Risk`**:
  - Background: `bg-rose-50`, Text: `text-rose-700`, Border: `border-rose-200`

---

## 3. Typography & Hierarchy

- **Font Family**: Modern sans-serif via Google Fonts: **`Inter`** or **`Plus Jakarta Sans`**.
- **Scale**:
  - `Page Title (h1)`: `text-2xl font-bold tracking-tight text-slate-900` (Mobile: `text-xl`)
  - `Section Heading (h2)`: `text-lg font-semibold text-slate-900`
  - `Card Title (h3)`: `text-base font-medium text-slate-800`
  - `Body Copy`: `text-sm font-normal text-slate-600 leading-relaxed`
  - `Metadata / Badges`: `text-xs font-medium text-slate-500`

---

## 4. Mobile Ergonomics & Breakpoints

### 4.1 Responsive Breakpoints
- **Mobile (`< 640px`)**: Single column layout, full-width cards, bottom fixed navigation bar, one-handed thumb reachability.
- **Tablet (`640px – 1024px`)**: 2-column dashboard grids, collapsible sidebar.
- **Desktop (`> 1024px`)**: Fixed 260px left sidebar, wide content stage, split-screen rapid grading console.

### 4.2 Touch Targets & Micro-Interactions
- Minimum touch target for any interactive element on mobile: **`48px x 48px`**.
- Subtle smooth transitions: `transition-all duration-150 ease-in-out` on buttons, card hovers, and tabs.
- Zero layout shift during video playback or photo upload.
