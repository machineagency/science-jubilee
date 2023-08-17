import numpy as np

from dataclasses import dataclass
from typing import List, Dict, Tuple


@dataclass
class Well: 
    name: str  # Name of the well, e.g., 'A1', 'B1', etc.
    depth: float
    totalLiquidVolume: float
    shape: str
    diameter: float
    x: float
    y: float
    z: float
    offset: Tuple[float] = None
        
    @property
    def x(self):
        if self.offset is not None:
            return self._x + self.offset[0]
        else:
            return self._x
    
    @x.setter
    def x(self, new_x):
        self._x = new_x
        
    @property
    def y(self):
        if self.offset is not None:
            return self._y + self.offset[1]
        else:
            return self._y
    
    @y.setter
    def y(self, new_y):
        self._y = new_y
        
    @property
    def z(self):
        return self._z
    
    @z.setter
    def z(self, new_z):
        self._z = new_z

    @property
    def top(self):
        return self.z + self.depth

    @property
    def bottom(self):
        return self.z
        

@dataclass(repr=False)
class WellSet:
    wells: Dict[str, Well]
    def __repr__(self):
        return str(list(f'{self.wells.keys()} on slot {self.slot}'))
    def __getitem__(self, id_):
        try:
            return self.wells[id_]
        except KeyError:
            return list(self.wells.values())[id_]
        
@dataclass(repr=False)
class Row(WellSet):
    identifier: str  # For example, "A", "B", etc.  

@dataclass(repr=False)
class Column(WellSet):
    identifier: int  # For example, 1, 2, etc.

class Labware(WellSet):
    def __init__(self, data: dict, offset: Tuple[float]=None):
        self.data = data
        self.wells_data = self.data.get('wells', {})
        self.data['ordering'] = np.array(self.data['ordering']).T
        self.row_data, self.column_data, self.wells = self._create_rows_and_columns()
        self.offset = offset
        self.slot= None 
        
    def __repr__(self):

        display = self.metadata()['displayCategory'] + ': ' + self.parameters()['loadName'] 
        if self.slot is not None:
            display = display + ' ' + f" on {self.slot}"
        return display

    def _create_rows_and_columns(self):
        rows = {}
        columns = {}
        wells = {}

        for row_order, column_data in enumerate(self.data.get('ordering', [])):
            row_id = column_data[0][0]  # Assumes the first char is the row identifier, e.g., "A" in "A1"
            col_ids = [int(well[1:]) for well in column_data]  # Extracts column number, e.g., "1" in "A1"
#             print(row_id, col_ids)

            if row_id not in rows:
                rows[row_id] = {}

            for col_order, well_id in enumerate(column_data):
                well = Well(name=well_id, **self.wells_data[well_id])
                rows[row_id][well_id] = well

                if col_order + 1 not in columns:  # +1 since indexing starts at 0
                    columns[col_order + 1] = {}

                columns[col_order + 1][well_id] = well
                wells[well_id] = well

        # Convert dictionary data to Row and Column classes
        rows = {k: Row(identifier=k, wells=v) for k, v in rows.items()}
        columns = {k: Column(identifier=k, wells=v) for k, v in columns.items()}

        return rows, columns, wells
    
    def get_row(self, row_id: str) -> Row:
        
        return self.row_data.get(row_id)

    def get_column(self, col_id: int) -> Column:
        return self.column_data.get(col_id)
    
    @property
    def shape(self):
        return (len(self.row_data), len(self.column_data))
    
    @property
    def ordering(self) -> List[List[str]]:
        return self.data.get('ordering', [])

    @property
    def brand(self) -> dict:
        return self.data.get('brand', {})

    # @property
    def metadata(self) -> dict:
        return self.data.get('metadata', {})
    
    @property
    def displayName(self):
        return self.metadata()['displayName']

    @ property
    def labwareType(self):
        return self.metadata()['displayCategory']
    
    @property
    def volumeUnits(self):
        return self.metadata()['displayVolumeUnits']

    @property
    def dimensions(self) -> dict:
        return self.data.get('dimensions', {})

    @property
    def groups(self) -> List[dict]:
        return self.data.get('groups', [])


    def parameters(self) -> dict:
        return self.data.get('parameters', {})

    @property
    def isTipRack(self):
        return self.parameters()['isTiprack']

    @property
    def tipLength(self):
        try:
            return self.parameters()['tipLength']
        except:
            pass

    @property
    def tipOverlap(self):
        try:
            return self.parameters()['tipOverlap']
        except:
            pass

    @property
    def namespace(self) -> str:
        return self.data.get('namespace', "")

    @property
    def version(self) -> int:
        return self.data.get('version', 1)

    @property
    def schemaVersion(self) -> int:
        return self.data.get('schemaVersion', 1)

    @property
    def cornerOffsetFromSlot(self) -> dict:
        return self.data.get('cornerOffsetFromSlot', {})
    
    @property
    def offset(self):
        return self._offset
    
    @offset.setter
    def offset(self, new_offset):
        self._offset = new_offset
        if new_offset is not None:
            for w in self:
                w.offset = new_offset
    
    def add_slot(self, slot_):
        self.slot = slot_
    
    def withWellOrder(self, order = 'cols') -> list:

        if order in ['rows', 'row', 'Rows', 'Row', 'R']:
            for row in self.row_data.values():
                for well in row:
                    yield well
        elif order in ['cols', 'col' ,'C', 'columns', 'Columns']:
            for col in self.column_data.values():
                for well in col:
                    yield well
        else:
            print('Order needs to be either rows or columns')
