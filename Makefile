# Make targets
all:
	python3 pdiffsim_gt.py simulation1.cfg

plots:
	Rscript frequencies.R simulation1.log

simulation1:
	python3 pdiffsim_gt.py simulation1.cfg
	if test -e "simulation1.log/frequencies.dat"; then Rscript frequencies.R simulation1.log; fi;

simulation2:
	python3 pdiffsim_gt.py simulation2.cfg
	if test -e "simulation2.log/frequencies.dat"; then Rscript frequencies.R simulation2.log; fi;

simulation3:
	python3 pdiffsim_gt.py simulation3.cfg
	if test -e "simulation3.log/frequencies.dat"; then Rscript frequencies.R simulation3.log; fi;

simulation4:
	python3 pdiffsim_gt.py simulation4.cfg
	if test -e "simulation4.log/frequencies.dat"; then Rscript frequencies.R simulation4.log; fi;

simulation5:
	python3 pdiffsim_gt.py simulation5.cfg
	if test -e "simulation5.log/frequencies.dat"; then Rscript frequencies.R simulation5.log; fi;

clean:
	rm -rf simulation1.log
	


# NOTES

# creating a video from frames
# convert -loop 0 frame*.png output.mp4

# simple timing of total execution speed
#~ time python3 pgdiffsim.py offscreen
