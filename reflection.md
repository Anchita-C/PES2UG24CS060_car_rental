# Reflection

## 1. What types of errors and potential vulnerabilities were identified by the static analysis tools?

Bandit identified SQL queries built from user input, executable promo input, weak SHA-1 hashing, an unsafe temporary-file API, permissive file permissions, assertion-based validation, a bare exception, predictable pseudo-random booking codes, and hardcoded administrator credentials. Pylint and Flake8 also highlighted maintainability and style problems such as missing documentation, inconsistent naming, a mutable default argument, an unused import, long lines, and formatting issues. Some important behavior defects—especially duplicate bookings and reversed rental dates—required running the demo and reviewing the logic; static analysis did not identify every one.

## 2. How did fixing the identified issues improve the security, reliability, and maintainability of the Car Rental System?

Parameterized SQL prevents customer values from changing query structure. Promo rules are allowlisted instead of executed. Licence values are stored as salted scrypt verifiers rather than plaintext, and lookup does not expose those verifiers. Receipt files are created securely with restrictive permissions, administrator credentials are supplied outside the source, and booking codes use a secure random generator. Explicit validation prevents duplicate rentals, reversed dates, invalid rates, and silent return failures. Clear function names, documentation, formatting, and regression tests make future changes easier to review.

## 3. What are the advantages and limitations of static code analysis tools such as Pylint, Bandit, and Flake8?

These tools provide quick, repeatable feedback without needing every path in a program to run. Pylint checks a broad set of code-quality and logic patterns, Flake8 catches common Python style and lint issues, and Bandit focuses on potentially risky security patterns. Their warnings help prioritize review and make recurring conventions easier to enforce. However, they can produce false positives, cannot establish that the overall business behavior is correct, and do not prove that code is secure. Running the program, adding tests, and using human review are still necessary.

## 4. What challenges did you face while fixing the issues, and what did you learn from this exercise?

The main challenge was distinguishing tool findings from behavioral bugs that only became obvious when examining the demo output. Fixes also needed to preserve the intended behavior—for example, keeping the supported 10% promotion while removing `exec`, and creating receipts without broad permissions. Licence handling required care: replacing SHA-1 with a different fast hash would not protect a predictable identifier, so the implementation uses a salted, deliberately slow verifier and documents when encryption is needed instead. I learned to establish expected behavior first, fix the root cause, and use focused tests together with static-analysis tools rather than relying on a score alone.
