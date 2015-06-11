# how to run
all:
	python3 pdiffsim_gt.py simulation1.cfg

plots:
	Rscript frequencies.R simulation1.log

simulation1:
	python3 pdiffsim_gt.py simulation1.cfg
	Rscript frequencies.R simulation1.log

simulation2:
	python3 pdiffsim_gt.py simulation2.cfg
	Rscript frequencies.R simulation2.log

clean:
	rm -rf simulation1.log

# NOTES
# had to manually install pycallgraph module, using pip3 (wouldn't work with python3 otherwise)
# installs in $USER/.local !
# later uninstalled, because didn't work
#~ pip3 install pycallgraph

# simple timing of total execution speed
#~ time python3 pgdiffsim.py offscreen
