with open("pogoda.conf") as f:
    config = f.read().splitlines()

for item in config:
    var=item.split("=",1)
    myVars = globals()
    myVars.__setitem__(var[0],var[1])

temp_corr=int(temp_corr)
hum_corr=int(hum_corr)