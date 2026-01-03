import pygame
import math
from enum import Enum
from pathlib import Path
from dataclasses import dataclass
from typing import Callable, Optional, Dict, Tuple

from utils.coords import Coord
from system.event_handler import EventHandler

from system.game_clock import game_clock
from system.settings import global_settings

from decorators import singleton
from constants import MAX_SOUND_DISTANCE



# -----------------------------------------------------------------------------
# Mixer configuration
# -----------------------------------------------------------------------------

# Number of mixer channels reserved exclusively for music.
MUSIC_CHANNELS = 8

# Total mixer channels (music + SFX).
MIXER_CHANNELS = 48

# Fade out time (ms) when switching tracks.
FADE_OUT_TIME = 1200


class SoundEvents(int, Enum):
    MUSIC_END_EVENT = pygame.event.custom_type()


# -----------------------------------------------------------------------------
# Sound registry
# -----------------------------------------------------------------------------

"""
When you add a new sound file under assets/sounds:
1) Add an enum entry in Sound where VALUE = filename (including extension).
2) Optionally add a default per-sound volume (0...1) in SOUNDS_TO_VOLUMES.
"""

class Sound(str, Enum):
    # Music
    MAIN_TRACK = "pixel_dreams.wav"
    GAME_TRACK_1 = "alkacrab_track_1.wav"
    GAME_TRACK_2 = "alkacrab_track_2.wav"

    # UI 
    BUTTON_CLICK = "button_click_1.wav"

    # SFX
    GRASS_1 = "grass_1.wav"
    GRASS_2 = "grass_2.wav"


# Default per-sound volume multipliers (0...1). Missing sounds default to 1.0.
SOUNDS_TO_VOLUMES: Dict[Sound, float] = {
    Sound.GAME_TRACK_1: 0.3,
    Sound.GAME_TRACK_2: 0.3,
    Sound.GRASS_1: 0.2,
    Sound.GRASS_2: 0.2,
}


# -----------------------------------------------------------------------------
# Runtime SFX request structure
# -----------------------------------------------------------------------------

SoundInstanceId = Optional[int | str]


@dataclass(frozen=True)
class SoundRequest:
    """
    A request to play a sound.

    sound:
        Which asset to play.
    id:
        Optional identifier used to cooldown / rate-limit repeated sounds.
        Example: use an entity id so each entity can have its own cooldown.
    repeats:
        pygame repeats arg: 0 = play once, 1 = play twice, etc.
    time_restricted:
        Cooldown duration (ms) for (sound, id) pairs. 0 disables cooldown.
    get_location:
        Callable returning current world location of the sound source.
        Used for positional audio; ignored for non-locational sounds.
    """

    sound: Sound
    id: SoundInstanceId = None
    repeats: int = 0
    time_restricted: int = 0
    get_location: Callable[[], Optional[Coord]] = lambda: None


# -----------------------------------------------------------------------------
# Sound mixer
# -----------------------------------------------------------------------------

@singleton
class SoundMixer:
    """
        Central audio manager for:
        - Loading sound assets
        - Playing music with crossfades
        - Playing SFX (optionally positional/locational)
        - Rate limiting repeated sounds via cooldowns

        Positional audio implementation:
        - Uses pygame Channel.set_source_location(angle, distance)
        - Angle is computed relative to a "base vector" in screen-space.
        - Distance is scaled to [0..255] based on MAX_SOUND_DISTANCE.
    """

    SOUND_PATH = Path(__file__).parent.parent.parent / 'assets' / 'sounds'

    def __init__(self):
        # Initialize pygame's audio mixer and channel pool.
        pygame.mixer.init()
        pygame.mixer.set_num_channels(MIXER_CHANNELS)
        pygame.mixer.set_reserved(MUSIC_CHANNELS)

         # Bound at runtime (player must expose `.location: Coord`)
        self.player = None
        
        # Master music volume [0..1] from settings
        self.current_volume = global_settings.get("volume") / 100

        # Loaded sound assets
        self.sounds: Dict[Sound, pygame.mixer.Sound] = {}

        # Active positional SFX channels to update each tick:
        #   channel_id -> SoundInstance
        self.channels_to_update: Dict[int, SoundRequest] = {}


        # Music state
        self.current_music = None
        self.next_music = None
        self.music_channels: Dict[Sound, pygame.mixer.Channel] = {}
        self.music_sounds_pos: Dict[Sound, int] = {}
        self.last_music_channel = 0

        # Reference vector for computing angle to sound source in 2D
        self.base_sound_vect = Coord.math(-math.sqrt(2) / 2, math.sqrt(2) / 2, 0)

        # Sound cooldown tracking:
        #   sound_clock increments by game_clock.dt (ms)
        #   last_sounds[(sound, id)] = last_time_played (ms)
        self.sound_clock = 0
        self.last_sounds: Dict[Tuple[Sound, int], int] = {}

        self._load_sounds()
        self._load_music()
        self.set_volume(self.current_volume)


    # -------------------------------------------------------------------------
    # Asset loading
    # -------------------------------------------------------------------------

    def _load_sounds(self):
        """ Load all Sound enum entries from disk into pygame.mixer.Sound objects. å"""
        for sound in Sound:
            sound_file = pygame.mixer.Sound(self.SOUND_PATH / sound.value)
            sound_file.set_volume(SOUNDS_TO_VOLUMES.get(sound, 1))
            self.sounds[sound] = sound_file

    def _load_music(self):
        """Pre-allocate channels for music tracks."""
        self.add_music_channel(Sound.MAIN_TRACK)
        self.add_music_channel(Sound.GAME_TRACK_1)
        self.add_music_channel(Sound.GAME_TRACK_2)

    # -------------------------------------------------------------------------
    # Update loop
    # -------------------------------------------------------------------------

    def _update_channels(self):
        """
            For each channel playing a locational sound, recompute its angle/distance.
            Removes channels that have finished.
        """
        for c_i in list(self.channels_to_update.keys()):
            channel = pygame.mixer.Channel(c_i)

            # Sound finished so stop tracking
            if not channel.get_busy():
                del self.channels_to_update[c_i]
                continue

            inst = self.channels_to_update[c_i]
            angle, dist = self._get_source_location(inst.get_location())
            channel.set_source_location(angle, dist)

    def update(self):
        """ Update positional channels and process music transition events. """
        self._update_channels()
        self.sound_clock += game_clock.dt
        for event in EventHandler().events():
            if event.type == SoundEvents.MUSIC_END_EVENT and self.next_music is not None:
                self.music_channels[self.next_music].unpause()
                self.current_music = self.next_music
                self.next_music = None
        
    # -------------------------------------------------------------------------
    # Music control
    # -------------------------------------------------------------------------

    def add_music_channel(self, music: Sound) -> None:
        """
            Allocate and initialize a dedicated channel for a music track.
            - Reserve a channel index
            - Set an end event
            - Start it paused (so it's ready to unpause immediately)
        """

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
        """
            Switch music to `music`.
            - If nothing playing: unpause requested track immediately.
            - If a different track is playing: fade out current track and prepare next.

            When fade completes, MUSIC_END_EVENT triggers the next track to unpause.
        """

        if self.current_music is None:
            self.current_music = music
            self.music_channels[self.current_music].unpause()
            return

        if self.current_music != music:
            self.next_music = music
            current_channel = self.music_channels[self.current_music]
            current_channel.fadeout(FADE_OUT_TIME)

            # Ensure next track is playing but paused. It will unpause on MUSIC_END_EVENT.
            next_channel = self.music_channels[self.next_music]
            next_channel.play(self.sounds[self.next_music], -1)
            next_channel.pause()

    # -------------------------------------------------------------------------
    # Sound effects
    # -------------------------------------------------------------------------

    def add_sound_effect(self, sound_effect: SoundRequest, force: bool = False) -> None:
        """
            Play a non-positional sound effect (UI, global SFX).
            force=True allows pygame to steal a channel if none are free.
        """
        if self._sound_in_cooldown(sound_effect): return
        if (channel := pygame.mixer.find_channel(force=force)):
            ch_id = channel.id

            # If this channel was previously used for positional audio, stop tracking it.
            if ch_id in self.channels_to_update: del self.channels_to_update[ch_id]
            channel.play(self.sounds[sound_effect.sound], sound_effect.repeats)

    def add_locational_sound_effect(
            self, 
            sound_effect: SoundRequest, 
            max_distance: int = MAX_SOUND_DISTANCE, 
            force: bool = False
        ) -> None:

        location = sound_effect.get_location()
        """
            Play a positional sound effect if it is close enough to the player.

            - If player is not bound or location is missing: does nothing.
            - If beyond max_distance: does nothing.
            - Respects cooldown (time_restricted).
        """

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

    # -------------------------------------------------------------------------
    # Cooldowns / rate limiting
    # -------------------------------------------------------------------------

    def _sound_in_cooldown(self, request: SoundRequest):
        """
            Return True if this sound should not be played yet due to time restriction.
            Cooldown key is (sound, id). If id is None, all instances of that sound share cooldown.
        """

        if request.time_restricted <= 0: return False
        
        sound_id_pair = (request.sound, request.id)
        if sound_id_pair in self.last_sounds:
            # Enough time passed -> allow and update timestamp
            if self.sound_clock - self.last_sounds[sound_id_pair] > request.time_restricted:
                self.last_sounds[sound_id_pair] = self.sound_clock
                return False
            return True
        
        # Sound is not tracked, start tracking it
        self.last_sounds[sound_id_pair] = self.sound_clock
        return False

    # -------------------------------------------------------------------------
    # Positional audio helpers
    # -------------------------------------------------------------------------

    def _get_source_location(self, sound_location: Optional[Coord]):
        """
            Convert a world-space sound location into pygame's (angle, distance) representation.

            Returns:
                (angle, distance) where:
                - angle is relative to base_sound_vect
                - distance is scaled to [0..255] using MAX_SOUND_DISTANCE
        """
        if sound_location is not None and self.player is not None:
            direction = sound_location - self.player.location
            angle = self.base_sound_vect.get_angle_2D(direction)
            return angle, min(255, direction.norm() * (255 / MAX_SOUND_DISTANCE))
        return 0, 0
    
    # -------------------------------------------------------------------------
    # Public controls
    # -------------------------------------------------------------------------

    def set_volume(self, volume: float) -> None:
        """ Set master volume on all channels """
        for c_i in range(MUSIC_CHANNELS):
            channel = pygame.mixer.Channel(c_i)
            channel.set_volume(volume)

    def bind_player(self, player) -> None:
        """ Bind a player object used for positional audio. """
        self.player = player