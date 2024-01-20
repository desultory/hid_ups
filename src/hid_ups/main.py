#! /usr/bin/env python3

from hid_ups import HIDUPS
from zenlib.util import get_kwargs
from asyncio import gather, get_event_loop


def main():
    kwargs = get_kwargs(package=__package__, description='HID based UPS reader')

    ups_list = [dev for dev in HIDUPS.get_UPSs(**kwargs)]

    if not ups_list:
        raise SystemExit('No UPS found')
        return

    mainloop = get_event_loop()
    tasks = [mainloop.create_task(ups.mainloop()) for ups in ups_list]

    try:
        mainloop.run_until_complete(gather(*tasks))
    except KeyboardInterrupt:
        for task in tasks:
            task.cancel()
    finally:
        mainloop.close()

    print("Exiting...")


if '__main__' == __name__:
    main()
