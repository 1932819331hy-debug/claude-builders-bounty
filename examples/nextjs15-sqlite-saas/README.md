# Next.js 15 + SQLite SaaS `CLAUDE.md`

A ready-to-copy project guide for a greenfield Next.js 15 App Router SaaS using TypeScript and one local SQLite driver: `better-sqlite3`. It fixes the framework, runtime, database, layout, migration, naming, and component defaults so Claude Code can start from a concrete baseline without asking you to choose between alternatives.

## Use it in a new project

Requires Node.js 22 LTS and npm. From the directory where you keep projects:

```sh
npx create-next-app@15 my-saas \
  --typescript --eslint --app --src-dir --import-alias "@/*" --use-npm --no-tailwind --yes
cd my-saas
npm install better-sqlite3@^13
npm install @next/env@^15
npm install --save-dev @types/better-sqlite3
mkdir -p data src/lib/db/migrations scripts
grep -qxF '/data/' .gitignore || printf '\n/data/\n' >> .gitignore
```

Copy this folder's `CLAUDE.md` to the new project's root, then start the scaffold:

```sh
cp /path/to/claude-builders-bounty/examples/nextjs15-sqlite-saas/CLAUDE.md ./CLAUDE.md
npm run dev
```

Replace `/path/to/claude-builders-bounty` with the checkout location. The instructions intentionally choose `better-sqlite3` on a persistent, single-node Node.js host. They do not assume an auth provider, billing service, product data model, or deployment vendor. The app can be built up incrementally; no placeholder product schema is imposed.

The standalone migration runner must load `.env*` before resolving `DATABASE_PATH` with `loadEnvConfig(projectRoot, isDevelopment)` from the direct `@next/env` dependency. Local runs default to `NODE_ENV=development` and the development `.env*` files; set `NODE_ENV=production` in the deployment environment for both migration and app processes so both select production settings. Use `data/app.sqlite` when unset, keep absolute paths unchanged, and resolve relative paths from the project root. This keeps the migration command and Next.js pointed at the same database. For tests, pass an explicit temporary `DATABASE_PATH`.

## Defaults at a glance

- Stack: Node.js 22 LTS, Next.js 15.5.x App Router, React 19.x, TypeScript 5.x strict, `better-sqlite3` 13.x
- Routes: `src/app`; reusable UI: `src/components`; domain code: `src/features/<feature>/server`
- SQL: ordered, committed `src/lib/db/migrations/NNN_short_description.sql`; parameterized queries and explicit transactions
- Components: Server Components by default; small Client Component boundaries; Server Actions for app-form mutations; Route Handlers for external HTTP interfaces
- Storage: local `data/app.sqlite` for development; persistent single-node/block storage in deployment; no ephemeral serverless or multi-replica SQLite file

The commands in `CLAUDE.md` distinguish scaffold commands from project scripts: `npm run db:migrate` is available after the project adds the migration runner and package script. The guide tells Claude Code to implement that runner before relying on it, never to invent an unavailable command or reset a database.

## Check the instructions

Start with a concrete task, for example: “Add a tasks feature with a title and creation time. Add a migration, a server query, a Server Action, and a page. Keep the migration additive and test it against a temporary SQLite database.” Claude Code should use the selected defaults and ask only for a product detail that the request leaves genuinely undecidable.

A successful `npm run build` or fixture test checks the project setup and SQL behavior; it does not establish that a Claude Code conversation has been run. Record that conversational acceptance check separately.
