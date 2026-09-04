# Tars AI Desk Robot
I wanted to create a sarcastic desk robot inspired from interstellar and also inspired from [Gptars on Youtube](https://www.youtube.com/@gptars) that you can ask things, chat with it, ask what is going on with the enviroment via camera that he can look around with 2 servos. And here it is. I didn't made a 3d printed case for it, I used lego technic to make a chasis. Now, here is step by step guide on how to make this robot:


## Features

- 🎤**Voice Interaction:** Low-latency STT via Whisper-large-v3-turbo and Orpheus TTS via Groq.
- 📸**Vision Recognition:** Qwen 2.5 72B vision integration to analyze camera input upon voice triggers.
- ⚙️ **Servo Control:** Smooth pan/tilt tracking via PCA9685 PWM driver board.
- 🌐**Web Search Integration:** Real-time information querying via DuckDuckGo Search API.
- 🔊**Pre-recorded Local Acknowledgments:** Pre-generated TTS wake-word acknowledgments to save API quota.


## **🔌 Needed Hardware**

- Raspberry Pi 4 1gb(Any other raspberry pi with atleast 1gb ram should work. I recommend having a heatsink or a cooler fan)
- Web cam(I used Logitech C270 but you can use any webcam that has a mic.)
- 2 Sg90 Servo Motors
- PCA9685 for controlling the servos
- 1s Lipo or 18650 li-on battery or a trustable 5V power source.
- MT3608(set the output to 5/5,1 volts) if you are using a lipo or 18650 because they output 4.2V max.(Look at **How to fix MT3608** part if the potentiometer on the board doesn't change the output voltage)
- MAX98357A amplifier
- Small speaker for the amp
- Breadboard
- 3D printed parts. Download links will be in the **Downloadables** folder.
- Lego techinc to make the chasis. The lego model will be in the **Downloadables** folder. (i would be pleased if someone makes a 3d printed chasis)



## **Setting Up The Chasis**

<img width="420" height="!" alt="legorender" src="https://github.com/user-attachments/assets/e2fe6531-cd35-4d9e-a010-e4baa86854f8" />
<img width="420" height="!" alt="legorender_2" src="https://github.com/user-attachments/assets/810e7104-c8d6-46bc-bbe6-3b5d9354e125" />
<img width="300" height="!" alt="legorender_3" src="https://github.com/user-attachments/assets/b466c017-e3d9-4b64-bd99-c0494d99b106" />




### Step 1: 3D printing and making the servo to be able to connect with lego
First, you need to download and 3D print the stl files (print both of them atleast 2 times because you have two servos with PLA [here](downloadables/3dprint).

After that, you have to screw both the servos to the SG90 shell using the small screws you get when buying a sg90 servo motor.(Make sure the output side on the servo is next to the 2 holes)

Then, put some super glue on the SG90 to lego's middle hole on the side where you can put it to sg90's output. after you put some super glue in the hole, put the Sg90-lego adapter(middle hole where you put glue on) to 
servo's output. Make sure to not push too much as if the glue touches the blue servo motor case, it might glue the motor output and the case and make it not moveable.

<img width="400" height="!" alt="13336" src="https://github.com/user-attachments/assets/f285278d-41b1-4992-abe0-5b6f680de8a7" />
<img width="400" height="!" alt="13337" src="https://github.com/user-attachments/assets/42ac4648-6d5b-41ff-ae15-c786237ed854" /> 
<img width="400" height="!" alt="Adsız" src="https://github.com/user-attachments/assets/0f758fde-3636-46c1-8b29-85a202d0fdaf" />


### Step 2: Building the chasis

Download the [lego.io](downloadables/lego.io) Also, download Studio 2.0 from bricklink's [official website](https://store.bricklink.com/v2/studio/download.page)
You can look at the model there and improvise. You don't need to make the same thing. After making the chasis, and pan/tilt sections, fix the webcam on top of the pan section with rubber bands like this:
<img width="300" height="!" alt="13352" src="https://github.com/user-attachments/assets/66c5429f-dabe-48bb-87b5-3d437e4a503b" />
<img width="300" height="!" alt="13353" src="https://github.com/user-attachments/assets/618e5fbe-e058-4049-8c10-51265f987f64" />
<img width="300" height="!" alt="13354" src="https://github.com/user-attachments/assets/24f64b28-8040-4b46-b8f4-c7d032e5b0e0" />


Then, asemble the two pieces(pan/tilt with camera) together like this:


<img width="300" height="!" alt="13358" src="https://github.com/user-attachments/assets/d8e340bb-4a12-4730-a808-f4228853da76" />
<img width="300" height="!" alt="13360" src="https://github.com/user-attachments/assets/6a5fa599-013f-40fa-a31a-cf05199e44dd" />
<img width="300" height="!" alt="13361" src="https://github.com/user-attachments/assets/1d807685-d948-48af-b017-9df94a2a4b75" />

After that, you can assemble the pan/tilt section with the servo motor on the main body. And after you do the wiring that i explain bellow, it should look like this: 

<img width="500" height="!" alt="13368" src="https://github.com/user-attachments/assets/fd1b81e5-60cb-4ed0-8168-7a8e05152777" />
<img width="500" height="!" alt="13364" src="https://github.com/user-attachments/assets/db7389b6-c23e-4c48-8012-ae80ee2907bb" />
<img width="500" height="!" alt="13363" src="https://github.com/user-attachments/assets/409ee6bb-95c8-43bd-872a-c11db1b390df" />
<img width="500" height="!" alt="13366" src="https://github.com/user-attachments/assets/cf7a37b6-8b86-4cb1-b37b-b825f81c0ffc" />
<img width="500" height="!" alt="13365" src="https://github.com/user-attachments/assets/eee1d6bf-1487-4642-8acc-20ebdad87f18" />


















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


## 🚀Setup

### Notes before we begin
#### *Get a free api key [here](https://groq.com)*
#### *Make sure you have [Raspberry Pi Connect](https://connect.raspberrypi.com) ready to make things easier*

(I will make an installer in the future)

*Assuming that you have raspberry pi os flashed and ready.(With gui you can disable the gui in the future if you want)*


Run the following commands in the Raspberry Pi terminal to enable the I2C interface for servo driving and install system audio/video dependencies:

```
sudo raspi-config nonint do_i2c 0
sudo apt update
sudo apt install -y python3-pip python3-venv python3-dev portaudio19-dev libasound2-dev alsa-utils ffmpeg vlc
```

Then, create the project workspace and install the libraries:


```
mkdir -p ~/tars_robot && cd ~/tars_robot
python3 -m venv venv
source venv/bin/activate
pip install --upgrade pip
pip install groq opencv-python pyaudio numpy adafruit-circuitpython-servokit duckduckgo_search
```


Create the main application file inside ~/tars_robot/tars.py:

```
nano tars.py
```

Copy and paste the tars.py code from [here](tars.py). And replace **PLACE YOUR GROQ API KEY HERE** on **line 82** with your Groq api key and save(Ctrl+O, Enter, Ctrl+X).

### ⚠DON'T RUN THE CODE YET

Create the generate_acks.py to generate "HUH?","YES?","THATS ME" and other bunch of words when you say "Hey Tars" and paste [this code](generate_acks.py)

**Again, replace "PLACE YOUR GROQ API KEY HERE" on line 5 with your Groq api key**

```
nano generate_acks.py
```

Now, make sure you are on (venv):

```
source venv/bin/activate
```

Then, run generate_acks.py **ONE** time:

```
python generate_acks.py
```


Now, you can run tars.py in (venv) whenever you want:

```
python tars.py
```



### Continue this guide if you want a shortcut and not get into (venv) when you want to run the code!

Exit from (venv):

```
deactivate
```

Create a shell script named run_tars.sh inside your project directory:

```
nano ~/run_tars.sh
```

Paste the following contents (update /home/pi/tars to your actual project folder path):

```
#!/bin/bash
cd /home/pi/tars
source venv/bin/activate
python tars.py

# Keeps the terminal window open if the script exits or crashes
echo ""
read -p "Press [Enter] to close..."
```

Make the script executable:

```
chmod +x ~/run_tars.sh
```

Create a file named TARS.desktop in your desktop. Open it with text editor and paste this code:

### **Replace "YOURUSERNAME" with opperating systems username**

```
[Desktop Entry]
Type=Application
Name=TARS Robot
Comment=Start TARS Voice & Vision Assistant
Exec=/home/YOURUSERNAME/run_tars.sh
Icon=utilities-terminal
Terminal=true
Categories=Development;
```


Make the shortcut file executable:

```
chmod +x ~/Desktop/TARS.desktop
```

Now you can double click and launch tars easily.
