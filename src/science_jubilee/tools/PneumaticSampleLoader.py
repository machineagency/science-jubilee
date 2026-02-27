import json
import time
from typing import Optional

import requests

from science_jubilee import Machine
from science_jubilee.tools import Tool
from science_jubilee.tools.Tool import (
    Tool,
    ToolConfigurationError,
    ToolStateError,
    requires_active_tool,
)


class PneumaticSampleLoader(Tool):
    """
    Interfaces the AFL sample loader tool with Jubilee deck
    """

    def __init__(
        self, url, port, name, cell_location, safe_position, username, password
    ):
        """
        HTTP Syringe is digital syringe for Jubilee

        """
        self.name = name
        self.url = url + ":" + port
        self.port = port
        self.safe_position = safe_position
        self.cell_location = cell_location

        self.username = username
        self.password = password

        self.arm_down_delay = 10

        self.login()
        self.update_status()
        self.index = None

    def login(self):
        r = requests.post(
            self.url + "/login",
            json={"username": self.username, "password": self.password},
        )

        token = r.json()["token"]
        self.auth_header = {"Authorization": f"Bearer {token}"}

    @classmethod
    def from_config(cls, fp):
        with open(fp) as f:
            kwargs = json.load(f)

        return cls(index, **kwargs)

    # @requires_active_tool
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

        self.prepare_cell()

        # verify arm is raised
        if self.arm_state != "UP":
            raise ValueError("Arm is not raised")

        # sample transfer
        if self._machine.active_tool_index != tool.index:
            self._machine.park_tool()
            self._machine.pickup_tool(tool)

        tool.aspirate(volume, sample_location)
        tool.dispense(volume, self.cell_location)

        self._machine.safe_z_movement()
        self._machine.move_to(z=self.safe_position[2])
        self._machine.move_to(
            x=self.safe_position[0], y=self.safe_position[1], z=self.safe_position[2]
        )

        self._load_sample(volume)

        # wait for arm to be down

        return

    def rinse_cell(self) -> bool:
        """
        Clean the sample cell using pressurized air or cleaning solution.

        Args:
            pressure (float, optional): The pressure (PSI) to use for cleaning.
                                      If None, uses default_clean_pressure from config.
            cycles (int): Number of cleaning cycles to perform.

        Returns:
            bool: True if cleaning was successful, False otherwise.
        """
        self._safe_position()
        self._rinse_cell()

    def prepare_cell(self):
        """
        Prepare the cell for loading - raise arm and make sure it is clean
        """
        if self.get_cell_state() != "RINSED" and self.get_cell_state() != "READY":
            self.rinse_cell()

        self._safe_position()

        self._prepare_load()

        self.update_status()

    def _prepare_load(self):
        """
        Raise the arm of the pneumatic sample loader.
        """

        task = {"task_name": "prepareLoad"}
        task_id = self.enqueue(task)

        while self.get_cell_state() != "READY":
            time.sleep(1)

        return

    def _load_sample(self, volume):

        task = {"task_name": "loadSample", "sampleVolume": volume}

        task_id = self.enqueue(task)

        while self.get_cell_state() != "LOADED":
            time.sleep(1)

        return

    def _rinse_cell(self):
        task = {"task_name": "rinseCell"}
        task_id = self.enqueue(task)

        # block until rinse is done
        while self.get_cell_state() != "RINSED":
            time.sleep(1)

        return

    def update_status(self) -> dict:
        """
        Get the current status of the sample loader.

        Returns:
            dict: Status information including whether sample is loaded
                 and current pressure settings.
        """
        # Get status from HTTP endpoint
        r = requests.get(self.url + "/driver_status", headers=self.auth_header)
        # print("status r code", r.status_code)
        # print("status: ", r.content)
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

    def parse_state(self, status_list: str) -> tuple[str, str]:
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

    def unpause_queue(self):

        r = requests.post(
            self.url + "/pause", headers=self.auth_header, json={"state": False}
        )

        if r.status_code != 200:
            raise Exception(f"Error unpausing queue: {r.json()}")

        return

    def pause_queue(self):

        r = requests.post(
            self.url + "/pause", headers=self.auth_header, json={"state": True}
        )

        if r.status_code != 200:
            raise Exception(f"Error pausing queue: {r.json()}")

        return

    def _safe_position(self):
        """
        Check if currentlu in safe postion, and if not, move to it
        """
        if not self.get_safety_state():
            self._machine.safe_z_movement()
            self._machine.move_to(
                x=self.safe_position[0],
                y=self.safe_position[1],
                z=self.safe_position[2],
            )

        return

    def get_safety_state(self):
        """
        Returns the safety state of the machine.
        """
        positions = self._machine.position
        x, y, z = positions[0], positions[1], positions[2]

        # Check if position is within safe bounds
        if x > self.safe_position[0]:
            return False

        if y < self.safe_position[1]:
            return False

        if z < self.safe_position[2]:
            return False

        return True
