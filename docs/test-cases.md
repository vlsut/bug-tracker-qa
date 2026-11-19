# Test cases

Owned by the QA lead. Each automated test traces back to a case here, and each case refers to the
requirement IDs it covers (`docs/requirements.md`).
Add a case before it is automated; change a case before its test changes.

## Template

### TC-<AREA>-NNN · <Short behaviour, e.g. "Wrong password">
- **Priority:** High | Medium | Low · **Level:** UI | API | DB | E2E | UI (mobile emulation) · **Markers:** `ui`, `api`, `db`, `e2e`, `smoke`, `mobile` · **Covers:** <requirement IDs, e.g. R1, R4.2>
- **Preconditions:** <state of the app and data before the test>
- **Data (parametrized):** <data rows, if the case is data-driven>
- **Steps:** 1. <action>. 2. <action>.
- **Expected:** <what the user or client sees>
- **DB check:** <SELECT query on the real schema and its expected result, if relevant>

## Login and logout

Requirements: `docs/requirements.md` → "Login and logout" (R1–R9).
Test users: see the test users table there. Passwords are referred to by their environment variable names.

---

### TC-LOGIN-001 · Successful login (user)
- **Priority:** High · **Level:** UI · **Markers:** `ui`, `smoke` · **Covers:** R1, R2
- **Preconditions:** user `tester` exists; browser is not logged in.
- **Steps:** 1. Open `/login`. 2. Enter `tester` / `TEST_USER_PASSWORD`. 3. Click "Log in".
- **Expected:** redirected to `/bugs`; header shows `tester`.

### TC-LOGIN-002 · Successful login (admin)
- **Priority:** Medium · **Level:** UI · **Markers:** `ui` · **Covers:** R1, R2
- **Preconditions:** user `admin` exists.
- **Steps:** 1. Open `/login`. 2. Enter `admin` / `TEST_ADMIN_PASSWORD`. 3. Click "Log in".
- **Expected:** redirected to `/bugs`; header shows `admin`.
- **Note:** role-specific checks wait for the open item "Roles".

### TC-LOGIN-003 · Wrong password
- **Priority:** High · **Level:** UI · **Markers:** `ui` · **Covers:** R3
- **Steps:** 1. Open `/login`. 2. Enter `tester` / `wrong-password`. 3. Click "Log in".
- **Expected:** stays on `/login`; error "Invalid username or password"; opening `/bugs` redirects to `/login`.

### TC-LOGIN-004 · Unknown username
- **Priority:** High · **Level:** UI · **Markers:** `ui` · **Covers:** R3
- **Steps:** 1. Open `/login`. 2. Enter `no_such_user` / `TEST_USER_PASSWORD`. 3. Click "Log in".
- **Expected:** stays on `/login`; error "Invalid username or password" (the same text as for a wrong password); no session.

### TC-LOGIN-005 · Empty fields are marked in the form
- **Priority:** Medium · **Level:** UI · **Markers:** `ui` · **Covers:** R4.1
- **Data (parametrized):** empty username; empty password; both empty.
- **Steps:** 1. Open `/login`. 2. Fill the form with the data row. 3. Click "Log in".
- **Expected:** the form is not submitted (still on `/login`, no request to the server); each empty field is marked as required.

### TC-LOGIN-006 · Username is case-sensitive and not trimmed
- **Priority:** Medium · **Level:** UI · **Markers:** `ui` · **Covers:** R1, R3
- **Data (parametrized):** `Tester`; `TESTER`; ` tester` (leading space); `tester ` (trailing space) — password `TEST_USER_PASSWORD`.
- **Steps:** 1. Open `/login`. 2. Enter the data row's username and `TEST_USER_PASSWORD`. 3. Click "Log in".
- **Expected:** login fails with "Invalid username or password"; no session.

### TC-LOGIN-007 · Anonymous access is redirected to login
- **Priority:** High · **Level:** UI · **Markers:** `ui`, `smoke` · **Covers:** R5, R2
- **Preconditions:** browser is not logged in.
- **Steps:** 1. Open `/bugs` directly. 2. Log in as `tester`.
- **Expected:** step 1 → redirected to `/login`, bug list not shown; step 2 → redirected to `/bugs`.
- **Also check:** `/health` is available without login.

### TC-LOGIN-008 · Logout
- **Priority:** High · **Level:** UI · **Markers:** `ui` · **Covers:** R6, R6.2
- **Preconditions:** logged in as `tester`.
- **Steps:** 1. Click "Log out". 2. Open `/bugs` directly. 3. Press browser "Back".
- **Expected:** step 1 → on `/login`; steps 2 and 3 → protected content is not shown, redirect to `/login`.

### TC-LOGIN-009 · Passwords are stored as salted hashes
- **Priority:** High · **Level:** DB · **Markers:** `db` · **Covers:** R7
- **Preconditions:** a second test user `tester_twin` is created with the same password as `tester`.
- **Steps:** 1. Log in as `tester`.
- **Expected:** login succeeds (redirected to `/bugs`).
- **DB check:** `SELECT password_hash = :password FROM users WHERE username = 'tester'` returns 0 (the stored value is not the plain password `TEST_USER_PASSWORD`); `SELECT a.password_hash = b.password_hash FROM users a, users b WHERE a.username = 'tester' AND b.username = 'tester_twin'` returns 0 (equal passwords, different stored values).

### TC-LOGIN-010 · Login on mobile devices
- **Priority:** Medium · **Level:** UI (mobile emulation) · **Markers:** `mobile` · **Covers:** R9, R1, R2
- **Data (parametrized):** every device from the device list in config.
- **Steps:** 1. Open `/login` on the emulated device. 2. Enter `tester` / `TEST_USER_PASSWORD`. 3. Tap "Log in".
- **Expected:** form fully visible without horizontal scroll; login succeeds; header shows `tester`.

### TC-LOGIN-011 · Server rejects empty or whitespace-only credentials
- **Priority:** High · **Level:** API · **Markers:** `api` · **Covers:** R4.2
- **Data (parametrized):** empty username; empty password; username `"   "`; password `"   "`.
- **Steps:** send the login form directly to the server (bypassing browser validation).
- **Expected:** login page with a field message; no session cookie that grants access to `/bugs`.

### TC-LOGIN-012 · Old session cookie is rejected after logout
- **Priority:** High · **Level:** API · **Markers:** `api` · **Covers:** R6.1
- **Steps:** 1. Log in as `tester`, save the session cookie. 2. Log out. 3. Request `/bugs` with the saved cookie.
- **Expected:** step 3 → redirected to `/login`; bug list not returned.

### TC-LOGIN-013 · Session expires after inactivity
- **Priority:** Medium · **Level:** API · **Markers:** `api` · **Covers:** R8, R5
- **Preconditions:** the session timeout is taken from config (`BT_SESSION_IDLE_TIMEOUT`); the test notes the Unix time before and after step 3.
- **Data (parametrized):** `expired` — last activity timeout + 1 s ago; `just-inside` — last activity timeout − 60 s ago (boundary check).
- **Steps:** 1. Log in as `tester`. 2. Set the session's last activity in the database to the data row's value (instead of waiting). 3. Request `/bugs`.
- **Expected:** `expired` → step 3 is redirected to `/login`; `just-inside` → step 3 shows `/bugs` (the session is still valid).
- **DB check:** `SELECT last_seen_at FROM sessions WHERE token = :token` (Unix seconds): `just-inside` → between the two noted times (the request resets the idle timer); `expired` → no row, or still the value set in step 2 (the expired session is not refreshed).

### TC-LOGIN-014 · Protected pages are not cached by the browser
- **Priority:** Medium · **Level:** API · **Markers:** `api` · **Covers:** R6.2
- **Why at API level:** automated Chromium and WebKit reload a page on Back instead of restoring it from cache, so the UI test (TC-LOGIN-008) passes even without this header and cannot catch its removal. This check is the regression guard for R6.2.
- **Preconditions:** logged in as `tester`.
- **Steps:** 1. Request `/bugs`.
- **Expected:** the page is returned with the response header `Cache-Control` containing `no-store`.

## Bugs

Requirements: `docs/requirements.md` → "Bugs" (R10–R22); pages also fall under R5 and R6.2, the API under R8.
Test users: `tester` (role user) and `admin` (role admin), as for login. "Another user's bug" means a bug authored by `admin` and viewed by `tester`.
Bugs are created per case through the API as the stated author, or inserted in the database when a fixed `created_at` is needed. Unless a case says otherwise, a bug has title `Test bug`, no description and severity `Minor`. DB checks use the `bugs` table (columns `id`, `title`, `description`, `severity`, `status`, `author_id`, `created_at`, `closed_at`, `closed_by_id`) and `users`; times are stored as `YYYY-MM-DD HH:MM:SS` in UTC.

---

### TC-BUG-001 · All bugs are returned to every user
- **Priority:** High · **Level:** API · **Markers:** `api`, `smoke` · **Covers:** R10, R21.3
- **Preconditions:** only these three bugs exist: `Open by admin` (open, by `admin`), `Closed by tester` (closed, by `tester`), `Closed by admin` (closed, by `admin`); logged in as `tester`.
- **Steps:** 1. `GET /api/bugs`.
- **Expected:** exactly three bugs, with the titles `Open by admin`, `Closed by tester` and `Closed by admin`.

### TC-BUG-002 · Bug list columns and values
- **Priority:** Medium · **Level:** UI · **Markers:** `ui` · **Covers:** R10, R18
- **Preconditions:** only one bug exists, by `admin`, inserted with title `List row check`, severity `Major`, status `Open`, `created_at` `2026-11-19 14:05:09`; logged in as `tester`.
- **Steps:** 1. Open `/bugs`.
- **Expected:** the columns are ID, title, severity, status, author, created; the row shows the bug's ID, `List row check`, `Major`, `Open`, `admin`, `2026-11-19 14:05 UTC`.

### TC-BUG-003 · Bugs are ordered newest first, equal times by highest ID
- **Priority:** Medium · **Level:** API · **Markers:** `api` · **Covers:** R10, R21.3
- **Preconditions:** only these three bugs exist, inserted in this order (so IDs increase): `A` at `2026-11-19 10:00:00`, `B` at `2026-11-19 10:00:05`, `C` at `2026-11-19 10:00:05`; logged in as `tester`.
- **Steps:** 1. `GET /api/bugs`.
- **Expected:** the titles in the order `C`, `B`, `A`.

### TC-BUG-004 · Create a bug in the UI
- **Priority:** High · **Level:** UI · **Markers:** `ui`, `smoke` · **Covers:** R11
- **Preconditions:** logged in as `tester`; no bugs exist.
- **Data (parametrized):** title `Save button does nothing`; description `Clicking Save on the profile page has no effect.`; severity `Major`.
- **Steps:** 1. Open `/bugs/new`. 2. Fill in title, description and severity. 3. Submit the form.
- **Expected:** the browser is on `/bugs/<id>` of the new bug and the message "Bug created" is shown.

### TC-BUG-005 · A new bug is stored with its initial values
- **Priority:** High · **Level:** DB · **Markers:** `db` · **Covers:** R11, R18
- **Preconditions:** logged in as `tester`; the test notes the UTC time, truncated to the second, before and after the create request.
- **Steps:** 1. Create a bug through the API with title `Initial values`, no description, severity `Minor`.
- **Expected:** 201.
- **DB check:** `SELECT b.title, b.description, b.severity, b.status, a.username AS author, b.created_at, b.closed_at, c.username AS closed_by FROM bugs b JOIN users a ON a.id = b.author_id LEFT JOIN users c ON c.id = b.closed_by_id WHERE b.id = :id` returns one row: title `Initial values`, description NULL, severity `Minor`, status `Open`, author `tester`, `created_at` between the two noted times (format `YYYY-MM-DD HH:MM:SS`), `closed_at` NULL, `closed_by` NULL.

### TC-BUG-006 · A bug created in the UI is the same in the API and the database
- **Priority:** High · **Level:** E2E · **Markers:** `e2e` · **Covers:** R11, R14, R21.2
- **Preconditions:** logged in as `tester` in the browser and in the API client.
- **Steps:** 1. Create a bug in the UI with title `Save button does nothing`, description `Clicking Save on the profile page has no effect.` and severity `Major`. 2. Request `GET /api/bugs/<id>` for the new ID.
- **Expected:** the API returns that title, description and severity, status `Open`, author `tester`, and `closed_at` / `closed_by` `null`.
- **DB check:** `SELECT b.title, b.description, b.severity, b.status, a.username AS author, b.created_at, b.closed_at, c.username AS closed_by FROM bugs b JOIN users a ON a.id = b.author_id LEFT JOIN users c ON c.id = b.closed_by_id WHERE b.id = :id` returns the same values, and its `created_at` is the API's `created_at` in DB format (`YYYY-MM-DD HH:MM:SS` for `YYYY-MM-DDTHH:MM:SSZ`).

### TC-BUG-007 · Title is trimmed before saving
- **Priority:** Medium · **Level:** API · **Markers:** `api`, `db` · **Covers:** R12, R12.1
- **Preconditions:** logged in as `tester`.
- **Data (parametrized):** title `"  Crash on save  "`; title `"\tCrash on save\n"`; title `"\n Crash on save \t "` — severity `Major`.
- **Steps:** 1. `POST /api/bugs` with the data row.
- **Expected:** 201.
- **DB check:** `SELECT title FROM bugs WHERE id = :id` returns exactly `Crash on save`.

### TC-BUG-008 · Empty or whitespace-only title is rejected by the server
- **Priority:** Medium · **Level:** API · **Markers:** `api` · **Covers:** R12.1, R13.2, R22.3
- **Preconditions:** logged in as `tester`; no bugs exist.
- **Data (parametrized):** title `""`; title `"   "`; title `"\t\n"` — severity `Major`.
- **Steps:** 1. `POST /api/bugs` with the data row.
- **Expected:** 400 with an `errors` object that has a `title` entry.
- **DB check:** `SELECT COUNT(*) FROM bugs` returns 0.

### TC-BUG-009 · Title length limit is 200 characters after trimming
- **Priority:** Medium · **Level:** API · **Markers:** `api` · **Covers:** R12.1, R13.2
- **Preconditions:** logged in as `tester`.
- **Data (parametrized):** 1 × `a` → accepted; 200 × `a` → accepted; 201 × `a` → rejected; 200 × `a` followed by one space → accepted; one space followed by 200 × `a` → accepted — severity `Major`.
- **Steps:** 1. `POST /api/bugs` with the data row.
- **Expected:** accepted rows: 201 and the returned title is the input without surrounding spaces (1 or 200 characters); rejected row: 400 with `errors.title`.

### TC-BUG-010 · Characters are counted as Unicode code points
- **Priority:** Medium · **Level:** API · **Markers:** `api` · **Covers:** R12, R12.1
- **Preconditions:** logged in as `tester`.
- **Data (parametrized):** 200 × `ж` → accepted; 201 × `ж` → rejected; 200 × `🐞` → accepted; 201 × `🐞` → rejected — severity `Major`.
- **Steps:** 1. `POST /api/bugs` with the data row.
- **Expected:** accepted rows: 201 and the returned title equals the input; rejected row: 400 with `errors.title`.

### TC-BUG-011 · Duplicate titles are allowed
- **Priority:** Low · **Level:** API · **Markers:** `api` · **Covers:** R12.1
- **Preconditions:** logged in as `tester`; a bug with title `Same title` exists.
- **Steps:** 1. `POST /api/bugs` with title `Same title`, severity `Minor`.
- **Expected:** 201 with a new ID different from the existing bug's ID.

### TC-BUG-012 · Empty description is stored as NULL
- **Priority:** Medium · **Level:** API · **Markers:** `api`, `db` · **Covers:** R12.2
- **Preconditions:** logged in as `tester`.
- **Data (parametrized):** description omitted; description `""`; description `"  \n\t "` — title `No description`, severity `Trivial`.
- **Steps:** 1. `POST /api/bugs` with the data row.
- **Expected:** 201.
- **DB check:** `SELECT description IS NULL FROM bugs WHERE id = :id` returns 1 (NULL, not an empty string).

### TC-BUG-013 · Description is trimmed and limited to 2000 characters
- **Priority:** Medium · **Level:** API · **Markers:** `api` · **Covers:** R12.2, R13.2
- **Preconditions:** logged in as `tester`.
- **Data (parametrized):** 2000 × `d` → accepted; 2001 × `d` → rejected; `"\n"` + 2000 × `d` + `"  "` → accepted; 2000 × `🐞` → accepted; 2001 × `🐞` → rejected — title `Description limit`, severity `Minor`.
- **Steps:** 1. `POST /api/bugs` with the data row.
- **Expected:** accepted rows: 201 and the returned description has exactly 2000 characters (Unicode code points); rejected rows: 400 with `errors.description`.

### TC-BUG-014 · Each severity value is accepted
- **Priority:** Medium · **Level:** API · **Markers:** `api` · **Covers:** R12.3
- **Preconditions:** logged in as `tester`.
- **Data (parametrized):** `Critical`; `Major`; `Minor`; `Trivial` — title `Severity check`.
- **Steps:** 1. `POST /api/bugs` with the data row.
- **Expected:** 201 and the returned severity equals the data row.

### TC-BUG-015 · Missing or unknown severity is rejected
- **Priority:** Medium · **Level:** API · **Markers:** `api` · **Covers:** R12.3, R22.3
- **Preconditions:** logged in as `tester`; no bugs exist.
- **Data (parametrized):** severity omitted; `critical` (lower case); `Blocker`; `""` — title `Severity check`.
- **Steps:** 1. `POST /api/bugs` with the data row.
- **Expected:** 400 with `errors.severity`.
- **DB check:** `SELECT COUNT(*) FROM bugs` returns 0.

### TC-BUG-016 · The create form does not submit without required fields
- **Priority:** Medium · **Level:** UI · **Markers:** `ui` · **Covers:** R13.1
- **Preconditions:** logged in as `tester`.
- **Data (parametrized):** title empty, severity chosen; title filled, no severity chosen; both empty.
- **Steps:** 1. Open `/bugs/new`. 2. Fill the form with the data row. 3. Submit.
- **Expected:** no request is sent to the server; the browser stays on `/bugs/new`; title and severity are marked as required.

### TC-BUG-017 · Over-limit text is submitted and rejected by the server
- **Priority:** Medium · **Level:** UI · **Markers:** `ui` · **Covers:** R13.1, R13.2
- **Preconditions:** logged in as `tester`; no bugs exist.
- **Data (parametrized):** title 201 × `a` → message for the title; title `Long description` with description 2001 × `d` → message for the description — severity `Major`.
- **Steps:** 1. Open `/bugs/new`. 2. Fill the form with the data row. 3. Submit.
- **Expected:** the field keeps the full typed text and the form is submitted; the browser stays on the create form with a message for the data row's field.
- **DB check:** `SELECT COUNT(*) FROM bugs` returns 0.

### TC-BUG-018 · Server rejection is shown in the form
- **Priority:** Medium · **Level:** UI · **Markers:** `ui` · **Covers:** R13.2, R12.1
- **Preconditions:** logged in as `tester`; no bugs exist.
- **Steps:** 1. Open `/bugs/new`. 2. Enter title `"   "` (spaces pass the browser's required check) and severity `Major`. 3. Submit.
- **Expected:** the browser stays on the create form with a message for the title field.
- **DB check:** `SELECT COUNT(*) FROM bugs` returns 0.

### TC-BUG-019 · One 400 response lists all invalid fields
- **Priority:** Medium · **Level:** API · **Markers:** `api` · **Covers:** R22.3, R13.2
- **Preconditions:** logged in as `tester`.
- **Steps:** 1. `POST /api/bugs` with title `""`, severity `Blocker` and description 2001 × `d`.
- **Expected:** 400; `errors` has exactly the keys `title`, `severity` and `description`.

### TC-BUG-020 · Bug page shows all fields of a closed bug
- **Priority:** Medium · **Level:** UI · **Markers:** `ui` · **Covers:** R14, R18
- **Preconditions:** a bug by `tester` inserted with title `Page check`, description `Steps to reproduce`, severity `Critical`, `created_at` `2026-11-19 14:05:59`, closed by `admin` at `2026-11-19 15:30:00`; logged in as `tester`.
- **Steps:** 1. Open `/bugs/<id>`.
- **Expected:** the page shows the ID, `Page check`, `Steps to reproduce`, `Critical`, `Closed`, author `tester`, created `2026-11-19 14:05 UTC` (truncated, not rounded), closed `2026-11-19 15:30 UTC`, closed by `admin`.

### TC-BUG-021 · Bug page shows "-" for empty values
- **Priority:** Medium · **Level:** UI · **Markers:** `ui` · **Covers:** R14
- **Preconditions:** an open bug by `tester` without description; logged in as `tester`.
- **Steps:** 1. Open `/bugs/<id>`.
- **Expected:** description, closed at and closed by each show `-`.

### TC-BUG-022 · Bug page for an ID that is not a bug gives 404
- **Priority:** Low · **Level:** API · **Markers:** `api` · **Covers:** R14
- **Preconditions:** logged in as `tester`; no bug with ID 999999 exists.
- **Data (parametrized):** `/bugs/999999`; `/bugs/abc`; `/bugs/0`; `/bugs/-1`.
- **Steps:** 1. Request the data row's page (no browser needed).
- **Expected:** the response status is 404.

### TC-BUG-023 · The Close button is shown only to those who may close an open bug
- **Priority:** High · **Level:** UI · **Markers:** `ui` · **Covers:** R15
- **Data (parametrized):** open bug by `tester`, viewer `tester` → shown; open bug by `tester`, viewer `admin` → shown; open bug by `admin`, viewer `tester` → hidden; closed bug by `tester`, viewer `tester` → hidden; closed bug by `tester`, viewer `admin` → hidden; closed bug by `admin`, viewer `tester` → hidden.
- **Steps:** 1. Log in as the viewer. 2. Open the bug's page.
- **Expected:** the Close button is shown or hidden as in the data row.

### TC-BUG-024 · Closing a bug in the UI
- **Priority:** High · **Level:** UI · **Markers:** `ui`, `smoke` · **Covers:** R16
- **Preconditions:** an open bug by `tester`; logged in as `tester`.
- **Steps:** 1. Open `/bugs/<id>`. 2. Click "Close".
- **Expected:** the browser stays on `/bugs/<id>`; the message "Bug closed" is shown; status `Closed`, closed at in the format `YYYY-MM-DD HH:MM UTC` and closed by `tester` are shown; the Close button is gone.

### TC-BUG-025 · A closed bug is stored with its closing values
- **Priority:** High · **Level:** DB · **Markers:** `db` · **Covers:** R16, R18
- **Preconditions:** an open bug by `tester`; logged in as `tester` in the API client; the test notes the UTC time, truncated to the second, before and after the close request.
- **Steps:** 1. `POST /api/bugs/<id>/close`.
- **Expected:** 200.
- **DB check:** `SELECT b.title, b.description, b.severity, b.status, a.username AS author, b.created_at, b.closed_at, c.username AS closed_by FROM bugs b JOIN users a ON a.id = b.author_id LEFT JOIN users c ON c.id = b.closed_by_id WHERE b.id = :id` returns status `Closed`, `closed_by` `tester`, `closed_at` between the two noted times (format `YYYY-MM-DD HH:MM:SS`); title, description, severity, author and `created_at` unchanged.

### TC-BUG-026 · Admin can close another user's bug
- **Priority:** High · **Level:** API · **Markers:** `api` · **Covers:** R15, R16, R21.4
- **Preconditions:** an open bug by `tester`; logged in as `admin`.
- **Steps:** 1. `POST /api/bugs/<id>/close`.
- **Expected:** 200; the returned bug has status `Closed` and `closed_by` `admin`.

### TC-BUG-027 · Close without permission is rejected in the API
- **Priority:** High · **Level:** API · **Markers:** `api` · **Covers:** R17.1
- **Preconditions:** an open bug by `admin`; logged in as `tester`.
- **Steps:** 1. `POST /api/bugs/<id>/close`.
- **Expected:** 403.
- **DB check:** `SELECT status, closed_at, closed_by_id FROM bugs WHERE id = :id` returns `Open`, NULL, NULL.

### TC-BUG-028 · Close without permission is rejected in the UI
- **Priority:** High · **Level:** UI · **Markers:** `ui` · **Covers:** R17.1
- **Preconditions:** an open bug by `admin`; logged in as `tester`.
- **Steps:** 1. Open `/bugs/<id>`. 2. Send the page's close request anyway (as the hidden button would, from the browser session).
- **Expected:** the bug page shows an error message and status `Open`.
- **DB check:** `SELECT status, closed_at, closed_by_id FROM bugs WHERE id = :id` returns `Open`, NULL, NULL.

### TC-BUG-029 · Closing an already closed bug is rejected in the API
- **Priority:** Medium · **Level:** API · **Markers:** `api` · **Covers:** R17.2
- **Preconditions:** a bug by `tester` closed by `tester` at `2026-11-19 15:30:00`; logged in as `admin`.
- **Steps:** 1. `POST /api/bugs/<id>/close`.
- **Expected:** 409.
- **DB check:** `SELECT b.closed_at, c.username FROM bugs b JOIN users c ON c.id = b.closed_by_id WHERE b.id = :id` returns `2026-11-19 15:30:00`, `tester` (unchanged).

### TC-BUG-030 · Closing an already closed bug is rejected in the UI
- **Priority:** Medium · **Level:** UI · **Markers:** `ui` · **Covers:** R17.2
- **Preconditions:** an open bug by `tester`; logged in as `tester`; the bug page is open in the browser.
- **Steps:** 1. Close the bug through the API as `tester`. 2. Click "Close" on the page opened before.
- **Expected:** the page shows a message and status `Closed`.
- **DB check:** `SELECT closed_at, closed_by_id FROM bugs WHERE id = :id` returns the values set in step 1 (step 2 changed nothing).

### TC-BUG-031 · API timestamps are ISO 8601 in UTC to the second
- **Priority:** Medium · **Level:** API · **Markers:** `api` · **Covers:** R18, R21.2
- **Preconditions:** a bug by `tester` inserted with `created_at` `2026-11-19 14:05:09`, closed at `2026-11-19 15:30:00`; logged in as `tester`.
- **Steps:** 1. `GET /api/bugs/<id>`.
- **Expected:** `created_at` is `2026-11-19T14:05:09Z` and `closed_at` is `2026-11-19T15:30:00Z`.

### TC-BUG-032 · Markup in title and description is shown as plain text
- **Priority:** High · **Level:** UI · **Markers:** `ui` · **Covers:** R19
- **Preconditions:** logged in as `tester`; a bug created with title `<script>window.injected = 1</script><b>Bold</b>` and description `<img src=x onerror="window.injected = 2">`, severity `Major`.
- **Steps:** 1. Open `/bugs`. 2. Open `/bugs/<id>`.
- **Expected:** on `/bugs` the title, and on `/bugs/<id>` the title and the description, are shown as the exact typed text; on both pages no bold text is rendered and `window.injected` is undefined.

### TC-BUG-033 · Bug pages fit mobile screens without horizontal scrolling
- **Priority:** Medium · **Level:** UI (mobile emulation) · **Markers:** `mobile` · **Covers:** R20
- **Preconditions:** two bugs by `tester`, each with a title of 200 × `a` (no spaces) and a description of 2000 × `d`: one open, one closed by `tester`; logged in as `tester`.
- **Data (parametrized):** pages `/bugs`, `/bugs/new`, `/bugs/<id>` of the open bug, `/bugs/<id>` of the closed bug × every device in the device list.
- **Steps:** 1. Open the page on the emulated device.
- **Expected:** the page has no horizontal scroll.

### TC-BUG-034 · Anonymous API requests get 401, not a redirect
- **Priority:** High · **Level:** API · **Markers:** `api` · **Covers:** R21.1
- **Preconditions:** no session; one bug exists.
- **Data (parametrized):** `GET /api/bugs`; `GET /api/bugs/<id>`; `POST /api/bugs` with a valid body; `POST /api/bugs/<id>/close`.
- **Steps:** 1. Send the data row's request without following redirects.
- **Expected:** 401; no `Location` header.

### TC-BUG-035 · An expired session gets 401 in the API
- **Priority:** Medium · **Level:** API · **Markers:** `api` · **Covers:** R21.1, R8
- **Preconditions:** logged in as `tester` in the API client.
- **Steps:** 1. Set the session's last activity in the database to `BT_SESSION_IDLE_TIMEOUT` + 1 s ago. 2. `GET /api/bugs`.
- **Expected:** 401.

### TC-BUG-036 · A bug in the API has exactly the agreed fields
- **Priority:** Medium · **Level:** API · **Markers:** `api` · **Covers:** R21.2, R21.3
- **Preconditions:** an open bug by `admin` without description; logged in as `tester`.
- **Steps:** 1. `GET /api/bugs/<id>`.
- **Expected:** a JSON object with exactly the keys `id`, `title`, `description`, `severity`, `status`, `author`, `created_at`, `closed_at`, `closed_by`; `id` is an integer; `author` is `admin`; `description`, `closed_at` and `closed_by` are `null`.

### TC-BUG-037 · The API list is a plain JSON array
- **Priority:** Medium · **Level:** API · **Markers:** `api` · **Covers:** R21.3
- **Preconditions:** only one bug exists, an open bug by `admin`; logged in as `tester`.
- **Steps:** 1. `GET /api/bugs`.
- **Expected:** the body is a JSON array (not an object) with exactly one element, the bug object with that bug's `id`.

### TC-BUG-038 · Create in the API returns 201 with the created bug
- **Priority:** High · **Level:** API · **Markers:** `api`, `smoke` · **Covers:** R21.4, R11
- **Preconditions:** logged in as the data row's user.
- **Data (parametrized):** `tester`; `admin`.
- **Steps:** 1. `POST /api/bugs` with title `API create`, description `From the API`, severity `Critical`.
- **Expected:** 201; the body is the bug with those values, status `Open`, author the data row's user, `closed_at` and `closed_by` `null`.

### TC-BUG-039 · Close in the API returns 200 with the updated bug
- **Priority:** Medium · **Level:** API · **Markers:** `api` · **Covers:** R21.4, R16
- **Preconditions:** an open bug by `tester`; logged in as `tester`.
- **Steps:** 1. `POST /api/bugs/<id>/close`.
- **Expected:** 200; the body is the bug with status `Closed`, `closed_by` `tester` and `closed_at` in the format `YYYY-MM-DDTHH:MM:SSZ`.

### TC-BUG-040 · Error precedence: 401 → 404 → 403 → 409
- **Priority:** Medium · **Level:** API · **Markers:** `api` · **Covers:** R22.2
- **Data (parametrized):** anonymous, close of unknown ID → 401; anonymous, close of a closed bug by `tester` → 401; anonymous, `GET /api/bugs/<id>` of unknown ID → 401; `tester`, close of unknown ID → 404; `tester`, close of a closed bug by `admin` → 403; `tester`, close of a closed bug by `tester` → 409.
- **Steps:** 1. Send the data row's request.
- **Expected:** the status code of the data row.

### TC-BUG-041 · Create accepts only a JSON body
- **Priority:** Medium · **Level:** API · **Markers:** `api` · **Covers:** R22.3
- **Preconditions:** logged in as `tester`; no bugs exist.
- **Data (parametrized):** form-encoded body with valid fields; `text/plain` body with valid JSON text.
- **Steps:** 1. `POST /api/bugs` with the data row.
- **Expected:** 415.
- **DB check:** `SELECT COUNT(*) FROM bugs` returns 0.

### TC-BUG-042 · Invalid JSON is rejected with 400
- **Priority:** Medium · **Level:** API · **Markers:** `api` · **Covers:** R22.3
- **Preconditions:** logged in as `tester`; no bugs exist.
- **Steps:** 1. `POST /api/bugs` with `Content-Type: application/json` and the body `{"title": "Broken",`.
- **Expected:** 400.
- **DB check:** `SELECT COUNT(*) FROM bugs` returns 0.

### TC-BUG-043 · Unknown fields and wrong types are rejected with 400
- **Priority:** Medium · **Level:** API · **Markers:** `api` · **Covers:** R22.3
- **Preconditions:** logged in as `tester`; no bugs exist.
- **Data (parametrized):** extra field `"foo": 1` → `errors.foo`; `"title": 123` → `errors.title`; `"severity": null` → `errors.severity`; `"description": 5` → `errors.description` — other fields valid.
- **Steps:** 1. `POST /api/bugs` with the data row.
- **Expected:** 400 with the data row's key in `errors`.
- **DB check:** `SELECT COUNT(*) FROM bugs` returns 0.

### TC-BUG-044 · Server-controlled fields are rejected on create
- **Priority:** High · **Level:** API · **Markers:** `api` · **Covers:** R22.3
- **Preconditions:** logged in as `tester`; no bugs exist.
- **Data (parametrized):** `"id": 5`; `"status": "Closed"`; `"author": "admin"`; `"created_at": "2026-01-01T00:00:00Z"`; `"closed_at": "2026-01-01T00:00:00Z"`; `"closed_by": "admin"` — with a valid title and severity.
- **Steps:** 1. `POST /api/bugs` with the data row.
- **Expected:** 400 with the field's own name in `errors`.
- **DB check:** `SELECT COUNT(*) FROM bugs` returns 0.

### TC-BUG-045 · IDs that are not a bug get 404 in the API
- **Priority:** Low · **Level:** API · **Markers:** `api` · **Covers:** R22.4
- **Preconditions:** logged in as `tester`; no bug with ID 999999 exists.
- **Data (parametrized):** IDs `999999`, `abc`, `0`, `-1` × `GET /api/bugs/<id>` and `POST /api/bugs/<id>/close`.
- **Steps:** 1. Send the data row's request.
- **Expected:** 404.

### TC-BUG-046 · Anonymous users are redirected from the new bug pages
- **Priority:** High · **Level:** API · **Markers:** `api` · **Covers:** R5
- **Preconditions:** no session; one bug exists.
- **Data (parametrized):** `/bugs/new`; `/bugs/<id>`.
- **Steps:** 1. Request the data row's page (no browser needed).
- **Expected:** the request ends on `/login`; the response contains no bug content.
- **Note:** `/bugs` itself is covered by TC-LOGIN-007.

### TC-BUG-047 · API errors other than validation share one body format
- **Priority:** Medium · **Level:** API · **Markers:** `api` · **Covers:** R22.1
- **Data (parametrized):** 401 — anonymous `GET /api/bugs`; 403 — `tester` closes an open bug by `admin`; 404 — `GET /api/bugs/999999`; 409 — `tester` closes a closed bug by `tester`; 415 — `POST /api/bugs` with a `text/plain` body.
- **Steps:** 1. Send the data row's request.
- **Expected:** the body is a JSON object with exactly one key, `error`, whose value is a non-empty string.

### TC-BUG-048 · Bug pages are not cached by the browser
- **Priority:** Medium · **Level:** API · **Markers:** `api` · **Covers:** R6.2
- **Preconditions:** one bug exists; logged in as `tester`.
- **Data (parametrized):** `/bugs/new`; `/bugs/<id>`.
- **Steps:** 1. Request the data row's page.
- **Expected:** the response header `Cache-Control` contains `no-store`.
- **Note:** `/bugs` is covered by TC-LOGIN-014; the same reason applies (automated browsers reload on Back).

### TC-BUG-049 · A title of 200 emoji can be created in the form
- **Priority:** Medium · **Level:** UI · **Markers:** `ui` · **Covers:** R13.1, R12.1
- **Preconditions:** logged in as `tester`.
- **Steps:** 1. Open `/bugs/new`. 2. Enter title 200 × `🐞` and severity `Minor`. 3. Submit.
- **Expected:** the browser is on the new bug's page and the message "Bug created" is shown.
- **DB check:** `SELECT length(title) FROM bugs WHERE id = :id` returns 200 (SQLite counts characters).

### TC-BUG-050 · The create form offers exactly the four severities, none preselected
- **Priority:** Medium · **Level:** UI · **Markers:** `ui` · **Covers:** R12.3
- **Preconditions:** logged in as `tester`.
- **Steps:** 1. Open `/bugs/new`.
- **Expected:** the selectable severity values are exactly `Critical`, `Major`, `Minor` and `Trivial`, and no severity is selected.

### TC-BUG-051 · Admin closes another user's bug in the UI
- **Priority:** High · **Level:** UI · **Markers:** `ui` · **Covers:** R15, R16
- **Preconditions:** an open bug by `tester`; logged in as `admin`.
- **Steps:** 1. Open `/bugs/<id>`. 2. Click "Close".
- **Expected:** the browser stays on `/bugs/<id>`; the message "Bug closed" is shown; status `Closed` and closed by `admin` are shown; the Close button is gone.

### TC-BUG-052 · Markup in a re-shown form value stays plain text
- **Priority:** High · **Level:** UI · **Markers:** `ui` · **Covers:** R19, R13.2
- **Preconditions:** logged in as `tester`; no bugs exist.
- **Steps:** 1. Open `/bugs/new`. 2. Enter title `"><script>window.injected = 3</script>`, description 2001 × `d` and severity `Major`. 3. Submit.
- **Expected:** the form is shown again with a message for the description; the title field's value is exactly the typed title; `window.injected` is undefined.
- **DB check:** `SELECT COUNT(*) FROM bugs` returns 0.

### TC-BUG-053 · Another user's close of a closed bug is rejected in the UI
- **Priority:** Medium · **Level:** UI · **Markers:** `ui` · **Covers:** R17.1, R17.2
- **Preconditions:** a bug by `admin`, closed by `admin` at `2026-11-19 15:30:00`; logged in as `tester`.
- **Steps:** 1. Open `/bugs/<id>`. 2. Send the page's close request anyway (from the browser session).
- **Expected:** the bug page shows a message and status `Closed`.
- **DB check:** `SELECT b.closed_at, c.username FROM bugs b JOIN users c ON c.id = b.closed_by_id WHERE b.id = :id` returns `2026-11-19 15:30:00`, `admin` (unchanged).

### TC-BUG-054 · The list page shows bugs newest first, equal times by highest ID
- **Priority:** Medium · **Level:** UI · **Markers:** `ui` · **Covers:** R10
- **Preconditions:** only these three bugs exist, inserted in this order (so IDs increase): `A` at `2026-11-19 10:00:00`, `B` at `2026-11-19 10:00:05`, `C` at `2026-11-19 10:00:05`; logged in as `tester`.
- **Steps:** 1. Open `/bugs`.
- **Expected:** the rows are in the order `C`, `B`, `A` (the same order as the API list).
