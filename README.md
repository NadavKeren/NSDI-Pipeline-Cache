# Adaptive Pipeline Cache

This repository contains the artifact for the paper **"Latency-Aware Caching with Delayed Hits: From Bursty Traffic to Pipeline Architectures"** accepted to NSDI '26.

## Table of Contents

- [Overview](#overview)
- [Repository Structure](#repository-structure)
- [System Requirements](#system-requirements)
- [Containers](#containers)
- [Running Containers](#running-containers)
- [Traces](#traces)
  - [Downloading Traces](#downloading-traces)
  - [Trace Processing Scripts](#trace-processing-scripts)
- [Experiments](#experiments)
  - [LHD / LRB Experiments](#lhd--lrb-experiments)
- [Graph Generation](#graph-generation)
- [Complete Workflow Example](#complete-workflow-example)
- [Additional Information](#additional-information)

## Overview

This artifact provides a complete experimental framework for evaluating cache eviction policies with latency awareness. The repository includes:

- **Trace processing scripts**: Tools to parse and prepare cache traces from IBM Object Storage, Meta KV, and Twitter datasets
- **Experiment runners**: Scripts to run cache simulations and evaluate different eviction policies
- **Pre-configured containers**: Docker/Podman containers with all dependencies installed
- **Cache simulator**: Based on a fork of [Caffeine's](https://github.com/ben-manes/caffeine) Java-based simulator

The artifact enables researchers to reproduce the results from the paper and run additional experiments with different cache policies and trace datasets.

We highly recommend to start with testing the IBM012 trace, since it is comparably short, and the tests for it are short. Longer traces such as the Twitter traces take up to a day to process.

It is also recommended to run multiple containers, each running a different set of the experiments. Running multiple scripts in parallel on the same container is ill-advised.

For the majority of the experiments, 2 cores and ~8GB of RAM will suffice, however, from our experiments, LRB demands more resources, tested on 4 cores in the paper.

## Repository Structure

```
NSDI-Pipeline-Cache/
├── experiments/          # Experiment execution scripts
├── trace_processing/     # Trace parsing and preparation tools
├── graph_generators/     # Visualization tools for experiment results
├── containers/           # Container definitions
└── conf.json            # Configuration file (see Configuration section)
```

### Code Repositories
The code used in this project is divided between the following repositories:
1. The implementation of the adaptive pipeline is available as [a fork of Caffeine](https://github.com/NadavKeren/caffeine).
2. LHD is available as a [fork](https://github.com/NadavKeren/LHD-tagged) of the original [LHD simulator](https://github.com/CMU-CORGI/LHD) provided by the authors of the paper ["LHD: Improving Cache Hit Rate by Maximizing Hit Density"](https://www.usenix.org/conference/nsdi18/presentation/beckmann).
3. LRB is available as a [fork](https://github.com/NadavKeren/lrb-tagged/tree/master) of the original [LRB simulator](https://github.com/sunnyszy/lrb), provided by the authors of the paper [Learning Relaxed Belady for Content Distribution Network Caching](https://www.usenix.org/conference/nsdi20/presentation/song).

## System Requirements

This code assumes:

* Any Linux distro (tested on Fedora 43)
- Python 3.14 or later
- Java 11 or later
- Required Python libraries: `rich`, `pandas`, `pyhocon`, `xxhash`, `polars`, `matplotlib`, `numpy`

We highly recommend to use the included containers for your convenience, which require:

- Docker or Podman installed
- Sufficient disk space (~5 GB per container)
- Local directories for traces and results
## Containers

We provide two pre-built containers available on Docker Hub:

### 1. General Experiments Container
- **Base image**: Fedora 43
- **Purpose**: Running most cache policy experiments using the Caffeine simulator. 

### 2. LHD/LRB Container
- **Base image**: Ubuntu 18.04
- **Purpose**: Running experiments with LHD and LRB algorithms; These algorithms use legacy codebases that require older system libraries.

**Note**: Containers are optimized for functionality, not size. Download size is approximately 5 GB.

## Running Containers

Both containers require two mounted directories:
1. `/home/traces`: Input trace files
   - For LHD/LRB container: traces must be in `/home/traces/latency/LRB`
   - For general container: traces should be xz-compressed in `/home/traces/latency`
2. `/home/results`: Output directory for experiment results

### General Experiments Container

**Using Podman:**
```bash
podman run -it --name nsdi-experiments \
  -v /path/to/traces:/home/traces:z \
  -v /path/to/results:/home/results:z \
  docker.io/nadavker/adaptive-pipeline-test-container:v1
```

**Using Docker:**
```bash
docker run -it --name nsdi-experiments \
  -v /path/to/traces:/home/traces \
  -v /path/to/results:/home/results \
  docker.io/nadavker/adaptive-pipeline-test-container:v1
```

### LHD/LRB Container

**Using Podman:**
```bash
podman run -it --name nsdi-lhd-lrb \
  -v /path/to/traces:/home/traces:z \
  -v /path/to/results:/home/results:z \
  docker.io/nadavker/adaptive-pipeline-lhd-lrb-container:v1
```

**Using Docker:**
```bash
docker run -it --name nsdi-lhd-lrb \
  -v /path/to/traces:/home/traces \
  -v /path/to/results:/home/results \
  docker.io/nadavker/adaptive-pipeline-lhd-lrb-container:v1
```

# Traces
## Downloading Traces

The experiments require cache traces from three sources:

### 1. IBM Object Storage Traces
- **Source**: [SNIA I/O Traces](https://iotta.snia.org/traces/key-value)
- **Required traces**: 010, 012, 024, 029, 031, 034, 045
- **Download**: Manual download required from SNIA website

### 2. Twitter Memcached Traces
- **Source**: [SNIA I/O Traces](https://iotta.snia.org/traces/key-value)
- **Required clusters**: 1, 3, 9, 28
- **Download**: Manual download required from SNIA website
- **Note**: Full Twitter dataset is ~2.8 TB compressed, 14 TB uncompressed

### 3. Meta KV Traces
- **Source**: [Meta Cache Dataset on S3](https://github.com/cacheMon/cache_dataset)
- **Required**: metakv2 and metakv4
- **Download**: Available via S3 (containers include download aliases)

These traces were last accessed in December 2025.

## Trace Processing Scripts

All trace processing scripts are located in the `trace_processing/` directory. They follow a standardized interface:
- `-i, --input-file`: Path to a single input trace file
- `-o, --output-path`: Output directory (filenames are auto-generated)

The output of these traces are space-separated values of the format `timestamp key`, one line for each operation.
### parse_IBM.py

Parses IBM Object Storage traces, filtering for GET operations only.

**Usage:**
```bash
cd trace_processing
python parse_IBM.py -i /path/to/IBMObjectStoreTrace010Part0 -o /path/to/output
```

**Input file name**: `IBMObjectStoreTraceXXXPart0` (e.g., IBMObjectStoreTrace010Part0)
**Output file name**: `IBMXXX.trace` (e.g., IBM010.trace)

### parse_twitter.py

Parses Twitter memcached traces, filtering for GET/GETS operations.

**Usage:**
```bash
python parse_twitter.py -i /path/to/cluster01.csv -o /path/to/output 
```

**Input file name**: `clusterXX...` (e.g., cluster01, cluster28)
**Output file name**: `twitterXX.trace` (e.g., twitter01.trace)

**Note**: This script automatically limits traces to 200M requests or 10 hours, whichever comes first.
### parse_meta.py

Parses Meta KV traces, extracting GET operations.

**Usage:**
```bash
python parse_meta.py -i /path/to/metakv2-data.csv -o /path/to/output
```

**Input file name**:
- `metakvX-...` (X is 2 or 4)
- `202210_kv_...` (treated as metakv2)
- `202401_kv_...` (treated as metakv4)
**Output file name**: `metakvX.trace` (e.g., metakv2.trace, metakv4.trace)

### latency_appender.py

Adds synthetic latency values to parsed traces, creating the final format for experiments. Latency distributions are specified via a JSON configuration file.

**Usage:**
```bash
python latency_appender.py -i /path/to/parsed -o /path/to/output -d /path/to/config.json [-c] [-v]
```

**Input**: Parsed trace files (format: `timestamp key`)
**Output**: Latency-augmented traces (format: `timestamp key miss_penalty`)

**Options**:
- `-i, --input-dir`: Directory containing parsed trace files
- `-o, --output-dir`: Output directory for latency-augmented traces
- `-d, --distribution-config`: Path to JSON configuration file (required)
- `-c, --compress`: Compress output files with xz
- `-v, --verbose`: Show detailed progress information

#### Latency Distribution Configuration

The latency distribution configuration is specified in a JSON file. The default configuration used in the paper is available in `trace_processing/latency_distributions.json`.

**Configuration Format:**

The configuration file contains a list of distribution sets. Each set defines:
- **generators**: A list of latency distribution generators
- **weights**: Integer weights determining how keys are distributed across generators (higher weight = more keys)

**Available Distribution Types:**

1. **Normal Distribution** - Gaussian distribution with mean and standard deviation
   ```json
   {
     "type": "normal",
     "mean": 120,
     "std_dev": 12.16
   }
   ```

2. **Uniform Distribution** - Uniform distribution between low and high values
   ```json
   {
     "type": "uniform",
     "low": 100,
     "high": 300
   }
   ```

3. **Multiple Peaks Distribution** - Discrete distribution with specific values and probabilities
   ```json
   {
     "type": "multiplepeaks",
     "values": [50, 100, 200, 500],
     "probs": [0.25, 0.25, 0.25, 0.25]
   }
   ```

4. **Single Value Distribution** - Constant value (no randomness)
   ```json
   {
     "type": "single",
     "value": 150
   }
   ```

**Example Configuration:**

```json
{
  "distributions": [
    {
      "generators": [
        {
          "type": "normal",
          "mean": 120,
          "std_dev": 12.16
        },
        {
          "type": "normal",
          "mean": 340,
          "std_dev": 14
        },
        {
          "type": "normal",
          "mean": 675,
          "std_dev": 15.2
        }
      ],
      "weights": [34, 33, 33]
    }
  ]
}
```

This configuration creates three normal distributions with weights [34, 33, 33], meaning approximately 34% of keys will use the first distribution, 33% the second, and 33% the third.

### trace_merger.py

Combines multiple traces into a single merged trace, useful for creating complex workloads.

**Usage:**
```bash
python trace_merger.py --input-dir /path/to/traces \
  --trace trace1.trace \
  --trace trace2.trace --times 5 \
  --trace trace3.trace
```


**Options**:
- `--input-dir`: Directory containing input trace files
- `--trace NAME`: Add trace to merge sequence
- `--times N`: Repeat the previous trace N times (default: 1)

**Behavior**: Traces are merged sequentially with timestamps adjusted to maintain continuity.
The example above concatenates trace1 once, followed by trace2 5 times, and finally trace3. 
This can create any combination of any number of traces and times.

# Experiments

All experiment scripts are located in the `experiments/` directory.
While the majority of the experiments are handled by the `run_experiemnts.py` script, we divide the experiments of LHD and LRB from the rest due to the complexity of the implementation of these experiments. These require additional steps in order to yield the results that include delayed hits and average request latency.
We also provide additional scripts (detailed below) for testing the synthetic workload.
## LHD / LRB Experiments

### convert_to_LRB_LHD.py

Converts traces to LRB (Learning Relaxed Belady) / LHD (Least Hit Density) format for compatibility with the LRB/LHD simulators.

**Usage:**
```bash
python convert_to_LRB_LHD.py -i /path/to/traces
```

**Input**: Directory containing the traces (format: `timestamp key`)
**Output**: LRB-formatted traces with `-LRB.trace` appended to the input file name.
**Output format**: `timestamp key_as_int64 1` (as required by the LHD and LRB simulators).
### run_lhd_lrb.py

Runs both LHD and LRB algorithms on a trace to generate operation result dump files, that is, whether an operation was considered a hit or miss by the LHD or LRB simulators. This script must be run inside the LHD/LRB container.

**Usage (inside LHD/LRB container):**
```bash
python /home/run_lhd_lrb.py --trace-name <trace-name> --trace-file /home/traces/LRB/<trace-file>
```

**Required Arguments**:
- `--trace-name`: Name of the trace (must match predefined names: trace010, trace012, trace024, trace029, trace031, trace034, trace045, twitter01, twitter03, twitter09, twitter28, metakv2, metakv4)
- `--trace-file`: Path to the trace file in LRB format (must be in `/home/traces/LRB/` directory)

**Output**: Two dump files in `/home/results/`:
- `LHD-<trace-name>.dump`: LHD algorithm predictions (format: `timestamp key is_hit`)
- `LRB-<trace-name>.dump`: LRB algorithm predictions (format: `timestamp key is_hit`)

**Behavior**:
- Automatically uses predefined cache sizes for each trace
- Runs both algorithms sequentially
- Moves dump files to `/home/results/` directory

**Note**: The trace file must be in LRB format (generated by `convert_to_LRB_LHD.py`).

### mark_existing_trace.py

Combines a latency-augmented trace with LHD/LRB operation result dump files to create a final trace with hit/miss information to be ran with the mock policy to yield the average request latency, including the calculation of delayed hits (not present at the LHD and LRB simulators).

**Usage:**
```bash
python mark_existing_trace.py \
  --trace_file /path/to/trace-with-latency.trace \
  --marked_file /path/to/LHD-trace.dump \
  --output /path/to/output-marked.trace
```

**Required Arguments**:
- `-t, --trace_file`: Path to latency-augmented trace file (format: `timestamp key miss_penalty`)
- `-m, --marked_file`: Path to LHD/LRB dump file (format: `timestamp key is_hit`)
- `-o, --output`: Path for output file

**Input Formats**:
- Trace file: `timestamp key miss_penalty` (from `latency_appender.py`)
- Marked file: `timestamp key is_hit` (from `run_lhd_lrb.py`)

**Output Format**: `timestamp key miss_penalty is_hit`

**Example Workflow**:
```bash
# Step 1: Convert trace to LRB format
python convert_to_LRB_LHD.py -i /path/to/traces

# Step 2: Run LHD/LRB in container (produces dump files)
python /home/run_lhd_lrb.py --trace-name trace010 --trace-file /home/traces/LRB/trace010-LRB.trace

# Step 3: Mark the original latency trace with predictions
python mark_existing_trace.py \
  --trace_file trace010-with-latency.trace \
  --marked_file /home/results/LHD-trace010.dump \
  --output trace010-final.trace
```

### run_experiments.py

Main experiment runner for evaluating cache policies on trace workloads.

**Usage:**
```bash
cd experiments
python run_experiments.py --input <trace-file> [options]
```

**Required Arguments**:
- `--input PATH`: Path to input trace file (must be xz-compressed for Caffeine experiments)

**General Options**:
- `--trace-name NAME`: Override trace name (default: auto-detected from filename)
- `--cache-size SIZE`: Cache size in entries (default: predefined per trace)
- `--rounds N`: Number of experimental rounds for sampled policies
- `--round-index-start N`: Starting index for round numbering (default: 0)

**Experiment Types** (select one or more):
- `--run-base`: Baseline policies (FGHC, LA-LRU, LA-LFU, LBU)
- `--run-all-shc`: Sampled Hill Climber with multiple sampling rates
- `--run-single-shc`: Sampled Hill Climber with single sampling rate
- `--run-aca`: Adaptive Cost-Aware Window-TinyLFU
- `--run-grid-search`: Static configuration grid search across parameter space
- `--run-other`: Comparison algorithms (Hyperbolic, GDWheel, ARC, FRD, LA-Cache, S3-FIFO, SIEVE)

**Example**:
```bash
python run_experiments.py \
  --input /home/traces/latency/IBM010.trace.xz \
  --trace-name trace010 \
  --run-base \
  --rounds 10 \
  --run-all-shc
```

**Output**: CSV files in the configured results directory containing hit rates, average penalties, and other metrics.

**Pre-defined Cache Sizes** (in `run_experiments.py`):
- trace010, trace024, trace029: 512 entries
- trace012: 1024 entries
- trace045: 4096 entries
- trace034: 16384 entries
- trace031: 65536 entries
- twitter01: 1024 entries 
- twitter03: 1024 entries
- twitter09: 4096 entries
- twitter28: 4096 entries
- metakv2: 8192 entries
- metakv4: 8192 entries

### run_mock_experiments.py

This script evaluates the performance, including delayed hits, of LHD and LRB algorithms by replaying their operation results using a mock policy in the Caffeine simulator.

**Usage:**
```bash
cd experiments
python run_mock_experiments.py --input <marked-trace-file> [options]
```

**Required Arguments**:
- `--input PATH`: Path to marked trace file (output from `mark_existing_trace.py`)

**Optional Arguments**:
- `--trace-name NAME`: Override trace name (default: auto-detected from filename)
- `--cache-size SIZE`: Cache size in entries (default: predefined per trace)
- `--trace-folder FOLDER`: Trace folder within resources directory (default: `latency`)
- `--algorithm-name NAME`: Name to use for output files (default: `mock`)

**Input Format**: `timestamp key miss_penalty is_hit` (output from `mark_existing_trace.py`)

**Output**: CSV file in the configured results directory with the format `<algorithm-name>-<trace-name>.csv`

**Example**:
```bash
# After marking a trace with LHD predictions
python run_mock_experiments.py \
  --input /home/traces/latency/trace010-marked-LHD.trace \
  --trace-name trace010 \
  --algorithm-name LHD

# After marking a trace with LRB predictions
python run_mock_experiments.py \
  --input /home/traces/latency/trace010-marked-LRB.trace \
  --trace-name trace010 \
  --algorithm-name LRB
```

**Complete Workflow for LHD/LRB Evaluation**:
```bash
# Step 1: Parse and add latency to traces
python trace_processing/parse_IBM.py -i IBMObjectStoreTrace010Part0 -o parsed/
python trace_processing/latency_appender.py -i parsed/ -o latency/ -d latency_distributions.json -c

# Step 2: Convert to LRB format
python trace_processing/convert_to_LRB_LHD.py -i latency/

# Step 3: Run LHD/LRB in container (produces dump files)
python /home/run_lhd_lrb.py --trace-name trace010 --trace-file /home/traces/LRB/trace010-LRB.trace

# Step 4: Mark traces with LHD/LRB predictions
python trace_processing/mark_existing_trace.py \
  --trace_file latency/trace010.trace \
  --marked_file /home/results/LHD-trace010.dump \
  --output latency/trace010-marked-LHD.trace

python trace_processing/mark_existing_trace.py \
  --trace_file latency/trace010.trace \
  --marked_file /home/results/LRB-trace010.dump \
  --output latency/trace010-marked-LRB.trace

# Step 5: Run mock experiments to evaluate predictions
python experiments/run_mock_experiments.py \
  --input trace010-marked-LHD.trace \
  --algorithm-name LHD

python experiments/run_mock_experiments.py \
  --input trace010-marked-LRB.trace \
  --algorithm-name LRB
```

**Note**: The script uses the `LATENCY_RESULT` trace format which expects the `is_hit` field from marked traces.

### run_synthetic_experiments.py

Generates synthetic traces and runs comprehensive experiments to evaluate LRU, LFU, and LBU algorithms on different traffic patterns (Recency, Frequency, Burstiness). Produces a 3x3 table showing average latency for each algorithm/traffic combination.

**Usage:**
```bash
cd experiments
python run_synthetic_experiments.py --cache-size <size> [--seed N]
```

**Required Arguments**:
- `--cache-size SIZE`: Cache size in entries

**Optional Arguments**:
- `--seed N`: Random seed for trace generation (default: random, for reproducibility use a fixed seed)

**Configuration**: Uses `synthetic_trace_config.json` for all traffic parameters. Modify this file to change trace characteristics.

**What the Script Does**:

1. **Generates Synthetic Trace**:
   - Creates traffic with three distinct patterns (configurable):
     - **Recency**: Items accessed in short temporal windows (default: 250,000)
     - **Frequency**: Items accessed repeatedly throughout the trace (default: 100)
     - **Burstiness**: Items accessed in intense bursts (default: 100)
   - Includes one-hit-wonders as noise (default: 150,000)

2. **Runs Three Pipeline Experiments**:
   - LRU* only pipeline
   - LFU* only pipeline
   - LBU only pipeline
   - Each generates a `.results_dump` file with hit/miss predictions

3. **Splits Results by Traffic Type**:
   - Separates each dump file into three parts based on key ranges:
     - Recency items (default keys 0-249,999)
     - Frequency items (default keys 250,000-250,099)
     - Burstiness items (default keys 250,100-250,199)

4. **Runs Mock Experiments**:
   - Evaluates each algorithm's predictions on each traffic type (9 combinations)
   - Uses the mock policy to replay predictions

5. **Generates 3x3 Results Table**:
   - Displays average latency for each algorithm/traffic combination
   - Saves results to `synthetic_3x3_results.csv`

**Output**:
- Console table showing 3x3 matrix of results
- CSV file: `results/synthetic_3x3_results.csv`
- Intermediate files in `results/splits/`

**Example**:
```bash
# Run experiments with random seed
python run_synthetic_experiments.py --cache-size 1024

# Run experiments with specific seed for reproducibility
python run_synthetic_experiments.py --cache-size 1024 --seed 42
```

**Example Output Table**:
```
           Average Latency Results
┏━━━━━━━━━━━━━┳━━━━━━━━━┳━━━━━━━━━━━┳━━━━━━━━━━━━┓
┃ Algorithm / ┃ Recency ┃ Frequency ┃ Burstiness ┃
┃ Traffic     ┃         ┃           ┃            ┃
┡━━━━━━━━━━━━━╇━━━━━━━━━╇━━━━━━━━━━━╇━━━━━━━━━━━━┩
│ LRU         │     150 │       850 │        900 │
│ LFU         │     950 │       120 │        880 │
│ LBU         │     920 │       870 │        110 │
└─────────────┴─────────┴───────────┴────────────┘
```

This table helps identify which algorithm performs best for each traffic pattern.

### synthetic_trace_gen.py

Generates synthetic cache traces with controlled traffic patterns for evaluating cache algorithms.

**Usage:**
```bash
cd experiments
python synthetic_trace_gen.py --gen-new-trace [--seed N]
```

**Options**:
- `--gen-new-trace`: Generate a new synthetic trace file
- `--gen-example`: Generate a visualization of traffic patterns (PDF)
- `--seed N`: Random seed for reproducible generation

**Traffic Patterns Generated** (configurable via `synthetic_trace_config.json`):
- **Recency Items** (default: 250,000): Items accessed in temporal clusters with gaps
- **Frequency Items** (default: 100): Items accessed consistently throughout the trace
- **Burstiness Items** (default: 100): Items accessed in intense bursts separated by long gaps
- **One-Hit-Wonders** (default: 150,000): Items accessed exactly once (noise)

**Output**: `synthetic.trace` with format `timestamp key hit_penalty miss_penalty`

**Configuration File**: The file `experiments/synthetic_trace_config.json` allows reconfiguration of the density of requests for each of the traffic types, the amount of items corresponding to each traffic type, and the length of the trace.

**Example**:
```bash
# Generate trace with random seed
python synthetic_trace_gen.py --gen-new-trace

# Generate trace with specific seed for reproducibility
python synthetic_trace_gen.py --gen-new-trace --seed 12345

# Generate visualization
python synthetic_trace_gen.py --gen-example
```

### simulatools.py

Low-level interface to the ***Caffeine simulator*** created by Ohad Eytan, the original version is available [here](https://github.com/ohadeytan/simulatools). This module is used by `run_experiments.py` and typically not invoked directly.

This file contains the function `single_run` which creates the configuration file for the Caffeine simulator, runs it, processes the output file and puts it in the `results` directory configured in the `conf.json` file.

This allows running many types of simulations that are available in this simulator, include those not included in the paper.

**Notice**: The majority of the policies available in the simulator are not latency-aware, and any experiment requires editing the policies to properly report the relevant results.

### policies.py

Enumeration of available cache policies with mappings to Java implementation classes.

## Graph Generation

This directory holds the graph generator for the "Under The Hood" section of the paper.

### adaptation_graph_gen.py

Generates visualization graphs showing how the adaptive pipeline cache adjusts its quanta allocation over time.

**Usage:**
```bash
cd graph_generators
python adaptation_graph_gen.py -i <dump-file> -o <output-directory>
```

**Arguments**:
- `-i, --input`: Path to the quanta dump file generated by the adaptive pipeline cache in the simulator.
- `-o, --output_dir`: Directory where output PDFs will be saved
- `--parts-length`: Allows changing the marks positions in the plots by defining how many operations are in each part (that is, the end of a trace in the merged/concatenated trace defined above). Defaults to the part lengths of the concatenated trace presented in the paper, that is, IBM24, IBM10, IBM12×10, IBM24.
  The part lengths are in ***number of requests***.

**Output**: Two PDF graphs are generated:
1. **Adaptation Graph** (`<input-name>-Adaption-prop.pdf`):
   Stacked area chart showing percentage of cache capacity allocated to each block (LRU, LFU, LBU) as a function of the request id.

2. **Average Latency Graph** (`<input-name>-Avg-latency.pdf`):
   Line plot of Average Request Latency (ARL) over time.

**Example**:
```bash
# Generate graphs with part lengths for the concat trace in the paper
python adaptation_graph_gen.py \
  -i /home/results/concat.quota_dump \
  -o /home/results/graphs/

# Generate graphs with custom part lengths
python adaptation_graph_gen.py \
  -i /home/results/adaptive-trace010.quota_dump \
  -o /home/results/graphs/ \
  --parts-length 40 30 100 140
```

## Complete Workflow Example

Here's a complete workflow from downloading traces to running experiments:

### 1. Download and Parse Traces

Download the the trace from source (in this example, IBM010 from SNIA).

```bash
cd trace_processing

python parse_IBM.py \
  -i /downloads/IBMObjectStoreTrace010Part0 \
  -o ./parsed_traces

python latency_appender.py \
  -i ./parsed_traces \
  -o ./latency_traces \
  -c -v
```

### 2. Configure Experiments

Create `experiments/conf.json`:
```json
{
  "caffeine_root": "/home/user/caffeine",
  "resources": "/home/user/traces",
  "output": "",
  "results": "/home/user/results"
}
```

### 3. Run Experiments

```bash
cd experiments

python run_experiments.py \
  --input /home/user/traces/latency/IBM010.trace.xz \
  --trace-name trace010 \
  --cache-size 512 \
  --run-base \
  --run-aca \
  --run-single-shc \
  --rounds 5 \
  --round-start-index 0 \
  --run-other
```

### 4. Analyze Results

Results are saved as CSV files in the configured results directory.

## Additional Information

All code is available on GitHub and containers are available on Docker Hub.
