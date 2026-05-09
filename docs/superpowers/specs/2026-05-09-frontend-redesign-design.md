# Frontend Redesign — Slate + Violet

**Status:** design-approved
**Date:** 2026-05-09

## Goal

Replace the current inline-style, generic-gray frontend with a polished, production-grade design system. Dark/light mode, loading skeletons, micro-animations, and a Linear-inspired slate+violet palette.

## Design Tokens

### Colors

```
Background:  #f8f9fb (light) / #0f1115 (dark)
Surface:     #ffffff (light) / #1a1d24 (dark)
Border:      #e5e7eb (light) / #272a33 (dark)
Text primary:#111827 (light) / #f1f5f9 (dark)
Text muted:  #6b7280 (light) / #8b949e (dark)
Accent:      #6d5dfc (violet-500)
Accent hover:#5a4de0
Green (pos): #10b981
Red (neg):   #ef4444
```

### Typography

- Headings + body: Inter
- Tickers, numbers, code: JetBrains Mono
- Scale: 12 / 14 / 16 / 18 / 20 / 24 / 28 / 32

### Spacing & Shape

- 4px grid: 4, 8, 12, 16, 20, 24, 32, 40, 48
- Radii: 6px cards, 8px buttons/inputs, 12px modals
- Shadows: layered (0/1/2/4/8px spreads), accent glow on interactive elements

## File Structure

```
frontend/src/
  styles/
    tokens.css           # CSS custom properties
    global.css            # CSS reset, body defaults, font imports
    theme.css             # [data-theme="dark"] overrides
  theme/
    ThemeContext.tsx       # ThemeProvider, useTheme hook
    ThemeToggle.tsx        # Sun/moon button
  components/
    SearchBar.tsx
    SearchBar.module.css
    AssetDetail.tsx
    AssetDetail.module.css
    PriceChart.tsx
    PriceChart.module.css
    NewsList.tsx
    NewsList.module.css
    SettingsDialog.tsx
    SettingsDialog.module.css
    AnalyzePanel.tsx
    AnalyzePanel.module.css
    Skeleton.tsx           # New: reusable shimmer skeleton
    Skeleton.module.css
  pages/
    SearchPage.tsx
    SearchPage.module.css
    AssetPage.tsx
    AssetPage.module.css
  App.tsx
  App.module.css
  main.tsx                  # Updated: import global styles, wrap ThemeProvider
```

Every existing component gets a `.module.css`. Inline `style={{}}` moves to class names. Component structure and logic stay unchanged — this is a styling pass, not a rewrite.

## Layout

### Top Nav (persistent across all pages)

- Logo/name left, search shortcut center (jumps to /search), theme toggle right
- 56px height, subtle bottom border, surface background
- Sticky on scroll

### SearchPage

- Hero section: "Analyze Any Asset, Globally" heading, muted subtitle
- Centered search bar with autocomplete dropdown
- Popular ticker chips below search for quick access (static list: AAPL, MSFT, 0700.HK, 300502.SZ)

### AssetPage

- Back link: "← Back to search" breadcrumb-style at top
- Asset header: single surface card merging profile (name, symbol, sector, country, description), price (current, change, change%), and 8 key metrics in a grid
- Price chart: section card with period selector
- News list: section card with article cards
- Analyze: button row (Analyze + Settings), result rendered in a section card

## Interactions & Polish

### Loading States

- Reusable `Skeleton` component: gray bar with CSS shimmer animation
- Skeleton placeholders for: asset header card, chart area, news list

### Dark/Light Mode

- ThemeContext provides `theme` and `toggleTheme`
- `[data-theme="dark"]` on `<html>` swaps CSS custom properties via `theme.css`
- Respects `prefers-color-scheme` on first visit; persists choice in localStorage
- Background transition: `0.2s ease` on `<body>`

### Micro-animations

- Search dropdown: fadeIn + slideDown (0.15s)
- Metric cards: hover lift (translateY -2px, shadow increase)
- News cards: hover border shifts to accent color
- Period buttons: active state color swap (existing behavior, themed)
- Analyze button: subtle glow on hover (accent box-shadow)
- Settings modal: scale(0.95→1) + fade entrance

### Page Transitions

- SearchPage → AssetPage: simple 0.2s opacity fade via CSS transition on route wrapper

### Empty & Error States

- Empty chart: "No price data for this period" with muted icon
- Empty news: "No recent news" placeholder
- Error banner: red-tinted card with error message and retry button
- 404: "Asset not found" with link back to search

## Implementation Notes

- Zero new dependencies. CSS Modules work natively in Vite. Inter + JetBrains Mono loaded from Google Fonts.
- React logic unchanged — this is a pure styling pass
- Theme toggle goes in top nav; ThemeProvider wraps entire app in `main.tsx`
- `tokens.css` imported once in `main.tsx`; each component imports its own `.module.css`
- Skeleton component is the only new component; everything else is existing components restyled
