# Static Analysis and Behavior Findings

Line numbers below refer to the original `car_rental.py` baseline. Static-analysis findings are marked with their tool rule where applicable; behavioral bugs are listed separately because the tools do not necessarily detect them.

| Issue | Type | Line(s) | Description | Fix Approach |
|-------|------|---------|-------------|--------------|
| Permissive receipt permissions (Bandit B103) | High security | 67 | `chmod(..., 0o777)` makes receipt contents readable and writable by all users. | Keep the restrictive permissions of the securely created temporary file; do not broaden them. |
| Weak licence hash (Bandit B324) | High security | 48 | Unsalted SHA-1 is fast to guess and unsuitable for protecting licence data. | Store a salted scrypt verifier and verify it using its embedded salt and parameters. This is not encryption and low-entropy values can still be guessed. |
| SQL injection in customer registration (Bandit B608) | Medium security | 23 | Customer fields are interpolated into an SQL statement. | Bind each value using SQLite placeholders. |
| SQL injection in customer lookup (Bandit B608) | Medium security | 26 | The lookup name is concatenated into SQL and can change the query. | Use a parameterized exact-match query. |
| Executable promo rule (Bandit B102) | Medium security | 53 | `exec` evaluates staff-provided input as Python code. | Replace evaluation with a fixed allowlist of supported discounts and reject unknown rules. |
| Unsafe temporary filename (Bandit B306) | Medium security | 63 | `tempfile.mktemp()` chooses a name without creating the file, allowing a race to claim that path. | Create and open the file atomically with `NamedTemporaryFile`. |
| Car can be booked repeatedly | Behavioral correctness | 29–34 | Booking does not check or update availability, so the same car can be rented more than once. | Reject unavailable cars and mark a car unavailable only after a valid booking. |
| Reversed dates create a negative rental | Behavioral correctness | 31–34 | The date difference is used without checking whether the end precedes the start, producing negative duration and cost. | Parse dates and reject an end date earlier than the start date. |
| Negative daily rate accepted | Behavioral correctness | 89–91 | The demo includes a negative-rate car, producing a negative booking price. | Validate that car rates are nonnegative when adding cars. |
| Unknown return is silently ignored (Bandit B110 / Pylint W0702) | Reliability | 38–42 | A bare exception catches any error and returns `None`, hiding failed returns and programming mistakes. | Validate the car and active rental explicitly, raising a clear error for invalid returns. |
| Customer validation uses `assert` (Bandit B101) | Reliability/security | 30 | Assertions can be disabled by optimized Python execution, so they are not reliable input validation. | Raise an explicit validation error when the customer is not registered. |
| Predictable booking identifiers (Bandit B311) | Security | 45 | The standard pseudo-random generator can make booking codes predictable. | Generate codes with Python's cryptographically secure `secrets` module. |
| Hardcoded administrator credential (Bandit B105/B107) | Security | 70–73 | A source-embedded credential can be recovered by anyone with access to the code. | Read credentials from environment configuration, compare safely, and fail closed when unset. |
| Mutable default and inconsistent return (Pylint W0102/R1710) | Maintainability | 16–20 | The `features=[]` default is shared between calls, and `addCar` has inconsistent return paths. | Use `None` as the optional default, create a fresh list per car, and return a consistent result. |
| Naming, docs, imports, and formatting findings (Pylint/Flake8) | Style | Throughout | CamelCase names, missing docstrings, an unused import, long lines, and whitespace issues reduce readability and tooling quality. | Use documented snake_case functions, remove unused imports, and format consistently. |

## Licence handling note

The fixed program stores the salted scrypt verifier instead of the raw licence and does not return the verifier from customer lookup. Scrypt slows offline guessing but does not make predictable identifiers secret. If the application must recover the licence, use encryption with managed keys and strict access controls rather than a one-way hash. SHA-256 alone would still be a fast, unsalted hash and is not an adequate fix.
