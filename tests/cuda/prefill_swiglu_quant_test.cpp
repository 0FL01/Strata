// Component-only adaptation of Niko1221/Strata PR #1525, f048d155.
// Compare the actual FP32 prefill API, never BF16 or native_expert_grouped:
// GU [rows,1280] -> swiglu H [rows,640] -> D4 q8_1 [rows,1024 padded].
// No skip can pass this gate: type 42 and a nonzero executed-case count are mandatory.
#include "strata/prefill/moe_mmq.hpp"
#include "ggml.h"
#include <cuda_runtime.h>

#include <algorithm>
#include <cmath>
#include <cstdint>
#include <cstdio>
#include <cstdlib>
#include <cstring>
#include <random>
#include <stdexcept>
#include <string>
#include <vector>

namespace {
namespace mmq = strata::prefill::mmq;
constexpr int64_t NFF = 640, GU_COLS = 1280, PAD_COLS = 1024;
constexpr size_t BLOCK_VALUES = 128, BLOCK_BYTES = 144, GUARD = 256;
constexpr uint8_t SENTINEL = 0x5a;
static_assert(GGML_TYPE_Q2_0 == 42, "The actual model's mandatory down type changed");

void require(bool ok, const char* what) { if (!ok) throw std::runtime_error(what); }
void ck(cudaError_t e, const char* what) {
    if (e != cudaSuccess) throw std::runtime_error(std::string(what) + ": " + cudaGetErrorString(e));
}
struct Dev {
    void* p = nullptr;
    explicit Dev(size_t n) { ck(cudaMalloc(&p, n), "cudaMalloc"); }
    ~Dev() { cudaFree(p); }
    Dev(const Dev&) = delete;
    Dev& operator=(const Dev&) = delete;
    template <class T> T* as() const { return static_cast<T*>(p); }
};
struct Stream {
    cudaStream_t s{};
    Stream() { ck(cudaStreamCreate(&s), "create stream"); }
    ~Stream() { cudaStreamDestroy(s); }
};
struct Event {
    cudaEvent_t e{};
    Event() { ck(cudaEventCreate(&e), "create event"); }
    ~Event() { cudaEventDestroy(e); }
};
enum class Pattern { Random, Zero, Outlier };
const char* label(Pattern p) {
    return p == Pattern::Random ? "random" : p == Pattern::Zero ? "zero" : "outlier";
}

void fill(std::vector<float>& gu, int64_t rows, bool il, Pattern pattern, uint32_t seed) {
    if (pattern == Pattern::Zero) return; // vector value-initialization is exact +0
    std::mt19937 rng(seed);
    std::normal_distribution<float> nd(0.f, 1.f);
    std::uniform_real_distribution<float> mag(0.05f, 40.f);
    auto set = [&](int64_t r, int64_t k, float g, float u) {
        float* row = gu.data() + r * GU_COLS;
        row[il ? 2 * k : k] = g;
        row[il ? 2 * k + 1 : NFF + k] = u;
    };
    for (int64_t r = 0; r < rows; ++r) {
        const float m = mag(rng);
        for (int64_t k = 0; k < NFF; ++k) set(r, k, nd(rng) * m, nd(rng) * m);
        if (pattern == Pattern::Outlier) {
            // Each 32-value scale group and each vector/padded-half boundary is exercised.
            for (int64_t k : {0, 31, 32, 127, 128, 511, 512, 639})
                set(r, k, (k & 1) ? -120.f : 30000.f, (k & 2) ? -30000.f : 30000.f);
            // An all-zero scale group inside a nonzero row.
            for (int64_t k = 256; k < 288; ++k) set(r, k, 0.f, 0.f);
        }
    }
}

struct Case {
    int64_t rows;
    bool il;
    size_t used, qb, alloc;
    Dev gu, h, q0, q1;
    Stream stream;
    explicit Case(int64_t n, bool interleaved, Pattern pattern, uint32_t seed)
        : rows(n), il(interleaved), used((size_t) rows * (PAD_COLS / BLOCK_VALUES) * BLOCK_BYTES),
          qb(mmq::q8_bytes(rows, NFF)), alloc(qb + 2 * GUARD),
          gu((size_t) rows * GU_COLS * sizeof(float)), h((size_t) rows * NFF * sizeof(float)),
          q0(alloc), q1(alloc) {
        require(qb == used + 128 * BLOCK_BYTES, "Unexpected pinned MMQ block layout/size");
        std::vector<float> input((size_t) rows * GU_COLS);
        fill(input, rows, il, pattern, seed);
        ck(cudaMemcpy(gu.p, input.data(), input.size() * sizeof(float), cudaMemcpyHostToDevice), "upload FP32 GU");
        ck(cudaMemset(q0.p, SENTINEL, alloc), "baseline sentinel");
        ck(cudaMemset(q1.p, SENTINEL, alloc), "fused sentinel");
        // Different used-region sentinels prevent unwritten matching bytes from passing.
        ck(cudaMemset(fused(), 0xa5, used), "fused used-region sentinel");
    }
    void* baseline() const { return q0.as<uint8_t>() + GUARD; }
    void* fused() const { return q1.as<uint8_t>() + GUARD; }
    void run_baseline(ggml_type t) {
        mmq::swiglu(gu.as<float>(), h.as<float>(), rows, NFF, il, stream.s);
        mmq::quantize(h.as<float>(), nullptr, baseline(), (int) t, NFF, NFF, rows, stream.s);
    }
    void run_fused() { mmq::swiglu_quant(gu.as<float>(), fused(), rows, il, stream.s); }
    bool compare(ggml_type t, Pattern pattern) {
        ck(cudaStreamSynchronize(stream.s), "synchronize comparison");
        std::vector<uint8_t> a(alloc), b(alloc);
        ck(cudaMemcpy(a.data(), q0.p, alloc, cudaMemcpyDeviceToHost), "download baseline");
        ck(cudaMemcpy(b.data(), q1.p, alloc, cudaMemcpyDeviceToHost), "download fused");
        size_t bad = 0, guard_bad = 0, pad_bad = 0, first = alloc;
        for (size_t i = 0; i < alloc; ++i) {
            if (a[i] != b[i]) { ++bad; if (first == alloc) first = i; }
            if (i < GUARD || i >= GUARD + used) guard_bad += a[i] != SENTINEL || b[i] != SENTINEL;
        }
        // D4 is column-block-major: blocks 5,6,7 are the entirely padded 640..1023 values.
        const size_t pad_begin = GUARD + 5 * (size_t) rows * BLOCK_BYTES;
        for (size_t i = pad_begin; i < GUARD + used; ++i) pad_bad += a[i] != b[i];
        std::printf("EXACT type=%d name=%s rows=%lld gu_cols=%lld h_cols=%lld layout=%s pattern=%s "
                    "used_bytes=%zu compared_bytes=%zu mismatched_bytes=%zu padded_mismatches=%zu guard_bad=%zu\n",
                    (int) t, ggml_type_name(t), (long long) rows, (long long) GU_COLS, (long long) NFF,
                    il ? "interleaved" : "split", label(pattern), used, alloc, bad, pad_bad, guard_bad);
        if (first != alloc) std::printf("FIRST_MISMATCH allocation_offset=%zu data_offset=%lld baseline=%u fused=%u\n",
                                       first, (long long) first - (long long) GUARD, a[first], b[first]);
        return bad == 0 && guard_bad == 0;
    }
};

void check_budget(int64_t rows) {
    const size_t qb = mmq::q8_bytes(rows, NFF);
    const size_t gpu = (size_t) rows * (GU_COLS + NFF) * sizeof(float) + 2 * (qb + 2 * GUARD);
    const size_t host_peak = std::max((size_t) rows * GU_COLS * sizeof(float), 2 * (qb + 2 * GUARD));
    require(gpu + host_peak < (size_t) 1024 * 1024 * 1024, "Probe allocations exceed combined 1 GiB budget");
    size_t free = 0, total = 0;
    ck(cudaMemGetInfo(&free, &total), "memory budget");
    require(free >= gpu + (64u << 20), "Insufficient free VRAM for bounded probe plus 64 MiB reserve");
    std::printf("MEMORY rows=%lld gpu_bytes=%zu host_peak_bytes=%zu combined_bytes=%zu free_vram=%zu\n",
                (long long) rows, gpu, host_peak, gpu + host_peak, free);
}

float time_batch(Case& c, bool fused, int iters, Event& start, Event& end) {
    ck(cudaEventRecord(start.e, c.stream.s), "start timing");
    for (int i = 0; i < iters; ++i) { if (fused) c.run_fused(); else c.run_baseline(GGML_TYPE_Q2_0); }
    ck(cudaEventRecord(end.e, c.stream.s), "end timing");
    ck(cudaEventSynchronize(end.e), "synchronize timing");
    float ms = 0;
    ck(cudaEventElapsedTime(&ms, start.e, end.e), "elapsed timing");
    require(std::isfinite(ms) && ms > 0, "Invalid event timing");
    return ms / iters;
}

void benchmark(int64_t rows, bool il, int& executed, int& q2_cases) {
    check_budget(rows);
    Case c(rows, il, Pattern::Outlier, 20261008);
    c.run_baseline(GGML_TYPE_Q2_0); c.run_fused();
    require(c.compare(GGML_TYPE_Q2_0, Pattern::Outlier), "Benchmark preflight is not byte-exact");
    ++executed; ++q2_cases;
    for (int i = 0; i < 10; ++i) { c.run_baseline(GGML_TYPE_Q2_0); c.run_fused(); }
    ck(cudaStreamSynchronize(c.stream.s), "benchmark warmup");
    Event start, end;
    constexpr int REPS = 7, ITERS = 40;
    std::vector<float> baseline, fused, ratios;
    for (int r = 0; r < REPS; ++r) {
        float a, b;
        if (r & 1) { b = time_batch(c, true, ITERS, start, end); a = time_batch(c, false, ITERS, start, end); }
        else { a = time_batch(c, false, ITERS, start, end); b = time_batch(c, true, ITERS, start, end); }
        baseline.push_back(a); fused.push_back(b); ratios.push_back(a / b);
        std::printf("SAMPLE type=42 rows=%lld layout=%s rep=%d baseline_us=%.6f fused_us=%.6f speedup=%.6f\n",
                    (long long) rows, il ? "interleaved" : "split", r, a * 1000, b * 1000, a / b);
    }
    auto median = [](std::vector<float> v) { std::sort(v.begin(), v.end()); return v[v.size() / 2]; };
    std::printf("BENCH type=42 rows=%lld gu_cols=1280 h_cols=640 layout=%s reps=%d iters=%d "
                "baseline_median_us=%.6f fused_median_us=%.6f paired_median_speedup=%.6f "
                "method=stream_events_alternating_order\n",
                (long long) rows, il ? "interleaved" : "split", REPS, ITERS,
                median(baseline) * 1000, median(fused) * 1000, median(ratios));
    require(c.compare(GGML_TYPE_Q2_0, Pattern::Outlier), "Benchmark postflight is not byte-exact");
}
} // namespace

int main(int argc, char** argv) {
    std::setvbuf(stdout, nullptr, _IONBF, 0);
    bool bench = false, gate_off = false;
    int device = 0, executed = 0, q2_cases = 0;
    try {
        for (int i = 1; i < argc; ++i) {
            if (!std::strcmp(argv[i], "--bench")) bench = true;
            else if (!std::strcmp(argv[i], "--gate-off")) gate_off = true;
            else if (!std::strcmp(argv[i], "--device") && i + 1 < argc) device = std::stoi(argv[++i]);
            else throw std::runtime_error("Usage: gfx906_swiglu_quant_probe [--bench] [--device N] [--gate-off]");
        }
        if (gate_off) {
            require(!bench, "--gate-off cannot benchmark");
            for (int t = 0; t < GGML_TYPE_COUNT; ++t)
                require(!mmq::swiglu_quant_ok(t), "Experimental gate unexpectedly enabled");
            std::puts("GATE_OFF_PASS: all types refused; component numerical validation was not run");
            return 0;
        }
        require(mmq::supported(42) && mmq::swiglu_quant_ok(42),
                "Mandatory Q2_0/type 42 unavailable: set STRATA_GFX906_MMQ_SWIGLU_QUANT=1 on gfx906");
        for (int t : {-1, (int) GGML_TYPE_COUNT, (int) GGML_TYPE_F32, (int) GGML_TYPE_Q4_K, (int) GGML_TYPE_Q5_1})
            require(!mmq::swiglu_quant_ok(t), "Unsupported or non-D4 type unexpectedly eligible");
        int ndev = 0;
        ck(cudaGetDeviceCount(&ndev), "device count");
        require(ndev > 0 && device >= 0 && device < ndev, "Requested GPU unavailable; numerical gate cannot skip");
        ck(cudaSetDevice(device), "select device");
        cudaDeviceProp props{};
        ck(cudaGetDeviceProperties(&props, device), "device properties");
#if defined(STRATA_HIP_GFX906)
        require(!std::strncmp(props.gcnArchName, "gfx906", 6) && (props.gcnArchName[6] == '\0' || props.gcnArchName[6] == ':'),
                "This bounded probe requires a gfx906 device");
        std::printf("DEVICE id=%d name=%s arch=%s warp=%d input=FP32 down_type=42 layout=D4\n",
                    device, props.name, props.gcnArchName, props.warpSize);
#else
        throw std::runtime_error("Build the STRATA_HIP_GFX906 component target");
#endif
        check_budget(4113);
        for (ggml_type t : {GGML_TYPE_Q2_0, GGML_TYPE_IQ4_NL, GGML_TYPE_Q8_0}) {
            require(mmq::swiglu_quant_ok((int) t), "A required D4 test type is ineligible; no silent skips");
            for (bool il : {false, true}) for (int64_t rows : {1, 37, 4113})
                for (Pattern pattern : {Pattern::Random, Pattern::Zero, Pattern::Outlier}) {
                    Case c(rows, il, pattern, 20261008 + (uint32_t) rows);
                    c.run_baseline(t); c.run_fused();
                    require(c.compare(t, pattern), "Numerical/layout gate failed; stop before timings or model integration");
                    ++executed;
                    if (t == GGML_TYPE_Q2_0) ++q2_cases;
                }
        }
        require(executed == 54 && q2_cases == 18, "Wrong or vacuous component case count");
        if (bench) for (bool il : {false, true}) for (int64_t rows : {1, 37, 256, 4113, 32768})
            benchmark(rows, il, executed, q2_cases);
        std::printf("STRICT_GATE_PASS executed_cases=%d mandatory_type42_cases=%d mismatched_bytes=0 guards=exact "
                    "timing_cases=%d model_callsite=absent\n", executed, q2_cases, bench ? 10 : 0);
        return 0;
    } catch (const std::exception& e) {
        std::fprintf(stderr, "STRICT_GATE_FAIL executed_cases=%d mandatory_type42_cases=%d reason=%s\n",
                     executed, q2_cases, e.what());
        return 1;
    }
}
