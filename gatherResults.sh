#!/bin/bash
nTop=$1
for protFile in $( ls sparseData2/protInfo_expr*.csv ); do
#	echo - $protFile -:
	cat $protFile.desc
	echo -n ";"
	python3.5 ../../getAUC.py $protFile $nTop
done
