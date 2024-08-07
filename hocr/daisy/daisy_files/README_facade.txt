The files in 'facade/' are the 'facade book' that is played when
a protected daisy is played on a device that doesn't have the
appropriate decryption key.

facade.xml (in this dir) is the source 'dtbook xml' file.

To rebuild the book files from the source xml, download the DAISY
Pipeline from http://daisymfc.sourceforge.net/ (get 'Core Binaries')
then execute something like the following from the top level pipeline
directory:

sh pipeline.sh scripts/create_distribute/dtb/DTBookToDaisy3TextOnlyDTB.taskScript --input=facade.xml --outputPath=facade

... where facade.xml and facade can be replaced with the appropriate relative pathnames.

