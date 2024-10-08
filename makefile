install: ensure_uv
	# install requirements
	uv pip install -e '.[test,lint,dev,docs,mypy]' --config-settings editable_mode=compat

	# enable pre-commit
	pre-commit install

	# ensure required folder structure
	mkdir -p ./profiles

	# gather eggs
	rm -rf ./eggs
	scrambler --target eggs

update: ensure_uv
	# update all dependencies
	uv pip compile setup.cfg -U --all-extras | uv pip install -U -r /dev/stdin

	# update the pre-commit hooks
	pre-commit autoupdate

	# apply install step to avoid deviations
	make install

ensure_uv: in_virtual_env
	@if which uv; then true; else pip install uv; fi

	# use latest uv
	uv pip install --upgrade uv

in_virtual_env:
	@if python -c 'import sys; (hasattr(sys, "real_prefix") or (hasattr(sys, "base_prefix") and sys.base_prefix != sys.prefix)) and sys.exit(1) or sys.exit(0)'; then \
		echo "An active virtual environment is required"; exit 1; \
		else true; fi
