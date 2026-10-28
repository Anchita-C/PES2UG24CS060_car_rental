# Lab 5: Static Code Analysis — Car Rental System

**Your file:** `car_rental.py`
**Python:** 3.10 or newer

This lab uses Pylint, Bandit, and Flake8 to analyze a small car-rental demo. The original implementation is an issue-rich baseline: tool findings should be considered alongside behavioral problems that static analysis may not identify.

## Correctness checklist

- Customer registration uses parameterized SQL; lookup returns only exact matches.
- A booking requires a registered customer, a known and available car, and valid rental dates.
- A successful booking marks the car unavailable until it is returned.
- Rental end dates cannot precede start dates. Rates, durations, and costs cannot be negative.
- Returning an unknown or inactive car reports an error. A valid return makes the car available and charges only for distance beyond the included allowance.
- Promotional discounts use supported rules only and cannot execute arbitrary input.
- Number plates match the expected format.
- Licence values are not stored or returned in plaintext. A salted, slow verifier is used for verification.
- Administrator credentials are configured outside the source code; missing configuration fails closed.
- Receipts contain the booking details and are created with restrictive permissions.

### Licence-data limitation

The demo stores a salted scrypt verifier, not the original licence number. A slow salted hash is appropriate when the application only needs to verify a supplied value, but it does not make low-entropy identifiers impossible to guess. If the business must retrieve the original number, use encryption with properly managed keys, minimize retention, and restrict access. Replacing SHA-1 with SHA-256 alone is not sufficient protection.

## What to do

1. **Run the demo and read the output carefully:**
   ```bash
   python car_rental.py
   ```
   The demo does not ask for input. Notice which invalid operations are rejected and whether the resulting state is sensible.

2. **Install the analysis tools:**
   ```bash
   python -m pip install pylint bandit flake8
   ```

3. **Preserve baseline and final reports separately.** Run the original tools before editing and save those outputs under `reports/before/`; save the final outputs under `reports/after/`. For example:
   ```bash
   python -m pylint car_rental.py > reports/before/pylint_report.txt
   python -m bandit -r car_rental.py > reports/before/bandit_report.txt
   python -m flake8 car_rental.py > reports/before/flake8_report.txt
   ```
   Use `python -m` so the tools run through the selected interpreter. The tools may exit nonzero when they report findings; that is expected. In Windows PowerShell 5.1, redirecting with `>` can save UTF-16; use `Out-File -Encoding utf8` if needed.

4. **Document findings** in `issues.md`. Include at least four rows, with high- and medium-severity issues first, using the requested columns: Issue, Type, Line(s), Description, and Fix Approach.

5. **Fix and verify issues.** Keep changes reviewable, rerun the analysis tools, and confirm the application still works:
   ```bash
   python -m unittest
   ```
   Aim for a Pylint score above 9.5.

6. **Reflect** in `reflection.md` by answering the four questions below.

## Reflection questions

1. What types of errors and potential vulnerabilities were identified by the static analysis tools?
2. How did fixing the identified issues improve the security, reliability, and maintainability of the Car Rental System?
3. What are the advantages and limitations of static code analysis tools such as Pylint, Bandit, and Flake8?
4. What challenges did you face while fixing the issues, and what did you learn from this exercise?

## Deliverables

- `car_rental.py`: cleaned implementation.
- `issues.md`: completed issue table.
- `reflection.md`: answers to all four questions.
- `reports/before/` and `reports/after/`: original and final static-analysis reports.

Be ready to explain the bugs you found and how you fixed them.
