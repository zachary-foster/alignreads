mkdir uninstalled_content
cp alignreads.py default_configuration.py makeconsensus.py README.txt LICENSE readtools_exceptions.py readtools.py runyasra.py uninstalled_content
mkdir alignreads_$1
tar -cf	uninstalled_content.tar	uninstalled_content
cp install.py uninstalled_content.tar alignreads_$1
rm -rf uninstalled_content.tar uninstalled_content
tar -cf alignreads_$1.tar alignreads_$1
rm -rf alignreads_$1
