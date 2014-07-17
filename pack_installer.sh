mkdir uninstalled_content
cp alignreads.py default_configuration.py makeconsensus.py README.txt LICENSE readtools_exceptions.py readtools.py runyasra.py uninstalled_content
mkdir alignreads_$1
tar -cf	uninstalled_content.tar	uninstalled_content
cp install.py README.txt INSTALL.txt uninstalled_content.tar alignreads_$1
rm -rf uninstalled_content.tar uninstalled_content
tar -zcf alignreads_$1.tar.gz alignreads_$1
rm -rf alignreads_$1
