import pygame
import math
from decorators import singleton
from constants import MAX_SOUND_DISTANCE
from utils.coords import Coord
from system.event_handler import EventHandler
from system.game_clock import game_clock
from system.settings import global_settings
from enum import Enum
from pathlib import Path
from dataclasses import dataclass
from typing import Callable, Optional, Dict, Tuple

MUSIC_CHANNELS = 8
MIXER_CHANNELS = 48
FADE_OUT_TIME = 1200

class SoundEvents(int, Enum):
    MUSIC_END_EVENT = pygame.event.custom_type()


"""

    When a new sound is added assets/sounds add it here as well with 
    enum_name = file_name so that it will be loaded. Also add the 
    volume of the sound [0, 1] to SOUND_TO_VOLUMES to set the correct
    sound level or let it default to 1. 

"""
class Sound(str, Enum):
    MAIN_TRACK = "pixel_dreams.wav"
    GAME_TRACK_1 = "alkacrab_track_1.wav"
    GAME_TRACK_2 = "alkacrab_track_2.wav"
    BUTTON_CLICK = "button_click_1.wav"
    GRASS_1 = "grass_1.wav"
    GRASS_2 = "grass_2.wav"


SOUNDS_TO_VOLUMES: Dict[Sound, float] = {
    Sound.GAME_TRACK_1: 0.3,
    Sound.GAME_TRACK_2: 0.3,
    Sound.GRASS_1: 0.2,
    Sound.GRASS_2: 0.2,
}

@dataclass
class SoundInstance:
    sound: Sound
    id: Optional[int | str] = None
    repeats: int = 0
    time_restricted: int = 0
    get_location: Callable[[], Optional[Coord]] = lambda: None


@singleton
class SoundMixer:
    SOUND_PATH = Path(__file__).parent.parent.parent / 'assets' / 'sounds'
    def __init__(self):
        # init mixer
        pygame.mixer.init()
        pygame.mixer.set_num_channels(MIXER_CHANNELS)
        pygame.mixer.set_reserved(MUSIC_CHANNELS)

        self.player = None
        
        self.current_volume = global_settings.get("volume") / 100
        self.sounds: Dict[Sound, pygame.mixer.Sound] = {}
        self.channels_to_update: Dict[int, SoundInstance] = {}


        # Music channels
        self.current_music = None
        self.next_music = None
        self.music_channels: Dict[Sound, pygame.mixer.Channel] = {}
        self.music_sounds_pos: Dict[Sound, int] = {}
        self.last_music_channel = 0

        # Vector to get sound angle against
        self.base_sound_vect = Coord.math(-math.sqrt(2) / 2, math.sqrt(2) / 2, 0)

        # Keep track of time and last calls to make sure time restricted sounds work as intended
        self.sound_clock = 0
        self.last_sounds: Dict[Tuple[Sound, int], int] = {}

        self._load_sounds()
        self._load_music()


    def _load_sounds(self):
        for sound in Sound:
            sound_file = pygame.mixer.Sound(self.SOUND_PATH / sound.value)
            sound_file.set_volume(SOUNDS_TO_VOLUMES.get(sound, 1))
            self.sounds[sound] = sound_file

    def _load_music(self):
        """Can add music that you know will used later here to have it ready"""
        self.add_music_channel(Sound.MAIN_TRACK)
        self.add_music_channel(Sound.GAME_TRACK_1)
        self.add_music_channel(Sound.GAME_TRACK_2)

    def _update_channels(self):
        for c_i in list(self.channels_to_update.keys()):
            channel = pygame.mixer.Channel(c_i)
            if channel.get_busy():
                channel_sound = self.channels_to_update[c_i]
                channel.set_source_location(
                    *self._get_source_location(channel_sound.get_location())
                )
            else: del self.channels_to_update[c_i]

    def update(self):
        self._update_channels()
        self.sound_clock += game_clock.dt
        for event in EventHandler().events():
            if event.type == SoundEvents.MUSIC_END_EVENT and self.next_music is not None:
                self.music_channels[self.next_music].unpause()
                self.current_music = self.next_music
                self.next_music = None
        
    
    def add_music_channel(self, music: Sound) -> None:
        if music not in self.music_channels:
            if len(self.music_channels) >= MUSIC_CHANNELS: 
                raise Exception(f"Attempted to allocate over {MUSIC_CHANNELS} music channels")
        
            channel = pygame.mixer.Channel(self.last_music_channel)
            self.music_channels[music] = channel
            self.music_sounds_pos[music] = 0
            self.last_music_channel += 1

            channel.set_endevent(SoundEvents.MUSIC_END_EVENT)
            channel.play(self.sounds[music], -1)
            channel.pause()


    def play_music(self, music: Sound) -> None:
        if self.current_music is None:
            self.current_music = music
            self.music_channels[self.current_music].unpause()
            return

        if self.current_music != music:
            self.next_music = music
            current_channel = self.music_channels[self.current_music]
            current_channel.fadeout(FADE_OUT_TIME)

            next_channel = self.music_channels[self.next_music]
            next_channel.play(self.sounds[self.next_music], -1)
            next_channel.pause()

    def add_sound_effect(self, sound_effect: SoundInstance, force: bool = False) -> None:
        if self._sound_in_cooldown(sound_effect): return
        if (channel := pygame.mixer.find_channel(force=force)):
            ch_id = channel.id
            if ch_id in self.channels_to_update: del self.channels_to_update[ch_id]
            channel.play(self.sounds[sound_effect.sound], sound_effect.repeats)

    def add_locational_sound_effect(
            self, 
            sound_effect: SoundInstance, 
            max_distance: int = MAX_SOUND_DISTANCE, 
            force: bool = False
        ) -> None:

        location = sound_effect.get_location()
        if (
            location is None or 
            self.player is None or
            location.manhattan(self.player.location) > max_distance or 
            self._sound_in_cooldown(sound_effect)
        ): return

        if (channel := pygame.mixer.find_channel(force=force)):
            ch_id = channel.id
            self.channels_to_update[ch_id] = sound_effect
            channel.set_source_location(*self._get_source_location(sound_effect.get_location()))
            channel.play(self.sounds[sound_effect.sound], sound_effect.repeats)

    def _sound_in_cooldown(self, sound: SoundInstance):
        if sound.time_restricted <= 0: return False
        
        sound_id_pair = (sound.sound, sound.id)
        if sound_id_pair in self.last_sounds:
            if self.sound_clock - self.last_sounds[sound_id_pair] > sound.time_restricted:
                self.last_sounds[sound_id_pair] = self.sound_clock
                return False
            return True
        
        self.last_sounds[sound_id_pair] = self.sound_clock
        return False


    def _get_source_location(self, sound_location: Optional[Coord]):
        if sound_location is not None and self.player is not None:
            direction = sound_location - self.player.location
            angle = self.base_sound_vect.get_angle_2D(direction)
            return angle, direction.norm()
        return 0, 0

    def set_volume(self, volume: float) -> None:
        for c_i in range(MUSIC_CHANNELS):
            channel = pygame.mixer.Channel(c_i)
            channel.set_volume(volume)

    def bind_player(self, player) -> None:
        self.player = player