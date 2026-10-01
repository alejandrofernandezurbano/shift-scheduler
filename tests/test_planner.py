import unittest
from collections import Counter
from datetime import date, time, timedelta

from scheduler import Assignment, Employee, Requirement, Roster, ShiftPlanner, ShiftType

M = ShiftType("M", "Morning", time(7), 6)
N = ShiftType("N", "Night", time(19), 12)
START = date(2026, 10, 5)


class PlannerTest(unittest.TestCase):
    def test_covers_requirements_without_breaking_rules(self):
        staff = [Employee(f"e{i}", f"E{i}", "nurse") for i in range(5)]
        p = ShiftPlanner([M, N], staff, [Requirement("M", "nurse", 1), Requirement("N", "nurse", 1)])
        r = p.plan(START, 7)
        self.assertEqual(r.gaps, [])
        self.assertEqual(len(r.assignments), 14)
        self.assertEqual(p.check(r), [])

    def test_no_morning_right_after_a_night(self):
        staff = [Employee("a", "A", "nurse"), Employee("b", "B", "nurse")]
        p = ShiftPlanner([M, N], staff, [Requirement("M", "nurse", 1), Requirement("N", "nurse", 1)])
        r = p.plan(START, 4)
        self.assertEqual(p.check(r), [])

    def test_reports_gap_instead_of_breaking_rules(self):
        p = ShiftPlanner([M, N], [Employee("a", "A", "nurse")], [Requirement("M", "nurse", 1), Requirement("N", "nurse", 1)])
        r = p.plan(START, 2)
        self.assertTrue(r.gaps)
        self.assertEqual(p.check(r), [])

    def test_unavailability_and_no_nights_are_respected(self):
        off = frozenset({START})
        staff = [Employee("a", "A", "nurse", unavailable=off), Employee("b", "B", "nurse", no_nights=True),
                 Employee("c", "C", "nurse")]
        p = ShiftPlanner([M, N], staff, [Requirement("M", "nurse", 1), Requirement("N", "nurse", 1)])
        r = p.plan(START, 3)
        for a in r.assignments:
            self.assertFalse(a.employee_id == "a" and a.day == START)
            self.assertFalse(a.employee_id == "b" and a.shift == "N")

    def test_weekly_cap(self):
        staff = [Employee("a", "A", "nurse", max_shifts_per_week=2), Employee("b", "B", "nurse")]
        p = ShiftPlanner([M], staff, [Requirement("M", "nurse", 1)])
        r = p.plan(START, 7)
        self.assertLessEqual(Counter(a.employee_id for a in r.assignments)["a"], 2)

    def test_load_is_spread_fairly(self):
        staff = [Employee(f"e{i}", f"E{i}", "nurse", max_shifts_per_week=7) for i in range(3)]
        p = ShiftPlanner([M], staff, [Requirement("M", "nurse", 1)])
        counts = Counter(a.employee_id for a in p.plan(START, 9).assignments)
        self.assertEqual(set(counts.values()), {3})

    def test_check_flags_a_bad_manual_edit(self):
        p = ShiftPlanner([M, N], [Employee("a", "A", "nurse")], [])
        bad = Roster([Assignment(START, "N", "a"), Assignment(START + timedelta(days=1), "M", "a")])
        self.assertTrue(p.check(bad))


if __name__ == "__main__":
    unittest.main()
