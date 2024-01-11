from hid_ups import HIDUPS


class CyberPowerUPS(HIDUPS):
    BATCH_SIZE = 4
    PARAMS = {'battery_percent', 'time_remaining', 'on_battery', 'output_watts', 'output_va'}

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.name = self.device['serial_number']

    def process_8(self, data):
        """ The first field is the battery precent, the 2nd and 3rd are remaining time """
        self.battery_percent = data[1]
        self.time_remaining = int((data[2] + (data[3] * 256)) / 60)

    def process_11(self, data):
        """ If the second field is 3, we're on utility power, if it's 4, we're on battery """
        self.on_battery = int(data[1] == 4)

    def process_25(self, data):
        """ The first field is the output watts, the second is the rollover count """
        self.output_watts = data[1] + (data[2] * 256)

    def process_29(self, data):
        """ The first field is the output VA, the second is the rollover count """
        self.output_va = data[1] + (data[2] * 256)

    def __str__(self):
        try:
            return f"[{self.name}] {self.battery_percent}% battery ({self.time_remaining} minutes), {self.output_watts}W, {self.output_va}VA"
        except AttributeError:
            return "No data"


