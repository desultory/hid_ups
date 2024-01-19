from zenlib.logging import ClassLogger
from threading import Semaphore
from asyncio import sleep


class HIDUPS(ClassLogger):
    BATCH_SIZE = 1
    PARAMS = {'name'}

    @staticmethod
    def get_UPSs(*args, **kwargs):
        """ Return a list of UPSs """
        from .hid_devices import get_hid_devices
        for data, device_type in get_hid_devices():
            yield device_type(data, *args, **kwargs)

    def __init__(self, device_data, run_forever=False, max_fails=5, *args, **kwargs):
        from hid import device
        super().__init__(*args, **kwargs)
        self.current_item = 0
        self.fail_count = 0
        self.max_fails = max_fails
        self.run_forever = run_forever
        self.device = device_data
        self.running = Semaphore()
        self.ups = device()

        for param in self.PARAMS:
            setattr(self, param, kwargs.pop(param, None))

        self.open_device()

    def open_device(self):
        """ Open the device """
        self.fail_count = 0
        self.ups.open_path(self.device['path'])

        # Ensure this message is logged
        level = self.logger.level
        if self.logger.level > 20:
            self.logger.setLevel(20)
        self.logger.info("[%s] Opened device." % self.device['serial_number'])
        self.logger.setLevel(level)

    def close(self):
        """ Close the device """
        self.running.release()
        with self.running:
            self.ups.close()
            self.logger.info("[%s] Closed device." % self.device['serial_number'])

    def _clear_data(self):
        self.logger.debug("[%s] Clearing data." % self.device['serial_number'])
        for param in self.PARAMS:
            setattr(self, param, None)

    async def mainloop(self):
        """ Main loop """
        self.logger.info("[%s] Starting main loop." % self.device['serial_number'])

        with self.running:
            while not self.running._value:
                await self.read_and_process_data()
        self.ups.close()
        self.logger.info("[%s] Main loop stopped." % self.device['serial_number'])

    async def read_and_process_data(self):
        """ Read data from the UPS and process it """
        while self.current_item < self.BATCH_SIZE and self.running._value == 0:
            try:
                if data := await self.read_data(64):
                    self.process_data(data)
                    self.fail_count = 0
            except (OSError, ValueError) as e:
                self.logger.error("[%s] Error processing data: %s" % (self.device['serial_number'], e))
                self.logger.info("[%s] Fail count: %s" % (self.device['serial_number'], self.fail_count))
                if not self.run_forever and self.fail_count >= self.max_fails:
                    self.logger.critical("[%s] Too many errors, stopping UPS listener." % self.device['serial_number'])
                    self.running.release()
                self.fail_count += 1
                self._clear_data()
                await sleep(5)
                self.update_device()
        self.current_item = 0
        self.logger.info(self)

    async def update_device(self):
        """ Updates the device path based on the serial """
        from .hid_devices import get_hid_path_from_serial
        if hasattr(self, 'ups'):
            self.logger.info("[%s] Closing device." % self.device['serial_number'])
            self.ups.close()
        if path := get_hid_path_from_serial(self.device['serial_number']):
            self.logger.info("[%s] Updating device path: %s" % (self.device['serial_number'], path))
            self.device['path'] = path
            try:
                self.open_device()
            except OSError as e:
                self.logger.error("[%s] Error opening device: %s" % (self.device['serial_number'], e), exc_info=True)
                await sleep(2)
        else:
            self.logger.warning("Could not find device path for serial: %s" % self.device['serial_number'])
            await sleep(5)

    def _read_data(self, length):
        """ Read a block of data from the UPS """
        self.logger.log(5, "[%s] Reading %s bytes." % (self.device['serial_number'], length))
        try:
            if data := self.ups.read(length):
                self.logger.debug("[%s] Read %s bytes: %s" % (self.device['serial_number'], length, data))
                return data
            else:
                self.logger.log(5, "No data read before timeout.")
        except (OSError, ValueError) as e:
            self.logger.error("[%s] Error reading data: %s" % (self.device['serial_number'], e))

    async def read_data(self, length):
        """ Read a block of data from the UPS """
        from asyncio import to_thread
        self.logger.debug("[%s] Creating thread to read data.", self.device['serial_number'])
        data = await to_thread(self._read_data, length)
        if data is None:
            raise ValueError("[%s] Unable to read data." % self.device['serial_number'])
        return data

    def process_data(self, data):
        """ Process data using the process_<type> methods """
        if not data:
            self.logger.warning("No data")
            return
        if not hasattr(self, f"process_{data[0]}"):
            raise NotImplementedError(f"Unknown data type {data[0]}")

        self.current_item += 1
        self.logger.debug("[%s] Processing data: %s" % (self.device['serial_number'], data))
        getattr(self, f"process_{data[0]}")(data)

