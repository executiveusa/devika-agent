"""
AST Agent
---------------
Scaffold agent that analyzes Python source code using the AST module,
finds simple issues, and suggests non-destructive fixes or transformations.

Public class: ASTAgent

Methods:
 - execute(context, **kwargs): main entry point
 - analyze_code(code: str) -> ast.AST
 - find_issues(tree: ast.AST) -> List[Dict]
 - suggest_fixes(issues: List[Dict]) -> List[Dict]

This is intentionally lightweight and dependency-free so it can run in the
existing environment.
"""
from __future__ import annotations

import ast
from typing import Any, Dict, List, Optional


class ASTAgent:
    """Minimal AST-based analysis agent scaffold."""

    def __init__(self):
        self.name = "ast"
        self.display_name = "AST Analyzer"

    def execute(self, context: Any, **kwargs) -> Dict[str, Any]:
        """Execute analysis on provided context.

        Expects context to be a dict with `code` (str) or `path` (str).
        Returns a dict with `issues` and `suggestions`.
        """
        code = None
        if isinstance(context, dict):
            code = context.get("code")
            path = context.get("path")
        else:
            path = None

        if not code and path:
            try:
                with open(path, "r", encoding="utf-8") as f:
                    code = f.read()
            except Exception as e:
                return {"error": f"Failed to read path {path}: {e}"}

        if not code:
            return {"error": "No code provided in context (expecting 'code' or 'path')"}

        try:
            tree = self.analyze_code(code)
            issues = self.find_issues(tree)
            suggestions = self.suggest_fixes(issues)

            return {
                "issues": issues,
                "suggestions": suggestions,
                "summary": f"Analyzed AST: {len(issues)} issues found"
            }

        except SyntaxError as e:
            return {"error": "syntax_error", "detail": str(e)}
        except Exception as e:
            return {"error": "analysis_failed", "detail": str(e)}

    def analyze_code(self, code: str) -> ast.AST:
        """Parse code into an AST tree."""
        return ast.parse(code)

    def find_issues(self, tree: ast.AST) -> List[Dict[str, Any]]:
        """Basic heuristic checks over the AST.

        Returns list of issue dicts with: type, lineno, col_offset, message
        """
        issues: List[Dict[str, Any]] = []

        for node in ast.walk(tree):
            # Detect bare except: clauses
            if isinstance(node, ast.ExceptHandler):
                if node.type is None:
                    issues.append({
                        "type": "bare-except",
                        "lineno": getattr(node, "lineno", None),
                        "col_offset": getattr(node, "col_offset", None),
                        "message": "Use specific exception types instead of bare 'except:'"
                    })

            # Detect use of eval
            if isinstance(node, ast.Call) and getattr(node.func, "id", None) == "eval":
                issues.append({
                    "type": "use-of-eval",
                    "lineno": getattr(node, "lineno", None),
                    "col_offset": getattr(node, "col_offset", None),
                    "message": "Avoid using eval(); prefer ast.literal_eval or safer parsing"
                })

            # Detect mutable default arguments
            if isinstance(node, ast.FunctionDef):
                for arg, default in zip(reversed(node.args.args), reversed(node.args.defaults)):
                    if isinstance(default, (ast.List, ast.Dict, ast.Set)):
                        issues.append({
                            "type": "mutable-default-argument",
                            "lineno": getattr(node, "lineno", None),
                            "col_offset": getattr(node, "col_offset", None),
                            "message": f"Function '{node.name}' has mutable default argument; use None and set inside body"
                        })

        return issues

    def suggest_fixes(self, issues: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Return simple textual suggestions for found issues."""
        suggestions: List[Dict[str, Any]] = []
        for issue in issues:
            if issue.get("type") == "bare-except":
                suggestions.append({
                    "lineno": issue.get("lineno"),
                    "suggestion": "Catch specific exceptions, e.g. 'except ValueError:' or add 'except Exception as e' with careful handling."
                })
            elif issue.get("type") == "use-of-eval":
                suggestions.append({
                    "lineno": issue.get("lineno"),
                    "suggestion": "Replace eval() with ast.literal_eval() when parsing Python literals, or use a proper parser for untrusted input."
                })
            elif issue.get("type") == "mutable-default-argument":
                suggestions.append({
                    "lineno": issue.get("lineno"),
                    "suggestion": "Use None as the default and set the mutable value inside the function body, e.g. 'if x is None: x = []'"
                })

        return suggestions


if __name__ == "__main__":
    # Quick smoke test when run directly
    sample = """
def foo(x=[]):
    try:
        return eval('1+1')
    except:
        return None
"""
    agent = ASTAgent()
    print(agent.execute({"code": sample}))
