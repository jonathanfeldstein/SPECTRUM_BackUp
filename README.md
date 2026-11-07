# SPECTRUM

SPECTRUM is an optimized C++ rule mining algorithm that learns logical rules from knowledge graphs and relational databases. 

It works by first mining pattern fragments in the data and then using these fragments to compute a heuristic utility of candidate rules. Finally, candidate rules are then optimised and ranked so as to maximise the utility of the set of rules.

## Table of Contents
- [Dependencies](#dependencies)
- [Building the Project](#building-the-project)
- [How to Run](#how-to-run)
- [Source Code Overview](#source-code-overview)
- [Reproducing Ablation Studies](#reproducing-ablation-studies)

## Dependencies

To run the pre-built executables the only requirements are:
- **OS**: A Linux environment 
- **OpenMP**: Required for multi-threading and parallelization.
- **Python 3.x**: (If you with to run ablation scripts).

If you wish to make modifications or build from scratch you will also need:

- **C++ Compiler**: A compiler supporting C++20 (e.g., GCC 10+ or Clang 10+).
- **CMake**: Version 3.16 or higher.
- **Bundled Libraries**: The following libraries are included in the `dependencies/` directory and are automatically linked during the build process:
  - Boost (1.83.0)
  - Eigen (3.4.0)
  - Spectra (1.0.1)

## Building the Project

Run

```bash
./build.sh
```

This will create a `build/` directory containing the compiled binaries, specifically:
- `SPECTRUM`: The standard pattern mining executable.
- `SPECTRUM_RW`: A variant of SPECTRUM where the pattern mining algorithm is replaced with a random-walk based one (as we show in the ablation studies, this is a strictly worse algorithm).

## Running SPECTRUM

The command line arguments are as follows:

```bash
./build/SPECTRUM <config_file.json> <M> <epsilon>
```

where `<config_file.json>` is the path to the configuration file, `<M>` is the number of candidate rules to consider (SPECTRUM selects an optimised subset of the `M` rules with highest heuristic utility), `<epsilon>` is permitted upper bound on theuncertainty in rule utility (smaller epsilon requires more computation).

For example, to run an experiment on WebKB with parameters M=200 and epsilon=0.01 you can run:

```bash
./build/SPECTRUM exp/configs/config_webkb.json 200 0.01
```

Pre-made configuration files for various datasets (like IMDB, WebKB, WN18RR) are located in the `exp/configs/` directory.

## Code Overview

- **`src/main.cpp`**: The main entry point for SPECTRUM.
- **`src/main_rw.cpp`**: The main entry point for the random-walk variant of SPECTRUM.
- **`src/HyperGraphs/`**: Contains the core data structures (`HyperGraph`, `Relation`) used to represent relational data and datasets in memory.
- **`src/Fragments/`**: Implements the logic for generating, storing, and managing rule fragments (both standard cyclic/acyclic and random-walk specific).
- **`src/CandidateRules/`**: Manages the construction, proposal, and validation of final candidate logical rules mined from the graph.
- **`src/Utils/`**: A collection of utility helpers for file I/O operations (`read_files_utils`), performance profiling (`profiling_utils`), and data structure helpers (`map_utils`, `set_utils`, `vector_utils`).

## Reproducing Ablation Studies

The project contains automated Python scripts to reproduce the ablation studies for `epsilon`, `M`, and Random Walk configurations. 

**1. Epsilon & M Ablation Study:**
```bash
python exp/ablation/epsilon_M_ablation/run_experiments.py
```

**2. Random Walk Ablation Study:**
```bash
python exp/ablation/random_walk_ablation/run_ablation.py
```