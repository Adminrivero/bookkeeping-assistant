# End User Quickstart (Windows 10) — Bookkeeping Assistant

This guide is for running two tools:

1. **Rule Generator Wizard** (`rulegen.exe`) — helps you create classification rules.
2. **Bookkeeping Assistant** (`project.exe`) — processes your files and generates the final Excel output.

You do **not** need to install Python.

---

## 1) Folder setup (important)

1. Download the zip from the GitHub “Releases” page.
2. Unzip it somewhere easy, for example:
   - `Documents\BookkeepingAssistant\`

When you unzip, keep this folder structure together:

- `rulegen.exe`
- `project.exe`
- `config\` (contains `allocation_rules.json`, schemas, bank profiles)
- `data\`
- `output\`

Do not move the `.exe` files away from the `config\` folder.

---

## 2) Where your files go

### Input files
Place your bank/credit card statement files under:

- `data\2025\`

Your statement files can be **CSV** and/or **PDF**, depending on the bank profile.

If you have statements for specific banks, they may go under subfolders like:

- `data\2025\td\`
- `data\2025\triangle\`
- `data\2025\cibc\`

(Exact subfolders depend on how your statements are organized.)

### Output files
Excel output will be written under:

- `output\2025\`

---

## 3) Step A — Create your classification rules (Rule Generator Wizard)

### 3.1 Open a Command Prompt in the folder
1. Open the folder where you unzipped the tool (where `rulegen.exe` is).
2. Click the address bar in File Explorer, type `cmd`, press Enter.

A black command window should open in the correct folder.

### 3.2 Run the wizard (recommended)
In the Command Prompt, type:

- `rulegen.exe --hints`

This starts an interactive wizard that asks questions.

### 3.3 Wizard flow (what it will ask you)

#### 1) Category name
Example: `Office Supplies` or `Meals and Entertainment`

#### 2) Transaction type
Choose one of:
- `EXPENSE`
- `INCOME_TO_OFFSET_EXPENSE`
- `MANUAL_CR`
- `MANUAL_DR`
- `IGNORE_TRANSACTION`

If you’re not sure, most purchases are `EXPENSE`.

#### 3) Rule ID
It will suggest a default based on your category name (for example `office-supplies`).
You can usually accept the default.

#### 4) Scope
You can press Enter to accept the default scope, which typically covers:
- chequing/saving accounts
- credit cards

#### 5) Logic
Choose how conditions combine:
- `MUST_MATCH_ANY` = OR (any condition matches)
- `MUST_MATCH_ALL` = AND (every condition must match)

Most rules start with `MUST_MATCH_ANY`.

#### 6) Add conditions and/or groups
You will be asked repeatedly:

- “Add a condition, add a group, or finish? (condition/group/finish)”

A **condition** asks for:
- **Field name** (examples shown in hints):
  - `Description`, `Debit`, `Credit`, `Balance`, `Date`
- **Operator**:
  - `CONTAINS`, `STARTS_WITH`, `EQUALS`, `BETWEEN`, `LESS_THAN_OR_EQUAL_TO`
- **Value**
  - Example: if field is `Description` and operator is `CONTAINS`, value could be `AMAZON` or `STARBUCKS`

A **group** is a nested set of conditions with its own logic (ANY/ALL). Use groups if you need more complex “(A OR B) AND (C OR D)” style rules.

When done adding conditions/groups, type:
- `finish`

#### 7) Dual-entry bookkeeping (optional)
The wizard may ask:
- “Configure dual-entry bookkeeping? (y/n)”

If you’re not sure, you can answer `n` and proceed. (This can be configured later.)

#### 8) Validate rule against schema (recommended)
Answer `y` when prompted. It should say:
- “Schema validation: OK”

If it shows errors, read them carefully and adjust your choices.

#### 9) Dry-run evaluation (optional)
The wizard may ask:
- “Perform a dry-run evaluation? (y/n)”

You can usually answer `n` unless you have a prepared transactions JSON file for testing.

#### 10) Save the rule (recommended)
Answer `y` to save.

**Rules are saved to:**
- `config\allocation_rules.json`

Repeat the wizard to add additional rules.

---

## 4) Step B — Run the full assistant and generate Excel (project.exe)

After you’ve created your rules and placed your input statement files under `data\2025\`, run:

- `project.exe --year 2025 --bank td triangle cibc`

This runs the pipeline:
- reads your inputs
- applies your rules
- produces an Excel workbook in `output\2025\`

---

## 5) Common issues

### Windows protected your PC / SmartScreen
If Windows warns about an unknown publisher:
- Click “More info”
- Click “Run anyway”

### “The system cannot find the path specified” / rules not saving
Make sure you are running the `.exe` **from the unzipped folder** that still contains the `config\` directory.

### Nothing appears in output
Double-check:
- You used the right year (`--year 2025`)
- Your files are under `data\2025\`
- You ran the correct command: `project.exe --year 2025 --bank td triangle cibc`

---

## 6) Where to find full documentation
See the repository README and the Rule Generator doc under section **Documentation** for deeper explanations at [**BKA Full Documentation**](https://github.com/Adminrivero/bookkeeping-assistant/blob/main/README.md).