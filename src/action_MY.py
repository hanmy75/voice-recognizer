# Copyright 2017 Google Inc.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

"""Carry out voice commands by recognising keywords."""

import datetime
import logging
import subprocess
import wemo_backend

import actionbase

# Power Control Operation
def TV_Operation(state):
    logging.info("TV Power state %d", state)

def Speaker_Operation(state):
    logging.info("Speaker state %d", state)

def TableLamp_Operation(state):
    logging.info("Table Lamp state %d", state)

def LivingRoom_Operation(state):
    logging.info("LivingRoom Lamp state %d", state)

def WindowLamp_Operation(state):
    logging.info("Window Lamp state %d", state)

POWER_OPERATIONS = {
    "TV": TV_Operation,
    "speaker": Speaker_Operation,
    "table": TableLamp_Operation,
    "center": LivingRoom_Operation,
    "window": WindowLamp_Operation,
}

# TV Control Operation
def TV_PlayOperation():
    logging.info("TV Cmd : Play")

def TV_PauseOperation():
    logging.info("TV Cmd : Pause")

def TV_STOPOperation():
    logging.info("TV Cmd : Stop")

def TV_VolumeUpOperation():
    logging.info("TV Cmd : Volume Up")

def TV_VolumeDownOperation():
    logging.info("TV Cmd : Volume Down")

TV_OPERATIONS = {
    "play": TV_PlayOperation,
    "pause": TV_PauseOperation,
    "stop": TV_STOPOperation,
    "volume up": TV_VolumeUpOperation,
    "volume down": TV_VolumeDownOperation,
}


# Example: Change the volume
# ==========================
#
# This example will can change the speaker volume of the Raspberry Pi. It uses
# the shell command SET_VOLUME to change the volume, and then GET_VOLUME gets
# the new volume. The example says the new volume aloud after changing the
# volume.

class VolumeControl(object):
    """Changes the volume and says the new level."""
    GET_VOLUME = r'amixer get Master | grep "Front Left:" | sed "s/.*\[\([0-9]\+\)%\].*/\1/"'
    SET_VOLUME = 'amixer -q set Master %d%%'

    def __init__(self, say, change):
        self.say = say
        self.change = change

    def run(self, voice_command):
        res = subprocess.check_output(VolumeControl.GET_VOLUME, shell=True).strip()
        try:
            logging.info("volume: %s", res)
            vol = int(res) + self.change
            vol = max(0, min(100, vol))
            subprocess.call(VolumeControl.SET_VOLUME % vol, shell=True)
            self.say(_('Volume at %d %%.') % vol)
        except (ValueError, subprocess.CalledProcessError):
            logging.exception("Error using amixer to adjust volume.")


class PowerOnControl(object):
    """Control Power for device."""
    def __init__(self, say, keyword):
        self.say = say
        self.keyword = keyword

    def run(self, voice_command):
        command = voice_command.replace(self.keyword, "").strip()
        #logging.info("Power On : %s", command)
        if command in POWER_OPERATIONS:
            POWER_OPERATIONS[command](1)
            self.say(_("Ok"))
        else:
            self.say(_("I couldn't find " + command))


class PowerOffControl(object):
    """Control Power for device."""
    def __init__(self, say, keyword):
        self.say = say
        self.keyword = keyword

    def run(self, voice_command):
        command = voice_command.replace(self.keyword, "").strip()
        #logging.info("Power Off : %s", command)
        if command in POWER_OPERATIONS:
            POWER_OPERATIONS[command](0)
            self.say(_("Ok"))
        else:
            self.say(_("I couldn't find " + command))


class TVControl(object):
    """Control TV."""
    def __init__(self, say, keyword):
        self.say = say
        self.keyword = keyword

    def run(self, voice_command):
        command = voice_command.replace(self.keyword, "").strip()
        #logging.info("TV Command: %s", command)
        if command in TV_OPERATIONS:
            TV_OPERATIONS[command]()
            self.say(_("Ok"))
        else:
            self.say(_(command + "is not valid"))


def make_actor(say, actor):
    """Create an actor to carry out the user's commands."""

#    actor.add_keyword(_('volume up'), VolumeControl(say, 10))
#    actor.add_keyword(_('volume down'), VolumeControl(say, -10))
#    actor.add_keyword(_('max volume'), VolumeControl(say, 100))

    actor.add_keyword(_('turn on'), PowerOnControl(say, 'turn on the'))
    actor.add_keyword(_('turn off'), PowerOffControl(say, 'turn off the'))
    actor.add_keyword(_('turn up'), PowerOffControl(say, 'turn up the'))

    actor.add_keyword(_('on TV'), TVControl(say, "on TV"))
