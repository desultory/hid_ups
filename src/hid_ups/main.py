#! /usr/bin/env python3

from hid_ups import HIDUPS
from zenlib.util import init_logger, init_argparser, process_args
from asyncio import run, gather, get_event_loop


async def run_loops(loops):
    await gather(*loops)


def main():
    argparser = init_argparser(prog=__package__, description='HID based UPS reader')
    logger = init_logger(__package__)
    process_args(argparser, logger=logger)

    ups_list = [dev for dev in HIDUPS.get_UPSs(logger=logger)]

    if not ups_list:
        logger.error('No UPS found')
        return

    mainloop = get_event_loop()
    for ups in ups_list:
        mainloop.run_until_complete(ups.mainloop())


if '__main__' == __name__:
    main()
