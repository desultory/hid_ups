
from zenlib.logging import ClassLogger
from zenlib.threading import ZenThread


class HIDUPS(ClassLogger):
    BATCH_SIZE = 1
    PARAMS = {'name'}

    @staticmethod
    def get_UPSs(*args, **kwargs):
        """ Return a list of UPSs """
        from .hid_devices import get_hid_devices
        for data, device_type in get_hid_devices():
            yield device_type(data, *args, **kwargs)

    def __init__(self, device_data, *args, **kwargs):
        super().__init__(*args, **kwargs)
        from hid import device
        self.loop_thread = ZenThread(target=self.read_and_process_data, looping=True, logger=self.logger)
        self.current_item = 0
        self.device = device_data

        for param in self.PARAMS:
            setattr(self, param, kwargs.pop(param, None))

        ups = device()
        ups.open_path(self.device['path'])
        self.ups = ups

    def start(self):
        """ Start the UPS """
        self.loop_thread.start()

    def read_and_process_data(self):
        """ Read data from the UPS and process it """
        while self.current_item < self.BATCH_SIZE:
            try:
                if data := self._read_data(64):
                    self.process_data(data)
            except OSError as e:
                from time import sleep
                self.logger.error("Error reading data: %s", e)
                sleep(1)
        self.current_item = 0
        self.logger.info(self)

    def _read_data(self, length):
        """ Read a block of data from the UPS """
        if data := self.ups.read(length):
            self.logger.debug("Read %s bytes: %s", length, data)
            return data
        else:
            self.logger.log(5, "No data read before timeout.")

    def process_data(self, data):
        """ Process data using the process_<type> methods """
        if not data:
            self.logger.warning("No data")
            return
        if not hasattr(self, f"process_{data[0]}"):
            raise NotImplementedError(f"Unknown data type {data[0]}")

        self.current_item += 1
        return getattr(self, f"process_{data[0]}")(data)

