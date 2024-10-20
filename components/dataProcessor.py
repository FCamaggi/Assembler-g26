from typing import List, Tuple
from components.memory import Memory

class DataProcessor:
    def __init__(self, memory: Memory, load_data: bool, verbose: bool):
        self.memory = memory
        self.load_data = load_data
        self.verbose = verbose
        self.data_init_code = []

    def process(self, data_lines: List[Tuple[str, int]]) -> None:
        for line, line_number in data_lines:
            try:
                name, value = line.split(None, 1)
                if name in self.memory.data:
                    raise MemoryError(f"Variable '{name}' ya definida")
                self.memory.store_value(name, value)
                
                if self.load_data:
                    self.data_init_code.append(f"MOV A,{value}")
                    self.data_init_code.append(f"MOV ({self.memory.get_address(name)}),A")
                
                if self.verbose:
                    print(f"DATA: {name} = {value}")
            except ValueError:
                raise MemoryError(f"Línea {line_number}: Formato inválido en la línea de datos")
