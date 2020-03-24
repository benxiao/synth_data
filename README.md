# Project Title
Generate synthetic data for kalinda application

## Getting Started

install conda

### Prerequisites

require python=3.8, if conda is available, we can create a new env by typing the following
```
conda create -n newpython python=3.8
conda activate newpython

```

### Installing
```
pip install -r requirements.txtGive the example
```

### Usages
##### create a golden synthetic dataset
```
python synth_data.py
```
##### create a sampled data source from the golden synthetic dataset
```
python sample_data.py edumaster -p 0.9 -d 0.4
```
p indicates the percent of the original golden set will be included, and d specifies
the duplication rate
##### add corruptions the sampled data source
```
python add_corruptions.py edumaster
```
