VERSION=${PROJECT_SRC_DIR}/director-1.0.0
ROOT=${PROJECT_SRC_DIR}


exe:
	mkdir -p ${VERSION}
	
	# Build the latest FDSDrivers and copy into build dir:
	cd ${ROOT}/FDSDrivers
	python setup.py bdist_egg
	cp ${ROOT}/FDSDrivers/dist/fdsdrivers-1.0.0-py2.6.egg ${VERSION}

	# Now build exe's:
	bb-freeze scripts/director scripts/morbidsvr scripts/shutdowndirector
	cp -r dist/* ${VERSION}
	

	
clean:
	rm -rf dist	
	rm -rf ${VERSION}
	

# Install the exe maker:	
setup:
	easy_install -ZU bbfreeze
