# Engineering Code Standards

## 1. Python & FastAPI Backend Standards

- **Python Version**: Python 3.11+.
- **Typing**: 100% type-annotated function signatures and return types. Use Python standard `typing` and Pydantic v2 `BaseModel`.
- **Domain Isolation**:
  - Domain logic resides inside `backend/app/domains/<domain_name>/`.
  - Modules must not directly import models or execute raw queries across private tables of another domain. Cross-domain queries must use public domain service functions.
- **Async Best Practices**:
  - Use `async def` for I/O-bound endpoints and async database sessions (`AsyncSession` with SQLAlchemy).
  - Avoid blocking synchronous calls inside async route handlers.
- **Linting & Formatting**:
  - `black` (line length 100).
  - `ruff` for fast linting and import sorting.

---

## 2. React & Frontend Standards

- **Framework & Build**: React 18+ with Vite.
- **Language**: Modern JavaScript / TypeScript (strict mode preferred).
- **Styling**: Tailwind CSS exclusively.
  - No arbitrary inline hex styles (e.g., `style={{ color: '#1a2b3c' }}`). Use Tailwind design tokens (e.g., `text-brand-primary`, `bg-slate-900`).
- **Component Architecture**:
  - Atomic, reusable components placed in `src/components/ui/` (buttons, modals, badges, cards).
  - Feature-specific views placed in `src/features/<domain>/`.
  - State management: Use lightweight hooks (`zustand` or React Context) rather than heavy boilerplate libraries like Redux.
- **Accessibility & Mobile Responsiveness**:
  - Every screen must be tested against 360px viewport width (standard Android mobile).
  - Proper semantic HTML elements (`<main>`, `<nav>`, `<article>`, `<button>`).
  - Form inputs must have descriptive associated `<label>` tags and unique IDs for automated test accessibility.
