"""Proposes a staff shift roster that a manager then reviews.

The goal is not a perfect optimum: it is a fair, rule-abiding first draft in
seconds, plus a clear list of the gaps a person must resolve by hand.
"""
from __future__ import annotations

import csv
from collections import defaultdict
from dataclasses import dataclass, field
from datetime import date, datetime, time, timedelta
from io import StringIO


@dataclass(frozen=True)
class ShiftType:
    code: str          # "M", "T", "N"
    name: str
    start: time
    hours: int

    def window(self, day: date) -> tuple[datetime, datetime]:
        start = datetime.combine(day, self.start)
        return start, start + timedelta(hours=self.hours)


@dataclass(frozen=True)
class Employee:
    id: str
    name: str
    role: str                                   # "nurse", "doctor", "assistant"
    max_shifts_per_week: int = 5
    unavailable: frozenset[date] = frozenset()  # vacations, leave, training
    no_nights: bool = False


@dataclass(frozen=True)
class Requirement:
    shift: str   # ShiftType.code
    role: str
    count: int


@dataclass
class Assignment:
    day: date
    shift: str
    employee_id: str


@dataclass
class Roster:
    assignments: list[Assignment] = field(default_factory=list)
    gaps: list[str] = field(default_factory=list)

    def by_employee(self) -> dict[str, list[Assignment]]:
        out = defaultdict(list)
        for a in self.assignments:
            out[a.employee_id].append(a)
        return dict(out)

    def to_csv(self, employees: list[Employee], days: list[date], shifts: dict[str, ShiftType]) -> str:
        names = {e.id: e for e in employees}
        grid = {(a.employee_id, a.day): a.shift for a in self.assignments}
        buf = StringIO()
        w = csv.writer(buf)
        w.writerow(["employee", "role"] + [d.isoformat() for d in days] + ["hours"])
        for e in employees:
            row = [grid.get((e.id, d), "") for d in days]
            hours = sum(shifts[c].hours for c in row if c)
            w.writerow([names[e.id].name, e.role] + row + [hours])
        return buf.getvalue()


class ShiftPlanner:
    def __init__(self, shifts: list[ShiftType], employees: list[Employee],
                 requirements: list[Requirement], min_rest_hours: int = 12):
        self.shifts = {s.code: s for s in shifts}
        self.employees = employees
        self.requirements = requirements
        self.min_rest = timedelta(hours=min_rest_hours)

    def _can_work(self, e: Employee, day: date, shift: ShiftType, taken: list[tuple[datetime, datetime]],
                  week_load: int) -> bool:
        if day in e.unavailable or week_load >= e.max_shifts_per_week:
            return False
        if e.no_nights and shift.start >= time(19, 0):
            return False
        start, end = shift.window(day)
        for s, f in taken:
            # one shift per day, and enough rest between any two shifts
            if s.date() == day or (start < f + self.min_rest and s < end + self.min_rest):
                return False
        return True

    def plan(self, first_day: date, days: int) -> Roster:
        roster = Roster()
        taken: dict[str, list[tuple[datetime, datetime]]] = defaultdict(list)
        hours: dict[str, int] = defaultdict(int)
        week_load: dict[tuple[str, int], int] = defaultdict(int)
        nights: dict[str, int] = defaultdict(int)

        for offset in range(days):
            day = first_day + timedelta(days=offset)
            week = day.isocalendar()[1]
            # nights first: they are the hardest to cover
            for req in sorted(self.requirements, key=lambda r: -self.shifts[r.shift].start.hour):
                shift = self.shifts[req.shift]
                for _ in range(req.count):
                    candidates = [e for e in self.employees
                                  if e.role == req.role
                                  and self._can_work(e, day, shift, taken[e.id], week_load[(e.id, week)])]
                    if not candidates:
                        roster.gaps.append(f"{day.isoformat()} {shift.name}: missing 1 {req.role}")
                        continue
                    is_night = shift.start >= time(19, 0)
                    # fairness: fewest hours first, and spread nights evenly
                    best = min(candidates, key=lambda e: (nights[e.id] if is_night else 0, hours[e.id], e.id))
                    roster.assignments.append(Assignment(day, shift.code, best.id))
                    taken[best.id].append(shift.window(day))
                    hours[best.id] += shift.hours
                    week_load[(best.id, week)] += 1
                    nights[best.id] += int(is_night)
        return roster

    def check(self, roster: Roster) -> list[str]:
        """Independent validation of any roster, including one edited by hand."""
        problems = []
        emp = {e.id: e for e in self.employees}
        for eid, items in roster.by_employee().items():
            windows = sorted(self.shifts[a.shift].window(a.day) for a in items)
            for (s1, f1), (s2, _) in zip(windows, windows[1:]):
                if s2 - f1 < self.min_rest:
                    problems.append(f"{emp[eid].name}: only {(s2 - f1).seconds // 3600} h rest before {s2:%Y-%m-%d %H:%M}")
            for a in items:
                if a.day in emp[eid].unavailable:
                    problems.append(f"{emp[eid].name} is unavailable on {a.day.isoformat()}")
        return problems
