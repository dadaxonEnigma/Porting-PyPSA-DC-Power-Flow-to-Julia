import pypsa
import numpy as np
import inspect

# Создаем ту же сеть
network = pypsa.Network()
network.add("Bus", "Bus 0", v_nom=380)
network.add("Bus", "Bus 1", v_nom=380)  
network.add("Bus", "Bus 2", v_nom=380)

network.add("Line", "Line 0-1", bus0="Bus 0", bus1="Bus 1",
            x=0.1, r=0.01, s_nom=1000)
network.add("Line", "Line 0-2", bus0="Bus 0", bus1="Bus 2",
            x=0.1, r=0.01, s_nom=1000)
network.add("Line", "Line 1-2", bus0="Bus 1", bus1="Bus 2",
            x=0.1, r=0.01, s_nom=1000)

network.add("Generator", "Gen 0", bus="Bus 0", p_nom=500, marginal_cost=10)
network.add("Load", "Load 1", bus="Bus 1", p_set=300)
network.add("Load", "Load 2", bus="Bus 2", p_set=200)

print("="*60)
print("EXPLORING PyPSA INTERNAL STRUCTURES")
print("="*60)

# Посмотрим на структуру данных
print("\n1. BUSES DataFrame:")
print(network.buses)

print("\n2. LINES DataFrame:")
print(network.lines[['bus0', 'bus1', 'x', 'r', 's_nom']])

print("\n3. GENERATORS DataFrame:")
print(network.generators[['bus', 'p_nom']])

print("\n4. LOADS DataFrame:")
print(network.loads[['bus', 'p_set']])

# Запускаем DC PF
network.lpf()

print("\n" + "="*60)
print("INTERNAL MATRICES AFTER DC POWER FLOW")
print("="*60)

# Получаем sub-network (там хранятся матрицы)
sub_network = network.sub_networks.obj[0]

print("\n5. ADMITTANCE MATRIX B (susceptance):")
if hasattr(sub_network, 'B'):
    print(sub_network.B.toarray() if hasattr(sub_network.B, 'toarray') else sub_network.B)
else:
    print("B matrix not directly accessible")

print("\n6. POWER INJECTIONS at each bus:")
# Генерация - нагрузка на каждом узле
for bus in network.buses.index:
    gen = network.generators[network.generators.bus == bus].p_nom.sum()
    load = network.loads[network.loads.bus == bus].p_set.sum()
    injection = gen - load
    print(f"{bus}: Gen={gen:.1f} MW, Load={load:.1f} MW, Injection={injection:.1f} MW")

print("\n7. LINE SUSCEPTANCES (1/x):")
for idx, line in network.lines.iterrows():
    b = 1.0 / line.x
    print(f"{idx}: x={line.x}, b=1/x={b:.2f}")