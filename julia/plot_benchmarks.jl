using Plots
using StatsPlots   
using CSV
using DataFrames
using Printf

python_data = CSV.read("../results/python_benchmark.csv", DataFrame)
julia_data  = CSV.read("../results/julia_benchmark.csv",  DataFrame)

speedup_dc   = Float64[]
speedup_lopf = Float64[]
sizes_dc     = Int[]
sizes_lopf   = Int[]

for mod in ["DC_PF", "LOPF"]
    py_mod = python_data[python_data.module .== mod, :]
    jl_mod = julia_data[julia_data.module .== mod, :]

    for i in 1:nrow(py_mod)
        n       = py_mod.n_buses[i]
        py_time = py_mod.time_ms[i]

        jl_idx = findfirst(jl_mod.n_buses .== n)
        if jl_idx !== nothing
            jl_time = jl_mod.time_ms[jl_idx]
            speedup = py_time / jl_time

            if mod == "DC_PF"
                push!(speedup_dc, speedup)
                push!(sizes_dc, n)
            else
                push!(speedup_lopf, speedup)
                push!(sizes_lopf, n)
            end
        end
    end
end

dc_py   = python_data[python_data.module .== "DC_PF", :]
dc_jl   = julia_data[julia_data.module  .== "DC_PF", :]
lopf_py = python_data[python_data.module .== "LOPF",  :]
lopf_jl = julia_data[julia_data.module  .== "LOPF",   :]

p1 = plot(title="Execution Time Comparison",
          xlabel="Network Size (buses)",
          ylabel="Time (ms, log scale)",
          yscale=:log10,
          legend=:topleft,
          size=(800, 600))

plot!(p1, dc_py.n_buses,   dc_py.time_ms,
      label="DC PF (Python/PyPSA)",
      marker=:circle,  linewidth=2, color=:red)
plot!(p1, dc_jl.n_buses,   dc_jl.time_ms,
      label="DC PF (Julia)",
      marker=:circle,  linewidth=2, color=:blue)
plot!(p1, lopf_py.n_buses, lopf_py.time_ms,
      label="LOPF (Python/PyPSA)",
      marker=:square,  linewidth=2, color=:orange, linestyle=:dash)
plot!(p1, lopf_jl.n_buses, lopf_jl.time_ms,
      label="LOPF (Julia)",
      marker=:square,  linewidth=2, color=:green,  linestyle=:dash)

savefig(p1, "../results/benchmark_time.png")
println("Saved: results/benchmark_time.png")

p2 = plot(title="Performance Speedup (Julia vs Python)",
          xlabel="Network Size (buses)",
          ylabel="Speedup Factor (x)",
          yscale=:log10,
          legend=:topright,
          size=(800, 600))

plot!(p2, sizes_dc,   speedup_dc,
      label="DC Power Flow",
      marker=:circle, linewidth=3, color=:blue,  markersize=8)
plot!(p2, sizes_lopf, speedup_lopf,
      label="LOPF",
      marker=:square, linewidth=3, color=:green, markersize=8)
hline!(p2, [1], color=:red, linestyle=:dash, linewidth=2,
       label="No speedup (1x)")

savefig(p2, "../results/benchmark_speedup.png")
println("Saved: results/benchmark_speedup.png")

selected_sizes = [10, 100, 500]
dc_speedups   = [speedup_dc[findfirst(sizes_dc     .== s)] for s in selected_sizes if s in sizes_dc]
lopf_speedups = [speedup_lopf[findfirst(sizes_lopf .== s)] for s in selected_sizes if s in sizes_lopf]

p3 = groupedbar([dc_speedups lopf_speedups],
                bar_position=:dodge,
                label=["DC PF" "LOPF"],
                title="Speedup by Network Size",
                xlabel="Network Size",
                ylabel="Speedup Factor (x)",
                xticks=(1:length(selected_sizes), string.(selected_sizes)),
                legend=:topleft,
                size=(800, 600),
                color=[:blue :green])

savefig(p3, "../results/benchmark_speedup_bars.png")
println("Saved: results/benchmark_speedup_bars.png")

println("\n" * "="^60)
println("BENCHMARK SUMMARY TABLE (for thesis)")
println("="^60)

println("\nDC POWER FLOW:")
@printf("%-12s %12s %12s %15s\n", "Size (buses)", "Python (ms)", "Julia (ms)", "Speedup (x)")
println("-"^55)
for i in 1:length(sizes_dc)
    @printf("%-12d %12.2f %12.4f %15.1fx\n",
            sizes_dc[i], dc_py.time_ms[i], dc_jl.time_ms[i], speedup_dc[i])
end

println("\nLOPF:")
@printf("%-12s %12s %12s %15s\n", "Size (buses)", "Python (ms)", "Julia (ms)", "Speedup (x)")
println("-"^55)
for i in 1:length(sizes_lopf)
    @printf("%-12d %12.2f %12.4f %15.1fx\n",
            sizes_lopf[i], lopf_py.time_ms[i], lopf_jl.time_ms[i], speedup_lopf[i])
end

println("\nAll benchmark visualizations saved to results/")
