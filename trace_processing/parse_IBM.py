import argparse
from pathlib import Path

from typing import List

from rich import pretty, print
pretty.install()

def parseLine(entry: str) -> str | None:
    splitted_line = entry.split(' ')
    
    time = splitted_line[0]
    cmd = splitted_line[1]
    object_id = splitted_line[2]
    
    if not 'DELETE' in cmd and not 'SET' in cmd:
        return f'{time} {object_id}'
    else:
        return None

def _processFile(input_path: Path, output_path: Path) -> None:
    with input_path.open(encoding='utf-8', errors='replace') as raw_file:
        lines_processed = 0
        lines_removed = 0
        with output_path.open('w') as output_file:
            line = raw_file.readline()
            while line:
                lines_processed += 1
                output_line = parseLine(line)
                if output_line != None:
                    output_file.write(f'{output_line}\n')
                else:
                    lines_removed += 1
                line = raw_file.readline()
        print(f"[green]Processed {lines_processed} lines ignoring [yellow]{lines_removed}")

                
def processFiles(files: List[Path], output_dir: Path):
    print(f'[bold yellow]Processing the files: [bold cyan]{[f.name for f in files]}\n')
    for file in files:
        output_path = output_dir / file.name
        if not output_path.exists():
            print(f'[orange]Start processing [purple]{file.name}')
            _processFile(file, output_path)

            print(f'[green]Done processing: [purple]{file.name}')
    print(f'[bold cyan]Done processing files\n\n')
    
    
def main():
    parser = argparse.ArgumentParser(description='Parse IBM Object Storage trace files')
    parser.add_argument('-i', '--input-dir', help='Input directory containing raw trace files', type=str, required=True)
    parser.add_argument('-o', '--output-dir', help='Output directory for parsed traces (default: <input-dir>/parsed_traces/IBMObjectStore)', type=str, default=None)

    args = parser.parse_args()

    input_dir = Path(args.input_dir)

    if args.output_dir is None:
        output_dir = input_dir / 'parsed_traces/IBMObjectStore'
    else:
        output_dir = Path(args.output_dir)

    print(f'Input dir: {str(input_dir.resolve())} Output dir: {str(output_dir.resolve())}')

    if not input_dir.exists():
        print(f'[bold red]Error: Input directory {input_dir} does not exist')
        return

    input_files_paths = [f for f in input_dir.iterdir()
                         if f.is_file()
                         and f.name.startswith('IBMObjectStore')]

    output_dir.mkdir(exist_ok=True, parents=True)

    processFiles(input_files_paths, output_dir)

     
if __name__ == '__main__':
    main()
