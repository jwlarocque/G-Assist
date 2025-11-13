DEFAULT_TAGS = {
"HassTurnOn": [
"turn_on",
"enable",
"lock",
"open",
"start"
],
"HassTurnOff": [
"turn_off",
"disable",
"unlock",
"close",
"stop"
],
"HassSetPosition": [
"set_position",
"set_level",
"percentage"
],
"HassCancelAllTimers": [
"cancel_timers",
],
"HassListAddItem": [
"add_item",
"todo_list",
"shopping_list"
],
"HassListCompleteItem": [
"mark_complete",
"todo_list",
"shopping_list"
],
"HassClimateSetTemperature": [
"set_temperature",
"set_heat",
"set_cool"
],
"HassFanSetSpeed": [
"set_fan_speed",
],
"HassHumidifierSetpoint": [
"set_humidity",
"humidifier"
],
"HassHumidifierMode": [
"set_humidifier_mode"
],
"HassLightSet": [
"set_brightness"
],
"HassMediaUnpause": [
"resume_playback",
"play_media"
],
"HassMediaPause": [
"pause_media"
],
"HassMediaNext": [
"next_track",
"skip_track"
],
"HassMediaPrevious": [
"previous_track",
"replay_track"
],
"HassSetVolume": [
"set_volume"
],
"HassSetVolumeRelative": [
"increase_volume",
"decrease_volume",
"turn_volume_up",
"turn_volume_down"
],
"HassMediaPlayerMute": [
"mute",
],
"HassMediaPlayerUnmute": [
"unmute"
],
"HassMediaSearchAndPlay": [
"find_and_play"
],
"HassVacuumStart": [
"start_vacuum"
],
"HassVacuumReturnToBase": [
"dock_vacuum",
"stop_vacuum"
],
"GetDateTime": [
"date",
"time"
],
"todo_get_items": [
"read_list",
"get_todo_items"
],
"GetLiveContext": [
"check_status",
"get_current_value",
"is_device_on"
]
}


# This new dictionary defines exactly which tools and properties to include
# and specifies any description or type overrides.
ALLOWED_TOOLS = {
    "HassTurnOn": {
        "name": {}
    },
    "HassTurnOff": {
        "name": {}
    },
    "HassSetPosition": {
        "name": {},
        "position": {}
    },
    "HassCancelAllTimers": {},
    "HassListAddItem": {
        "item": {},
        "name": {"description": "the name of the list"}
    },
    "HassClimateSetTemperature": {
        "temperature": {},
        "name": {}
    },
    "HassFanSetSpeed": {
        "name": {},
        "percentage": {}
    },
    "HassHumidifierSetpoint": {
        "name": {},
        "humidity": {}
    },
    "HassLightSet": {
        "name": {},
        "color": {"description": "color (optional)"},
        "brightness": {}
    },
    "HassMediaUnpause": {
        "name": {}
    },
    "HassMediaPause": {
        "name": {}
    },
    "HassMediaNext": {
        "name": {}
    },
    "HassMediaPrevious": {
        "name": {}
    },
    "HassSetVolume": {
        "name": {},
        "volume_level": {}
    },
    "HassSetVolumeRelative": {
        "name": {},
        "volume_step": {"type": "integer", "description": "amount to change the volume"}
    },
    "HassMediaPlayerMute": {
        "name": {}
    },
    "HassMediaPlayerUnmute": {
        "name": {}
    },
    "HassMediaSearchAndPlay": {
        "name": {},
        "search_query": {}
    },
    "HassVacuumStart": {
        "name": {}
    },
    "HassVacuumReturnToBase": {
        "name": {}
    },
    "GetDateTime": {},
    "todo_get_items": {
        "todo_list": {}
    },
    "GetLiveContext": {}
}