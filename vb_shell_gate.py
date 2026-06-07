#!/usr/bin/env python3
"""
VB Shell Gate CLI - Code Governance System

VBSTYLE Architecture:
- Authority: Cascade (VBShellGate)
- Return: Tuple3 (status, payload, error)
- Orchestration: none
- Model: one_class_one_domain_one_authority_complete

Features:
- Validates C code against VB-style contract patterns
- Automatic code repair with templates
- Artifact history tracking
- SQLite persistence
- CLI + programmatic interface
"""

import sys
import re
import sqlite3
from datetime import datetime
from typing import Tuple, List, Optional
import os


# ─────────────────────────────────────────────────────────────────────────────
# VBSTYLE Utility Functions
# ─────────────────────────────────────────────────────────────────────────────

def _ok(payload) -> Tuple[int, any, any]:
    """Success response: (1, payload, None)"""
    return (1, payload, None)


def _err(code: str, msg: str, meta=None) -> Tuple[int, any, any]:
    """Error response: (0, None, (code, msg, meta))"""
    return (0, None, (code, msg, meta))


def _safe(func, *args, **kwargs) -> Tuple[int, any, any]:
    """Safely execute function with exception handling"""
    try:
        return func(*args, **kwargs)
    except Exception as e:
        return _err("INTERNAL", str(e), None)


# ─────────────────────────────────────────────────────────────────────────────
# VB Validator - Contract Validation Engine
# ─────────────────────────────────────────────────────────────────────────────

class VBValidator:
    """Validates C code against VB_ClassShell contract."""

    REQUIRED_SYMBOLS = [
        "VB_ClassState",
        "VB_Parameters",
        "VB_Results",
        "VB_MethodTable",
        "VB_ClassShell",
        "VB_bind_shell",
        "VB_execute",
        "VB_set_error",
        "VB_validate",
        "VB_log"
    ]

    REQUIRED_PATTERNS = {
        "ghost_header": r"/\*\s*Ghost\{",
        "classinfo": r"/\*\s*CLASSINFO",
        "domain": r"DOMAIN:\s*\w+",
        "purpose": r"PURPOSE:",
        "structs": r"STRUCTS:",
        "functions": r"FUNCTIONS:",
        "includes": r"INCLUDES:",
    }

    METHOD_SIGNATURES = {
        "VB_bind_shell": r"int\s+VB_bind_shell\(VB_ClassShell\s+\*shell\)",
        "VB_execute": r"int\s+VB_execute\(VB_ClassState\s+\*self,\s*const\s+VB_Parameters\s+\*params_in,\s*VB_Results\s+\*results_out\)",
        "VB_set_error": r"int\s+VB_set_error\(VB_ClassState\s+\*self,\s+int\s+code,\s*const\s+char\s+\*message\)",
        "VB_validate": r"int\s+VB_validate\(VB_ClassState\s+\*self\)",
        "VB_log": r"int\s+VB_log\(VB_ClassState\s+\*self,\s*const\s+char\s+\*message\)",
    }

    def validate(self, code: str) -> Tuple[bool, List[str]]:
        """Validate code against VB shell contract."""
        violations = []

        # Check required symbols
        for symbol in self.REQUIRED_SYMBOLS:
            if symbol not in code:
                violations.append(f"missing_symbol: {symbol}")

        # Check required patterns
        for pattern_name, pattern in self.REQUIRED_PATTERNS.items():
            if not re.search(pattern, code, re.IGNORECASE):
                violations.append(f"missing_pattern: {pattern_name}")

        # Check method signatures
        for method, signature in self.METHOD_SIGNATURES.items():
            if not re.search(signature, code):
                violations.append(f"signature_mismatch: {method}")

        # Check for disallowed print statements
        lines = code.split('\n')
        for i, line in enumerate(lines):
            if re.search(r"printf\s*\(", line) and not line.strip().startswith('#include'):
                if not re.search(r"snprintf", line):
                    violations.append(f"print_statement: printf detected at line {i+1}")

        # Check for extra functions outside shell
        all_functions = re.findall(r"int\s+(\w+)\s*\(", code)
        extra_functions = [f for f in all_functions if f not in self.REQUIRED_SYMBOLS]
        for func in extra_functions:
            violations.append(f"extra_function: {func}")

        return len(violations) == 0, violations


# ─────────────────────────────────────────────────────────────────────────────
# VB Shell Gate - Main Orchestrator
# ─────────────────────────────────────────────────────────────────────────────

class VBShellGate:
    """
    Code governance system for VB-style C code.
    
    Validates code against contracts, repairs violations, tracks history.
    """

    REPAIR_TEMPLATES = {
        "VB_ClassState": """typedef struct VB_ClassState {
    int initialized;
    int error_code;
    char error_message[256];
    void *user_data;
} VB_ClassState;""",

        "VB_Parameters": """typedef struct VB_Parameters {
    void *input_data;
    size_t input_size;
    int operation_mode;
} VB_Parameters;""",

        "VB_Results": """typedef struct VB_Results {
    void *output_data;
    size_t output_size;
    int status_code;
} VB_Results;""",

        "VB_MethodTable": """typedef struct VB_MethodTable {
    int (*execute)(VB_ClassState*, const VB_Parameters*, VB_Results*);
    int (*set_error)(VB_ClassState*, int, const char*);
    int (*validate)(VB_ClassState*);
    int (*log)(VB_ClassState*, const char*);
} VB_MethodTable;""",

        "VB_ClassShell": """typedef struct VB_ClassShell {
    VB_ClassState state;
    VB_MethodTable methods;
} VB_ClassShell;""",
    }

    def __init__(self, mem=None, db=None, param=None):
        """Initialize VB Shell Gate."""
        self.param = param or {}
        self.db_path = self.param.get("db_path", 
                      os.environ.get("VB_SHELL_DB", "vb_shell.db"))
        self.validator = VBValidator()
        
        self.state = {
            "config": {
                "db_path": self.db_path,
                "required_symbols": self.validator.REQUIRED_SYMBOLS,
                "repair_templates": list(self.REPAIR_TEMPLATES.keys()),
            },
            "catalog": [],
            "results": []
        }

    def Run(self, command: str, params: dict) -> Tuple[int, any, any]:
        """Execute command via VBSTYLE interface."""
        commands = {
            "init_db": lambda: self.init_db(params),
            "validate_file": lambda: self.validate_file(params),
            "validate_code": lambda: self.validate_code(params),
            "store_class": lambda: self.store_class(params),
            "store_code_artifact": lambda: self.store_code_artifact(params),
            "get_class_history": lambda: self.get_class_history(params),
            "get_rejected_artifacts": lambda: self.get_rejected_artifacts(params),
            "repair_artifact": lambda: self.repair_artifact(params),
            "repair_all": lambda: self.repair_all(params),
            "read_state": lambda: self.read_state(params),
            "set_config": lambda: self.set_config(params),
        }

        if command not in commands:
            return _err("UNKNOWN_CMD", f"Unknown command: {command}", None)

        return _safe(commands[command])

    # ─────────────────────────────────────────────────────────────────────────
    # Database Operations
    # ─────────────────────────────────────────────────────────────────────────

    def init_db(self, params: dict) -> Tuple[int, any, any]:
        """Initialize SQLite database with required tables."""
        try:
            conn = sqlite3.connect(self.db_path)
            cur = conn.cursor()
            cur.execute("PRAGMA foreign_keys = ON")

            cur.execute("""
                CREATE TABLE IF NOT EXISTS classes (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    name TEXT UNIQUE,
                    status TEXT,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)

            cur.execute("""
                CREATE TABLE IF NOT EXISTS code_artifacts (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    class_id INTEGER,
                    code TEXT,
                    is_valid INTEGER,
                    error_report TEXT,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY(class_id) REFERENCES classes(id)
                )
            """)

            conn.commit()
            return _ok({"initialized": True})
        except sqlite3.Error as e:
            return _err("DB_INIT_ERROR", str(e), None)
        finally:
            conn.close()

    def store_class(self, params: dict) -> Tuple[int, any, any]:
        """Store or update class in database."""
        name = params.get("name")
        status = params.get("status", "pending")

        try:
            conn = sqlite3.connect(self.db_path)
            cur = conn.cursor()

            cur.execute("SELECT id FROM classes WHERE name = ?", (name,))
            existing = cur.fetchone()

            if existing:
                class_id = existing[0]
                cur.execute("UPDATE classes SET status = ? WHERE id = ?", 
                           (status, class_id))
            else:
                cur.execute("INSERT INTO classes(name, status) VALUES (?, ?)", 
                           (name, status))
                class_id = cur.lastrowid

            conn.commit()
            return _ok({"class_id": class_id, "name": name})
        except sqlite3.Error as e:
            return _err("STORE_CLASS_ERROR", str(e), None)
        finally:
            conn.close()

    def store_code_artifact(self, params: dict) -> Tuple[int, any, any]:
        """Store code artifact in database."""
        class_id = params.get("class_id")
        code = params.get("code")
        is_valid = params.get("is_valid", 0)
        error_report = params.get("error_report")

        try:
            conn = sqlite3.connect(self.db_path)
            cur = conn.cursor()

            cur.execute("""
                INSERT INTO code_artifacts(class_id, code, is_valid, error_report)
                VALUES (?, ?, ?, ?)
            """, (class_id, code, is_valid, error_report))

            conn.commit()
            return _ok({"artifact_id": cur.lastrowid})
        except sqlite3.Error as e:
            return _err("STORE_ARTIFACT_ERROR", str(e), None)
        finally:
            conn.close()

    def get_class_history(self, params: dict) -> Tuple[int, any, any]:
        """Get validation history for a class."""
        class_name = params.get("class_name")

        try:
            conn = sqlite3.connect(self.db_path)
            cur = conn.cursor()

            cur.execute("""
                SELECT ca.id, ca.is_valid, ca.error_report, ca.created_at
                FROM code_artifacts ca
                JOIN classes c ON ca.class_id = c.id
                WHERE c.name = ?
                ORDER BY ca.created_at DESC
            """, (class_name,))

            history = cur.fetchall()
            return _ok({"class_name": class_name, "history": history})
        except sqlite3.Error as e:
            return _err("GET_HISTORY_ERROR", str(e), None)
        finally:
            conn.close()

    def get_rejected_artifacts(self, params: dict) -> Tuple[int, any, any]:
        """Get all rejected code artifacts."""
        try:
            conn = sqlite3.connect(self.db_path)
            cur = conn.cursor()

            cur.execute("""
                SELECT ca.id, ca.class_id, c.name, ca.code, ca.error_report
                FROM code_artifacts ca
                JOIN classes c ON ca.class_id = c.id
                WHERE ca.is_valid = 0
                ORDER BY ca.created_at DESC
            """)

            artifacts = cur.fetchall()
            return _ok({"count": len(artifacts), "artifacts": artifacts})
        except sqlite3.Error as e:
            return _err("GET_REJECTED_ERROR", str(e), None)
        finally:
            conn.close()

    # ─────────────────────────────────────────────────────────────────────────
    # Validation Operations
    # ─────────────────────────────────────────────────────────────────────────

    def validate_file(self, params: dict) -> Tuple[int, any, any]:
        """Validate C file and store in database."""
        filepath = params.get("filepath")

        try:
            with open(filepath, 'r') as f:
                code = f.read()
        except FileNotFoundError:
            return _err("FILE_NOT_FOUND", f"File not found: {filepath}", None)

        valid, violations = self.validator.validate(code)
        class_name = filepath.split('/')[-1].replace('.c', '')

        # Store class
        ok, class_data, err = self.store_class({
            "name": class_name,
            "status": "approved" if valid else "rejected"
        })
        if ok == 0:
            return (0, None, err)

        class_id = class_data["class_id"]

        # Store artifact
        error_report = "\n".join(violations) if violations else None
        self.store_code_artifact({
            "class_id": class_id,
            "code": code,
            "is_valid": 1 if valid else 0,
            "error_report": error_report
        })

        return _ok({
            "filepath": filepath,
            "valid": valid,
            "violations": violations,
            "class_id": class_id
        })

    def validate_code(self, params: dict) -> Tuple[int, any, any]:
        """Validate code string."""
        code = params.get("code", "")

        valid, violations = self.validator.validate(code)
        return _ok({
            "valid": valid,
            "violations": violations,
            "violation_count": len(violations)
        })

    # ─────────────────────────────────────────────────────────────────────────
    # Repair Operations
    # ─────────────────────────────────────────────────────────────────────────

    def _repair_code(self, code: str, violations: List[str]) -> str:
        """Repair code by injecting missing symbols."""
        repaired = code
        missing_symbols = []

        for violation in violations:
            if violation.startswith("missing_symbol:"):
                symbol = violation.replace("missing_symbol: ", "").strip()
                if symbol in self.REPAIR_TEMPLATES:
                    missing_symbols.append(symbol)

        for symbol in missing_symbols:
            if symbol not in repaired:
                template = self.REPAIR_TEMPLATES[symbol]
                
                # Find insertion point after last #include
                lines = repaired.split('\n')
                insert_idx = 0
                for i, line in enumerate(lines):
                    if line.strip().startswith('#include'):
                        insert_idx = i + 1

                lines.insert(insert_idx, f"\n/* Auto-repaired: {symbol} */")
                lines.insert(insert_idx + 1, template)
                lines.insert(insert_idx + 2, "")
                repaired = '\n'.join(lines)

        return repaired

    def repair_artifact(self, params: dict) -> Tuple[int, any, any]:
        """Repair a specific rejected artifact."""
        artifact_id = params.get("artifact_id")

        try:
            conn = sqlite3.connect(self.db_path)
            cur = conn.cursor()

            cur.execute("""
                SELECT class_id, code, error_report
                FROM code_artifacts
                WHERE id = ?
            """, (artifact_id,))

            row = cur.fetchone()
            if not row:
                return _err("ARTIFACT_NOT_FOUND", 
                           f"Artifact {artifact_id} not found", None)

            class_id, code, error_report = row
            violations = error_report.split('\n') if error_report else []

            # Repair code
            repaired_code = self._repair_code(code, violations)

            # Re-validate
            valid, new_violations = self.validator.validate(repaired_code)

            # Store repaired artifact
            new_error_report = "\n".join(new_violations) if new_violations else None
            self.store_code_artifact({
                "class_id": class_id,
                "code": repaired_code,
                "is_valid": 1 if valid else 0,
                "error_report": new_error_report
            })

            # Update class status if valid
            if valid:
                cur.execute(
                    "UPDATE classes SET status = 'approved' WHERE id = ?",
                    (class_id,)
                )
                conn.commit()

            return _ok({
                "artifact_id": artifact_id,
                "repaired": valid,
                "violations": new_violations,
                "violation_count": len(new_violations)
            })
        except sqlite3.Error as e:
            return _err("REPAIR_ERROR", str(e), None)
        finally:
            conn.close()

    def repair_all(self, params: dict) -> Tuple[int, any, any]:
        """Repair all rejected artifacts."""
        ok, data, err = self.get_rejected_artifacts({})

        if ok == 0:
            return (0, None, err)

        artifacts = data["artifacts"]

        if not artifacts:
            return _ok({"message": "No rejected artifacts to repair", "count": 0})

        results = []
        for artifact_id, class_id, class_name, code, error_report in artifacts:
            ok, repair_data, _ = self.repair_artifact({"artifact_id": artifact_id})
            results.append({
                "artifact_id": artifact_id,
                "class_name": class_name,
                "repaired": repair_data.get("repaired", False) if ok else False,
                "violations": repair_data.get("violations", []) if ok else []
            })

        return _ok({
            "total": len(artifacts),
            "results": results
        })

    # ─────────────────────────────────────────────────────────────────────────
    # State Management
    # ─────────────────────────────────────────────────────────────────────────

    def read_state(self, params: dict) -> Tuple[int, any, any]:
        """Read current state."""
        return _ok(self.state["config"].copy())

    def set_config(self, params: dict) -> Tuple[int, any, any]:
        """Update configuration."""
        for key, value in params.items():
            self.state["config"][key] = value
        return _ok(self.state["config"].copy())


# ─────────────────────────────────────────────────────────────────────────────
# CLI Interface
# ─────────────────────────────────────────────────────────────────────────────

class VBShellGateCLI:
    """Interactive CLI for VB Shell Gate."""

    def __init__(self, gate: VBShellGate):
        self.gate = gate

    def print_banner(self):
        """Print CLI banner."""
        print("=" * 60)
        print("VB SHELL GATE - Code Governance CLI")
        print("=" * 60)
        print()

    def print_help(self):
        """Print help information."""
        print("Commands:")
        print("  validate <file>     - Validate C file")
        print("  check <code>        - Validate code string")
        print("  history <name>      - Show class validation history")
        print("  repair <id>         - Repair specific artifact")
        print("  repair_all          - Repair all rejected artifacts")
        print("  template            - Show VB shell template")
        print("  symbols             - List required symbols")
        print("  help                - Show this help")
        print("  exit                - Exit CLI")
        print()

    def show_template(self):
        """Show VB shell template."""
        print("VB SHELL TEMPLATE:")
        print("-" * 60)
        print("/* Ghost{[ClassName][active][DATE][VERSION][AUTHOR]} */")
        print("/* CLASSINFO")
        print(" * DOMAIN: DOMAIN_NAME")
        print(" * PURPOSE: class_purpose")
        print(" * STRUCTS: VB_ClassState, VB_Parameters, VB_Results")
        print(" * FUNCTIONS: VB_bind_shell, VB_execute, VB_set_error")
        print(" * INCLUDES: stdio.h, stdlib.h, string.h")
        print(" */")
        print()

    def list_symbols(self):
        """List required symbols."""
        print("REQUIRED SYMBOLS:")
        print("-" * 60)
        for symbol in VBValidator.REQUIRED_SYMBOLS:
            print(f"  {symbol}")
        print()

    def validate_file(self, filepath: str):
        """Validate C file."""
        ok, data, err = self.gate.Run("validate_file", {"filepath": filepath})

        if ok == 0:
            print(f"✖ ERROR: {err[1]}")
            return

        valid = data["valid"]
        violations = data["violations"]

        if valid:
            print(f"✔ ACCEPTED: {filepath}")
            print("Code complies with VB shell contract")
        else:
            print(f"✖ REJECTED: {filepath}")
            print("Violations:")
            for v in violations:
                print(f"  - {v}")
        print()

    def validate_code(self, code: str):
        """Validate code string."""
        ok, data, err = self.gate.Run("validate_code", {"code": code})

        if ok == 0:
            print(f"✖ ERROR: {err[1]}")
            return

        valid = data["valid"]
        violations = data["violations"]

        if valid:
            print("✔ ACCEPTED")
            print("Code complies with VB shell contract")
        else:
            print("✖ REJECTED")
            print(f"Found {len(violations)} violations:")
            for v in violations:
                print(f"  - {v}")
        print()

    def show_history(self, class_name: str):
        """Show validation history."""
        ok, data, err = self.gate.Run("get_class_history", 
                                     {"class_name": class_name})

        if ok == 0:
            print(f"✖ ERROR: {err[1]}")
            return

        history = data["history"]

        if not history:
            print(f"No history for class: {class_name}")
            print()
            return

        print(f"VALIDATION HISTORY: {class_name}")
        print("-" * 60)
        for row in history:
            artifact_id, is_valid, error_report, created_at = row
            status = "✔ VALID" if is_valid else "✖ INVALID"
            print(f"Artifact {artifact_id}: {status} at {created_at}")
            if error_report:
                print(f"  Errors: {error_report[:80]}...")
        print()

    def repair_artifact(self, artifact_id: int):
        """Repair specific artifact."""
        ok, data, err = self.gate.Run("repair_artifact", 
                                     {"artifact_id": artifact_id})

        if ok == 0:
            print(f"✖ ERROR: {err[1]}")
            return

        repaired = data["repaired"]
        violations = data["violations"]

        if repaired:
            print(f"✔ REPAIRED: Artifact {artifact_id}")
            print("Code now complies with VB shell contract")
        else:
            print(f"✖ REPAIR FAILED: Artifact {artifact_id}")
            print(f"Remaining violations ({len(violations)}):")
            for v in violations:
                print(f"  - {v}")
        print()

    def repair_all(self):
        """Repair all rejected artifacts."""
        ok, data, err = self.gate.Run("repair_all", {})

        if ok == 0:
            print(f"✖ ERROR: {err[1]}")
            return

        message = data.get("message")
        if message:
            print(message)
            return

        results = data["results"]
        print(f"Repairing {len(results)} rejected artifacts...")
        print()

        for result in results:
            status = "✔" if result["repaired"] else "✖"
            print(f"{status} Artifact {result['artifact_id']} "
                  f"({result['class_name']})")

        print()

    def run(self):
        """Run interactive CLI loop."""
        self.gate.Run("init_db", {})
        self.print_banner()
        self.print_help()

        while True:
            try:
                cmd = input("vb> ").strip()
            except (EOFError, KeyboardInterrupt):
                break

            if not cmd:
                continue

            if cmd in ("exit", "quit"):
                print("Exiting VB Shell Gate")
                break

            if cmd == "help":
                self.print_help()
            elif cmd == "template":
                self.show_template()
            elif cmd == "symbols":
                self.list_symbols()
            elif cmd == "repair_all":
                self.repair_all()
            elif cmd.startswith("validate "):
                filepath = cmd[9:].strip()
                self.validate_file(filepath)
            elif cmd.startswith("check "):
                code = cmd[6:].strip()
                self.validate_code(code)
            elif cmd.startswith("history "):
                class_name = cmd[8:].strip()
                self.show_history(class_name)
            elif cmd.startswith("repair "):
                try:
                    artifact_id = int(cmd[7:].strip())
                    self.repair_artifact(artifact_id)
                except ValueError:
                    print("Invalid artifact ID. Must be an integer.")
            else:
                print(f"Unknown command: {cmd}")
                print("Type 'help' for available commands")
            print()


# ─────────────────────────────────────────────────────────────────────────────
# Main Entry Point
# ─────────────────────────────────────────────────────────────────────────────

def main():
    """Main entry point."""
    gate = VBShellGate(param={
        "db_path": os.environ.get("VB_SHELL_DB", "vb_shell.db")
    })

    # Initialize database
    gate.Run("init_db", {})

    if len(sys.argv) > 1:
        # Command-line mode
        cmd = sys.argv[1]
        
        if cmd == "validate" and len(sys.argv) > 2:
            ok, data, err = gate.Run("validate_file", {"filepath": sys.argv[2]})
            if ok:
                print("VALID" if data["valid"] else "INVALID")
            else:
                print(f"ERROR: {err[1]}")
        
        elif cmd == "repair_all":
            ok, data, err = gate.Run("repair_all", {})
            if ok:
                print(f"Repaired {len(data.get('results', []))} artifacts")
            else:
                print(f"ERROR: {err[1]}")
        
        else:
            print("Usage: vb_shell_gate.py [validate <file>|repair_all]")
            print("Or run without arguments for interactive mode")
    
    else:
        # Interactive mode
        cli = VBShellGateCLI(gate)
        cli.run()


if __name__ == "__main__":
    main()
