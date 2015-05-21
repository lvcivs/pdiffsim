
args <- commandArgs(trailingOnly = TRUE)

logFileName <- args[1]
imageName <- paste(logFileName, "/frequencies.png", sep="")
datFileName <- paste(logFileName, "/frequencies.dat", sep="")

png(imageName, width=20, height=15, units="cm", res=300)

myGreen <- rgb(0, 128, 0, maxColorValue=255)

h <- read.csv(file=datFileName,head=TRUE,sep=",")
plot(h$Ticks,ylim=c(1,100),type="n",xlab="time (ticks)",ylab="variant frequency (indexed)", main="variant frequencies in simulation1")
lines(h$AlphaY,type="l",col=myGreen)
lines(h$BetaY,type="l",col="red")

dev.off()
