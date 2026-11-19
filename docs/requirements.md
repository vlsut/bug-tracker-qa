# Requirements

Requirement IDs are stable: a changed requirement keeps its ID, a new one gets the next free number.
Each test case in `docs/test-cases.md` refers to the requirements it covers.
Review history: `docs/requirements-review.md`.

## Login and logout

Status: **Approved 2026-11-19** (after review RR-001; open items listed below).

### Test users
| Username | Password | Role |
|---|---|---|
| `admin` | `TEST_ADMIN_PASSWORD` | admin |
| `tester` | `TEST_USER_PASSWORD` | user |

Passwords are not stored in the repository. The table names the environment variables that hold
them (`.env` locally, GitHub Secrets in CI); see `.env.example`.

### Requirements

**R1. Login with username and password.**
A user logs in on `/login` with a username and a password.
The username comparison is case-sensitive; leading and trailing spaces are not trimmed.
The password must match exactly.

**R2. Successful login.**
After a successful login the user is redirected to `/bugs` — always, regardless of the page the user
tried to open before logging in — and sees their username in the page header.

**R3. Failed login.**
If the username or the password does not match (including a username that differs only in letter case
or surrounding spaces), the user stays on `/login`, sees the error "Invalid username or password",
and no session is created. The message is the same for an unknown username and for a wrong password.

**R4. Required fields.**
Username and password are required.
- R4.1 (UI): an empty field is marked as required in the form, and the form is not submitted.
- R4.2 (server): a request with an empty or whitespace-only username or password is rejected:
  the user stays on `/login`, a message is shown for the field, and no session is created.

**R5. Access control.**
All pages except `/login` and `/health` require an authenticated session.
An anonymous request to any other page is redirected to `/login`.

**R6. Logout.**
Logout invalidates the session on the server and redirects the user to `/login`.
After logout:
- R6.1: a request to a protected page with the session cookie from before logout is redirected to `/login`;
- R6.2: the browser Back button does not show protected content.

**R7. Password storage.**
Passwords are never stored in plain text. They are stored with an adaptive, salted
password-hashing function, so two users with the same password have different stored values.

**R8. Session expiry.**
A session expires after 30 minutes of inactivity. Any request made with a valid session resets
the idle timer: the 30 minutes start again from that request. The next request after expiry is
treated as anonymous (R5). The timeout is configurable so tests can use a short value.

**R9. Mobile layout of the login page.**
On every device in the project's device list, the login form is fully visible without horizontal
scrolling, and login works as in R1–R3.

### Out of scope (decided 2026-11-19)
- **Brute-force protection** (lockout, delay or rate limiting after failed attempts): deliberately out
  of scope for this demo application. Known risk RISK-001 in the review. Revisit before any real use.

### Open items (not decided yet)
- **Input limits** (RR-001 DEF-008): maximum length of username and password, and the response to
  over-limit or special input.
- **Roles** (RR-001 DEF-009): settled for `/bugs` by R15 (RR-002): the role matters only for
  closing other users' bugs. Whether the role changes anything in login is still open.
- **HTTP contract** (RR-001 DEF-006, partly): exact status codes for failed login and for redirects.
  Tests check the observable result (page and redirect target), not the status code, until decided.

## Bugs

Status: **Approved 2026-11-19** (spec `docs/specs/bugs.md`, review RR-002 with its Resolution).

Pages in this section fall under R5 (anonymous users are redirected to `/login`); the JSON API
under R21.1 (anonymous requests get 401). Every user referred to below is logged in.

### Bug fields
| Field | Set by | Notes |
|---|---|---|
| `id` | automatic | increasing integer |
| `title` | user | required (R12.1) |
| `description` | user | optional (R12.2) |
| `severity` | user | required: `Critical`, `Major`, `Minor` or `Trivial` (R12.3) |
| `status` | automatic | `Open` on create, `Closed` after closing (R16) |
| `author` | automatic | the user who created the bug |
| `created_at` | automatic | time of creation (R18) |
| `closed_at` | automatic | time of closing; empty while open (R16, R18) |
| `closed_by` | automatic | the user who closed the bug; empty while open (R16) |

### Requirements

**R10. Bug list.**
`/bugs` shows all bugs to every user, including closed ones, with the columns ID, title,
severity, status, author and created. Author is the username. Order: newest `created_at` first;
bugs with equal `created_at` are ordered by `id`, highest first. No filtering, no paging.

**R11. Create a bug.**
Every user can create a bug on `/bugs/new` with title, description and severity. On success the
user is taken to the new bug's page (`/bugs/<id>`) and sees the message "Bug created". The new bug
has status `Open`, the current user as author, the creation time as `created_at`, and no
`closed_at` or `closed_by`.

**R12. Field rules.**
A *character* is one Unicode code point. *Trimming* removes all leading and trailing whitespace,
including tabs and newlines.
- R12.1 Title: required; trimmed before saving; a title that is empty after trimming is rejected;
  at most 200 characters after trimming; duplicate titles are allowed.
- R12.2 Description: optional; trimmed before saving; at most 2000 characters after trimming; a
  description that is empty after trimming is stored as NULL, not as an empty string.
- R12.3 Severity: required, no default; one of `Critical`, `Major`, `Minor`, `Trivial`,
  case-sensitive; a missing or other value is rejected.

**R13. Where the field rules are enforced.**
- R13.1 (UI): the create form marks title and severity as required; a form with an empty required
  field is not submitted. The form does not limit the length of title or description: length
  limits are enforced only by the server (R13.2), which shows a message after submit.
- R13.2 (server): the server applies R12 to every request, whether it comes from the form or the
  API. Rejected input creates no bug; the UI shows a message for each invalid field (the wording
  is not fixed; tests check that the message is present), the API answers as in R22.3.

**R14. Bug page.**
`/bugs/<id>` shows all fields of the bug. Author and closed by are usernames. Empty values (e.g.
description, or `closed_at` and `closed_by` while open) are shown as "-". An ID that is not an
existing bug — unknown, non-numeric, zero or negative — gives a 404 page.

**R15. Who may close a bug.**
Only the bug's author or a user with the role `admin` may close a bug. The Close button on the bug
page is shown only to them, and only while the bug is open.

**R16. Close a bug.**
The only status transition is `Open` → `Closed`; reopening is out of scope. Closing needs no
confirmation. It sets status `Closed`, `closed_at` to the closing time and `closed_by` to the
current user. In the UI the user stays on the bug page, sees the message "Bug closed", the status
`Closed`, `closed_at` and `closed_by`, and no Close button.

**R17. Rejected close.**
- R17.1 A user who may not close the bug (R15) and sends the close request anyway: the bug does
  not change; the UI shows an error message on the bug page; the API answers 403.
- R17.2 Closing a bug that is already closed: the bug does not change (`closed_at` and `closed_by`
  keep their values); the UI shows a message; the API answers 409.

**R18. Timestamps.**
`created_at` and `closed_at` are stored in UTC, to the second. UI format: `2026-11-19 14:05 UTC`;
the UI truncates to the minute, it does not round (`14:05:59` is shown as `14:05`). API format:
ISO 8601 with `Z`, e.g. `2026-11-19T14:05:00Z`.

**R19. User text is shown as plain text.**
Markup in title and description (e.g. `<script>`, `<b>`) is stored as typed and shown as plain
text in the UI; it is never interpreted by the browser.

**R20. Mobile layout of the bug pages.**
On every device in the project's device list, `/bugs`, `/bugs/new` and `/bugs/<id>` fit the screen
without horizontal scrolling.

**R21. JSON API.**
- R21.1 Authentication: the API uses the same login session (cookie) as the UI. A request without
  a valid session — anonymous or expired (R8) — gets 401 with a JSON error, not a redirect. This is
  a deliberate difference from R5, which applies to pages.
- R21.2 Representation: a bug is a JSON object with `id`, `title`, `description`, `severity`,
  `status`, `author`, `created_at`, `closed_at`, `closed_by`. Empty fields are `null`; `author` and
  `closed_by` are usernames; timestamps as R18.
- R21.3 Read: `GET /api/bugs` returns a plain JSON array of all bugs in the order of R10;
  `GET /api/bugs/<id>` returns one bug.
- R21.4 Write: `POST /api/bugs` creates a bug (R11, R12) and answers 201 with the created bug;
  `POST /api/bugs/<id>/close` closes it (R15–R17) and answers 200 with the updated bug.

**R22. API errors.**
- R22.1 Errors other than validation (401, 403, 404, 409, 415) have the body
  `{"error": "<message>"}`.
- R22.2 When several conditions apply, they are checked in this order: authentication (401) →
  bug exists (404) → permission (403) → state (409).
- R22.3 `POST /api/bugs` accepts only a JSON body: another `Content-Type` → 415; invalid JSON →
  400. Validation errors answer 400 with `{"errors": {"<field>": "<message>"}}` listing all
  invalid fields at once. Also rejected with 400: unknown fields; fields of the wrong type;
  server-controlled fields (`id`, `status`, `author`, `created_at`, `closed_at`, `closed_by`),
  each reported under its own name in `errors`.
- R22.4 An ID that is not an existing bug — unknown, non-numeric, zero or negative — gets 404.

### Out of scope (decided 2026-11-19)
- The Excel bug report (a separate feature), reopening, editing and deleting bugs, filtering and
  paging, assignee and priority fields.
- **Protection against cross-site requests (CSRF):** deliberately out of scope for this version.
  Accepted risk RR-002 RISK-001 (the session cookie is SameSite=Lax, D-015). Revisit before any
  real use.

### Open items
None for this section.
