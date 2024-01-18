from zenlib.logging import ClassLogger


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

        for param in self.PARAMS:
            setattr(self, param, kwargs.pop(param, None))

        self.open_device()

    def open_device(self):
        """ Open the device """
        self.ups.close()
        self.ups.open_path(self.device['path'])

    async def mainloop(self):
        """ Main loop """
        self.logger.info("[%s] Starting main loop." % self.device['serial_number'])
        while True:
            await self.read_and_process_data()

    async def read_and_process_data(self):
        """ Read data from the UPS and process it """
        while self.current_item < self.BATCH_SIZE:
            try:
                if data := await self.read_data(64):
                    self.process_data(data)
            except OSError as e:
                self.logger.error("[%s] Error reading data: %s" % (self.device['serial_number'], e))
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
            from time import sleep
            self.logger.warning("Could not find device path for serial: %s" % self.device['serial_number'])
            sleep(5)

    async def read_data(self, length):
        """ Read a block of data from the UPS """
        from asyncio import to_thread
        if data := await to_thread(self.ups.read, length):
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

