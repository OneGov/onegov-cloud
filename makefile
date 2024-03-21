install: in_virtual_env
	# use latest pip
	pip install --upgrade pip

	# install requirements
	pip install -e '.[test,dev,docs,mypy]' \
	--config-settings editable_mode=compat --upgrade-strategy=eager

	# enable pre-commit
	pre-commit install

	# ensure required folder structure
	mkdir -p ./profiles

	# gather eggs
	rm -rf ./eggs
	scrambler --target eggs

update: in_virtual_env

	# update all dependencies, but make sure we take setup.cfg into account
	pip list --outdated --format=json | jq --raw-output '.[].name' \
	| pip install -U -r /dev/stdin -e .[test,dev,docs,mypy]

	# force update the latest honyaku release
	pip install git+https://github.com/seantis/honyaku#egg=honyaku --force

	# update the pre-commit hooks
	pre-commit autoupdate

	# apply install step to avoid deviations
	make install

in_virtual_env:
	@if python -c 'import sys; (hasattr(sys, "real_prefix") or (hasattr(sys, "base_prefix") and sys.base_prefix != sys.prefix)) and sys.exit(1) or sys.exit(0)'; then \
		echo "An active virtual environment is required"; exit 1; \
		else true; fi
