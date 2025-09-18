PY := python3

.PHONY: help venv install dev package-cli package-ui clean

help:
	@echo "Targets:"
	@echo "  install        - pip install package (editable)"
	@echo "  dev            - install with LLM extras"
	@echo "  package-cli    - build single-file CLI binary via PyInstaller"
	@echo "  package-ui     - build single-file UI binary via PyInstaller"
	@echo "  clean          - remove build/ dist/ __pycache__/"

venv:
	@echo "Use your preferred venv; Makefile keeps things simple."

install:
	$(PY) -m pip install -e .

dev:
	$(PY) -m pip install -e .[llm]
	$(PY) -m pip install pyinstaller

package-cli:
	$(PY) -m PyInstaller --onefile -n turkify turkify/cli.py

package-ui:
	$(PY) -m PyInstaller --onefile -n turkify-ui turkify/__main__.py

clean:
	rm -rf build dist __pycache__ */__pycache__ .pytest_cache *.spec

