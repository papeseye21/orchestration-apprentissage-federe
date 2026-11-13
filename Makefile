.PHONY: all install test experiment approfondissement figures clean

all: install experiment approfondissement figures test

install:
	python3 -m pip install -r requirements.txt

experiment:
	python3 experiment.py

approfondissement:
	python3 approfondissement.py

figures:
	python3 plot_figures.py

test:
	python3 -m pytest -q

clean:
	rm -f resultats.csv resultats_bruts.csv \
	      resultats_approfondissement.csv resultats_approfondissement_bruts.csv
	rm -rf figures __pycache__ .pytest_cache tests/__pycache__
