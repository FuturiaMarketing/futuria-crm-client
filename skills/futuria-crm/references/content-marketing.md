# Content & marketing — email, social, blog

Create and manage content assets in the user's Futuria CRM account: email templates, social posts, and blog posts.

## Email templates

- `emails_fetch-template` — read an existing template (get its id/content before editing).
- `emails_create-template` — create a new email template.
- **Mass email is a usage cost.** Sending newsletters/bulk email draws down the wallet — don't trigger sends casually; see the cost model in `references/terminology-and-voice.md`.
- When drafting copy, match the brand/tone the account already uses; keep the platform name as **Futuria CRM** if it appears.

## Social posting

- `social-media-posting_get-account` — list connected social accounts/profiles.
- `social-media-posting_get-posts` / `get-post` — read scheduled or published posts.
- `social-media-posting_create-post` — schedule or publish a post.
- `social-media-posting_edit-post` — edit an existing post.
- `social-media-posting_get-social-media-statistics` — read engagement/stats.
- **Publishing is outward-facing.** Confirm the target profiles, the text, the media, and the schedule time with the user before creating or publishing.

## Blog

- `blogs_get-blogs` — list the blogs on the account.
- `blogs_get-all-categories-by-location` / `blogs_get-all-blog-authors-by-location` — get valid category and author ids before creating a post.
- `blogs_check-url-slug-exists` — verify the slug is free before publishing.
- `blogs_create-blog-post` / `blogs_update-blog-post` / `blogs_get-blog-post` — manage posts.
- **Order of operations:** resolve blog id → category → author → check slug → create. A published article is public — confirm before publishing and re-read the live result.

## Output example (Italian)

> Ho programmato il post su **Instagram e Facebook** dal tuo account Futuria CRM per giovedì alle 12:00. Testo e immagine come concordato. Vuoi che lo pubblichi subito invece di programmarlo?
