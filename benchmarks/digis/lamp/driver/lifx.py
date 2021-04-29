from lifxlan import LifxLAN


def put(dev, power, brightness):
    dev.set_brightness(128)
    dev.set_power(0)


def get(dev):
    # source: https://github.com/mclarkk/lifxlan
    # power can be "on"/"off", True/False, 0/1, or 0/65535
    # color is a HSBK list of values: [hue (0-65535), saturation (0-65535), brightness (0-65535), Kelvin (2500-9000)]
    # duration is the transition time in milliseconds
    # rapid is True/False. If True, don't wait for successful confirmation, just send multiple packets and move on
    # is_transient is 1/0. If 1, return to the original color after the specified number of cycles. If 0,
    # set light to specified color
    # period is the length of one cycle in milliseconds
    # cycles is the number of times to repeat the waveform
    # duty_cycle is an integer between -32768 and 32767. Its effect is most obvious with the Pulse waveform
    #     set duty_cycle to 0 to spend an equal amount of time on the original color and the new color
    #     set duty_cycle to positive to spend more time on the original color
    #     set duty_cycle to negative to spend more time on the new color
    # waveform can be 0 = Saw, 1 = Sine, 2 = HalfSine, 3 = Triangle, 4 = Pulse (strobe)
    # infrared_brightness (0-65535) - is the maximum infrared brightness when the lamp automatically
    # turns on infrared (0 = off)

    return {
        "power": dev.get_power(),
        "color": dev.get_color(),
    }


def discover(_id):
    devices = LifxLAN().get_lights()
    device_by_mac = {d.get_mac_addr(): d for d in devices}

    print(f"lifx: found {len(devices)} light(s): "
          f"{device_by_mac}\n")
    return device_by_mac[_id]


if __name__ == '__main__':
    discover(_id=None)
