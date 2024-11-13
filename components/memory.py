from typing import Union, List
from utils.exceptions import MemoryError
from components.valueConverter import ValueConverter

class Memory:
    def __init__(self):
        self.data = {}
        self.memory = {}
        self.next_data_address = 0

    def store_value(self, name: str, value: Union[str, List[str]]) -> None:
        if isinstance(value, list):  # Es un array
            self._store_array(name, value)
        elif ValueConverter.is_string(value):  # Es un string
            self._store_string(name, value)
        elif value.startswith("'") and value.endswith("'") and len(value) == 3:  # Es un char
            self._store_char(name, value)
        else:
            self._store_number(name, value)

    def _store_array(self, name: str, values: List[str]) -> None:
        start_address = self.next_data_address
        for value in values:
            if value.startswith("'") and value.endswith("'"):
                self.memory[self.next_data_address] = ord(value[1])
            else:
                self.memory[self.next_data_address] = ValueConverter.parse_numeric(value)
            self.next_data_address += 1
        self.data[name] = (start_address, len(values))

    def _store_char(self, name: str, value: str) -> None:
        """Almacena un carácter como su valor ASCII"""
        ascii_value = ord(value[1])
        self.memory[self.next_data_address] = ascii_value
        self.data[name] = self.next_data_address
        self.next_data_address += 1

    def _store_string(self, name: str, value: str) -> None:
        """Almacena un string como array de valores ASCII + null terminator"""
        start_address = self.next_data_address
        string_content = value[1:-1]  # Remover comillas
        
        # Almacenar cada carácter
        for char in string_content:
            self.memory[self.next_data_address] = ord(char)
            self.next_data_address += 1
            
        # Agregar null terminator
        self.memory[self.next_data_address] = 0
        self.next_data_address += 1
        
        # Guardar referencia al inicio y longitud del string
        self.data[name] = (start_address, len(string_content) + 1)

    def _store_number(self, name: str, value: str) -> None:
        """Almacena un número"""
        parsed_value = ValueConverter.parse_numeric(value)
        self.memory[self.next_data_address] = parsed_value
        self.data[name] = self.next_data_address
        self.next_data_address += 1
        
    def get_value(self, name: str, index: int = None) -> int:
        if name not in self.data:
            raise MemoryError(f"Variable no definida: {name}")
        
        if isinstance(self.data[name], tuple):  # Es un array o string
            start_address, size = self.data[name]
            if index is None:
                raise MemoryError(f"Se requiere un índice para acceder al array o string: {name}")
            if index < 0 or index >= size:
                raise MemoryError(f"Índice fuera de rango para {name}: {index}")
            return self.memory[start_address + index]
        else:  # Es un valor simple
            if index is not None:
                raise MemoryError(f"No se puede indexar un valor simple: {name}")
            return self.memory[self.data[name]]

    def get_address(self, name: str) -> int:
        """Obtiene la dirección de una variable"""
        if name not in self.data:
            raise MemoryError(f"Variable no definida: {name}")
        if isinstance(self.data[name], tuple):
            return self.data[name][0]  # Retorna la dirección de inicio para arrays y strings
        return self.data[name]
