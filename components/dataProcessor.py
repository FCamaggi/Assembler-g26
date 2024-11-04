from typing import List, Tuple
from components.memory import Memory
from utils.exceptions import MemoryError

class DataProcessor:
    def __init__(self, memory: Memory, load_data: bool, verbose: bool):
        self.memory = memory
        self.load_data = load_data
        self.verbose = verbose
        self.data_init_code = []

    def process(self, data_lines: List[Tuple[str, int]]) -> None:
        current_array_name = None
        current_array_values = []

        for line, line_number in data_lines:
            try:
                parts = line.split(None, 1)
                
                # Si tenemos solo un valor, podría ser parte de un array
                if len(parts) == 1 and current_array_name is not None:
                    current_array_values.append(parts[0])
                    if self.verbose:
                        print(f"DATA: {current_array_name}[{len(current_array_values)-1}] = {parts[0]}")
                else:
                    # Si estábamos procesando un array, guardarlo
                    if current_array_name is not None:
                        self.memory.store_value(current_array_name, current_array_values)
                        current_array_name = None
                        current_array_values = []
                    
                    # Procesar nueva variable o inicio de array
                    if len(parts) != 2:
                        raise MemoryError(f"Línea {line_number}: Formato inválido en la línea de datos")
                    
                    name, value = parts
                    current_array_name = name
                    current_array_values = [value]
                    
                    if self.verbose:
                        print(f"DATA: {name} = {value}")
                        
            except ValueError as e:
                raise MemoryError(f"Línea {line_number}: {str(e)}")
        
        # Guardar el último array si existe
        if current_array_name is not None:
            self.memory.store_value(current_array_name, current_array_values)

        if self.load_data and self.verbose:
            print("Código de inicialización de datos generado")