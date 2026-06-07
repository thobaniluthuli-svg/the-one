#!/usr/bin/env python3
"""
VBSTKLE Rule Enforcement Engine

VBSTKLE = VB + StableTokenVocab + Linting + Enforcement

Enforces strict code governance rules across:
- Contract validation (VB Shell contracts)
- Semantic consistency (StableTokenVocab token patterns)
- Code quality metrics
- Naming conventions
- Architecture constraints
"""

import re
import sqlite3
from datetime import datetime
from typing import Tuple, List, Dict, Optional
from dataclasses import dataclass
from enum import Enum


# ─────────────────────────────────────────────────────────────────────────────
# Rule Severity Levels
# ─────────────────────────────────────────────────────────────────────────────

class SeverityLevel(Enum):
    """Rule violation severity levels."""
    CRITICAL = 5   # Must fix immediately
    HIGH = 4       # High priority
    MEDIUM = 3     # Should fix
    LOW = 2        # Nice to fix
    INFO = 1       # Informational


class RuleCategory(Enum):
    """Rule categories for organization."""
    CONTRACT = "contract"           # VB contract violations
    SEMANTIC = "semantic"           # Token/semantic violations
    NAMING = "naming"               # Naming convention violations
    ARCHITECTURE = "architecture"   # Architecture constraint violations
    QUALITY = "quality"             # Code quality violations
    SECURITY = "security"           # Security violations


# ─────────────────────────────────────────────────────────────────────────────
# Rule Violation Data Structure
# ─────────────────────────────────────────────────────────────────────────────

@dataclass
class RuleViolation:
    """Represents a single rule violation."""
    rule_id: str
    rule_name: str
    category: RuleCategory
    severity: SeverityLevel
    line: int
    column: int
    message: str
    suggestion: str
    affected_code: str
    auto_fixable: bool
    fix_code: Optional[str] = None


# ─────────────────────────────────────────────────────────────────────────────
# VBSTKLE Rule Engine
# ─────────────────────────────────────────────────────────────────────────────

class VBSTKLERuleEngine:
    """
    VBSTKLE Rule Enforcement Engine
    
    Enforces strict governance rules across code.
    """

    # Contract Rules
    CONTRACT_RULES = {
        "VB001": {
            "name": "Missing VB_ClassState struct",
            "severity": SeverityLevel.CRITICAL,
            "category": RuleCategory.CONTRACT,
            "pattern": r"typedef\s+struct\s+VB_ClassState",
            "message": "Required VB_ClassState struct not found",
            "suggestion": "Add VB_ClassState struct definition"
        },
        "VB002": {
            "name": "Missing VB_Parameters struct",
            "severity": SeverityLevel.CRITICAL,
            "category": RuleCategory.CONTRACT,
            "pattern": r"typedef\s+struct\s+VB_Parameters",
            "message": "Required VB_Parameters struct not found",
            "suggestion": "Add VB_Parameters struct definition"
        },
        "VB003": {
            "name": "Missing VB_Results struct",
            "severity": SeverityLevel.CRITICAL,
            "category": RuleCategory.CONTRACT,
            "pattern": r"typedef\s+struct\s+VB_Results",
            "message": "Required VB_Results struct not found",
            "suggestion": "Add VB_Results struct definition"
        },
        "VB004": {
            "name": "Missing required method: VB_bind_shell",
            "severity": SeverityLevel.CRITICAL,
            "category": RuleCategory.CONTRACT,
            "pattern": r"int\s+VB_bind_shell\s*\(\s*VB_ClassShell\s*\*\s*shell\s*\)",
            "message": "Required method VB_bind_shell not found",
            "suggestion": "Implement VB_bind_shell method"
        },
        "VB005": {
            "name": "Missing required method: VB_execute",
            "severity": SeverityLevel.CRITICAL,
            "category": RuleCategory.CONTRACT,
            "pattern": r"int\s+VB_execute\s*\(\s*VB_ClassState\s*\*",
            "message": "Required method VB_execute not found",
            "suggestion": "Implement VB_execute method"
        },
    }

    # Semantic Rules
    SEMANTIC_RULES = {
        "STKL001": {
            "name": "Inconsistent naming convention",
            "severity": SeverityLevel.HIGH,
            "category": RuleCategory.SEMANTIC,
            "check": "semantic_naming",
            "message": "Variable/function naming is inconsistent",
            "suggestion": "Use consistent naming: snake_case for vars, CamelCase for types"
        },
        "STKL002": {
            "name": "Semantic token cluster violation",
            "severity": SeverityLevel.HIGH,
            "category": RuleCategory.SEMANTIC,
            "check": "semantic_clustering",
            "message": "Code violates semantic coherence",
            "suggestion": "Refactor to maintain semantic consistency"
        },
    }

    # Naming Rules
    NAMING_RULES = {
        "NM001": {
            "name": "Invalid struct name format",
            "severity": SeverityLevel.HIGH,
            "category": RuleCategory.NAMING,
            "pattern": r"struct\s+([a-z][a-z0-9_]*)\s*\{",
            "message": "Struct name should use PascalCase",
            "suggestion": "Use PascalCase: struct MyStruct"
        },
        "NM002": {
            "name": "Invalid function name format",
            "severity": SeverityLevel.MEDIUM,
            "category": RuleCategory.NAMING,
            "pattern": r"^([A-Z]+_[a-z_]+)\s*\(",
            "message": "Function names should use snake_case",
            "suggestion": "Use snake_case with underscore separator"
        },
        "NM003": {
            "name": "Invalid macro name format",
            "severity": SeverityLevel.MEDIUM,
            "category": RuleCategory.NAMING,
            "pattern": r"#define\s+([a-z][a-zA-Z0-9_]*)",
            "message": "Macro names should use UPPER_CASE",
            "suggestion": "Use UPPER_CASE: #define MY_MACRO"
        },
    }

    # Architecture Rules
    ARCHITECTURE_RULES = {
        "ARCH001": {
            "name": "Direct global variable usage",
            "severity": SeverityLevel.HIGH,
            "category": RuleCategory.ARCHITECTURE,
            "pattern": r"^\s*[a-zA-Z_][a-zA-Z0-9_]*\s+[a-z][a-z0-9_]*\s*=",
            "message": "Global variables violate encapsulation",
            "suggestion": "Use struct members or static locals instead"
        },
        "ARCH002": {
            "name": "Function exceeds 50 lines",
            "severity": SeverityLevel.MEDIUM,
            "category": RuleCategory.ARCHITECTURE,
            "check": "function_length",
            "message": "Function is too long (>50 lines)",
            "suggestion": "Refactor into smaller functions"
        },
        "ARCH003": {
            "name": "Circular dependency",
            "severity": SeverityLevel.CRITICAL,
            "category": RuleCategory.ARCHITECTURE,
            "check": "circular_deps",
            "message": "Circular dependency detected",
            "suggestion": "Restructure to eliminate circular dependencies"
        },
    }

    # Quality Rules
    QUALITY_RULES = {
        "QL001": {
            "name": "Missing error handling",
            "severity": SeverityLevel.HIGH,
            "category": RuleCategory.QUALITY,
            "pattern": r"(?<!if\s*\()\w+\s*\(\s*.*\s*\)\s*;",
            "message": "Function call result not checked",
            "suggestion": "Add error handling: if (func() != 0) { error_handling; }"
        },
        "QL002": {
            "name": "Missing NULL check",
            "severity": SeverityLevel.HIGH,
            "category": RuleCategory.QUALITY,
            "pattern": r"->",
            "message": "Pointer dereference without NULL check",
            "suggestion": "Add NULL check before dereference"
        },
        "QL003": {
            "name": "Memory leak risk",
            "severity": SeverityLevel.MEDIUM,
            "category": RuleCategory.QUALITY,
            "pattern": r"malloc|calloc|realloc",
            "message": "Dynamic memory allocated but may not be freed",
            "suggestion": "Ensure corresponding free() calls"
        },
    }

    # Security Rules
    SECURITY_RULES = {
        "SEC001": {
            "name": "Unsafe string function",
            "severity": SeverityLevel.CRITICAL,
            "category": RuleCategory.SECURITY,
            "pattern": r"\b(strcpy|strcat|scanf|sprintf|gets)\s*\(",
            "message": "Unsafe string function used",
            "suggestion": "Use safe alternative: strncpy, strncat, snprintf"
        },
        "SEC002": {
            "name": "Potential buffer overflow",
            "severity": SeverityLevel.HIGH,
            "category": RuleCategory.SECURITY,
            "pattern": r"char\s+\w+\s*\[\s*\d+\s*\]\s*;",
            "message": "Fixed-size buffer could overflow",
            "suggestion": "Use dynamic allocation or bounds checking"
        },
        "SEC003": {
            "name": "Missing input validation",
            "severity": SeverityLevel.HIGH,
            "category": RuleCategory.SECURITY,
            "pattern": r"params_in\s*->",
            "message": "Input parameter used without validation",
            "suggestion": "Validate all input parameters"
        },
    }

    def __init__(self, db_path="vbstkle_rules.db"):
        """Initialize rule engine."""
        self.db_path = db_path
        self.violations: List[RuleViolation] = []
        self.all_rules = {
            **self.CONTRACT_RULES,
            **self.SEMANTIC_RULES,
            **self.NAMING_RULES,
            **self.ARCHITECTURE_RULES,
            **self.QUALITY_RULES,
            **self.SECURITY_RULES,
        }

    def _ok(self, payload) -> Tuple[int, any, any]:
        """Success response."""
        return (1, payload, None)

    def _err(self, code: str, msg: str, meta=None) -> Tuple[int, any, any]:
        """Error response."""
        return (0, None, (code, msg, meta))

    # ─────────────────────────────────────────────────────────────────────────
    # Core Rule Enforcement
    # ─────────────────────────────────────────────────────────────────────────

    def enforce(self, code: str, rules: List[str] = None) -> Tuple[int, Dict, any]:
        """
        Enforce rules on code.
        
        Args:
            code: Source code to check
            rules: Specific rule IDs to enforce (None = all)
        
        Returns:
            (status, {violations, summary}, error)
        """
        self.violations = []
        rules_to_check = rules if rules else list(self.all_rules.keys())

        lines = code.split('\n')

        for rule_id in rules_to_check:
            if rule_id not in self.all_rules:
                continue

            rule = self.all_rules[rule_id]

            if "pattern" in rule:
                self._check_pattern_rule(rule_id, rule, lines, code)
            elif "check" in rule:
                self._check_custom_rule(rule_id, rule, lines, code)

        # Calculate summary
        summary = self._calculate_summary()

        return self._ok({
            "violations": [self._violation_to_dict(v) for v in self.violations],
            "summary": summary,
            "total_violations": len(self.violations)
        })

    def _check_pattern_rule(self, rule_id: str, rule: Dict, lines: List[str], 
                           code: str) -> None:
        """Check pattern-based rules."""
        pattern = rule["pattern"]
        matches = list(re.finditer(pattern, code, re.MULTILINE | re.IGNORECASE))

        if not matches:
            # Pattern not found = violation
            violation = RuleViolation(
                rule_id=rule_id,
                rule_name=rule["name"],
                category=rule["category"],
                severity=rule["severity"],
                line=0,
                column=0,
                message=rule["message"],
                suggestion=rule["suggestion"],
                affected_code="",
                auto_fixable=False
            )
            self.violations.append(violation)

    def _check_custom_rule(self, rule_id: str, rule: Dict, lines: List[str], 
                          code: str) -> None:
        """Check custom rule logic."""
        check_type = rule["check"]

        if check_type == "semantic_naming":
            self._check_semantic_naming(rule_id, rule, lines)
        elif check_type == "semantic_clustering":
            self._check_semantic_clustering(rule_id, rule, lines)
        elif check_type == "function_length":
            self._check_function_length(rule_id, rule, lines)
        elif check_type == "circular_deps":
            self._check_circular_deps(rule_id, rule, lines)

    def _check_semantic_naming(self, rule_id: str, rule: Dict, 
                              lines: List[str]) -> None:
        """Check semantic naming consistency."""
        # Extract all identifiers
        identifiers = []
        for line_num, line in enumerate(lines):
            matches = re.findall(r'\b([a-zA-Z_][a-zA-Z0-9_]*)\b', line)
            identifiers.extend([(m, line_num) for m in matches])

        # Check consistency
        snake_case = re.compile(r'^[a-z][a-z0-9_]*$')
        camel_case = re.compile(r'^[A-Z][a-zA-Z0-9]*$')
        upper_case = re.compile(r'^[A-Z_]+$')

        styles = {"snake": 0, "camel": 0, "upper": 0}
        
        for ident, line_num in identifiers:
            if snake_case.match(ident):
                styles["snake"] += 1
            elif camel_case.match(ident):
                styles["camel"] += 1
            elif upper_case.match(ident):
                styles["upper"] += 1

        # Check for mixing (violation if more than 1 style)
        active_styles = sum(1 for v in styles.values() if v > 0)
        
        if active_styles > 1:
            violation = RuleViolation(
                rule_id=rule_id,
                rule_name=rule["name"],
                category=rule["category"],
                severity=rule["severity"],
                line=0,
                column=0,
                message=f"Mixing naming styles: {styles}",
                suggestion=rule["suggestion"],
                affected_code="",
                auto_fixable=False
            )
            self.violations.append(violation)

    def _check_semantic_clustering(self, rule_id: str, rule: Dict, 
                                  lines: List[str]) -> None:
        """Check semantic token clustering."""
        # Extract function definitions
        for line_num, line in enumerate(lines):
            # Look for function definitions
            if re.search(r"int\s+\w+\s*\(", line):
                # Simple check: verify function has related operations
                func_match = re.search(r"int\s+(\w+)\s*\(", line)
                if func_match:
                    func_name = func_match.group(1)
                    # Check if function body has related keywords
                    if "error" in func_name.lower() or "validate" in func_name.lower():
                        # Should have error checking code
                        func_body = "\n".join(lines[line_num:min(line_num+10, len(lines))])
                        if not re.search(r"(error|invalid|fail|check)", func_body, re.IGNORECASE):
                            violation = RuleViolation(
                                rule_id=rule_id,
                                rule_name=rule["name"],
                                category=rule["category"],
                                severity=rule["severity"],
                                line=line_num + 1,
                                column=0,
                                message=f"Function '{func_name}' lacks semantic consistency",
                                suggestion=rule["suggestion"],
                                affected_code=line,
                                auto_fixable=False
                            )
                            self.violations.append(violation)
                            break

    def _check_function_length(self, rule_id: str, rule: Dict, 
                              lines: List[str]) -> None:
        """Check function length."""
        in_function = False
        func_start = 0
        func_name = ""

        for line_num, line in enumerate(lines):
            if re.search(r"^\s*\w+\s+\w+\s*\([^)]*\)\s*\{", line):
                in_function = True
                func_start = line_num
                func_match = re.search(r"(\w+)\s*\(", line)
                if func_match:
                    func_name = func_match.group(1)

            elif in_function and line.strip() == "}":
                func_length = line_num - func_start
                if func_length > 50:
                    violation = RuleViolation(
                        rule_id=rule_id,
                        rule_name=rule["name"],
                        category=rule["category"],
                        severity=rule["severity"],
                        line=func_start + 1,
                        column=0,
                        message=f"Function '{func_name}' is {func_length} lines (limit: 50)",
                        suggestion=rule["suggestion"],
                        affected_code=func_name,
                        auto_fixable=False
                    )
                    self.violations.append(violation)
                in_function = False

    def _check_circular_deps(self, rule_id: str, rule: Dict, 
                            lines: List[str]) -> None:
        """Check for circular dependencies."""
        # Simple heuristic: look for mutual includes or calls
        includes = []
        for line_num, line in enumerate(lines):
            match = re.search(r'#include\s*[<"]([^>"]*)[>"]', line)
            if match:
                includes.append(match.group(1))

        # Check for patterns like A->B and B->A
        # (This is simplified; real detection would need deeper analysis)
        if len(includes) > 1:
            # For now, flag as info (could be false positive)
            pass

    # ─────────────────────────────────────────────────────────────────────────
    # Utilities
    # ─────────────────────────────────────────────────────────────────────────

    def _calculate_summary(self) -> Dict:
        """Calculate violation summary."""
        by_category = {}
        by_severity = {}

        for v in self.violations:
            cat = v.category.value
            by_category[cat] = by_category.get(cat, 0) + 1

            sev = v.severity.name
            by_severity[sev] = by_severity.get(sev, 0) + 1

        return {
            "total": len(self.violations),
            "by_category": by_category,
            "by_severity": by_severity,
            "auto_fixable": sum(1 for v in self.violations if v.auto_fixable)
        }

    def _violation_to_dict(self, v: RuleViolation) -> Dict:
        """Convert violation to dictionary."""
        return {
            "rule_id": v.rule_id,
            "rule_name": v.rule_name,
            "category": v.category.value,
            "severity": v.severity.name,
            "line": v.line,
            "column": v.column,
            "message": v.message,
            "suggestion": v.suggestion,
            "affected_code": v.affected_code,
            "auto_fixable": v.auto_fixable
        }

    def get_rule_info(self, rule_id: str) -> Tuple[int, Dict, any]:
        """Get detailed rule information."""
        if rule_id not in self.all_rules:
            return self._err("RULE_NOT_FOUND", f"Rule {rule_id} not found", None)

        rule = self.all_rules[rule_id]
        return self._ok({
            "rule_id": rule_id,
            "name": rule["name"],
            "category": rule.get("category", "unknown").value,
            "severity": rule["severity"].name,
            "message": rule["message"],
            "suggestion": rule["suggestion"]
        })

    def get_rules_by_category(self, category: str) -> Tuple[int, List, any]:
        """Get all rules in a category."""
        matching = []
        for rule_id, rule in self.all_rules.items():
            if rule.get("category", RuleCategory.QUALITY).value == category:
                matching.append({
                    "rule_id": rule_id,
                    "name": rule["name"],
                    "severity": rule["severity"].name
                })
        return self._ok(matching)

    def enforce_strict(self, code: str) -> Tuple[int, Dict, any]:
        """Enforce all rules with CRITICAL/HIGH severity."""
        strict_rules = [
            rid for rid, rule in self.all_rules.items()
            if rule["severity"] in (SeverityLevel.CRITICAL, SeverityLevel.HIGH)
        ]
        return self.enforce(code, strict_rules)

    def enforce_relaxed(self, code: str) -> Tuple[int, Dict, any]:
        """Enforce only CRITICAL rules."""
        relaxed_rules = [
            rid for rid, rule in self.all_rules.items()
            if rule["severity"] == SeverityLevel.CRITICAL
        ]
        return self.enforce(code, relaxed_rules)


# ─────────────────────────────────────────────────────────────────────────────
# VBSTKLE CLI
# ─────────────────────────────────────────────────────────────────────────────

class VBSTKLECLI:
    """Interactive CLI for VBSTKLE Rule Engine."""

    def __init__(self, engine: VBSTKLERuleEngine):
        self.engine = engine

    def print_banner(self):
        """Print CLI banner."""
        print("=" * 70)
        print("VBSTKLE - Rule Enforcement Engine")
        print("VB + StableTokenVocab + Linting + Enforcement")
        print("=" * 70)
        print()

    def print_help(self):
        """Print help information."""
        print("Commands:")
        print("  check <file>              - Check file against all rules")
        print("  check-strict <file>       - Check with strict rules (CRITICAL+HIGH)")
        print("  check-relaxed <file>      - Check with relaxed rules (CRITICAL only)")
        print("  rule <id>                 - Show rule information")
        print("  rules <category>          - List rules by category")
        print("  categories                - Show rule categories")
        print("  summary                   - Show rule summary")
        print("  help                      - Show this help")
        print("  exit                      - Exit CLI")
        print()

    def show_categories(self):
        """Show rule categories."""
        print("RULE CATEGORIES:")
        print("-" * 70)
        for cat in RuleCategory:
            print(f"  {cat.value:<20} - {cat.name}")
        print()

    def check_file(self, filepath: str, mode: str = "all"):
        """Check file against rules."""
        try:
            with open(filepath, 'r') as f:
                code = f.read()
        except FileNotFoundError:
            print(f"✖ ERROR: File not found: {filepath}")
            print()
            return

        if mode == "strict":
            ok, data, err = self.engine.enforce_strict(code)
        elif mode == "relaxed":
            ok, data, err = self.engine.enforce_relaxed(code)
        else:
            ok, data, err = self.engine.enforce(code)

        if ok == 0:
            print(f"✖ ERROR: {err[1]}")
            return

        violations = data["violations"]
        summary = data["summary"]

        print(f"CHECKING: {filepath}")
        print(f"Mode: {mode.upper()}")
        print("-" * 70)
        print(f"Found {summary['total']} violation(s)")
        print()

        if violations:
            # Group by severity
            by_sev = {}
            for v in violations:
                sev = v["severity"]
                if sev not in by_sev:
                    by_sev[sev] = []
                by_sev[sev].append(v)

            for severity in ["CRITICAL", "HIGH", "MEDIUM", "LOW", "INFO"]:
                if severity in by_sev:
                    print(f"\n{severity} ({len(by_sev[severity])}):")
                    for v in by_sev[severity]:
                        print(f"  [{v['rule_id']}] {v['rule_name']}")
                        print(f"      Line {v['line']}: {v['message']}")
                        print(f"      Suggestion: {v['suggestion']}")
        else:
            print("✔ No violations found!")

        print()
        print("SUMMARY:")
        print(f"  By Category: {summary['by_category']}")
        print(f"  By Severity: {summary['by_severity']}")
        print(f"  Auto-fixable: {summary['auto_fixable']}")
        print()

    def show_rule(self, rule_id: str):
        """Show rule information."""
        ok, data, err = self.engine.get_rule_info(rule_id)

        if ok == 0:
            print(f"✖ ERROR: {err[1]}")
            print()
            return

        print(f"RULE: {data['rule_id']}")
        print("-" * 70)
        print(f"Name:       {data['name']}")
        print(f"Category:   {data['category']}")
        print(f"Severity:   {data['severity']}")
        print(f"Message:    {data['message']}")
        print(f"Suggestion: {data['suggestion']}")
        print()

    def show_rules(self, category: str):
        """Show rules by category."""
        ok, rules, err = self.engine.get_rules_by_category(category)

        if ok == 0:
            print(f"✖ ERROR: {err[1]}")
            print()
            return

        print(f"RULES: {category.upper()}")
        print("-" * 70)

        if not rules:
            print(f"No rules found for category: {category}")
        else:
            for rule in rules:
                print(f"  [{rule['rule_id']}] {rule['name']:<40} ({rule['severity']})")

        print()

    def run(self):
        """Run interactive CLI loop."""
        self.print_banner()
        self.print_help()

        while True:
            try:
                cmd = input("vbstkle> ").strip()
            except (EOFError, KeyboardInterrupt):
                break

            if not cmd:
                continue

            if cmd in ("exit", "quit"):
                print("Exiting VBSTKLE Rule Engine")
                break

            if cmd == "help":
                self.print_help()
            elif cmd == "categories":
                self.show_categories()
            elif cmd.startswith("check-strict "):
                filepath = cmd[13:].strip()
                self.check_file(filepath, "strict")
            elif cmd.startswith("check-relaxed "):
                filepath = cmd[14:].strip()
                self.check_file(filepath, "relaxed")
            elif cmd.startswith("check "):
                filepath = cmd[6:].strip()
                self.check_file(filepath, "all")
            elif cmd.startswith("rule "):
                rule_id = cmd[5:].strip()
                self.show_rule(rule_id)
            elif cmd.startswith("rules "):
                category = cmd[6:].strip()
                self.show_rules(category)
            else:
                print(f"Unknown command: {cmd}")
                print("Type 'help' for available commands")
            print()


# ─────────────────────────────────────────────────────────────────────────────
# Main Entry Point
# ─────────────────────────────────────────────────────────────────────────────

def main():
    """Main entry point."""
    engine = VBSTKLERuleEngine()

    import sys
    if len(sys.argv) > 1:
        # Command-line mode
        cmd = sys.argv[1]
        
        if cmd in ("check", "check-strict", "check-relaxed") and len(sys.argv) > 2:
            cli = VBSTKLECLI(engine)
            mode = cmd.replace("check", "all").replace("-strict", "strict").replace("-relaxed", "relaxed")
            cli.check_file(sys.argv[2], mode.replace("all", "all"))
        else:
            print("Usage: vbstkle_rules.py [check|check-strict|check-relaxed] <file>")
            print("Or run without arguments for interactive mode")
    else:
        # Interactive mode
        cli = VBSTKLECLI(engine)
        cli.run()


if __name__ == "__main__":
    main()
