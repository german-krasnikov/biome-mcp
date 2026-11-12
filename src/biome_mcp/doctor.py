"""Diagnostic runner skeleton."""

from __future__ import annotations

from dataclasses import dataclass, field


@dataclass
class DiagnosticResult:
    name: str
    passed: bool
    message: str = ""


@dataclass
class DoctorReport:
    checks: list[DiagnosticResult] = field(default_factory=list)

    @property
    def all_passed(self) -> bool:
        return all(c.passed for c in self.checks)

    def summary(self) -> str:
        total = len(self.checks)
        passed = sum(1 for c in self.checks if c.passed)
        return f"{passed}/{total} checks passed"


class Doctor:
    def __init__(self) -> None:
        self._checks: list[tuple[str, callable]] = []

    def add_check(self, name: str, fn: callable) -> None:
        self._checks.append((name, fn))

    async def run(self) -> DoctorReport:
        report = DoctorReport()
        for name, fn in self._checks:
            try:
                result = await fn()
                report.checks.append(DiagnosticResult(
                    name=name, passed=bool(result), message=str(result),
                ))
            except Exception as exc:
                report.checks.append(DiagnosticResult(
                    name=name, passed=False, message=str(exc),
                ))
        return report
