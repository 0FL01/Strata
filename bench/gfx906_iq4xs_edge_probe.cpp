// Deterministic, conversion-only IQ4_XS boundary/slicing test. No model or GEMM.
// Build as CXX, linked to strata_kernels and the selected HIP runtime target.
// Run old and flat in SEPARATE processes: the environment switch is cached.
// Every finite d case covers all 64 signed scale codes and all 16 nonlinear codes
// in both low and high nibbles. Finite d may legitimately yield +/-Inf in FP16.
// Independent INTEGER oracle: exact half significand * scale * nonlinear value,
// then one round-to-nearest-even conversion. Mathematical signed-zero differences
// are counted, not fatal: the existing GPU baseline may canonicalize zero signs.
// Dumps preserve ALL raw bits; baseline/candidate full-byte parity is a separate gate.
// NaN/Inf input scales are intentionally outside this finite-scale contract.
// -DIQ4XS_EDGE_HOST_ONLY builds/runs oracle and fixture tests without a GPU.
#ifndef IQ4XS_EDGE_HOST_ONLY
#include "strata/kernels/dequant_bf16.hpp"
#include "strata/kernels/iq_kernels.hpp"
#include <cuda_runtime.h>
#if !defined(STRATA_HIP_GFX906)
#error "Use the project's gfx906 compatibility build for this probe"
#endif
#endif
#include <algorithm>
#include <cmath>
#include <cstdint>
#include <cstdio>
#include <cstdlib>
#include <cstring>
#include <limits>
#include <stdexcept>
#include <string>
#include <vector>

namespace {
constexpr size_t kBlockBytes = 136, kInputGuard = 64, kOutputGuard = 64;
constexpr uint16_t kCanary = 0xa55a;
constexpr int kValues[16] = {-127, -104, -83, -65, -49, -35, -22, -10, 1, 13, 25, 38, 53, 69, 89, 113};
std::vector<uint16_t> scale_cases() {
    // zero, subnormal/normal boundary, adjacent mantissas, exponent boundaries,
    // overflow boundary at multiplier 4064, and the largest finite half.
    constexpr uint16_t positive[] = {0x0000, 0x0001, 0x0002, 0x0010, 0x01ff, 0x0200,
        0x03fe, 0x03ff, 0x0400, 0x0401, 0x07ff, 0x0800, 0x1bff, 0x1c00, 0x1c01,
        0x3555, 0x3bff, 0x3c00, 0x3c01, 0x3c02, 0x3fff, 0x4000, 0x4bff, 0x4c00,
        0x4c07, 0x4c08, 0x4c09, 0x77ff, 0x7800, 0x7bfe, 0x7bff};
    std::vector<uint16_t> out;
    for (uint16_t h : positive) { out.push_back(h); out.push_back(h | 0x8000u); }
    return out;
}
uint16_t product_bits(uint16_t d, int scale, int value) {
    const unsigned de = (d >> 10) & 31u;
    if (de == 31) throw std::runtime_error("Oracle expects finite half scales");
    const uint16_t sign = ((d >> 15) ^ (scale < 0) ^ (value < 0)) ? 0x8000u : 0;
    const unsigned significand = (d & 1023u) | (de ? 1024u : 0u);
    unsigned m = significand * static_cast<unsigned>(std::abs(scale)) * static_cast<unsigned>(std::abs(value));
    if (!m) return sign;
    const int base_exponent = de ? static_cast<int>(de) - 25 : -24;
    int top = 0;
    for (unsigned v = m; v > 1; v >>= 1) ++top;
    int exponent = top + base_exponent;
    if (exponent < -14) {
        // Products of finite half scales and integers are multiples of 2^-24;
        // their nonzero subnormal outputs need no rounding and cannot underflow.
        return sign | static_cast<uint16_t>(m << (base_exponent + 24));
    }
    if (exponent > 15) return sign | 0x7c00u;
    const int shift = top - 10;
    if (shift > 0) {
        const unsigned rem = m & ((1u << shift) - 1u), midpoint = 1u << (shift - 1);
        m >>= shift;
        if (rem > midpoint || (rem == midpoint && (m & 1u))) ++m;
    } else {
        m <<= -shift;
    }
    if (m == 2048) { m >>= 1; ++exponent; }
    if (exponent > 15) return sign | 0x7c00u;
    return sign | static_cast<uint16_t>(((exponent + 15) << 10) | (m - 1024));
}
void require(bool ok, const char* what) { if (!ok) throw std::runtime_error(what); }
bool zero_sign_only(uint16_t got, uint16_t want) {
    return got != want && ((got | want) & 0x7fffu) == 0;
}
void oracle_selftest() {
    require(zero_sign_only(0x0000, 0x8000) && zero_sign_only(0x8000, 0x0000), "Zero-sign exception check");
    require(!zero_sign_only(0x0000, 0x0000), "Equal bits are not exceptions");
    require(!zero_sign_only(0x0000, 0x0001) && !zero_sign_only(0x8000, 0x8001), "FTZ must still fail");
    require(!zero_sign_only(0x7c00, 0xfc00) && !zero_sign_only(0x0000, 0x7e00), "Nonzero mismatch must fail");
    require(product_bits(0x4c07, -32, -127) == 0x7bfe, "Below-overflow oracle check");
    require(product_bits(0x4c08, -32, -127) == 0x7c00, "Overflow oracle check");
    require(product_bits(0xcc08, -32, -127) == 0xfc00, "Negative-overflow oracle check");
    require(product_bits(0x8000, 0, -127) == 0x0000, "Signed-zero oracle check");
    require(product_bits(0x0000, 0, -127) == 0x8000, "Signed-zero oracle check");
    require(product_bits(0x0001, 1, 1) == 0x0001, "Minimum-subnormal oracle check");
    require(product_bits(0x03ff, 1, 1) == 0x03ff, "Maximum-subnormal oracle check");
    require(product_bits(0x0400, 1, 1) == 0x0400, "Minimum-normal oracle check");
#if defined(IQ4XS_EDGE_HOST_ONLY) && defined(__FLT16_MANT_DIG__)
    // Independent host floating conversion checks the integer oracle. No fast math.
    size_t checked = 0;
    for (uint16_t d : scale_cases()) {
        const int e = (d >> 10) & 31;
        const float magnitude = std::ldexp(static_cast<float>((d & 1023u) | (e ? 1024u : 0u)), e ? e - 25 : -24);
        const float df = (d & 0x8000u) ? -magnitude : magnitude;
        for (int s = -32; s <= 31; ++s) for (int v : kValues) {
            const _Float16 reference = static_cast<_Float16>((df * static_cast<float>(s)) * static_cast<float>(v));
            uint16_t bits = 0;
            std::memcpy(&bits, &reference, sizeof(bits));
            require(bits == product_bits(d, s, v), "Host _Float16 disagrees with integer oracle");
            ++checked;
        }
    }
    std::printf("host_integer_oracle_checked=%zu\n", checked);
#endif
}
struct Case { const char* name; int64_t cols, total_rows, row0, rows, slice; size_t first_block; };
std::vector<Case> cases() {
    const int64_t full_rows = static_cast<int64_t>(scale_cases().size() * 8);
    return {{"all-finite-boundaries", 256, full_rows, 0, full_rows, full_rows, 0},
            {"all-boundaries-tail-one", 256, full_rows, 0, full_rows, full_rows - 1, 0},
            {"cols256-offset-one-row", 256, 5, 1, 1, 1, 36 * 8},
            {"cols256-offset-three-rows", 256, 5, 1, 3, 3, 36 * 8},
            {"cols256-offset-tail-one", 256, 5, 1, 3, 2, 36 * 8},
            {"cols768-offset-one-row", 768, 5, 1, 1, 1, 36 * 8},
            {"cols768-offset-three-rows", 768, 5, 1, 3, 3, 36 * 8},
            {"cols768-offset-tail-one", 768, 5, 1, 3, 2, 36 * 8}};
}
std::vector<uint8_t> make_input(const Case& c) {
    const auto ds = scale_cases();
    const size_t blocks = static_cast<size_t>(c.total_rows * c.cols / 256);
    std::vector<uint8_t> data(blocks * kBlockBytes, 0);
    for (size_t b = 0; b < blocks; ++b) {
        const size_t logical = b + c.first_block;
        uint8_t* p = data.data() + b * kBlockBytes;
        const uint16_t d = ds[(logical / 8) % ds.size()];
        p[0] = static_cast<uint8_t>(d); p[1] = static_cast<uint8_t>(d >> 8);
        uint16_t high = 0;
        for (unsigned g = 0; g < 8; ++g) {
            const unsigned sc = static_cast<unsigned>((logical % 8) * 8 + g);
            high |= static_cast<uint16_t>((sc >> 4) << (2 * g));
            p[4 + g / 2] |= static_cast<uint8_t>((sc & 15) << (4 * (g % 2)));
            for (unsigned j = 0; j < 16; ++j) {
                const unsigned low = static_cast<unsigned>((j + logical + g) & 15);
                const unsigned hi = 15 - low;
                p[8 + 16 * g + j] = static_cast<uint8_t>(low | (hi << 4));
            }
        }
        p[2] = static_cast<uint8_t>(high); p[3] = static_cast<uint8_t>(high >> 8);
    }
    return data;
}
std::vector<uint16_t> expected(const Case& c, const std::vector<uint8_t>& input) {
    const size_t n = static_cast<size_t>(c.rows * c.cols), offset = static_cast<size_t>(c.row0 * c.cols / 256);
    std::vector<uint16_t> out(n);
    for (size_t b = 0; b < n / 256; ++b) {
        const uint8_t* p = input.data() + (offset + b) * kBlockBytes;
        const uint16_t d = p[0] | (p[1] << 8), high = p[2] | (p[3] << 8);
        for (unsigned g = 0; g < 8; ++g) {
            const int sc = static_cast<int>(((p[4 + g / 2] >> (4 * (g % 2))) & 15) | (((high >> (2 * g)) & 3) << 4)) - 32;
            for (unsigned j = 0; j < 16; ++j) {
                const uint8_t q = p[8 + g * 16 + j];
                out[b * 256 + g * 32 + j] = product_bits(d, sc, kValues[q & 15]);
                out[b * 256 + g * 32 + j + 16] = product_bits(d, sc, kValues[q >> 4]);
            }
        }
    }
    return out;
}
void fixture_selftest() {
    const auto cs = cases();
    const auto input = make_input(cs[0]);
    const auto out = expected(cs[0], input);
    size_t zeros[2] = {}, infs[2] = {}, subnormals = 0;
    for (uint16_t h : out) {
        if (!(h & 0x7fffu)) ++zeros[h >> 15];
        else if ((h & 0x7fffu) == 0x7c00u) ++infs[h >> 15];
        else if (!(h & 0x7c00u)) ++subnormals;
    }
    require(zeros[0] && zeros[1] && infs[0] && infs[1] && subnormals, "Missing boundary classes in fixture");
    std::printf("finite_d_cases=%zu scale_codes=64 nonlinear_codes=16 output_values=%zu "
                "positive_zero=%zu negative_zero=%zu positive_inf=%zu negative_inf=%zu subnormal=%zu\n",
                scale_cases().size(), out.size(), zeros[0], zeros[1], infs[0], infs[1], subnormals);
    for (const Case& c : cs) {
        require(c.row0 >= 0 && c.rows > 0 && c.row0 + c.rows <= c.total_rows && c.slice > 0 && c.cols % 256 == 0,
                "Invalid test geometry");
        const auto in = make_input(c);
        const auto selected = expected(c, in);
        if (c.row0) {
            Case wrong = c; wrong.row0 = 0;
            require(selected != expected(wrong, in), "Offset fixture cannot detect ignored row0");
        }
    }
}
#ifndef IQ4XS_EDGE_HOST_ONLY
void check(cudaError_t e, const char* what) {
    if (e != cudaSuccess) throw std::runtime_error(std::string(what) + ": " + cudaGetErrorString(e));
}
struct Buffer {
    void* p = nullptr;
    explicit Buffer(size_t n) { check(cudaMalloc(&p, n), "cudaMalloc"); }
    ~Buffer() { if (p) (void) cudaFree(p); }
    Buffer(const Buffer&) = delete; Buffer& operator=(const Buffer&) = delete;
};
struct Stream {
    cudaStream_t s = nullptr;
    Stream() { check(cudaStreamCreateWithFlags(&s, cudaStreamNonBlocking), "create stream"); }
    ~Stream() { if (s) (void) cudaStreamDestroy(s); }
};
struct File {
    FILE* f = nullptr;
    ~File() { if (f) (void) std::fclose(f); }
};
void bytes(FILE* f, const void* p, size_t n) {
    if (f && std::fwrite(p, 1, n, f) != n) throw std::runtime_error("Dump write failed");
}
void run_case(const Case& c, cudaStream_t stream, FILE* dump) {
    namespace k = strata::kernels;
    require(k::iq_supported(23) && k::iq_row_bytes(23, c.cols) == static_cast<size_t>(c.cols / 256) * kBlockBytes,
            "Unexpected packed IQ4_XS geometry");
    const auto input = make_input(c);
    const auto want = expected(c, input);
    std::vector<uint8_t> guarded_in(input.size() + 2 * kInputGuard, 0xa5);
    std::copy(input.begin(), input.end(), guarded_in.begin() + kInputGuard);
    std::vector<uint16_t> output(want.size() + 2 * kOutputGuard, kCanary);
    for (size_t i = 0; i < want.size(); ++i) output[kOutputGuard + i] = want[i] ^ 0xffffu;
    Buffer in(guarded_in.size()), out(output.size() * sizeof(uint16_t));
    check(cudaMemcpyAsync(in.p, guarded_in.data(), guarded_in.size(), cudaMemcpyHostToDevice, stream), "input copy");
    check(cudaMemcpyAsync(out.p, output.data(), output.size() * sizeof(uint16_t), cudaMemcpyHostToDevice, stream), "poison copy");
    auto* dst = static_cast<uint16_t*>(out.p) + kOutputGuard;
    const auto* src = static_cast<const uint8_t*>(in.p) + kInputGuard;
    const uintptr_t input_address = reinterpret_cast<uintptr_t>(src);
    const size_t first_row_byte_offset = static_cast<size_t>(c.row0 * c.cols / 256) * kBlockBytes;
    const size_t first_row_mod16 = (input_address + first_row_byte_offset) % 16;
    require(input_address % 16 == 0, "Fixture input base must be 16-byte aligned");
    require(reinterpret_cast<uintptr_t>(dst) % 16 == 0, "Fixture output base must be 16-byte aligned");
    if (c.row0 == 1 && (c.cols == 256 || c.cols == 768))
        require(first_row_mod16 == 8, "Offset fixture must exercise input alignment 8 mod16");
    for (int64_t r = 0; r < c.rows; r += c.slice) {
        const int64_t rows = std::min(c.slice, c.rows - r);
        k::dequant_f16(23, src, c.row0 + r, rows, c.cols, dst + r * c.cols, stream);
    }
    check(cudaGetLastError(), "dequant launch");
    check(cudaMemcpyAsync(output.data(), out.p, output.size() * sizeof(uint16_t), cudaMemcpyDeviceToHost, stream), "output copy");
    std::vector<uint8_t> input_after(guarded_in.size());
    check(cudaMemcpyAsync(input_after.data(), in.p, input_after.size(), cudaMemcpyDeviceToHost, stream), "input guard copy");
    check(cudaStreamSynchronize(stream), "dequant sync");
    require(input_after == guarded_in, "Input or input canary changed");
    for (size_t i = 0; i < kOutputGuard; ++i)
        require(output[i] == kCanary && output[kOutputGuard + want.size() + i] == kCanary, "Output canary changed");
    size_t zero_sign_differences = 0;
    for (size_t i = 0; i < want.size(); ++i) if (output[kOutputGuard + i] != want[i]) {
        if (zero_sign_only(output[kOutputGuard + i], want[i])) {
            ++zero_sign_differences;
            continue;  // Never normalize output: raw bits below are the parity gate.
        }
        std::fprintf(stderr, "%s mismatch at row=%zu col=%zu got=0x%04x expected=0x%04x\n", c.name,
                     i / static_cast<size_t>(c.cols), i % static_cast<size_t>(c.cols),
                     static_cast<unsigned>(output[kOutputGuard + i]), static_cast<unsigned>(want[i]));
        throw std::runtime_error("Full-bit comparison to integer oracle failed");
    }
    if (dump) {
        require(std::fprintf(dump, "case=%s cols=%lld total_rows=%lld row0=%lld rows=%lld slice=%lld input_bytes=%zu output_halves=%zu\n",
                c.name, (long long)c.cols, (long long)c.total_rows, (long long)c.row0, (long long)c.rows,
                (long long)c.slice, guarded_in.size(), output.size()) > 0, "Dump header failed");
        bytes(dump, guarded_in.data(), guarded_in.size());
        bytes(dump, output.data(), output.size() * sizeof(uint16_t));
    }
    std::printf("case=%s cols=%lld row0=%lld rows=%lld slice=%lld input_row_mod16=%zu oracle_exact_halves=%zu zero_sign_differences=%zu input_unchanged=ok canaries=ok\n",
                c.name, (long long)c.cols, (long long)c.row0, (long long)c.rows, (long long)c.slice, first_row_mod16,
                want.size() - zero_sign_differences, zero_sign_differences);
}
#endif
}  // namespace

int main(int argc, char** argv) {
    try {
        const uint16_t endian = 1;
        require(*reinterpret_cast<const uint8_t*>(&endian) == 1, "Little-endian host required for dumps");
        oracle_selftest(); fixture_selftest();
#ifdef IQ4XS_EDGE_HOST_ONLY
        (void) argc; (void) argv;
        std::printf("HOST_ONLY PASS; GPU not tested\n");
#else
        std::vector<int> devices;
        std::string dump_path;
        for (int i = 1; i < argc; ++i) {
            const std::string arg = argv[i];
            if (arg == "--help") {
                std::printf("Usage: %s [--device N ...] [--dump PATH]\nRepeated devices check switching (e.g. 0, 1, 0). Run switch modes in separate processes.\n", argv[0]);
                return 0;
            }
            require((arg == "--device" || arg == "--dump") && i + 1 < argc, "Unknown or incomplete option");
            const char* value = argv[++i];
            if (arg == "--dump") { require(dump_path.empty(), "Only one --dump allowed"); dump_path = value; }
            else {
                char* end = nullptr;
                const long n = std::strtol(value, &end, 10);
                require(end != value && !*end && n >= 0 && n <= 1024, "Invalid device ordinal");
                devices.push_back(static_cast<int>(n));
            }
        }
        if (devices.empty()) devices.push_back(0);
        File dump;
        if (!dump_path.empty()) {
            dump.f = std::fopen(dump_path.c_str(), "wb"); require(dump.f != nullptr, "Cannot open dump");
            constexpr char header[] = "IQ4XS_EDGE_V1\n";
            bytes(dump.f, header, sizeof(header) - 1);
        }
        for (int device : devices) {
            check(cudaSetDevice(device), "set device");
            cudaDeviceProp prop{};
            check(cudaGetDeviceProperties(&prop, device), "device properties");
            require(std::strncmp(prop.gcnArchName, "gfx906", 6) == 0 &&
                    (prop.gcnArchName[6] == '\0' || prop.gcnArchName[6] == ':') && prop.warpSize == 64,
                    "GPU probe is restricted to gfx906 wave64");
            std::printf("device=%d arch=%s warp=%d finite_input_scales=1 legitimate_output_inf=allowed\n",
                        device, prop.gcnArchName, prop.warpSize);
            Stream stream;
            for (const Case& c : cases()) run_case(c, stream.s, dump.f);
        }
        if (dump.f) {
            FILE* f = dump.f; dump.f = nullptr;
            require(std::fclose(f) == 0, "Dump close failed");
        }
        std::printf("GPU ORACLE PASS; zero-sign differences reported; raw baseline/candidate dump comparison still required\n");
#endif
        return 0;
    } catch (const std::exception& e) {
        std::fprintf(stderr, "iq4xs_edge_probe FAILED: %s\n", e.what());
        return 1;
    }
}
