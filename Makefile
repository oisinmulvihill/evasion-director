VERSION=director-1.0.0

exe:
	bb-freeze scripts/director
	bb-freeze scripts/morbidsvr
	bb-freeze scripts/shutdowndirector
	mv dist ${VERSION}

	
clean:
	rm -rf dist	
	rm -rf ${VERSION}
	

# Install the exe maker:	
setup:
	easy_install -ZU bbfreeze
