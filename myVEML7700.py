import machine
import time

#https://www.vishay.com/docs/84323/designingveml7700.pdf
#VEML7700 address
VEML7700_ADDR=0x10

    # Ambient light sensor gain settings
VEML7700_ALS_GAIN_1 = const(0x00)
VEML7700_ALS_GAIN_2 = const(0x01)
VEML7700_ALS_GAIN_1_8 = const(0x02)
VEML7700_ALS_GAIN_1_4 = const(0x03)

# Ambient light integration time settings

VEML7700_ALS_25MS = const(0xC)
VEML7700_ALS_50MS = const(0x8)
VEML7700_ALS_100MS = const(0x0)
VEML7700_ALS_200MS = const(0x1)
VEML7700_ALS_400MS = const(0x2)
VEML7700_ALS_800MS = const(0x3)

class myVEML7700:
    
    def __init__(self, i2c):
        self._i2c=i2c
        #poweron with defaults, int_time=100ms (0) & ALS_PERS=0, ALS_GAIN=1 and disable INT ALS_INT_EN=0
        self._i2c.writeto_mem(VEML7700_ADDR, 0x00, bytes([0x00,0x00]) )
        time.sleep(0.1)
        #turning off power saving mode PSM=0 and PSM_EN=0
        self._i2c.writeto_mem(VEML7700_ADDR, 0x03, bytes([0x00,0x00]))
        time.sleep(0.1)
        self.setGain(VEML7700_ALS_GAIN_1_8)
        
    def _calculate(self):
# These settings are based on CEML770 application note PDF
# https://www.vishay.com/docs/84323/designingveml7700.pdf
# base is 800ms & GAIN 2 that is 0.0036 LUX per ALS unit.
# GAIN = GAIN doubles for each GAIN step: GAIN_2=*1 GAIN_1=*2
# GAIN_1/4=*8. GAIN_1/8=*16
# same goes for values 800,400,200,100,50,25 that coresponds to multiplier
# x1, x2, x4, x8, x16, x32
# lets calculate resolution
        buf=self._i2c.readfrom_mem(VEML7700_ADDR,0x00,2)
        CONF_REG_VAL=buf[1]<<8 | buf[0]
        
        GAIN_RAW=(CONF_REG_VAL>>11) & 0x03
        ALS_RAW=(CONF_REG_VAL>>6) & 0x0F
        
        if GAIN_RAW==0:
            GAIN_X=2
        if GAIN_RAW==1:
            GAIN_X=1
        if GAIN_RAW==2:
            GAIN_X=16
        if GAIN_RAW==3:
            GAIN_X=8
        
        if ALS_RAW==0:
            ALS_X=8
        if ALS_RAW==0x01:
            ALS_X=4
        if ALS_RAW==0x02:
            ALS_X=2
        if ALS_RAW==0x03:
            ALS_X=1
        if ALS_RAW==0x08:
            ALS_X=16
        if ALS_RAW==0xC:
            ALS_X=32
        return (0.0036*ALS_X*GAIN_X)
        
        
    def getLuxWhite(self):
        buf=self._i2c.readfrom_mem(VEML7700_ADDR,0x00,2)
        data=buf[1] << 8 | buf[0]
        buf=self._i2c.readfrom_mem(VEML7700_ADDR,0x05,2)
        tempLux=buf[1] << 8 | buf[0]
        LUX=tempLux*(self._calculate())
        if LUX>1000:
            LUX = LUX * (1.0023 + LUX * (8.1488e-5 + LUX * (-9.3924e-9 + LUX * 6.0135e-13)))
        return (LUX)

    def getLuxAls(self):
        buf=self._i2c.readfrom_mem(VEML7700_ADDR,0x00,2)
        data=buf[1] << 8 | buf[0]
        buf=self._i2c.readfrom_mem(VEML7700_ADDR,0x04,2)
        tempLux=buf[1] << 8 | buf[0]
        
        LUX=tempLux*(self._calculate())
        if LUX>1000:
            LUX = LUX * (1.0023 + LUX * (8.1488e-5 + LUX * (-9.3924e-9 + LUX * 6.0135e-13)))
        return (LUX)


    def setGain(self, gain):
#bit 12:11
#00 - ALS GAIN x1
#01 - ALS GAIN x2
#10 - ALS GAIN x(1/8)
#11 - ALS GAIN x1(1/4)

        buf=self._i2c.readfrom_mem(VEML7700_ADDR,0x00,2)
        data=buf[1] << 8 | buf[0]
        data=(data & 0xE7FF) | (gain << 11)


        self._i2c.writeto_mem(VEML7700_ADDR, 0x00, bytes([(data & 0xff),(data>>8)&0xff]) )
        time.sleep(0.1)
       
        
    def setALS(self, als):
#bit 9:6
#ALS integration time setting
#0000 = 100 ms  = 0
#0001 = 200 ms  = 1
#0010 = 400 ms  = 2
#0011 = 800 ms  = 3
#1000 = 50 ms   = 4
#1100 = 25 ms   = 5
        
                
        buf=self._i2c.readfrom_mem(VEML7700_ADDR,0x00,2)
        data=buf[1] << 8 | buf[0]
        data=(data & 0xFC3F) | (als << 6)

        self._i2c.writeto_mem(VEML7700_ADDR, 0x00, bytes([(data & 0xff),(data>>8)&0xff]) )
        time.sleep(0.1)


