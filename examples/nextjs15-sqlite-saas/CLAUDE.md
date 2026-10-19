# Next.js 15 + SQLite SaaS defaults

Use these defaults for this repository. It is a greenfield, single-Node-server SaaS starter using Next.js 15 App Router, TypeScript, and local SQLite through `better-sqlite3`. Do not ask which database, ORM, router, or directory layout to choose. Follow the rules below unless the user explicitly changes the product requirement. Ask only when a product decision or missing data truly blocks the requested behavior.

## Stack and runtime

- Use Node.js 22 LTS, Next.js 15.5.x App Router, React 19.x, TypeScript 5.x with `strict: true`, and `better-sqlite3` 13.x. This keeps the starter on the requested Next 15 line with a predictable compatible stack; strict types catch mistakes at the UI/database boundary. Keep the existing lockfile and package manager so unrelated work does not silently change dependencies.
- Use `better-sqlite3` for SQLite access. Run database code only in the Node.js runtime; never import it from Edge code or a Client Component because this is a native, synchronous Node driver.
- Keep server modules server-only (`import "server-only"` in database and data-access modules). Use `export const runtime = "nodejs"` in a Route Handler that imports the database.
- Local development stores the database at `data/app.sqlite`; a single predictable file outside `public/` is easy to reset locally and is not exposed as a static asset. Allow `DATABASE_PATH` to override it for deployment. Create its parent directory before opening the database, and ignore `data/` in Git so local user data is never committed.
- Declare `@next/env` 15.x directly because the migration runner runs outside Next.js. In the `.mjs` runner, default-import this CommonJS package and destructure `loadEnvConfig`; before reading `DATABASE_PATH`, call `loadEnvConfig(projectRoot, isDevelopment)`, where `isDevelopment = (process.env.NODE_ENV ?? "development") === "development"`. This loads the same `.env*` mode as Next.js; set `NODE_ENV=production` in the deployment environment for both migration and app processes. In both the runner and app, default to `data/app.sqlite`, keep absolute `DATABASE_PATH` values absolute, and resolve relative values from `projectRoot` so they cannot silently open different files.
- This default is for one long-lived Node.js process on persistent local/block storage. SQLite allows concurrent readers but serializes writes. Do not deploy this file to ephemeral serverless storage, a network filesystem, or multiple app replicas. If the hosting requirement changes, stop and propose a hosted database instead of silently changing drivers.
- Keep the existing lint/build tooling to avoid adding configuration work to a greenfield app. Use the commands below; add a command only when the corresponding script exists in `package.json`.

## Project layout

Keep framework routing in `src/app/` and feature logic outside route files:

```text
src/
  app/
    (site)/                 # public pages; route groups do not affect URLs
    (dashboard)/            # authenticated product pages
    api/                    # only public HTTP integrations/webhooks
    actions.ts              # small Server Actions used by app forms
  components/
    ui/                     # reusable, domain-neutral UI
  features/
    accounts/
      components/           # account-specific UI
      server/               # queries, mutations, validation
    billing/
      components/
      server/
  lib/
    db/
      index.ts              # one server-only database connection
      migrations/           # immutable, ordered .sql files
    auth/                   # authentication boundary
    env.ts                  # validated server environment
scripts/
  db-migrate.mjs            # runnable migration entry point
```

Create a feature folder when a feature has more than one file or owns domain logic. Keep one-off page markup in its route; do not add abstraction folders solely to mirror this example. This keeps simple pages simple while giving growing domain logic one predictable home. Route files should compose features, not become the home for SQL or business rules, so routing stays thin and query authorization is easier to review.

## Names and files

- Route segments and folders: `kebab-case`; React components: `PascalCase.tsx`; ordinary TypeScript values/functions: `camelCase`; types: descriptive `PascalCase` names. These familiar distinctions make files and symbols easy to scan.
- SQL tables and columns: lowercase `snake_case`; use plural table names (`users`, `subscriptions`) consistently so names are predictable in queries. Use stable text IDs, generated with Node's `randomUUID()` when no existing schema dictates a format, so IDs are portable and do not depend on SQLite row numbers.
- Migration files: zero-padded sequence plus a short name, for example `001_create_users.sql`, `002_add_user_status.sql`. Sort and apply by filename so lexical order is migration order and review history stays legible.
- Keep imports using the configured `@/` alias. Do not introduce a second alias or rename the existing `src/` layout; one root mapping keeps imports consistent as features move.

## Database and migrations

- Open one `better-sqlite3` connection per Node process and reuse it (including across Next.js development hot reload) to avoid needless native connections and lock contention. Resolve the file path from the repository root and create its parent directory so dev and migration commands target the same file. Set `PRAGMA foreign_keys = ON` because SQLite does not enforce foreign keys unless enabled per connection, and `PRAGMA busy_timeout = 5000` to wait briefly on a lock instead of failing immediately. Enable WAL on a local persistent database to let readers proceed while a writer is active; WAL is not a substitute for a durable volume or multi-writer database.
- Put every schema change in a committed `.sql` file under `src/lib/db/migrations/`. Maintain a `schema_migrations` table keyed by the full migration filename. The migration runner exclusively owns transaction control: apply each unapplied migration and its registry insert together in one transaction, in sorted order; `.sql` files must not issue transaction-control statements such as `BEGIN`, `COMMIT`, `ROLLBACK`, `SAVEPOINT`, or `RELEASE`, so DDL and its registry row commit or roll back atomically.
- If a migration fails, first verify the whole transaction rolled back and its filename is absent from `schema_migrations`. Only then may you correct that file and rerun it, and only if it has not been successfully applied in any shared environment. Never manually mark a failed migration successful or reset a database to hide the failure. Never edit or renumber a migration that has been successfully applied in any shared environment; add a new forward migration instead. Do not rely on ORM auto-sync, runtime schema creation, destructive reset commands, or implicit migrations on every request.
- Make deployed changes backward-compatible: add nullable/defaulted fields or new tables first, deploy compatible code, backfill if needed, then remove old schema only in a later, explicitly reviewed migration. Before a destructive/irreversible change, make a consistent SQLite backup (for example, `await db.backup(destination)`) and verify it can be restored in a separate copy. Never back up an active WAL database by copying only the main `.sqlite` file, because committed data may still be in the WAL.
- Define constraints in SQL: `NOT NULL`, `UNIQUE`, `CHECK`, primary keys, and foreign keys where the product requires them, so the database protects invariants even when writes come from different code paths. Add indexes for actual filter/join/order paths to support observed queries without paying write/storage cost speculatively. Store timestamps as UTC ISO-8601 text so records have one portable format; convert at the application boundary.
- Use prepared statements with bound values for all input. Never build SQL by concatenating user data. Use a `better-sqlite3` transaction for a logical multi-statement write. Keep queries bounded and short because the driver is synchronous and holds the Node event loop while a query runs.
- Give query functions explicit row types matching their selected columns. If the driver returns `unknown` for a result set, narrow it at the data-access boundary; do not let `unknown` leak through feature APIs or silence it with `any`.
- Put reads and domain writes in feature `server/` modules. Check authentication and authorization before every protected read/write; validation is not authorization. Keep secrets and the database module out of client bundles.

## Next.js component and request patterns

- App Router pages and layouts are Server Components by default. Read data in a server feature query and call it directly from the Server Component; do not make the server call its own `/api` endpoint.
- Add `"use client"` only at the smallest component boundary that needs state, effects, event handlers, or browser APIs. Pass serializable view data down; Client Components never import database, auth-secret, or server modules.
- Use a small `"use server"` Server Action for a mutation submitted by an app form. Parse and validate `FormData` at the action boundary, authenticate/authorize, call a feature service, then revalidate or redirect. Return a typed, user-safe error for expected validation/conflict cases; do not expose SQL or stack traces.
- Use Route Handlers only when an HTTP endpoint is needed by an external client, webhook, file response, or protocol. Validate request bodies, authenticate the caller, and return explicit status codes. Webhooks must verify their provider signature before changing data.
- In Next.js 15, `cookies()`, `headers()`, and page/Route Handler `params` and page `searchParams` are async; always `await` them rather than copying older synchronous examples.
- For any page that must read live SQLite data, explicitly export `const dynamic = "force-dynamic"` because a direct database call does not opt a route out of build-time static rendering. Choose caching deliberately: for user-specific or newly-mutated data, avoid shared/static caching and revalidate the narrow affected path or tag after the write. Never place user-specific data in a shared cache.

## Commands

From the project root:

- `npm run dev` starts local development.
- `npm run lint` checks the scaffold's lint rules.
- `npm run build` checks the production build.
- `npm run db:migrate` applies committed pending migrations before starting the app or deploying, once the project defines that package script and `scripts/db-migrate.mjs` entry point.
- `npm run db:migrate` must never drop/reset a database. If no migration runner exists yet, implement the small JavaScript runner at `scripts/db-migrate.mjs` before relying on that command; do not invent a different migration tool without asking.

For a schema or database-access change, add or update a focused test that exercises the SQLite constraint/behavior, run the migration against a fresh temporary database, then run lint and build. Report commands that were not run rather than implying they passed.

## Avoid these patterns

- No Prisma, Drizzle, ORM schema sync, or second database driver by default: this starter has one explicit SQL source of truth and a deliberately small dependency surface.
- No `better-sqlite3` in Edge runtime, Client Components, or request-per-connection code: the native synchronous driver belongs to a long-lived Node server connection.
- No SQL in JSX, route composition files, or Server Actions: feature server modules keep queries reviewable and authorization close to the data operation.
- No self-fetch from Server Components, catch-all `"use client"` pages, or server secrets in props: these add hops, bundle code unnecessarily, or expose private data.
- No unbounded table scans, large synchronous imports, or long transactions in a request: they block Node and SQLite's single writer.
- No swallowed errors, `any` for domain data, fake success responses, or fabricated product/auth/billing behavior. Surface unknowns and ask only for the genuinely missing product decision.
