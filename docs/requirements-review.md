# Requirements reviews

## Requirements review RR-001 — Login and logout (R1–R7)

- **Date:** 2026-11-19
- **Source:** "Login and logout" section of `docs/test-cases.md` (draft): requirements R1–R7, test data table, TC-LOGIN-001…010
- **Method:** wiegers-requirements-checker v3.4, **Standard Audit**
- **Intended use:** test design and automation readiness
- **Artifact type:** user requirements + business rules + security constraint (R7); test artifact (TC-LOGIN-*) used for traceability only

### 1. Executive verdict

**Overall: Needs Clarification.** The happy path and access control (R1, R2, R3, R5) are clear enough to automate now. R4, R6 and R7 do not yet give an objective pass/fail oracle, and several test cases check behaviour that no requirement states.

| Gate | Status | Reason |
|---|---|---|
| Requirements Readiness | Needs Clarification | Matching rules, hashing, logout semantics and session lifetime undefined (DEF-001, 002, 004, 007) |
| Test Design Readiness | Needs Clarification | No oracle for R4, R6, R7; test cases exceed requirements (DEF-003, 004, 005) |
| Automation Readiness | Needs Clarification | R1, R2, R3, R5 ready (seeded users, local DB, stable UI); R4, R6, R7 blocked by the same oracles; HTTP contract missing for API checks (DEF-006) |

### 2. Defect and risk inventory

#### DEF-001 · R7 does not define what "stored as hashes" means
- **Evidence [CONFIRMED]:** R7: "Passwords are stored as hashes, never as plain text."
- **Problem [MISSING]:** no algorithm, salting or work-factor requirement. An unsalted fast hash (e.g. MD5/SHA-1) satisfies R7 as written. TC-LOGIN-009 expects "the format of the hashing algorithm used by the app", which is not defined anywhere, so the oracle is circular.
- **Impact:** weak password storage can pass review and tests; TC-LOGIN-009 cannot fail for the right reason.
- **Severity** High · **Urgency** P1 · **Confidence** High
- **Recommendation:** state the accepted scheme as a security constraint (an adaptive, salted password-hashing function) and the observable oracle (e.g. stored value has the scheme's prefix and differs for two users with the same password).
- **Question:** Which password-hashing scheme is acceptable, and must two equal passwords produce different stored values?

#### DEF-002 · Username matching rules are undefined
- **Evidence [CONFIRMED]:** R1: "Users log in with username and password". TC-LOGIN-006 marks the rule as "confirm the rule".
- **Problem [MISSING]:** case sensitivity, trimming of leading/trailing spaces and Unicode normalization are not stated.
- **Impact:** TC-LOGIN-006 has no expected result; developers and tests may pick different rules.
- **Severity** Medium · **Urgency** P1 · **Confidence** High
- **Recommendation:** add one explicit rule for username comparison; keep passwords exact-match.
- **Question:** Is the username case-sensitive, and are leading/trailing spaces trimmed before comparison?

#### DEF-003 · R4 does not say where "required" is enforced
- **Evidence [CONFIRMED]:** R4: "the form is not submitted with an empty field."
- **Problem [ASSUMPTION]:** can be read as browser-side validation only (HTML `required`) or as server-side validation. A direct POST with empty values (API, script, disabled JS) has no defined outcome. Whitespace-only input is not covered.
- **Impact:** UI tests may pass while the server accepts empty credentials; no oracle for API-level checks.
- **Severity** Medium · **Urgency** P1 · **Confidence** High
- **Recommendation:** split into a UI rule and a server rule with the server's response for empty/whitespace-only fields.
- **Question:** Must the server also reject empty or whitespace-only username/password, and with which response?

#### DEF-004 · R6 "ends the session" has no observable oracle
- **Evidence [CONFIRMED]:** R6: "Logout ends the session and redirects to /login."
- **Problem [MISSING]:** not stated whether the session is invalidated on the server (an old session cookie is rejected after logout) or only removed from the browser.
- **Impact:** a test that only checks the redirect passes even if a copied session cookie still grants access.
- **Severity** Medium · **Urgency** P1 · **Confidence** High
- **Recommendation:** define the observable outcome: after logout, a request to a protected page with the previous session cookie is redirected to `/login`.
- **Question:** Must a session cookie captured before logout be rejected after logout?

#### DEF-005 · Test cases verify behaviour that no requirement states
- **Evidence [DERIVED]:** comparison of TC-LOGIN-* with R1–R7:
  - TC-LOGIN-005 "the empty field is marked as required" — R4 says nothing about marking;
  - TC-LOGIN-008 step 3 "browser Back does not show /bugs" — not in R5 or R6;
  - TC-LOGIN-010 "form fits the screen without horizontal scroll" — no responsive/mobile requirement exists.
- **Problem:** broken traceability; these expectations are untraced assumptions.
- **Impact:** coverage per requirement is misleading; failures in these checks cannot be judged as defects.
- **Severity** Medium · **Urgency** P1 · **Confidence** High
- **Recommendation:** either add requirements for these behaviours or remove the checks from the test cases.
- **Question:** Are field highlighting, Back-button behaviour after logout and responsive layout required behaviours?

#### DEF-006 · No HTTP-level contract for login and redirects
- **Evidence [CONFIRMED]:** R2 "redirected to /bugs", R3 "stays on /login", R5 "redirected to /login".
- **Problem [MISSING]:** status codes for successful login, failed login and anonymous access are not defined; R5 does not say whether the originally requested URL is restored after login.
- **Impact:** API/DB-level tests (planned in this project) have no oracle; behaviour may differ between UI and direct requests.
- **Severity** Medium · **Urgency** P2 · **Confidence** High
- **Recommendation:** add the expected status per case (e.g. redirect vs error response) and the post-login target.
- **Question:** After an anonymous user is sent to /login from a protected page, should a successful login return them to that page or always to /bugs?

#### DEF-007 · Session lifetime is undefined
- **Evidence [MISSING]:** R1–R7 define login and logout but no idle or absolute session timeout and no "remember me" behaviour.
- **Impact:** expiry cannot be tested; sessions may live indefinitely.
- **Severity** Medium · **Urgency** P2 · **Confidence** High
- **Recommendation:** state the session lifetime or mark expiry explicitly out of scope.
- **Question:** Does a session expire after inactivity or after a fixed time, and if so after how long?

#### DEF-008 · Input limits for username and password are undefined
- **Evidence [MISSING]:** no length limits or character rules for either field.
- **Impact:** boundary tests (very long strings, non-Latin letters, emoji, injection-like input) have no expected result.
- **Severity** Low · **Urgency** P2 · **Confidence** High
- **Recommendation:** state maximum lengths and the expected response to over-limit and special input.
- **Question:** What are the maximum lengths of username and password, and is over-limit input rejected or truncated?

#### DEF-009 · Roles appear in test data but in no requirement
- **Evidence [CONFIRMED]:** test data lists `admin` (role admin) and `tester` (role user); R1–R7 never mention roles; TC-LOGIN-002 expects the same result as TC-LOGIN-001.
- **Impact:** unclear whether role-specific behaviour must be tested; TC-LOGIN-002 adds little value as written.
- **Severity** Low · **Urgency** P2 · **Confidence** High
- **Recommendation:** either define what differs by role (now or in a later feature) or note that roles have no effect on login.
- **Question:** Does the role change anything in login or on /bugs?

#### RISK-001 · No protection against password guessing
- **Evidence [MISSING]:** no requirement on failed-attempt limits, lockout, delay or rate limiting (OWASP Top 10: identification and authentication failures).
- **Impact:** unlimited guessing is possible; if added later, existing tests may need to change.
- **Severity** Medium · **Urgency** P2 · **Confidence** Medium (may be acceptable for a demo application)
- **Recommendation:** decide explicitly: in scope with defined limits, or out of scope with the reason recorded.
- **Question:** Is brute-force protection in scope for this release?

#### OBS-001 · Scope of protected pages and authenticated access to /login
- R5 protects only `/bugs`. Future pages and the public status of `/health` are not covered. The behaviour of `/login` for an already logged-in user is not defined. Not blocking now; worth one sentence in the requirements. **Urgency** P3.

### 3. Proposed rules (for confirmation — not approved)

All items below are **[PROPOSED]**; they become requirements only after the owner confirms them.

- R1a: Username comparison is case-sensitive; leading and trailing spaces are not trimmed. *(alternative: case-insensitive and trimmed)*
- R4a: The server rejects an empty or whitespace-only username or password; the user stays on `/login` with a field-level message; no session is created.
- R6a: After logout, the previous session is invalid on the server: a request to a protected page with the old session cookie is redirected to `/login`.
- R7a: Passwords are stored with an adaptive, salted password-hashing function; two users with the same password have different stored values.
- R8: All pages except `/login` and `/health` require authentication.
- R9: A session expires after N minutes of inactivity *(value to be decided)*.

### 4. Clarification questions (priority order)

1. Which password-hashing scheme is acceptable, and must equal passwords produce different stored values? (DEF-001)
2. Is the username case-sensitive, and are spaces trimmed? (DEF-002)
3. Must the server reject empty or whitespace-only credentials, and with which response? (DEF-003)
4. Must an old session cookie be rejected after logout? (DEF-004)
5. Are field highlighting, Back-button behaviour after logout and responsive layout required? (DEF-005)
6. After login from a protected page, return to that page or always to /bugs? (DEF-006)
7. Do sessions expire, and after how long? (DEF-007)
8. Is brute-force protection in scope? (RISK-001)

### 5. Coverage and limitations

- **Applicable and checked:** Wiegers criteria (single and set), linguistic precision, negative paths, boundaries and validation, state (session lifecycle), testability and oracles, security quality attribute, traceability to TC-LOGIN-*.
- **Not applicable:** events/distributed behaviour, data migration, native mobile add-on.
- **Not assessable:** Correct and Feasible (no stakeholder or architecture input); Necessary (no business goal stated).
- **Not checked:** accessibility (no standard stated), performance of login (no requirement), API contract for `/api/bugs` (outside this section).
- **Limitation:** the requirements are a draft written alongside the test cases; findings refer to that draft only.

### 6. Resolution (2026-11-19)

Owner decisions on the questions in section 4. Approved requirements: `docs/requirements.md`.

| Finding | Decision | Result |
|---|---|---|
| DEF-001 | Adaptive, salted password hashing; equal passwords → different stored values | R7 rewritten; TC-LOGIN-009 updated |
| DEF-002 | Username case-sensitive, spaces not trimmed | R1, R3 updated; TC-LOGIN-006 has an expected result |
| DEF-003 | Server also rejects empty / whitespace-only input | R4.1 + R4.2; new TC-LOGIN-011 |
| DEF-004 | Old session cookie is rejected after logout | R6.1; new TC-LOGIN-012 |
| DEF-005 | Field marking, Back after logout, mobile layout become requirements | R4.1, R6.2, R9; traceability restored |
| DEF-006 | After login always go to `/bugs`; status codes still open | R2 updated; status codes → open item |
| DEF-007 | Session expires after 30 minutes of inactivity (configurable) | R8; new TC-LOGIN-013 |
| DEF-008 | Not decided | Open item |
| DEF-009 | Not decided | Open item |
| RISK-001 | Brute-force protection out of scope for the demo app | Recorded as out of scope; risk accepted |
| OBS-001 | All pages except `/login` and `/health` are protected | R5 rewritten |

**Status after resolution:** Requirements Readiness — Ready for R1–R9 except the open items;
Test Design Readiness — Ready; Automation Readiness — Ready (status-code checks deferred).

## Requirements review RR-002 — Bugs: list, create, close, JSON API

- **Date:** 2026-11-19
- **Source:** `docs/specs/bugs.md` (approved spec, commit c5397dc), sections 1–9. Context read: `docs/requirements.md` (R4.2, R5, R8 referenced by the spec), `app/schema.sql` (no bugs table yet), `docs/test-cases.md` (no bug cases yet)
- **Method:** wiegers-requirements-checker v3.5, **Standard Audit** (several roles, rules, a lifecycle and an API contract)
- **Intended use:** test design and automation readiness
- **Artifact type:** user requirements + business rules (permissions, validation, lifecycle) + interface contract (JSON API)

### 1. Executive verdict

**Overall: Needs Clarification.** Scope, permissions, fields, statuses, validation rules, timestamps and the main API status codes are clear and testable. Not yet decided: what a successful close returns and shows, what the bug page shows, the error bodies other than 400, which error wins when several apply, the API request contract, where limits are enforced and how characters are counted, the list order for equal timestamps, and the handling of non-numeric IDs.

| Gate | Status | Reason |
|---|---|---|
| Requirements Readiness | Needs Clarification | Close outcome, error precedence and request contract undefined (DEF-001, 004, 005) |
| Test Design Readiness | Needs Clarification | No oracle for successful close, bug page content and non-400 error bodies (DEF-001, 002, 003); boundary rules for limits incomplete (DEF-006, 007) |
| Automation Readiness | Needs Clarification | Seeded users, session login, local DB and stable pages are available; list order for bugs created in the same second is not deterministic (DEF-008) |

### 2. Defect and risk inventory

#### DEF-001 · The outcome of a successful close is not defined
- **Evidence [CONFIRMED]:** 8.6 defines only the rejected closes (403, 409); 7.3 says "Closing needs no confirmation" but not what follows. The spec lists this itself as open question 9.1.
- **Problem [MISSING]:** API status code and body for a successful close; in the UI, where the user lands and whether a message is shown.
- **Impact:** the main happy path of closing has no oracle in either layer; API clients and tests would guess.
- **Severity** High · **Urgency** P1 · **Confidence** High
- **Recommendation:** state the success response (status, body) and the UI result (page, message).
- **Question:** What does a successful close return in the API, and what does the user see in the UI?

#### DEF-002 · The content of the bug page is not defined
- **Evidence [CONFIRMED]:** 7.3 defines the Close button, errors and 404 for `/bugs/<id>`, but not which fields the page shows. 7.1 lists the list columns, including "author", without saying how the author is shown (open question 9.8).
- **Problem [MISSING]:** which fields `/bugs/<id>` shows (e.g. description, `closed_at`, `closed_by`), and whether author and closed by are shown as usernames in the UI.
- **Impact:** after create ("lands on the new bug's page") and after close, UI tests cannot check that the right data is shown; the key scenario "create in UI → API → DB" has no UI-side oracle beyond the message.
- **Severity** Medium · **Urgency** P1 · **Confidence** High
- **Recommendation:** list the fields shown on the bug page and their display form.
- **Question:** Which fields does the bug page show, and are author and closed by shown as usernames?

#### DEF-003 · Error bodies other than 400 are not defined
- **Evidence [CONFIRMED]:** 8.5 defines the 400 body `{"errors": {"<field>": "<message>"}}`; 8.2 says 401 comes "with a JSON error" without a format; 403, 404 and 409 have no body. Open question 9.2.
- **Problem [MISSING]:** the JSON format of 401, 403, 404 and 409. Also undefined: which key carries the error when a server-controlled field (e.g. `status`) is sent on create — the field name itself?
- **Impact:** API tests can check only status codes; clients cannot rely on a consistent error shape.
- **Severity** Medium · **Urgency** P1 · **Confidence** High
- **Recommendation:** define one error shape for non-validation errors and the key used for rejected server-controlled fields.
- **Question:** What JSON body do 401, 403, 404 and 409 return, and under which key is a rejected server-controlled field reported?

#### DEF-004 · Precedence between error conditions is not defined
- **Evidence [DERIVED]:** 8.2 (401), 8.6 (403, 409), 8.7 (404) and 8.5 (400) each define one condition, but several can apply to one request: an anonymous request for an unknown ID (401 or 404?); a user without permission closing an already closed bug (403 or 409?); a create request with both a validation error and a server-controlled field (one 400 with both errors, or only one?).
- **Problem [MISSING]:** no order of checks; the same request can legitimately get different answers.
- **Impact:** tests for these combinations have no expected result; a 404 before 401 or a 409 before 403 would also reveal information to users who should not get it.
- **Severity** Medium · **Urgency** P1 · **Confidence** High
- **Recommendation:** state the order in which conditions are checked (see proposed rule P-3).
- **Question:** In which order are authentication, bug existence, permission, state and validation checked?

#### DEF-005 · The API request contract for create is incomplete
- **Evidence [CONFIRMED]:** 8.5: "`POST /api/bugs` with `title`, `description` (optional) and `severity`". Open questions 9.3, 9.4, 9.5.
- **Problem [MISSING]:** the request format (JSON body only?) and the response to invalid JSON or another content type; whether unknown non-server fields (e.g. `"foo": 1`) are rejected or ignored; whether wrong types (`"title": 123`, `"severity": null`, `"description": ""`) are validation errors.
- **Impact:** negative API tests have no oracle; behaviour would be decided by the framework's defaults.
- **Severity** Medium · **Urgency** P1 · **Confidence** High
- **Recommendation:** state the accepted content type and the response to malformed bodies, unknown fields and wrong types.
- **Question:** Does `POST /api/bugs` accept only a JSON body, and are invalid JSON, unknown fields and wrong types each rejected with 400?

#### DEF-006 · It is not stated where the limits are enforced
- **Evidence [CONFIRMED]:** 5.1–5.3 define the rules; for login, R4.1 (UI) and R4.2 (server) were split explicitly. Open question 9.6.
- **Problem [ASSUMPTION]:** "rejected" can be read as server-side only or as UI and server. For the UI it is open whether the form prevents input over the limit (no request sent) or the server rejects it (message after submit).
- **Impact:** UI tests for 201 characters cannot be written: the expected result is either "cannot type the 201st character" or "a message for the field after submit".
- **Severity** Medium · **Urgency** P1 · **Confidence** High
- **Recommendation:** split each rule into a UI rule and a server rule, as R4.1/R4.2.
- **Question:** Does the create form itself enforce required fields and the 200/2000 limits, or only the server?

#### DEF-007 · How characters are counted for the limits is undefined
- **Evidence [CONFIRMED]:** 5.1 "At most 200 characters, counted after trimming"; 5.2 "at most 2000 characters". Open question 9.9.
- **Problem [MISSING]:** the unit of "character" for non-Latin text and emoji (e.g. one emoji: one character, or several code units); which whitespace counts for trimming (only spaces, or also tabs and newlines).
- **Impact:** boundary tests with non-Latin text, emoji or newlines have no expected result; the UI and the server may count differently.
- **Severity** Low · **Urgency** P2 · **Confidence** High
- **Recommendation:** define the counting unit and the whitespace set for trimming.
- **Question:** How is a "character" counted for the limits, and does trimming also remove tabs and newlines?

#### DEF-008 · "Newest first" has no rule for equal timestamps
- **Evidence [CONFIRMED]:** 7.1 and 8.4: "newest first"; section 6 shows timestamps to the minute (UI) and to the second (API).
- **Problem [MISSING]:** bugs created within the same second (or minute, if that is the stored precision) have no defined order; the stored precision of `created_at` is not stated.
- **Impact:** tests that create several bugs quickly and check the list order become flaky.
- **Severity** Medium · **Urgency** P1 · **Confidence** High
- **Recommendation:** define a tie-breaker and the stored precision (see proposed rule P-4).
- **Question:** How are bugs with the same `created_at` ordered, and to which precision is `created_at` stored?

#### DEF-009 · Non-numeric bug IDs are not covered
- **Evidence [CONFIRMED]:** 3: `id` is an "increasing integer"; 7.3 and 8.7 define 404 for an "unknown bug ID". Open question 9.7.
- **Problem [MISSING]:** the response to `/bugs/abc` or `/api/bugs/abc` (also `0`, negative numbers).
- **Impact:** small, but a framework default (e.g. an HTML 404 page from the API) would contradict the JSON-only API.
- **Severity** Low · **Urgency** P2 · **Confidence** High
- **Recommendation:** state that any ID that is not an existing bug gets 404 (JSON in the API).
- **Question:** Do non-numeric, zero and negative IDs get the same 404 as an unknown ID?

#### RISK-001 · User-supplied text and state-changing requests have no security rules
- **Evidence [MISSING]:** title and description are free text shown to every user (7.1, 7.3); create and close are POST requests authenticated by the session cookie (8.2). The spec says nothing about markup or script in text, or about cross-site requests (OWASP Top 10: injection, broken access control).
- **Impact:** stored script in a title would run for every user viewing the list; a forged cross-site request could create or close bugs as the logged-in user. The session cookie is SameSite=Lax (D-015), which blocks most cross-site POSTs, but this is not a stated requirement.
- **Severity** Medium · **Urgency** P2 · **Confidence** Medium (may be acceptable for a demo application)
- **Recommendation:** decide explicitly: e.g. text is stored as typed and always shown as plain text; cross-site request protection is in scope or out of scope with the reason recorded (as RISK-001 in RR-001).
- **Question:** Must markup in title and description be shown as plain text, and is protection against cross-site requests in scope?

#### OBS-001 · The spec settles RR-001 DEF-009 (Roles) for `/bugs`
Section 2 states that the role matters only for closing other users' bugs. The open item "Roles" in `docs/requirements.md` can be closed for `/bugs` when the requirements are written (step 4); login behaviour is unaffected.

#### OBS-002 · An unbounded list is an accepted scope decision
No paging (7.1, 8.4) means the list and `GET /api/bugs` grow with the data. This is a confirmed scope decision, not a defect; no performance requirement exists to test against.

### 3. Proposed rules (for confirmation — not approved)

All items below are **[PROPOSED]**; they become requirements only after the owner confirms them.

- P-1 (DEF-001): Successful close: API **200** with the updated bug; UI stays on `/bugs/<id>`, shows status `Closed`, `closed_at`, `closed_by` and a message. *(alternative: API 204 without body)*
- P-2 (DEF-003): Non-validation errors return `{"error": "<message>"}`; a rejected server-controlled field is reported under its own name in `errors`.
- P-3 (DEF-004): Checks in this order: authentication (401) → bug exists (404) → permission (403) → state (409); for create: one 400 listing all field errors, including rejected server-controlled fields.
- P-4 (DEF-008): `created_at` is stored to the second; bugs with equal `created_at` are ordered by `id`, highest first.
- P-5 (DEF-005): `POST /api/bugs` accepts only `application/json`; invalid JSON, another content type, unknown fields and wrong types are rejected with 400.
- P-6 (DEF-009): Any ID that is not an existing bug, including non-numeric, zero and negative, gets 404.

### 4. Clarification questions (priority order)

1. What does a successful close return in the API, and what does the user see in the UI? (DEF-001)
2. In which order are authentication, bug existence, permission, state and validation checked? (DEF-004)
3. What JSON body do 401, 403, 404 and 409 return, and under which key is a rejected server-controlled field reported? (DEF-003)
4. Does `POST /api/bugs` accept only a JSON body, and are invalid JSON, unknown fields and wrong types each rejected with 400? (DEF-005)
5. Which fields does the bug page show, and are author and closed by shown as usernames? (DEF-002)
6. Does the create form itself enforce required fields and the 200/2000 limits, or only the server? (DEF-006)
7. How are bugs with the same `created_at` ordered, and to which precision is `created_at` stored? (DEF-008)
8. Must markup in title and description be shown as plain text, and is protection against cross-site requests in scope? (RISK-001)
9. How is a "character" counted for the limits, and does trimming also remove tabs and newlines? (DEF-007)
10. Do non-numeric, zero and negative IDs get the same 404 as an unknown ID? (DEF-009)

### 5. Coverage and limitations

- **Applicable and checked:** Wiegers criteria (single and set), linguistic precision, negative paths, boundaries and validation, state and lifecycle (Open → Closed, repeated close), business rules (permissions), testability and oracles, API contract (methods, status codes, bodies, authentication), security quality attribute (input handling, access control), traceability to R4.2, R5, R8 and RR-001.
- **Not applicable:** events and distributed behaviour, data migration, native mobile add-on.
- **Not assessable:** Correct and Feasible (no other stakeholder or architecture input); Necessary (no business goal stated beyond the showcase).
- **Not checked:** accessibility (no standard stated), performance (no requirement; see OBS-002), mobile layout of the new pages (the spec states no mobile rule; R9 covers only the login page), concurrent closes by two users.
- **Limitation:** the spec was drafted from an interview by the reviewer's own agent session; the findings were checked against the spec text only, not against the interview transcript.

### 6. Resolution (2026-11-19)

Owner decisions on the questions in section 4 and on the coverage note about mobile layout.
Approved requirements: `docs/requirements.md` → "Bugs" (R10–R22).

| Finding | Decision | Result |
|---|---|---|
| DEF-001 | Successful close: API 200 with the updated bug. UI stays on the bug page with the message "Bug closed", status Closed, `closed_at` and `closed_by` shown, no Close button | R16, R21.4 |
| DEF-002 | The bug page shows all fields; author and closed by are usernames in the list and on the page; empty values are shown as "-" in the UI | R10, R14 |
| DEF-003 | P-2 accepted: non-validation errors return `{"error": "<message>"}`; a rejected server-controlled field is reported under its own name in `errors` | R22.1, R22.3 |
| DEF-004 | P-3 accepted: checks in the order 401 → 404 → 403 → 409; validation returns one 400 listing all field errors | R22.2, R22.3 |
| DEF-005 | JSON only: wrong `Content-Type` → 415; invalid JSON → 400; unknown fields → 400; wrong types → 400 | R22.3 |
| DEF-006 | Both the form and the server enforce required fields and the 200/2000 limits, split like R4.1 / R4.2 | R13.1, R13.2 |
| DEF-007 | A character is one Unicode code point (as Python counts it); trimming removes all leading and trailing whitespace, including tabs and newlines | R12 |
| DEF-008 | P-4 accepted: `created_at` stored to the second; ties ordered by `id`, highest first | R10, R18 |
| DEF-009 | Non-numeric, zero and negative IDs get the same 404 as an unknown ID | R14, R22.4 |
| RISK-001 | Markup in title and description is shown as plain text (in scope). CSRF protection is out of scope for this version; risk accepted, like brute-force protection in RR-001 | R19; CSRF protection listed as out of scope (accepted risk RR-002 RISK-001) |
| OBS-001 | Noted: the role matters only for closing other users' bugs | R15; open item "Roles" settled for `/bugs` |
| OBS-002 | Noted: no paging is a scope decision | Out of scope |
| Coverage note (mobile) | All bug pages must fit the devices in the device list without horizontal scrolling | R20 |

**Status after resolution:** all findings decided; none left open. Requirements Readiness — Ready;
Test Design Readiness — Ready; Automation Readiness — Ready (list order deterministic by R18;
seeded users, session login and local DB available). Not Assessed: accessibility and performance
(no requirement).
