help:
	@echo "Possible targets:"
	@echo "    test           - runs the testsuite"
	@echo "    test-all       - runs the testsuite against all python versions"
	@echo "    doc            - builds the html documentation"
	@echo "    view-doc       - opens the documentation in your web browser"
	@echo "    upload-doc     - uploads the documentation to PyPI"
	@echo "    dev-env <DIR=> - creates a development environment"
	@echo "    clean          - deletes every generated file"
	@echo "    release        - performs the release"
	@echo "    coverage       - create coverage report"
	@echo "    view-coverage  - show HTML coverage report in your web browser"

test:
	@python runtests.py
	@PYTHONPATH=. python brownie/terminal

test-all:
	@tox

doc:
	@make -C docs/ html

view-doc: doc
	@python -c "import webbrowser; webbrowser.open('docs/_build/html/index.html')"

upload-doc: doc
	@python setup.py upload_docs --upload-dir=docs/_build/html

DIR ?= env
dev-env:
	@virtualenv $(DIR)
	@. $(DIR)/bin/activate && pip install -r requirements.txt

clean:
	@make -C docs/ clean > /dev/null
	@find . -iname "*.pyc" -delete
	@rm -rf .tox Brownie.egg-info dist

release: clean test upload-doc
	python setup.py release sdist upload

coverage:
	@coverage run runtests.py
	@coverage report
	@coverage html

view-coverage: coverage
	@python -c "import webbrowser; webbrowser.open('.coverage_html/index.html')"
