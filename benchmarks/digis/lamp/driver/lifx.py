from digi import logger
from lifxlan import LifxLAN


def put(dev, power, color):
    # TBD: in a single call
    dev.set_power(power)
    dev.set_color(color)


def get(dev, retry=3):
    for _ in range(retry):
        try:
            status = {
                "power": dev.get_power(),
                "color": dev.get_color(),
            }
            return status
        except Exception as e:
            logger.info(f"lifx: unable to get status due to {e}")
            continue
    return None


def discover(_id):
    try:
        devices = LifxLAN().get_lights()
        device_by_mac = {d.get_mac_addr(): d for d in devices}

        logger.info(f"lifx: found {len(devices)} light(s): "
                    f"{device_by_mac}\n")
        return device_by_mac[_id]
    except Exception as e:
        logger.info(f"lifx: unable to find device due to {e}")
        return None


if __name__ == '__main__':
    discover(_id=None)
