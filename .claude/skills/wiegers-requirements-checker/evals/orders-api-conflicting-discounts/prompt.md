---
tags: [skill-creator]
max_turns: 20
timeout_seconds: 600
allowed_tools: [Read, Glob, Grep, Skill, Write, Edit, Bash]
---

Review this API spec for test readiness before we automate it:

POST /orders - creates an order. Returns 200 on success.
Body: product_id (required), quantity (integer), discount_percent.
BR-1: quantity must be positive.
BR-2: discount is up to 50%.
BR-3: VIP customers get a 60% discount on orders over 1000 PLN.
BR-4: if stock is insufficient, return an error.
