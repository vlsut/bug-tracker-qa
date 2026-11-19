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
- **Expected:** <what the user or client sees; expected DB values, if relevant>

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
- **Steps:** same as TC-LOGIN-001 with `admin` / `TEST_ADMIN_PASSWORD`.
- **Expected:** redirected to `/bugs`; header shows `admin`.
- **Note:** role-specific checks wait for the open item "Roles".

### TC-LOGIN-003 · Wrong password
- **Priority:** High · **Level:** UI · **Markers:** `ui` · **Covers:** R3
- **Steps:** 1. Open `/login`. 2. Enter `tester` / `wrong-password`. 3. Click "Log in".
- **Expected:** stays on `/login`; error "Invalid username or password"; opening `/bugs` redirects to `/login`.

### TC-LOGIN-004 · Unknown username
- **Priority:** High · **Level:** UI · **Markers:** `ui` · **Covers:** R3
- **Steps:** 1. Open `/login`. 2. Enter `no_such_user` / `TEST_USER_PASSWORD`. 3. Click "Log in".
- **Expected:** exactly the same error text as TC-LOGIN-003; no session.

### TC-LOGIN-005 · Empty fields are marked in the form
- **Priority:** Medium · **Level:** UI · **Markers:** `ui` · **Covers:** R4.1
- **Data (parametrized):** empty username; empty password; both empty.
- **Steps:** 1. Open `/login`. 2. Fill the form with the data row. 3. Click "Log in".
- **Expected:** the form is not submitted (still on `/login`, no request to the server); each empty field is marked as required.

### TC-LOGIN-006 · Username is case-sensitive and not trimmed
- **Priority:** Medium · **Level:** UI · **Markers:** `ui` · **Covers:** R1, R3
- **Data (parametrized):** `Tester`; `TESTER`; ` tester` (leading space); `tester ` (trailing space) — password `TEST_USER_PASSWORD`.
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
- **Preconditions:** a second test user is created with the same password as `tester`.
- **Steps:** 1. Read both users' stored password values from the database. 2. Log in as `tester`.
- **Expected:** neither stored value equals the plain password (`TEST_USER_PASSWORD`); the two stored values differ; login in step 2 succeeds.

### TC-LOGIN-010 · Login on mobile devices
- **Priority:** Medium · **Level:** UI (mobile emulation) · **Markers:** `mobile` · **Covers:** R9, R1, R2
- **Data (parametrized):** every device from the device list in config.
- **Steps:** same as TC-LOGIN-001 on the emulated device.
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
- **Preconditions:** the session timeout is taken from config (`BT_SESSION_IDLE_TIMEOUT`).
- **Data (parametrized):** `expired` — last activity timeout + 1 s ago; `just-inside` — last activity timeout − 60 s ago (boundary check).
- **Steps:** 1. Log in as `tester`. 2. Set the session's last activity in the database to the data row's value (instead of waiting). 3. Request `/bugs`.
- **Expected:** `expired` → step 3 is redirected to `/login`; `just-inside` → step 3 shows `/bugs` (the session is still valid).
