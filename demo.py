"""Two-week roster for a small made-up unit: python demo.py"""
from datetime import date, time, timedelta

from scheduler import Employee, Requirement, ShiftPlanner, ShiftType

shifts = [
    ShiftType("M", "Morning", time(7), 6),
    ShiftType("T", "Afternoon", time(13), 6),
    ShiftType("N", "Night", time(19), 12),
]
start = date(2026, 10, 5)
employees = [
    Employee("n1", "Nurse Ana", "nurse"),
    Employee("n2", "Nurse Beto", "nurse"),
    Employee("n3", "Nurse Caro", "nurse", no_nights=True),
    Employee("n4", "Nurse Dani", "nurse", unavailable=frozenset({start + timedelta(days=i) for i in range(3)})),
    Employee("n5", "Nurse Eli", "nurse"),
    Employee("n6", "Nurse Fer", "nurse"),
    Employee("d1", "Dr. Gómez", "doctor", max_shifts_per_week=6),
    Employee("d2", "Dr. Henao", "doctor", max_shifts_per_week=6),
    Employee("d3", "Dr. Ibarra", "doctor", max_shifts_per_week=6),
]
requirements = [
    Requirement("M", "nurse", 2), Requirement("T", "nurse", 1), Requirement("N", "nurse", 1),
    Requirement("M", "doctor", 1), Requirement("N", "doctor", 1),
]

planner = ShiftPlanner(shifts, employees, requirements)
days = [start + timedelta(days=i) for i in range(14)]
roster = planner.plan(start, len(days))

print(roster.to_csv(employees, days, planner.shifts))
print("Gaps for the manager to resolve:")
for g in roster.gaps or ["none"]:
    print(" -", g)
print("Rule check:", planner.check(roster) or "all rules respected")
