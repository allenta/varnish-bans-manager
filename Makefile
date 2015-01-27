VBM_ROOT = $(abspath $(dir $(lastword $(MAKEFILE_LIST))))

sdist: build
	@echo
	@echo "> Creating Python source distribution package..."
	cd $(VBM_ROOT)/build; python setup.py sdist

	@echo
	@echo "> Source distribution package successfully generated in $(VBM_ROOT)/build/dist/"
	@echo

upload: build
	cd $(VBM_ROOT)/build; python setup.py register sdist upload

build: clone
	@echo
	@echo "> Compiling .po files..."
	python "$(VBM_ROOT)/build/varnish_bans_manager/runner.py" compilemessages

	@echo
	@echo "> Generating static media..."
	python "$(VBM_ROOT)/build/varnish_bans_manager/runner.py" generatemedia

	@echo
	@echo "> Cleaning up..."
	rm -rf "$(VBM_ROOT)/build/varnish_bans_manager/static"
	find "$(VBM_ROOT)/build" \
		-name "*.pyc" -o \
		-name "*.po" | xargs rm -f

clone: clean
	@echo
	@echo "> Cloning VBM source files..."
	mkdir -p "$(VBM_ROOT)/build/"
	rsync -a --delete --delete-excluded \
		--exclude="build" --exclude="extras" \
		--exclude="Makefile" --exclude="DEVELOPERS.rst" \
		--exclude="vbm.sublime-project" --exclude="vbm.sublime-workspace" \
		--exclude="sftp-config.json" \
		"$(VBM_ROOT)/" "$(VBM_ROOT)/build/"

clean:
	rm -rf "$(VBM_ROOT)/build/"
	find "$(VBM_ROOT)" -name "*.pyc" -o -name "*.mo" | xargs rm -f
