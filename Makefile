.PHONY: setup data index baseline rag eval test lint clean

setup:
	pip install -r requirements.txt && pip install -e .

data:
	python scripts/download_data.py --dataset aslg_pc12

index:
	python scripts/build_index.py --config configs/context_plus_rag.yaml

baseline:
	python scripts/run_experiment.py --config configs/baseline.yaml

rag:
	python scripts/run_experiment.py --config configs/rag_only.yaml

all-conditions:
	python scripts/run_experiment.py --config configs/baseline.yaml
	python scripts/run_experiment.py --config configs/rag_only.yaml
	python scripts/run_experiment.py --config configs/context_only.yaml
	python scripts/run_experiment.py --config configs/context_plus_rag.yaml

eval:
	python scripts/evaluate.py --results-dir results/ --out results/summary.csv

test:
	pytest -q

lint:
	ruff check src/ scripts/ tests/

clean:
	rm -rf data/interim/* data/processed/*
