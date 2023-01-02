# ----------------------------------
#          INSTALL & TEST
# ----------------------------------
install:
	@pip install -r requirements.txt

check:
	@flake8 src/numerai_signals/*.py
	@flake8 src/numerai_signals/module/*.py
	@flake8 src/numerai_signals/util/*.py

black:
	@black src/numerai_signals/*.py
	@black src/numerai_signals/module/*.py
	@black src/numerai_signals/util/*.py

test:
	@coverage run -m pytest -v
	@coverage report -m

clean:
	@rm -f */version.txt
	@rm -f .coverage
	@rm -fr */__pycache__ */*.pyc __pycache__
	@rm -fr build dist
	@rm -fr numerai_signals-*.dist-info
	@rm -fr numerai_signals.egg-info

copy:
	@find docker/load -type f -not -name 'Dockerfile' -delete
	@find docker/transform -type f -not -name 'Dockerfile' -delete
	@find docker/ubuntu -type f -not -name 'Dockerfile' -delete

	@cp requirements.txt docker/load
	@cp -r src docker/load
	@cp -r data docker/load
	@cp load.sh docker/load

	@cp requirements.txt docker/transform
	@cp -r src docker/transform
	@cp -r data docker/transform
	@cp transform.sh docker/transform

	@sh -c 'rm -f docker/*/*/*/*.csv'
	@sh -c 'rm -f docker/*/*/*/log*'

	@cp requirements.txt docker/ubuntu

success:
	@echo 'Build complete'

all: clean install test black check copy success

count_lines:
#	@find ./ -name '*.py' -exec  wc -l {} \; | sort -n| awk \
#        '{printf "%4s %s\n", $$1, $$2}{s+=$$0}END{print s}'
	@echo ''
	@find ./src -name '*.py' -exec  wc -l {} \; | sort -n| awk \
				'{printf "%4s %s\n", $$1, $$2}{s+=$$0}END{print s}'
	@echo ''
	@find ./test -name '*.py' -exec  wc -l {} \; | sort -n| awk \
		'{printf "%4s %s\n", $$1, $$2}{s+=$$0}END{print s}'
	@echo ''

# # ----------------------------------
# #      UPLOAD PACKAGE TO PYPI
# # ----------------------------------
# PYPI_USERNAME=<AUTHOR>
# build:
# 	@python setup.py sdist bdist_wheel

# pypi_test:
# 	@twine upload -r testpypi dist/* -u $(PYPI_USERNAME)

# pypi:
# 	@twine upload dist/* -u $(PYPI_USERNAME)
