# Ai-Desk-Robot-Tars-With-Pan-Tilt-Camera
I wanted to create a desk robot that you can ask things, chat with it, ask what is going on with the enviroment via camera that he can look around with 2 servos. And here it is. I didn't made a 3d printed case for it, I used lego technic to make a chasis. I am planing to share the lego file soon. Now, here is step by step guide on how to make this robot:


**Needed Hardware:**

- Raspberry Pi 4 1gb(Any other raspberry pi with atleast 1gb ram should work)
- Logitech web cam(C270 to be exact but you can use any webcam that has a mic.)
- 2 Sg90 Servo Motors
- PCA9685 for controlling the servos
- 1s Lipo or 18650 li-on battery or a trustable 5V power source.
- MT3608(set the output to 5/5,2 volts) if you are using a lipo or 18650 because they output 4.2V max.(Look at **How to fix MT3608** part if the potentiometer on the board doesn't change the output voltage)
- MAX98357A amplifier
- Small speaker for the amp


**How to fix MT3608**

If the potentiometer on the MT3608 doesn't change the output voltage, add a solder bridge at the back of the board as shown on the picture.

<img width="890" height="442" alt="mt fix" src="https://github.com/user-attachments/assets/506ada10-7514-42bf-a105-8146ea34c411" />


**Wiring**

Here is the Raspberry pi 4 pinout to make things easier.
<img width="2064" height="1185" alt="GPIO-Pinout-Diagram-2" src="https://github.com/user-attachments/assets/fa54dea6-1ea0-4ec2-be7b-4d2bfb1a8ce0" />
