.PHONY: install test lint format update-data backtest clean

install:
	pip install -e ".[dev,ml,live]"

test:
	pytest tests/ -v --cov=core --cov=adapters --cov=strategies

lint:
	black --check .
	isort --check-only .

format:
	black .
	isort .

update-data:
	python run.py data update

backtest:
	python scripts/run_backtest.py

clean:
	find . -type d -name "__pycache__" -exec rm -rf {} +
	find . -type f -name "*.pyc" -delete
	rm -rf .pytest_cache .coverage htmlcov
