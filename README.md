# Tars AI Desk Robot
I wanted to create a desk robot that you can ask things, chat with it, ask what is going on with the enviroment via camera that he can look around with 2 servos. And here it is. I didn't made a 3d printed case for it, I used lego technic to make a chasis. Now, here is step by step guide on how to make this robot:


## **🔌 Needed Hardware**

- Raspberry Pi 4 1gb(Any other raspberry pi with atleast 1gb ram should work. I recommend having a heatsink or a cooler fan)
- Web cam(I used Logitech C270 but you can use any webcam that has a mic.)
- 2 Sg90 Servo Motors
- PCA9685 for controlling the servos
- 1s Lipo or 18650 li-on battery or a trustable 5V power source.
- MT3608(set the output to 5/5,1 volts) if you are using a lipo or 18650 because they output 4.2V max.(Look at **How to fix MT3608** part if the potentiometer on the board doesn't change the output voltage)
- MAX98357A amplifier
- Small speaker for the amp
- 3D printed parts. Download links will be in the **Downloadables** folder.
- Lego techinc to make the chasis. The lego model will be in the **Downloadables** folder. (i would be pleased if someone makes a 3d printed chasis)
  



## **⚡ Wiring**

Here is the Raspberry pi 4 pinout to make things easier.
<img width="2064" height="1185" alt="GPIO-Pinout-Diagram-2" src="https://github.com/user-attachments/assets/fa54dea6-1ea0-4ec2-be7b-4d2bfb1a8ce0" />

First, just like in any other project, wire GND(PIN 6) to a power rail.

### The wiring for MAX98357a will be like this:

Vin ------ PIN 2(5V power)

Gnd ------ GND power rail

SD  ------ Empty

Gain ----- Gnd power rail

DIN ------ GPIO 21(PIN 40)

BCLK ----- GPIO 18(PIN 12)

LRC ------ GPIO 19(PIN 35)

Output + = Speaker +

Output - = Speaker -

### ---------------------The wiring for PCA9685:-------------------------

 Gnd ----- Gnd power rail
 
 Oe ------ Empty
 
 SCL ----- GPIO 3(PIN 5)
 
 SDA ----- GPIO 2(PIN 3)
 
 VCC ----- 3v3 power (PIN 1)
 
 Power terminal V+ = External 5v power source or 1s lipo wired to Mt3608(output voltage must be set to 5/5,1 volts)
 
 Power terminal - = External 5v power source or 1s lipo wired to Mt3608(output voltage must be set to 5/5,1 volts)

 **IMPORTANT: DO NOT WIRE THE POWER TERMINALS DIRECTLY TO 5V POWER ON RASPBERRY PI AS IT WILL DRAW TOO MUCH POWER AND MAY BURN YOUR BOARD**

 Pan Servo motor = The 3 pins on the very left(Match the colors)
 
 Tilt Servo motor = The 3 pins right next to the pan servo motor pins(Match the colors)<img width="1001" height="1001" alt="servo" src="https://github.com/user-attachments/assets/df7c4a65-417b-444d-8c6d-92fa6eea9670" />



 ### ----------------------📷 Wiring for the usb webcam---------------

 Just plug the usb to the raspberry pi :)




## **🔧 How to fix MT3608**

If the potentiometer on the MT3608 doesn't change the output voltage, add a solder bridge at the back of the board as shown on the picture.

<img width="890" height="442" alt="mt fix" src="https://github.com/user-attachments/assets/506ada10-7514-42bf-a105-8146ea34c411" />


##Setup##



 
