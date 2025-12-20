#!/usr/bin/env python3

import argparse
import subprocess
import shutil
from pathlib import Path

SIZES = {
    'trace010': 2 ** 9,
    'trace024': 2 ** 9,
    'trace031': 2 ** 16,
    'trace045': 2 ** 12,
    'trace034': 2 ** 14,
    'trace029': 2 ** 9,
    'trace012': 2 ** 10,
    'twitter-cluster1': 2 ** 10,
    'twitter-cluster3': 2 ** 10,
    'twitter-cluster9': 2 ** 12,
    'twitter-cluster28': 2 ** 12,
    'metakv4': 2 ** 13,
    'metakv2': 2 ** 13
}

def count_trace_lines(trace_path):
    with open(trace_path, 'r') as f:
        return sum(1 for _ in f)

def create_lhd_config(trace_file, trace_name, cache_size, total_accesses):
    config_content = f"""cache:
{{
    admissionSamples = 8;
    associativity = 64;
    capacity = {cache_size};
}};

repl:
{{
    nClasses = 16;
    maxRefs = 3;
    debug = false;
    errTolerance = 0.01;
    accsPerInterval = {min(1000 * cache_size, total_accesses)};
    ewmaDecay = 0.9;
    type = "LHD";
}};

trace:
{{
    totalAccesses = {total_accesses};
    file = "{trace_file}";
    path = "/home/traces/";
}};
"""

    config_path = Path(f"/home/lhd_config_{trace_name}.cfg")
    with open(config_path, 'w') as f:
        f.write(config_content)

    return config_path

def run_lhd(config_path, trace_name):
    print(f"Running LHD for {trace_name}...")
    subprocess.run(['/home/LHD/bin/cache', str(config_path)], check=True)

    dump_files = list(Path('/home').glob('*.dump'))
    if dump_files:
        for dump_file in dump_files:
            dest = Path('/home/results') / f'LHD-{trace_name}.dump'
            shutil.move(str(dump_file), str(dest))
            print(f"Moved LHD dump file to {dest}")

def run_lrb(trace_path, trace_name, cache_size):
    print(f"Running LRB for {trace_name}...")
    subprocess.run([
        '/home/LRB/build/bin/webcachesim_cli',
        str(trace_path),
        'LRB',
        str(cache_size)
    ], check=True)

    dump_files = list(Path('/home').glob('*.dump'))
    if dump_files:
        for dump_file in dump_files:
            dest = Path('/home/results') / f'LRB-{trace_name}.dump'
            shutil.move(str(dump_file), str(dest))
            print(f"Moved LRB dump file to {dest}")

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--trace-name', required=True, type=str)
    parser.add_argument('--trace-file', required=True, type=str)

    args = parser.parse_args()

    trace_name = args.trace_name
    trace_path = Path(args.trace_file)

    if trace_name not in SIZES:
        print(f"Error: Unknown trace name '{trace_name}'")
        print(f"Available traces: {list(SIZES.keys())}")
        return 1

    if not trace_path.exists():
        print(f"Error: Trace file not found: {trace_path}")
        return 1

    cache_size = SIZES[trace_name]
    trace_file = trace_path.name

    Path('/home/results').mkdir(parents=True, exist_ok=True)

    print(f"Processing {trace_name} with cache size {cache_size}")
    print(f"Counting trace lines...")
    total_accesses = count_trace_lines(trace_path)
    print(f"Total accesses: {total_accesses}")

    config_path = create_lhd_config(trace_file, trace_name, cache_size, total_accesses)

    run_lhd(config_path, trace_name)

    run_lrb(trace_path, trace_name, cache_size)

    config_path.unlink()

    print(f"Completed processing {trace_name}")

if __name__ == "__main__":
    main()
