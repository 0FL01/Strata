from pathlib import Path
import hashlib, json
R=Path(__file__).resolve().parents[1]
s=(R/'generate.cpp').read_text()
b=(R.parent/'baseline/active-generate.cpp').read_text()
assert hashlib.sha256(b.encode()).hexdigest() == '614034787daa9e5c9a114dc36845cea821f01f44a84b7d1aa2fb6597fd0c671e'
# Existing deferred-primary arithmetic and draft launch call sites are unchanged.
for text in ['ver.commit(a + 1, err, defer_primary_commit)',
             'mtp.draft(T, outv.data(), p, a, drafts.data(), err, dprob.data(), (float) req_spec_min_p)',
             'const int T = (int) std::min<int64_t>(S, b - q);',
             'if (!sp.run(ids.data() + q, r - q, q, e)) return false;']:
    assert s.count(text)==b.count(text) and text in s, text
serial=s[s.index('            while (!pl_ran && !cancelled && produced_n < max_new)'):]
assert serial.index('primary_drained = ver.wait_commit(drain_err)')<serial.index('"decode"')
assert serial.index('policy.observe_chain(')<serial.index('"decode"')<serial.index('if (eos) { finish = "stop"; break; }')
assert '&consumed, nullptr, "decode"' in serial
cap=s[s.index('        auto checkpoint_at = [&]'):s.index('        sp.on_chunk = [&]')]
assert cap.index('cache_budget.reserve(peak)')<cap.index('gpu_sync_ok()')
assert cap.index('allocation->commit(inventory())')<cap.index('(void) coverage.saved(L)')
assert 'conversation_checkpoint_validate(c.stage_parts[i]' in cap
sel=s[s.index('            const auto parked = conversations.best(ids, req_imgs, want_cvec);'):]
assert sel.index('incoming.emplace(conversations.take(parked.index))')<sel.index('cache_room(merge_peak, incoming->bytes())')
assert 'n > o.max_context - 8 || max_new > o.max_context - n - 8' in s
assert s.index('MemoryBudget cache_budget(size_t(16) << 30)')<s.index('std::map<int64_t, MemoryBudget::Reservation> part_budget')<s.index('std::map<int64_t, std::vector<ConvCheckpoint>> part_at')
print('source integration contracts: PASS (ordering/call-site checks; not a compiler or GPU parity test)')
