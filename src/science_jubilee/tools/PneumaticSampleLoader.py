from typing import Optional
from science_jubilee.machine import Machine
import json
import time

class PneumaticSampleLoader(Tool):
    """
    Interfaces the AFL sample loader tool with Jubilee deck
    """


    def __init__(self, url, port, name, cell_location, safe_position, username, password):
        """
        HTTP Syringe is digital syringe for Jubilee

        """
        self.name = name
        self.url = url
        self.port = port
        self.safe_position = safe_position
        self.cell_location = cell_location

        self.username = username
        self.password = password

        self.arm_down_delay = 10
        self.status = self.get_status()

        self.login()



    def login(self):
        r = requests.post(self.url + "/login", json={"username": self.username, "password": self.password})

        token = r.json()['token']
        self.auth_header = {"Authorization": f"Bearer {token}"}


    @classmethod
    def from_config(cls, fp):
        with open(fp) as f:
            kwargs = json.load(f)

        return cls(index, **kwargs)

    @requires_active_tool
    def load_sample(self, tool, sample_location: str, volume) -> bool:
        """
        Load a sample into the sample cell using pneumatic pressure.
        First moves to the specified position, then performs the loading operation.
        
        Args:
            tool: pipette-like tool (ie OT P300, HTTP syringe)
            sample_location: location 
        Returns:
            bool: True if sample was loaded successfully, False otherwise.
        """

        # Check that cell is in state rinsed
        if self.get_cell_state() != "RINSED":
            raise ValueError("Cell is not in state rinsed")
        
        # move jubilee to safe position
        self.machine.move_to(x=self.safe_position[0], y=self.safe_position[1], z=self.safe_position[2])

        # raise arm
        self.prepare_load()

        # sample transfer
        current_tool = self.machine.active_tool_index
        if self.machine._get_tool_index(current_tool) != current_tool:
            machine.park_tool()
            machine.pickup_tool(tool)

        tool.aspirate(volume, sample_location)
        tool.dispense(volume, self.cell_location)

        self.machine.move_to(x=self.safe_position[0], y=self.safe_position[1], z=self.safe_position[2])

        self._load_sample(volume)

        # wait for arm to be down
        

        return

    def rinse_cell(self, pressure: Optional[float] = None, cycles: int = 3) -> bool:
        """
        Clean the sample cell using pressurized air or cleaning solution.
        
        Args:
            pressure (float, optional): The pressure (PSI) to use for cleaning.
                                      If None, uses default_clean_pressure from config.
            cycles (int): Number of cleaning cycles to perform.
        
        Returns:
            bool: True if cleaning was successful, False otherwise.
        """
        
        self._rinse_cell()


    def _prepare_load(self):
        """
        Raise the arm of the pneumatic sample loader.
        """

        task = {'task': 'prepareLoad'}
        task_id = self.enqueue(task)

    def _load_sample(self, volume):

        task = {'task': 'loadSample', 'volume': volume}

        task_id = self.enqueue(task)

    def _rinse_cell(self):
        task = {'task': 'rinseCell'}
        task_id = self.enqueue(task)


    def update_status(self) -> dict:
        """
        Get the current status of the sample loader.
        
        Returns:
            dict: Status information including whether sample is loaded
                 and current pressure settings.
        """
        # Get status from HTTP endpoint
        r = requests.post(self.url + "/driver_status", headers=self.auth_header)
        status_str = r.content.decode("utf-8")
        

        self.status_list = json.loads(status_str)
        self.cell_state, self.arm_state = self.parse_state(self.status_list)

    def get_cell_state(self) -> str:    
        """
        Get the current state of the sample cell.
        
        Returns:
            str: The current state of the sample cell (e.g., 'LOADED', 'IDLE', etc.)

        """
        self.update_status()
        return self.cell_state
    def parse_state(self, status_str: str) -> tuple[str, str]:
        """
        Parse the state and arm state from a status string.
        
        Args:
            status_str (str): Raw status string from the device
            
        Returns:
            tuple[str, str]: A tuple containing (cell_state, arm_state)
                            e.g., ('LOADED', 'DOWN')
        """
        try:
            # Convert string to list using json.loads
            status_list = json.loads(status_str)
            
            cell_state = "UNKNOWN"
            arm_state = "UNKNOWN"
            
            # Find both state entries
            for item in status_list:
                if item.startswith("State: "):
                    cell_state = item.split("State: ")[1]
                elif item.startswith("Arm State: "):
                    arm_state = item.split("Arm State: ")[1]
            
            return cell_state, arm_state
            
        except json.JSONDecodeError:
            print("Error parsing status string")
            return "UNKNOWN", "UNKNOWN"

        def enqueue(self, task: dict):
            """
            Enqueue a task to be executed by the pneumatic sample loader.

            returns task uuid
            """

            r = requests.post(self.url + "/enqueue", headers=self.auth_header, json=task)

            if r.status_code != 200:
                raise Exception(f"Error enqueuing task: {r.json()}")

            return r.content.decode("utf-8")
