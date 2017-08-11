Google Voice Recognizer
============================

Branch from https://github.com/google/aiyprojects-raspbian


### Install

apt-get update:
```
$ sudo apt-get upgrade
$ sudo apt-get update
```

voice regpgnizer:
```
$ sudo apt-get install git scons swig
$ cd ~
$ git clone https://github.com/hanmy75/voice-recognizer.git
$ cd ~/voice-recognizer
$ scripts/install-deps.sh
$ sudo scripts/install-services.sh
$ sudo scripts/install-alsa-config.sh
$ make deploy
```

neopixel & etc
```
$ cd ~/voice-recognizer
$ source env/bin/activate

(env) $ git clone https://github.com/jgarff/rpi_ws281x.git
(env) $ cd rpi_ws281x
(env) $ scons
(env) $ cd python
(env) $ python -m pip install -e .
(env) $ pip install peewee
```

I2S hifiberry_dac Setup:
```
$ cd ~/
$ curl -sS https://raw.githubusercontent.com/adafruit/Raspberry-Pi-Installer-Scripts/master/i2samp.sh | bash
# Reboot is required
$ speaker-test
$ alsamixer
$ sudo alsactl store
```


### Test script

```
$ cd ~/voice-recognizer
$ source env/bin/activate
$ python3 src/main.py
```


### Enable and Start Service

```
$ sudo systemctl enable voice-recognizer
$ sudo service voice-recognizer start

$ sudo service status-led start
```
