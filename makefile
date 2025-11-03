install: ensure_uv
	# install all dependencies
	uv pip compile setup.cfg --all-extras | uv pip install -r /dev/stdin

	# install source in editable mode
	uv pip install -e . --config-settings editable_mode=compat

	# enable pre-commit
	pre-commit install

	# ensure required folder structure
	mkdir -p ./profiles

	# gather eggs
	rm -rf ./eggs
	scrambler --target eggs

lint: ensure_uv
	# Run linters in parallel with proper cleanup on exit/interrupt
	@set -e; \
	cleanup() { \
		pkill -P $$ 2>/dev/null || true; \
		kill $$(jobs -p) 2>/dev/null || true; \
		pkill -f "mypy\|ruff\|bandit\|flake8" 2>/dev/null || true; \
		exit 130; \
	}; \
	trap cleanup INT TERM; \
	bash ./mypy.sh & \
	ruff check src/ tests/ stubs/ & \
	bandit \
		--quiet \
		--recursive \
		--configfile pyproject.toml \
		src/ 2> /dev/null & \
	flake8 \
		src/ & \
	wait

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
