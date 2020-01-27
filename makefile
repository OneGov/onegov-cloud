install: in_virtual_env
	# use latest pip
	pip install --upgrade pip

	# install requirements
	pip install -e '.[test,dev,docs]' --upgrade-strategy=eager

	# ensure required folder structure
	mkdir -p ./profiles

	# gather eggs
	rm -rf ./eggs
	scrambler --target eggs

update: in_virtual_env

	# update all dependencies
	pip list --outdated --format=freeze |  sed 's/==/>/g' | pip install --upgrade -r /dev/stdin

	# force update the latest honyaku release
	pip install git+https://github.com/seantis/honyaku#egg=honyaku --force

	# apply install step to avoid deviations
	make install

in_virtual_env:
	@if python -c 'import sys; (hasattr(sys, "real_prefix") or (hasattr(sys, "base_prefix") and sys.base_prefix != sys.prefix)) and sys.exit(1) or sys.exit(0)'; then \
		echo "An active virtual environment is required"; exit 1; \
		else true; fi
