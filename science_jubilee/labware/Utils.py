import json
import os


def json2dict(f, path =None):
    lab_def = {}
    if path:
        file_path = os.path.join(path,f)
    else:
        file_path = f
    with open(file_path) as lab_file:
        # removes the .json extnesion for name

        labware_name = os.path.splitext(f)[0]
        lab_def = json.load(lab_file)
    

    return lab_def


def dict2json(filename: str , dict: dict , path : str= None):
    
    if path:
             name = path + filename + '.json'
    else:
        name = filename + '.json'
    with open(name , 'w') as lab_file:
        
        json.dump(dict, lab_file , indent=4)

    lab_file.close()

    if path == None:
         path='./'
    else:
         pass
        
    return print('The JSON file was saved as *{}* in {}'. format(filename, path))

class pipette_iterator():

    def __init__(self, tiprack):
        self.tiprack = tiprack
        self.index = 0

    def next(self):
        try:
            result = self.tiprack[self.index]
            self.index += 1
        except IndexError:
            raise StopIteration
        return result

    def prev(self):
        self.index -= 1
        if self.index < 0:
            raise StopIteration
        return self.tiprack[self.index]

    def __iter__(self):
        return self