#!/usr/bin/env python3

import argparse
import simulatools
import re
from pathlib import Path
import json

from rich import pretty
from rich.console import Console

filepath = Path(__file__)
current_dir = filepath.parent
filepath = current_dir.resolve()
conf_file = current_dir / 'conf.json'

with conf_file.open('r') as conf_file:
    local_conf = json.load(conf_file)
caffeine_root = local_conf['caffeine_root']
resources = local_conf['resources'] if local_conf['resources'] != '' else caffeine_root
TRACES_DIR = f'{resources}'
RESULTS_DIR = local_conf['results'] if local_conf['results'] != '' else './results/'

pretty.install()
console = Console()

SIZES = {
    'trace010': 2 ** 9,
    'trace024': 2 ** 9,
    'trace031': 2 ** 16,
    'trace045': 2 ** 12,
    'trace034': 2 ** 14,
    'trace029': 2 ** 9,
    'trace012': 2 ** 10,
    'twitter01': 2 ** 10,
    'twitter03': 2 ** 10,
    'twitter09': 2 ** 12,
    'twitter28': 2 ** 12,
    'metakv4': 2 ** 13,
    'metakv2': 2 ** 13
}


def get_trace_name(input_file: Path):
    stem = input_file.stem.lower()

    if 'twitter' in stem:
        match = re.search(r'twitter(\d{2})', stem)
        if match:
            return f'twitter{match.group(1)}'
    elif 'ibm' in stem or 'trace' in stem:
        match = re.search(r'trace(\d{3})', stem)
        if match:
            return f'trace{match.group(1)}'
    elif 'metakv' in stem:
        match = re.search(r'metakv([24])', stem)
        if match:
            return f'metakv{match.group(1)}'

    return stem


def run_mock(fname: str, trace_name: str, cache_size: int, trace_folder: str, algorithm_name: str) -> None:
    output_filename = f'{algorithm_name}-{trace_name}'
    output_path = Path(RESULTS_DIR) / f'{output_filename}.csv'

    console.log(f'[bold #a98467]Running {algorithm_name} on trace: {trace_name}, size: {cache_size}')

    if output_path.exists():
        console.log(f'[yellow]Output file already exists, skipping: {output_path}')
        return

    Path(RESULTS_DIR).mkdir(parents=True, exist_ok=True)

    single_run_result = simulatools.single_run(
        'mock',
        trace_file=fname,
        trace_folder=trace_folder,
        trace_format='LATENCY_RESULT',
        size=cache_size,
        additional_settings={},
        name=f'mock-{trace_name}',
        save=False,
        verbose=False
    )

    if single_run_result is False:
        console.log(f'[bold red]Error running {algorithm_name} on {fname}: exiting')
        exit(1)
    else:
        single_run_result['Cache Size'] = cache_size
        single_run_result['Trace'] = trace_name
        single_run_result['Algorithm'] = algorithm_name

        single_run_result.to_csv(output_path, index=False)
        console.log(f"[bold #ffd166]Results saved to: {output_path}")
        console.log(f"[bold #ffd166]Hit Rate: {single_run_result['Hit Rate'].iloc[0]:.4f}")
        console.log(f"[bold #ffd166]Avg. Penalty: {int(single_run_result['Average Penalty'].iloc[0])}")


def main():
    parser = argparse.ArgumentParser(
        description='Run mock policy experiments on marked traces (traces with LHD/LRB predictions)'
    )

    parser.add_argument('--input', help='Path to marked trace file', required=True, type=str)
    parser.add_argument('--trace-name', help='Name of the trace (overrides auto-detection)', required=False, type=str)
    parser.add_argument('--cache-size', help='Cache size in entries (overrides default)', required=False, type=int)
    parser.add_argument('--trace-folder', help='Trace folder within resources directory', required=False, type=str, default='latency')
    parser.add_argument('--algorithm-name', help='Name to use for output files (default: mock)', required=False, type=str, default='mock')

    args = parser.parse_args()

    console.print(f'[bold]Running mock experiments with args:[/bold]\n{args}')

    input_file = Path(args.input)

    if not input_file.exists():
        console.print(f'[bold red]Error: Input file does not exist: {input_file}')
        exit(1)

    trace_name = args.trace_name if args.trace_name else get_trace_name(input_file)
    cache_size = args.cache_size if args.cache_size else SIZES.get(trace_name)

    if cache_size is None:
        console.print(f'[bold red]Error: Cannot determine cache size for trace: {trace_name}')
        console.print(f'[yellow]Please specify --cache-size or use a known trace name')
        console.print(f'[yellow]Known traces: {list(SIZES.keys())}')
        exit(1)

    console.print(f'[bold cyan]Trace name: {trace_name}')
    console.print(f'[bold cyan]Cache size: {cache_size}')
    console.print(f'[bold cyan]Trace folder: {args.trace_folder}')

    dump_path = Path(caffeine_root)
    console.print(f'[bold yellow]Cleaning up temporary CSV files in {dump_path}')

    for csv_file in dump_path.rglob('*.csv'):
        csv_file.unlink()
        console.print(f'[dim]Removed {csv_file.name}')

    run_mock(input_file.name, trace_name, cache_size, args.trace_folder, args.algorithm_name)

    console.print(f'[bold green]Completed successfully!')


if __name__ == '__main__':
    main()
