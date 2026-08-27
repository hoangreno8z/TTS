# ANTIGRAVITY MASTER SYSTEM CONSTITUTION & RULES

This document defines the permanent, immutable engineering standards and behavioral rules for this workspace.

---

## 1. ABSOLUTE ZERO-EMOJI RULE (TIÊU CHUẨN 0 EMOJI TUYỆT ĐỐI)
- NEVER insert Unicode emojis (e.g. 🚀, 💡, 🎙️, 📱, ✨, 🎉, ⚠️, ❌, ✅, etc.) anywhere in:
  - Frontend HTML, CSS, JavaScript, or UI components.
  - Backend API responses, logs, or error messages.
  - Button labels, notifications, toasts, or modals.
- ALWAYS use vector SVG icons, CSS-rendered shapes, or clean text badges instead.

---

## 2. MOBILE-FIRST ERGONOMICS & COMPACT SCREEN SPACE
- Design every UI component to work flawlessly on mobile touchscreens (360px - 430px) and scale smoothly to desktop (1920px).
- All interactive buttons, tabs, and sliders must have at least 44px x 44px tap targets.
- Primary controls must live in the comfortable thumb zone (bottom half of mobile screens).
- Maximize screen space efficiency: Use compact padding (8px - 16px), collapsible panels, and clean drawer sheets instead of cluttered page sprawl.

---

## 3. ZERO-LAG ARCHITECTURE & PERFORMANCE FIRST
- Only animate `transform` and `opacity` with CSS GPU acceleration (`will-change: transform`).
- Avoid Layout Thrashing and heavy recalculations in JavaScript loops.
- Use `dvh` for responsive mobile viewports to prevent address-bar jitter.
- Keep frontend codebase lightweight, dependency-free, and blazing fast (< 0.5s initial render).

---

## 4. MODULAR, CLEAN CODE ORGANIZATION
- Maintain strict separation of concerns:
  - Data / Audio Core Models $ightarrow$ Service Handlers $ightarrow$ UI Controllers $ightarrow$ Presentation Views.
- Write clean, self-documenting code with deterministic names and zero redundant copy-paste.
- Always include robust error handling with clean visual toast notifications for the user.

---

## 5. SKILL INHERITANCE
- Automatically apply guidelines from `.agents/skills/`:
  - `ui-ux-pro-max` (Design & Ergonomics)
  - `mobile-responsive-craftsman` (Responsive & Viewports)
  - `zero-lag-frontend-architecture` (Performance & Memory)
  - `clean-code-logic-organizer` (Directory & Code Cleanliness)
  - `audio-web-app-engineer` (Audio Studio & Web Audio API)
