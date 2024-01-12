#! /usr/bin/env python3

from hid_ups import HIDUPS

from zenlib.util import init_logger, init_argparser, process_args

from signal import signal, SIGINT


def main():
    argparser = init_argparser(prog=__package__, description='HID based UPS reader')
    logger = init_logger(__package__)
    process_args(argparser, logger=logger)

    ups_list = [dev for dev in HIDUPS.get_UPSs(logger=logger)]

    if not ups_list:
        logger.error('No UPS found')
        return

    def shutdown(signum, frame):
        logger.warning('Shutting down on signal %d', signum)
        for ups in ups_list:
            ups.loop_thread.loop.clear()

    signal(SIGINT, shutdown)
    for ups in ups_list:
        ups.loop_thread.start()


if '__main__' == __name__:
    main()
