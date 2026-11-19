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
