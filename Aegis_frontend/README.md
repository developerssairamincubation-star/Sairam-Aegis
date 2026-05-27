# Aegis Frontend

Three-page Next.js application for Sairam Aegis:

- `/login`
- `/chat`
- `/projects`

## Setup

```bash
npm install
cp .env.example .env.local
npm run dev
```

Fill in Supabase public credentials before using login/signup.

For local visual QA without Supabase configured, temporarily run with:

```bash
NEXT_PUBLIC_AUTH_PREVIEW_MODE=true npm run dev
```

Keep `NEXT_PUBLIC_AUTH_PREVIEW_MODE=false` for normal use.
