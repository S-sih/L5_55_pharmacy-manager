# Lab 5: Static Code Analysis Report

**Project:** L5_55_pharmacy-manager (`pharmacy_manager.py`)
**Tools:** Bandit 1.9.4, Pylint 4.1.3, Flake8 7.4.1

## 1. Before and after summary

| Tool | Before | After |
|---|---|---|
| Bandit | 8 issues (2 High, 2 Medium, 4 Low) | No issues identified |
| Pylint | 4.83 / 10 | 10.00 / 10 |
| Flake8 | 22 issues | 0 issues |

Reports are in the repo: `bandit_before.txt`, `pylint_before.txt`, `flake8_before.txt` and the matching `_after.txt` files. Line numbers below refer to the original file.

## 2. Issues found and fixed

### Bandit (security)

| Issue | ID | Severity | Line(s) | Description | Fix approach |
|---|---|---|---|---|---|
| Weak MD5 hash | B324 | High | 51 | `hashlib.md5` is cryptographically weak and was used to build patient IDs | Replaced with `hashlib.sha256` |
| Shell command | B605 | High | 68 | `os.system("echo ..." + name)` allows shell injection | Replaced with `print()`, same output, no shell |
| Use of `eval` | B307 | Medium | 48 | `eval(formula)` can run arbitrary code from the doctor's note | Wrote a safe `ast`-based evaluator that only allows numbers and `+ - * /` |
| Pickle load | B301 | Medium | 64 | `pickle.load` can execute code when loading untrusted data | Switched storage to `json` |
| Pickle import | B403 | Low | 3 | Import of the unsafe `pickle` module | Removed, now using `json` |
| Hardcoded password | B105 | Low | 11 | `DB_PASSWORD = "pharma@123"` is stored in source code | Read from the `PHARMACY_DB_PASSWORD` environment variable and compared with `hmac.compare_digest` |
| Try/except/pass | B110 | Low | 27-28 | Silent `except: pass` hides every error | Handle the missing medicine explicitly and log a warning |
| Weak random | B311 | Low | 54 | `random.randint` is predictable for Rx numbers | Replaced with `secrets.randbelow` |

### Pylint (code quality)

| Issue | ID | Type | Line(s) | Description | Fix approach |
|---|---|---|---|---|---|
| Mutable default argument | W0102 | Bug | 13 | `audit=[]` is shared between calls | Default `None`, create a new list inside the function |
| Bare except | W0702 | Bug | 27 | Catches all errors without a type | No bare except, medicine lookup uses `.get()` |
| Use of eval | W0123 | Security | 48 | `eval-used` | Safe evaluator (see B307) |
| Inconsistent returns | R1710 | Bug | 13 | `add_medicine` returned `None` or a list | Always return the audit list |
| Files not closed safely | R1732 | Resource | 57, 62 | `open()` without `with` | Used `with open(..., encoding="utf-8")` |
| Global statement | W0603 | Design | 63 | `global medicines` in `loadStock` | Mutate the dict with `clear()` and `update()` |
| camelCase names | C0103 | Style | 13-84 (13 functions) | e.g. `addMedicine`, `getQuantity` | Renamed to snake_case |
| Missing docstrings | C0114, C0116 | Style | 1, 13-89 | No module or function docstrings | Added docstrings |
| Needless else / simplifiable if | R1705, R1703 | Style | 35, 79 | `if ...: return True else: return False` | Return the condition directly |
| Old string formatting | C0209 | Style | 19 | `%` formatting | f-string |
| Unused imports | W0611 | Cleanup | 2, 6 | `sys` and `logging` never used | Removed `sys`, started using `logging` |
| Line too long | C0301 | Style | 87 | 111 characters | Wrapped the line |

### Flake8 (formatting)

| Issue | ID | Line(s) | Description | Fix approach |
|---|---|---|---|---|
| Unused imports | F401 | 2, 6 | `sys` and `logging` imported but unused | Removed or used |
| Blank lines before functions | E302 | 13, 22, 30, 33, 40, 46, 50, 53, 56, 61, 67, 70, 78, 84, 89 | Expected 2 blank lines, found 1 | Two blank lines before every function |
| Line too long | E501 | 19, 87, 98 | Lines over 79 characters | Wrapped long lines |
| Bare except | E722 | 27 | `except:` without a type | Removed |
| Blank lines after function | E305 | 108 | Expected 2 blank lines after function | Added, and used `if __name__ == "__main__"` |

### Logic bugs found while fixing

The original program output showed some bugs that the tools do not detect:

- **Negative stock:** `Cetirizine 10mg -> -10 units`. Negative quantities are now rejected.
- **Invalid medicine name:** `404` (a number) was accepted as a medicine name. Non-string names are now rejected.
- **Over-dispensing:** Stock could go below zero when dispensing more than available. It is now rejected with a warning.

## 3. Commits

1. Baseline reports (before)
2. Fix Bandit security issues
3. Fix Pylint issues, score above 9.5
4. Fix Flake8 style issues
5. After reports and this report

## 4. Reflection

**Which issues were the easiest and which were the hardest to fix?**

Flake8 issues were the easiest because most were formatting (blank lines, line length) and could be fixed mechanically. Pylint naming and docstring issues were also simple but affected many functions. The hardest were the Bandit findings, because they needed a different design: replacing `eval` with a safe expression evaluator, replacing `pickle` with JSON, and moving the password out of the source code into an environment variable.

**Did the tools report any false positives?**

Mostly no. The hardcoded password warning (B105) is Low severity and could be seen as noise in a demo program, but it points at a real bad practice. Pylint's `eval-used` and Bandit's `B307` reported the same line, which is a duplicate, not a false positive. The tools also did not catch some real logic bugs, such as negative stock, which I found by reading the program output.

**How could static analysis be integrated into a real workflow?**

It can run automatically on every commit or pull request, for example with pre-commit hooks or a GitHub Actions job that runs Bandit, Pylint and Flake8 and fails the build if the Bandit report has issues or the Pylint score drops below a threshold. Developers can also run the tools in their editor, so problems are fixed while the code is written.

**What tangible improvements did we see in the code?**

Security improved the most: the code no longer runs arbitrary strings, unpickles files, spawns a shell, uses MD5 or has a hardcoded password. Readability and maintainability improved too: the Pylint score went from 4.83 to 10.00, names follow one style, and every function has a docstring. Flake8 now reports nothing, so the formatting is consistent, and fixing the bare `except` and mutable default removed real sources of hidden bugs.
