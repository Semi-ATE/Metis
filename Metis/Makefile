
all:

package: 
	cp debian/changelog debian/changelog.org
	cp debian/control debian/control.org
	@sed s/'__DATE_TIME__'/'$(shell date +"%a, %d %b %Y %T %z")'/ debian/changelog > debian/changelog.temp
	@sed s/'__VERSION__'/"$(shell cat ver)"/  debian/changelog.temp >  debian/changelog
	@sed s/'__ARCH__'/"$(shell cat arch)"/  debian/control >  debian/control.temp
	cp debian/control.temp debian/control
	debuild -i -us -uc -b
	mv debian/changelog.org debian/changelog
	mv debian/control.org debian/control

clean:
	rm -f *.so
	rm -f *.o
	rm -f *~ 
	rm -f stil_loader
	rm -rf debian/metis-server
	rm -rf debian/metis-server.debhelper.log
	rm -rf debian/metis-server.substvars
	rm -rf debian/.debhelper
	rm -rf debian/changelog.temp
	rm -rf debian/control.temp
	rm -rf debian/files
	rm -rf debian/*~
	
