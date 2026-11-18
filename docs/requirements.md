# Requirements

Requirement IDs are stable: a changed requirement keeps its ID, a new one gets the next free number.
Each test case in `docs/test-cases.md` refers to the requirements it covers.
Review history: `docs/requirements-review.md`.

## Login and logout

Status: **Approved 2026-11-19** (after review RR-001; open items listed below).

### Test users
| Username | Password | Role |
|---|---|---|
| `admin` | `Admin#2026` | admin |
| `tester` | `Tester#2026` | user |

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
A session expires after 30 minutes of inactivity. The next request after expiry is treated as
anonymous (R5). The timeout is configurable so tests can use a short value.

**R9. Mobile layout of the login page.**
On every device in the project's device list, the login form is fully visible without horizontal
scrolling, and login works as in R1–R3.

### Out of scope (decided 2026-11-19)
- **Brute-force protection** (lockout, delay or rate limiting after failed attempts): deliberately out
  of scope for this demo application. Known risk RISK-001 in the review. Revisit before any real use.

### Open items (not decided yet)
- **Input limits** (RR-001 DEF-008): maximum length of username and password, and the response to
  over-limit or special input.
- **Roles** (RR-001 DEF-009): whether the role changes anything in login or on `/bugs`.
- **HTTP contract** (RR-001 DEF-006, partly): exact status codes for failed login and for redirects.
  Tests check the observable result (page and redirect target), not the status code, until decided.
