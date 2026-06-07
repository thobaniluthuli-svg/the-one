"""Crash Store - Crash Problem/Solution Ledger with MySQL Persistence

Converts crashes into structured problems and maps them to solutions.
"""

from typing import Dict, Any, List, Optional
import json
import time


class CrashStore:
    """Crash problem/solution ledger with MySQL persistence."""

    def __init__(self, db_handler: Optional[Any] = None):
        """Initialize CrashStore with optional DBHandler.

        Args:
            db_handler: DBHandler instance for MySQL persistence
        """
        self.db_handler = db_handler
        self._problems: List[Dict[str, Any]] = []
        self._solutions: Dict[int, List[str]] = {}
        self._problem_counter = 0

    def record_problem(self, crash: Dict[str, Any]) -> Dict[str, Any]:
        """Convert crash to problem and store.

        Args:
            crash: Crash record from CrashTracker

        Returns:
            Problem record dictionary
        """
        self._problem_counter += 1
        problem_id = self._problem_counter

        problem = {
            "id": problem_id,
            "crash_id": crash.get("crash_id", problem_id),
            "description": f"{crash.get('exception_type', 'Unknown')} in {crash.get('function', 'unknown')} function",
            "exception_type": crash.get("exception_type"),
            "file": crash.get("file"),
            "function": crash.get("function"),
            "line": crash.get("line"),
            "created_at": time.strftime("%Y-%m-%d %H:%M:%S"),
            "crash_message": crash.get("message"),
        }

        self._problems.append(problem)
        self._solutions[problem_id] = []

        # Persist to DB if available
        if self.db_handler:
            try:
                self.db_handler.insert_problem(problem)
            except Exception as e:
                print(f"Failed to persist problem to DB: {e}")

        return problem

    def record_solution(self, problem_id: int, solution_text: str) -> Dict[str, Any]:
        """Add solution to problem.

        Args:
            problem_id: ID of the problem
            solution_text: Solution text

        Returns:
            Solution record dictionary
        """
        if problem_id not in self._solutions:
            self._solutions[problem_id] = []

        solution = {
            "problem_id": problem_id,
            "solution_text": solution_text,
            "created_at": time.strftime("%Y-%m-%d %H:%M:%S"),
        }

        self._solutions[problem_id].append(solution_text)

        # Persist to DB if available
        if self.db_handler:
            try:
                self.db_handler.insert_solution(solution)
            except Exception as e:
                print(f"Failed to persist solution to DB: {e}")

        return solution

    def get_db_problems(self, limit: int = 100) -> List[Dict[str, Any]]:
        """Retrieve problems from database.

        Args:
            limit: Maximum number of problems to retrieve

        Returns:
            List of problem records
        """
        if self.db_handler:
            try:
                return self.db_handler.get_all_problems(limit)
            except Exception as e:
                print(f"Failed to get problems from DB: {e}")

        return self._problems[:limit]

    def get_db_solutions(self, problem_id: int) -> List[str]:
        """Retrieve solutions for a problem.

        Args:
            problem_id: ID of the problem

        Returns:
            List of solution texts
        """
        if self.db_handler:
            try:
                solutions = self.db_handler.get_solutions_for_problem(problem_id)
                return [s.get("solution_text") for s in solutions if s]
            except Exception as e:
                print(f"Failed to get solutions from DB: {e}")

        return self._solutions.get(problem_id, [])

    def get_all_problems(self) -> List[Dict[str, Any]]:
        """Get all problems."""
        return self._problems.copy()

    def get_all_solutions(self) -> Dict[int, List[str]]:
        """Get all solutions."""
        return self._solutions.copy()
