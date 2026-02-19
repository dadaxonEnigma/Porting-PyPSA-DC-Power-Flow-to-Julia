"""
Benchmark: Python/PyPSA — DC Power Flow & LOPF
Запускай рядом с julia/benchmark.jl для сравнения скоростей.
"""
import numpy as np
import pypsa
import time
import statistics
import csv
import warnings
import logging

# Убираем лишние предупреждения PyPSA из вывода
warnings.filterwarnings("ignore")
logging.disable(logging.CRITICAL)


# ----------------------------------------------------------------
#  Генератор сети (та же логика, что и в julia/benchmark.jl)
# ----------------------------------------------------------------
def generate_network(n_buses, seed=42):
    rng = np.random.default_rng(seed)

    lines = []
    # Spanning tree
    for i in range(1, n_buses):
        x = 0.05 + rng.random() * 0.45
        lines.append((i, i + 1, x))
    # Дополнительные рёбра
    for _ in range(max(1, n_buses // 3)):
        u = int(rng.integers(1, n_buses))
        v = int(rng.integers(u + 1, n_buses + 1))
        x = 0.05 + rng.random() * 0.45
        lines.append((u, v, x))

    loads = {}
    total_load = 0.0
    for bus in range(2, n_buses + 1):
        if rng.random() > 0.3:
            p = 50.0 + rng.random() * 450.0
            loads[bus] = p
            total_load += p
    if not loads:
        loads[2] = 200.0
        total_load = 200.0

    generators = {1: total_load * 1.1}
    for bus in range(2, n_buses + 1, 4):
        generators[bus] = loads.get(bus, 0.0) * 0.5 + 50.0

    return n_buses, lines, generators, loads


# ----------------------------------------------------------------
#  Создание PyPSA Network из наших данных
# ----------------------------------------------------------------
def build_pypsa_network(n_buses, lines, generators, loads, line_capacity=1e6):
    n = pypsa.Network()

    for bus in range(1, n_buses + 1):
        n.add("Bus", f"Bus{bus}", v_nom=380.0)

    for idx, (f, t, x) in enumerate(lines):
        n.add("Line", f"L{idx}", bus0=f"Bus{f}", bus1=f"Bus{t}",
              x=x, r=0.01, s_nom=line_capacity)

    for bus, p_max in generators.items():
        ctrl = "Slack" if bus == 1 else "PQ"
        n.add("Generator", f"G{bus}", bus=f"Bus{bus}",
              p_nom=p_max, marginal_cost=20.0, control=ctrl)

    for bus, p in loads.items():
        n.add("Load", f"Load{bus}", bus=f"Bus{bus}", p_set=p)

    return n


# ----------------------------------------------------------------
#  Замер времени
# ----------------------------------------------------------------
def time_median(func, n_runs):
    times = []
    for _ in range(n_runs):
        t0 = time.perf_counter()
        func()
        times.append(time.perf_counter() - t0)
    return statistics.median(times), min(times)


# ================================================================
#  ОСНОВНОЙ БЕНЧМАРК
# ================================================================
print("=" * 70)
print("BENCHMARK: Python/PyPSA — DC Power Flow & LOPF")
print("=" * 70)

DC_SIZES   = [3, 10, 50, 100, 500, 1000, 2000]
LOPF_SIZES = [3, 10, 50, 100, 500]

dc_results   = {}
lopf_results = {}

# ── DC Power Flow (lpf) ─────────────────────────────────────────
print("\n[DC POWER FLOW BENCHMARK]")
print("-" * 70)
print(f"{'Buses':<10} {'Median (ms)':>12} {'Min (ms)':>12} {'Lines':>10}")
print("-" * 70)

for n in DC_SIZES:
    n_buses, lines, generators, loads = generate_network(n, seed=42)
    net = build_pypsa_network(n_buses, lines, generators, loads)

    n_runs = 50 if n <= 100 else (10 if n <= 500 else 3)
    med, mn = time_median(lambda: net.lpf(), n_runs)

    dc_results[n] = med * 1000
    print(f"{n:<10} {med*1000:>12.4f} {mn*1000:>12.4f} {len(lines):>10}")

# ── LOPF (optimize) ─────────────────────────────────────────────
print("\n[LOPF BENCHMARK  (linopy + HiGHS)]")
print("-" * 70)
print(f"{'Buses':<10} {'Median (ms)':>12} {'Min (ms)':>12} {'Lines':>10}")
print("-" * 70)

for n in LOPF_SIZES:
    n_buses, lines, generators, loads = generate_network(n, seed=42)
    # Для LOPF нужно пересоздавать Network на каждом запуске
    # (иначе PyPSA меняет внутреннее состояние и время нечестное)

    def run_lopf():
        net = build_pypsa_network(n_buses, lines, generators, loads)
        net.optimize(solver_name="highs")

    n_runs = 10 if n <= 50 else (5 if n <= 100 else 3)
    med, mn = time_median(run_lopf, n_runs)

    lopf_results[n] = med * 1000
    print(f"{n:<10} {med*1000:>12.3f} {mn*1000:>12.3f} {len(lines):>10}")

# ── Сохраняем CSV ───────────────────────────────────────────────
with open("results/python_benchmark.csv", "w", newline="") as f:
    writer = csv.writer(f)
    writer.writerow(["module", "n_buses", "time_ms"])
    for n in DC_SIZES:
        writer.writerow(["DC_PF", n, dc_results[n]])
    for n in LOPF_SIZES:
        writer.writerow(["LOPF", n, lopf_results[n]])

print("\n[OK] Results saved to results/python_benchmark.csv")
print("Run julia/benchmark.jl to get Julia times for comparison.")
