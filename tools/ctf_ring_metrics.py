#!/usr/bin/env python3
"""Minimal CTF 1.8 (LTTng-UST) reader for the mpi_ring Tracevizlab trace.

Reproduces every metric quoted in the lab-204 report directly from the
trace packets, without babeltrace. Usage:

    python3 ctf_ring_metrics.py [path/to/mpi_ring] [--plot]

Options:
    --plot    Generate publication-quality causality & timeline diagram
"""
import struct
import glob
import os
import sys

EVENTS = {0: "ring:init", 1: "ring:recv_exit", 2: "ring:send_entry",
          3: "ring:recv_entry", 4: "ring:send_exit"}
FIELD = {0: "worker_id", 1: "source", 2: "dest", 3: None, 4: None}

# Layout from the trace's own metadata (TSDL):
#   packet header  = magic u32 | uuid[16] | stream_id u32 | stream_instance_id u64 = 32 B
#   packet context = 6 x u64 + cpu_id u32 = 52 B
#   event header   = tag u16; tag==0xFFFF -> id u32 + ts u64 (extended)
#                    else id=tag, ts u32 relative to packet timestamp_begin (compact)
#   event context  = _vtid i32 ; payload = one i32 for init/recv_exit/send_entry
HDR_CTX = 84


def parse_stream(path):
    data = open(path, "rb").read()
    events = []
    off = 0
    while off + HDR_CTX <= len(data):
        magic, = struct.unpack_from("<I", data, off)
        if magic != 0xC1FC1FC1:
            break
        (ts_begin, ts_end, content_size, packet_size,
         seq, discarded, cpu_id) = struct.unpack_from("<QQQQQQI", data, off + 32)
        pos = off + HDR_CTX
        end = off + content_size // 8
        while pos + 6 <= end:
            tag, = struct.unpack_from("<H", data, pos)
            pos += 2
            if tag == 0xFFFF:
                eid, = struct.unpack_from("<I", data, pos)
                pos += 4
                ts, = struct.unpack_from("<Q", data, pos)
                pos += 8
            else:
                eid = tag
                ts32, = struct.unpack_from("<I", data, pos)
                pos += 4
                ts = (ts_begin & ~0xFFFFFFFF) + ts32
                if ts32 < (ts_begin & 0xFFFFFFFF):
                    ts += 1 << 32
            vtid, = struct.unpack_from("<i", data, pos)
            pos += 4
            fval = None
            if FIELD.get(eid) is not None:
                fval, = struct.unpack_from("<i", data, pos)
                pos += 4
            events.append((ts, eid, vtid, fval))
        if packet_size <= 0:
            break
        off += packet_size // 8
    return events


def read_trace(base_path=None):
    if base_path is None:
        base_path = "traces/mpi_ring" if os.path.isdir("traces/mpi_ring") else "mpi_ring"
    events = []
    for f in sorted(glob.glob(os.path.join(base_path, "channel0_*"))):
        events.extend(parse_stream(f))
    events.sort()
    return events


def main():
    args = [a for a in sys.argv[1:] if not a.startswith("--")]
    do_plot = "--plot" in sys.argv
    base = args[0] if len(args) > 0 else None
    
    all_events = read_trace(base)
    if not all_events:
        print(f"Error: No events found in trace at '{base}'")
        sys.exit(1)

    t0 = all_events[0][0]
    print(f"total events: {len(all_events)}")
    print(f"{'ts_rel_ns':>10}  {'event':<16} {'vtid':>8}  field")
    for ts, eid, vtid, fval in all_events:
        print(f"{ts - t0:>10}  {EVENTS[eid]:<16} {vtid:>8}  "
              f"{'' if fval is None else f'{FIELD[eid]}={fval}'}")

    tid2worker = {}
    init_ts, recv_entry_ts, recv_exit_ts, send_entry_ts = {}, {}, {}, {}
    for ts, eid, vtid, fval in all_events:
        name = EVENTS[eid]
        if name == "ring:init":
            tid2worker[vtid] = fval
            init_ts[fval] = ts
        elif name == "ring:recv_entry":
            recv_entry_ts[tid2worker.get(vtid)] = ts
        elif name == "ring:recv_exit":
            recv_exit_ts[tid2worker.get(vtid)] = (ts, fval)
        elif name == "ring:send_entry":
            send_entry_ts[tid2worker.get(vtid)] = (ts, fval)

    us = lambda ns: f"{ns} ns = {ns / 1000:.3f} us"
    first = min(init_ts.values())
    print("\n---- metrics ----")
    for w in sorted(init_ts, key=lambda x: init_ts[x]):
        print(f"ring:init rank {w}: +{init_ts[w] - first} ns")
    print(f"init spread (last-first init): {us(max(init_ts.values()) - first)}")
    print(f"rank2.init -> rank0.init: {us(init_ts[0] - init_ts[2])}")
    for w in sorted(init_ts):
        wait = recv_exit_ts[w][0] - recv_entry_ts[w]
        print(f"rank {w} wait (recv_entry->recv_exit): {us(wait)} (src={recv_exit_ts[w][1]})")
    for w in sorted(init_ts):
        s, d = send_entry_ts[w]
        print(f"hop {w}->{d} (send_entry->recv_exit): {us(recv_exit_ts[d][0] - s)}")
    for w in sorted(init_ts):
        if w != 0:
            turn = send_entry_ts[w][0] - recv_exit_ts[w][0]
            print(f"rank {w} relay turnaround (recv_exit->send_entry): {us(turn)}")
    s0, _ = send_entry_ts[0]
    print(f"round trip (rank0 send_entry->rank0 recv_exit): {us(recv_exit_ts[0][0] - s0)}")

    if do_plot:
        from plot_ring_causality import generate_causality_diagram
        generate_causality_diagram(all_events)


if __name__ == "__main__":
    main()