# Content & marketing — email, social, blog

Create and manage content assets in the user's Futuria CRM account: email templates, social posts, and blog posts. Base URL and headers in `references/api-and-troubleshooting.md`.

## Email templates

- List/read: `GET /emails/builder?locationId={id}&limit=10&offset=0` → `builders[]`, `total`. (A `/emails/templates` path does **not** exist — 404.)
- Creating or editing a template body is builder territory: prefer guiding the user in the web editor. If asked to automate it, verify the write endpoint's response shape on first use and re-read afterwards.
- **Mass email is a usage cost.** Sending newsletters/bulk email draws down the wallet — don't trigger sends casually; see the cost model in `references/terminology-and-voice.md`.
- When drafting copy, match the brand/tone the account already uses; keep the platform name as **Futuria CRM** if it appears.

## Social posting

- Connected profiles: `GET /social-media-posting/{locationId}/accounts` → `results` (validated).
- List posts: `POST /social-media-posting/{locationId}/posts/list` — body `{"skip": "0", "limit": "10"}` — **skip/limit as strings** (numbers return 422); → `results.{posts, count}` (validated).
- Read one: `GET /social-media-posting/{locationId}/posts/{postId}`.
- Create/schedule: `POST /social-media-posting/{locationId}/posts` — include target account ids, text, media, schedule time.
- Edit: `PUT /social-media-posting/{locationId}/posts/{postId}`.
- **Publishing is outward-facing.** Confirm the target profiles, the text, the media, and the schedule time with the user before creating or publishing; re-read the post after the write.

## Blog

- Blog sites of the account: `GET /blogs/site/all?locationId={id}&skip=0&limit=10` → `data[]` (site id in `_id`) (validated).
- Posts of a blog: `GET /blogs/posts/all?locationId={id}&blogId={blogId}&limit=10&offset=0` (validated).
- Valid authors / categories: `GET /blogs/authors?locationId={id}&limit=10&offset=0` and `GET /blogs/categories?locationId={id}&limit=10&offset=0` (validated).
- Slug check: `GET /blogs/posts/url-slug-exists?urlSlug={slug}&locationId={id}` → `{exists}` (validated).
- Create: `POST /blogs/posts`; update: `PUT /blogs/posts/{postId}`.
- **Order of operations:** resolve blog id → category ids → author id → check slug → create → re-read (and check the public page for published posts). A published article is public — confirm before publishing.

## Output example (Italian)

> Ho programmato il post su **Instagram e Facebook** dal tuo account Futuria CRM per giovedì alle 12:00. Testo e immagine come concordato. Vuoi che lo pubblichi subito invece di programmarlo?
