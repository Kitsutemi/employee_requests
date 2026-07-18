"""
Замер производительности запроса просроченных заявок исполнителя в статусе «В работе».

Запрос:
  SELECT * FROM requests
  WHERE executor_id = ?
    AND status = 'in_progress'
    AND deadline < NOW()
  ORDER BY deadline;
"""
import statistics
import time
from datetime import datetime, timezone

from sqlalchemy import text

from app.database import SessionLocal, engine
from app.models import Request


QUERY = """
SELECT id, number, deadline
FROM requests
WHERE executor_id = :executor_id
  AND status = 'in_progress'
  AND deadline < :now
ORDER BY deadline
"""

EXPLAIN = f"EXPLAIN QUERY PLAN {QUERY}"


def drop_index(db):
    db.execute(text("DROP INDEX IF EXISTS idx_requests_executor_status_deadline"))
    db.commit()


def create_index(db):
    db.execute(
        text(
            "CREATE INDEX idx_requests_executor_status_deadline "
            "ON requests (executor_id, status, deadline)"
        )
    )
    db.commit()
    db.execute(text("ANALYZE requests"))
    db.commit()


def explain_plan(db, executor_id: int, now: datetime) -> list[str]:
    rows = db.execute(
        text(EXPLAIN),
        {"executor_id": executor_id, "now": now.isoformat()},
    ).fetchall()
    return [row[3] for row in rows]


def run_query(db, executor_id: int, now: datetime) -> tuple[int, float]:
    start = time.perf_counter()
    rows = db.execute(
        text(QUERY),
        {"executor_id": executor_id, "now": now.isoformat()},
    ).fetchall()
    elapsed = time.perf_counter() - start
    return len(rows), elapsed


def benchmark(db, executor_id: int, runs: int = 5) -> tuple[float, int]:
    now = datetime.now(timezone.utc).replace(tzinfo=None)
    timings = []
    count = 0
    for _ in range(runs):
        count, elapsed = run_query(db, executor_id, now)
        timings.append(elapsed)
    return statistics.mean(timings), count


def measure(executor_id: int = 1, runs: int = 5):
    print("=" * 60)
    print("Запрос: просроченные заявки исполнителя в статусе «В работе»")
    print(f"Исполнитель ID={executor_id}, прогонов: {runs}")
    print("=" * 60)

    db = SessionLocal()
    now = datetime.now(timezone.utc).replace(tzinfo=None)

    drop_index(db)
    print("\n--- БЕЗ индекса ---")
    plan_before = explain_plan(db, executor_id, now)
    for line in plan_before:
        print(f"  {line}")
    avg_before, count = benchmark(db, executor_id, runs)
    print(f"Найдено записей: {count}")
    print(f"Среднее время: {avg_before:.4f} с")

    create_index(db)
    print("\n--- С составным индексом (executor_id, status, deadline) ---")
    plan_after = explain_plan(db, executor_id, now)
    for line in plan_after:
        print(f"  {line}")
    avg_after, count = benchmark(db, executor_id, runs)
    print(f"Найдено записей: {count}")
    print(f"Среднее время: {avg_after:.4f} с")

    speedup = avg_before / avg_after if avg_after > 0 else float("inf")
    print("\n--- Итог ---")
    print(f"До оптимизации:  {avg_before:.4f} с")
    print(f"После оптимизации: {avg_after:.4f} с")
    print(f"Ускорение: {speedup:.2f}x")

    db.close()
    return avg_before, avg_after, count


if __name__ == "__main__":
    measure(executor_id=1, runs=5)
