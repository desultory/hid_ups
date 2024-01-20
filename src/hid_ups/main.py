#! /usr/bin/env python3

from hid_ups import HIDUPS
from zenlib.util import get_args_n_logger
from asyncio import gather, get_event_loop


def main():
    args, logger = get_args_n_logger(package=__package__, description='HID based UPS reader')

    ups_list = [dev for dev in HIDUPS.get_UPSs(logger=logger)]

    if not ups_list:
        logger.error('No UPS found')
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
        logger.info('Main loop closed')


if '__main__' == __name__:
    main()
