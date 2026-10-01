# Shift scheduler

> **ES:** Genera en segundos una propuesta de turnos justa que respeta las reglas (descanso mínimo,
> sin mañana después de noche, vacaciones, tope semanal, quien no hace noches) y le deja al jefe
> la lista de huecos que debe resolver a mano. Reescritura desde cero, con datos inventados, de la
> lógica que construí para la gestión de turnos del personal de una clínica.

Building a monthly roster by hand takes a coordinator days and still breaks rules. This tool
produces a **first draft** that respects every hard rule, spreads hours and night shifts
fairly, and lists the gaps a person has to decide. A separate `check()` validates any roster,
including one edited by hand.

In production I built a staff-shift app with automatic roster proposals for a clinic (Power
Apps). This is an independent re-implementation in plain Python with fictitious staff.

## Rules

- Coverage per shift and role (e.g. morning: 2 nurses + 1 doctor).
- One shift per day and a minimum rest between shifts (default 12 h), so no morning right after a night.
- Unavailable days (vacation, leave, training) and people who do not work nights.
- Maximum shifts per week per person.
- Fairness: nights first (hardest to cover), then the person with the fewest hours / nights.
- If a shift cannot be covered without breaking a rule, it is **reported as a gap**, never forced.

## Run it

```bash
python demo.py          # 2-week roster for 9 people, as CSV, plus gaps
python -m unittest discover -s tests -t .   # 7 tests
```

```
employee,role,2026-10-05,2026-10-06,...,hours
Nurse Ana,nurse,N,,T,M,M,M,,N,,M,,N,,T,72
...
Gaps for the manager to resolve:
 - 2026-10-11 Morning: missing 1 nurse
Rule check: all rules respected
```

The CSV opens directly in Excel. Python 3.10+, no dependencies.

## Author

Alejandro Fernández Urbano — Power Platform & AI automation · **Calidá S.A.S.** (Colombia).
[LinkedIn](https://www.linkedin.com/in/alejandro-fernandez-urbano) · alejandrofernandezurbano@gmail.com
