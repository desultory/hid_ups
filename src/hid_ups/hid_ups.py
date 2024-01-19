from zenlib.logging import ClassLogger
from threading import Event
from time import sleep


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
        self.current_item = 0
        self.device = device_data
        self.ups = device()
        self.running = Event()

        for param in self.PARAMS:
            setattr(self, param, kwargs.pop(param, None))

        self.open_device()

    def open_device(self):
        """ Open the device """
        self.ups.close()
        try:
            self.ups.open_path(self.device['path'])
        except OSError as e:
            self.logger.error("[%s] Error opening device: %s" % (self.device['serial_number'], e), exc_info=e)
            sleep(5)
            self.update_device()

    def close(self):
        """ Close the device """
        self.logger.info("[%s] Closing device." % self.device['serial_number'])
        self.running.clear()
        self.ups.close()

    async def mainloop(self):
        """ Main loop """
        self.running.set()
        self.logger.info("[%s] Starting main loop." % self.device['serial_number'])
        while self.running.is_set():
            await self.read_and_process_data()

    async def read_and_process_data(self):
        """ Read data from the UPS and process it """
        while self.current_item < self.BATCH_SIZE and self.running.is_set():
            try:
                if data := await self.read_data(64):
                    self.process_data(data)
            except OSError as e:
                self.logger.error("[%s] Error processing data: %s" % (self.device['serial_number'], e))
                sleep(5)
                self.update_device()
        self.current_item = 0
        self.logger.info(self)

    def update_device(self):
        """ Updates the device path based on the serial """
        from .hid_devices import get_hid_path_from_serial
        if path := get_hid_path_from_serial(self.device['serial_number']):
            self.logger.info("[%s] Updating device path: %s" % (self.device['serial_number'], path))
            self.device['path'] = path
            self.open_device()
        else:
            self.logger.warning("Could not find device path for serial: %s" % self.device['serial_number'])
            sleep(5)

    def _read_data(self, length):
        """ Read a block of data from the UPS """
        try:
            if data := self.ups.read(length):
                self.logger.debug("Read %s bytes: %s", length, data)
                return data
            else:
                self.logger.log(5, "No data read before timeout.")
        except (OSError, ValueError) as e:
            self.logger.error("[%s] Error reading data: %s" % (self.device['serial_number'], e))

    async def read_data(self, length):
        """ Read a block of data from the UPS """
        from asyncio import to_thread
        return await to_thread(self._read_data, length)

    def process_data(self, data):
        """ Process data using the process_<type> methods """
        if not data:
            self.logger.warning("No data")
            return
        if not hasattr(self, f"process_{data[0]}"):
            raise NotImplementedError(f"Unknown data type {data[0]}")

        self.current_item += 1
        return getattr(self, f"process_{data[0]}")(data)

