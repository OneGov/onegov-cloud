DART_SASS_VERSION := 1.100.0

install: ensure_uv ensure_sass
	# install all dependencies
	uv pip compile setup.cfg --all-extras | uv pip install -r /dev/stdin

	# install source in editable mode
	uv pip install -e . --config-settings editable_mode=compat

	# enable pre-commit
	prek install -f

	# install chromium for playwright
	playwright install chromium

	# ensure required folder structure
	mkdir -p ./profiles

	# clean up old eggs folder if it still exists
	rm -rf ./eggs

update: ensure_uv
	# update all dependencies
	uv pip compile setup.cfg -U --all-extras | uv pip install -U -r /dev/stdin

	# update the pre-commit hooks
	prek autoupdate

	# apply install step to avoid deviations
	make install

ensure_sass: in_virtual_env
	@if which sass > /dev/null 2>&1; then true; else \
		if [ "$$(uname -s)" = "Darwin" ]; then \
			brew install sass/sass/sass; \
		else \
			echo "Installing Dart Sass $(DART_SASS_VERSION)..."; \
			ARCH=$$(uname -m); \
			if [ "$$ARCH" = "x86_64" ]; then ARCH="x64"; \
			elif [ "$$ARCH" = "aarch64" ]; then ARCH="arm64"; fi; \
			curl -sL "https://github.com/sass/dart-sass/releases/download/$(DART_SASS_VERSION)/dart-sass-$(DART_SASS_VERSION)-linux-$${ARCH}.tar.gz" \
				| tar xz -C /tmp; \
			mv /tmp/dart-sass "$$VIRTUAL_ENV/dart-sass"; \
			ln -sf "$$VIRTUAL_ENV/dart-sass/sass" "$$VIRTUAL_ENV/bin/sass"; \
			rm -rf /tmp/dart-sass; \
		fi; \
	fi

ensure_uv: in_virtual_env
	@if which uv; then true; else pip install uv; fi

	# use latest uv
	uv pip install --upgrade uv

in_virtual_env:
	@if python -c 'import sys; (hasattr(sys, "real_prefix") or (hasattr(sys, "base_prefix") and sys.base_prefix != sys.prefix)) and sys.exit(1) or sys.exit(0)'; then \
		echo "An active virtual environment is required"; exit 1; \
		else true; fi
