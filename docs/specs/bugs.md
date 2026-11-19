# Spec: Bugs — list, create, close, JSON API

- **Status:** Approved by the owner 2026-11-19 (Feature workflow step 0). Reviewed in RR-002; the
  open questions in section 9 are decided in its Resolution. The approved requirements are
  R10–R22 in `docs/requirements.md` → "Bugs"; where they are more precise, they take precedence.
- **Source:** interview with the owner (QA lead), 2026-11-19. Every statement below was confirmed
  in that interview. Statements tagged [DERIVED] follow from an approved requirement (the
  reasoning is given) and were confirmed by the owner at approval. The items under
  "Open questions" are not decided; they go into the review.

## 1. Scope

In scope: the bug list, creating a bug, closing a bug, and the JSON API `/api/bugs`.

Out of scope for this version:
- the Excel bug report (a separate feature later);
- reopening a closed bug;
- editing or deleting a bug;
- filtering and paging of the bug list;
- assignee and priority fields.

## 2. Users and permissions

All actions require a logged-in user (roles `admin` and `user`, see "Login and logout" in
`docs/requirements.md`).

| Action | Who may do it |
|---|---|
| See the bug list and any bug | every logged-in user (all bugs, not only their own) |
| Create a bug | every logged-in user |
| Close a bug | only the bug's author, or a user with the role `admin` |

This settles the open item "Roles" (RR-001 DEF-009) for `/bugs`: the role matters only for
closing other users' bugs.

## 3. Bug fields

| Field | Set by | Required | Rules |
|---|---|---|---|
| `id` | automatic | — | increasing integer |
| `title` | user | yes | see 5.1 |
| `description` | user | no | see 5.2 |
| `severity` | user | yes | one of `Critical`, `Major`, `Minor`, `Trivial` (see 5.3) |
| `status` | automatic | — | `Open` on create; `Closed` after closing |
| `author` | automatic | — | the user who created the bug |
| `created_at` | automatic | — | time of creation |
| `closed_at` | automatic | — | time of closing; empty while the bug is open |
| `closed_by` | automatic | — | the user who closed the bug; empty while the bug is open |

## 4. Statuses

Only `Open` and `Closed`. The only transition is `Open` → `Closed` (closing). Reopening is out
of scope.

## 5. Validation and limits

### 5.1 Title
- Required. A title that is empty or whitespace-only is rejected.
- Leading and trailing spaces are trimmed before saving.
- At most 200 characters, counted after trimming (200 characters plus a trailing space are
  accepted).
- Duplicate titles are allowed.

### 5.2 Description
- Optional; at most 2000 characters.
- Trimmed like the title.
- An empty or whitespace-only description is stored as NULL, not as an empty string.

### 5.3 Severity
- Required; no default — the user must choose one.
- Case-sensitive: `Critical` is valid, `critical` is not.
- A missing or unknown value is rejected.

### 5.4 Messages
When input is rejected, a message is shown for the field. The requirements do not fix the
wording; tests check that a message for the field is present, not its text (as R4.2).

## 6. Timestamps
- `created_at` and `closed_at` are stored in UTC.
- UI format: `2026-11-19 14:05 UTC`.
- API format: ISO 8601 with `Z`, e.g. `2026-11-19T14:05:00Z`.

## 7. UI

### 7.1 Bug list — `/bugs`
- Columns: ID, title, severity, status, author, created.
- Newest first.
- Closed bugs are shown too.
- No filtering, no paging.

### 7.2 Create a bug — `/bugs/new`
- A separate page with the create form (title, description, severity).
- After a successful create, the user lands on the new bug's page (`/bugs/<id>`) and sees the
  message "Bug created".

### 7.3 Bug page — `/bugs/<id>`
- Each bug has its own page.
- The Close button is on this page and is shown only to users who may close the bug (its author
  or `admin`); other users do not see it.
- Closing needs no confirmation.
- If a user without permission sends the close request anyway, the server rejects it, the bug
  does not change, and an error message is shown on the bug page.
- Closing an already closed bug is rejected with a message; nothing changes (`closed_at` and
  `closed_by` keep their values).
- An unknown bug ID gives a 404 page.

### 7.4 Anonymous access
[DERIVED, confirmed] `/bugs`, `/bugs/new` and `/bugs/<id>` are pages, so R5 applies: anonymous users are
redirected to `/login`. (R5: all pages except `/login` and `/health` require an authenticated
session.)

## 8. JSON API

### 8.1 Endpoints
| Method and path | Purpose |
|---|---|
| `GET /api/bugs` | list of all bugs |
| `GET /api/bugs/<id>` | one bug |
| `POST /api/bugs` | create a bug |
| `POST /api/bugs/<id>/close` | close a bug |

### 8.2 Authentication
- The API uses the same login session (cookie) as the UI.
- An anonymous request gets **401** with a JSON error, not a redirect. This is a deliberate
  difference from R5, which applies to pages.
- [DERIVED, confirmed] A request with an expired session (R8) is anonymous, so it also gets 401.

### 8.3 Bug representation
Fields: `id`, `title`, `description`, `severity`, `status`, `author`, `created_at`,
`closed_at`, `closed_by`.
- Empty fields are `null` (e.g. `description` when empty; `closed_at` and `closed_by` while open).
- `author` and `closed_by` are usernames.
- Timestamps as in section 6.

### 8.4 List
`GET /api/bugs` returns a plain JSON array of bugs, newest first.

### 8.5 Create
- `POST /api/bugs` with `title`, `description` (optional) and `severity`; the same validation as
  section 5.
- Success: **201** with the created bug.
- Validation error: **400** with `{"errors": {"<field>": "<message>"}}`.
- If the request contains `status`, `author`, `created_at` or any other server-controlled field,
  it is rejected with **400** (not silently ignored).

### 8.6 Close
- `POST /api/bugs/<id>/close`.
- Without permission (not the author, not `admin`): **403**; the bug does not change.
- Already closed: **409**; the bug does not change.

### 8.7 Unknown bug
`GET /api/bugs/<id>` and `POST /api/bugs/<id>/close` for an unknown ID: **404**.

## 9. Open questions (not decided in the interview)

These are gaps the interview did not cover. They are listed, not answered; the requirements
review (step 1) will pick them up.

1. **Close success:** the API status code and body for a successful close (e.g. 200 with the
   updated bug, or 204); in the UI, where the user lands and whether a message is shown.
2. **Error bodies other than 400:** the JSON format of the 401, 403, 404 and 409 responses.
3. **Request format for `POST /api/bugs`:** JSON body only? The response to invalid JSON or a
   wrong content type.
4. **Unknown fields on create** that are not server-controlled (e.g. `"foo": 1`): rejected or
   ignored?
5. **Wrong types in the API** (e.g. `"title": 123`, `"severity": null`): rejected with 400 like
   other validation errors?
6. **Where the limits are enforced:** in the UI form as well (e.g. a field that does not accept
   more than 200 characters), or only on the server — as R4.1 / R4.2 separate it for login?
7. **Non-numeric bug IDs** (e.g. `/bugs/abc`, `/api/bugs/abc`): 404 like an unknown ID?
8. **Author and "closed by" in the UI:** shown as usernames (as in the API)?
9. **Character counting for limits:** how characters are counted for non-Latin text and emoji
   (e.g. one emoji = one character?).
