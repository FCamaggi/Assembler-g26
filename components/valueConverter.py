from typing import Dict
from utils.exceptions import InvalidOperandError

class ValueConverter:
    @staticmethod
    def get_type(param: str, types: Dict) -> str:
        if param in types:
            return 'reg'
        elif '(' in param:
            return 'dir'
        elif ValueConverter.is_numeric(param):
            return 'lit'
        return 'unknown'

    @staticmethod
    def is_numeric(value: str) -> bool:
        # Comprueba si es un número decimal, binario o hexadecimal
        return (value.isdigit() or 
                (value.endswith('b') and set(value[:-1]).issubset('01')) or
                (value.endswith('h') and all(c in '0123456789ABCDEFabcdef' for c in value[:-1])) or
                (value.startswith("'") and value.endswith("'") and len(value) == 3))

    @staticmethod
    def parse_numeric(value: str) -> int:
        if value.endswith('b'):
            return int(value[:-1], 2)
        elif value.endswith('h'):
            return int(value[:-1], 16)
        elif value.startswith("'") and value.endswith("'"):
            return ord(value[1])
        else:
            return int(value)

    @staticmethod
    def param_to_binary(param: str, types: Dict, types_params: Dict) -> str:
        param_type = ValueConverter.get_type(param, types)
        if param_type == 'reg':
            return types[param]
        elif param_type == 'dir':
            return ValueConverter.process_dir(param, types)
        elif param_type == 'lit':
            return types[param_type]
        return "".zfill(int(types_params['bits']/2))

    @staticmethod
    def process_dir(param: str, types: Dict) -> str:
        if param[1] in types:
            return types[param]
        return types['(dir)']

    @staticmethod
    def literal_or_direct_value(param: str, types: Dict, lit_params: Dict, labels: Dict, data: Dict, memory: Dict) -> str:
        param_type = ValueConverter.get_type(param, types)
        max_value = 2**lit_params['bits'] - 1  # 4095 para un literal de 12 bits

        if param_type == 'dir':
            dir_value = param[1:-1]
            
            # Si es un número, tratarlo como una dirección literal
            if ValueConverter.is_numeric(dir_value):
                address = ValueConverter.parse_numeric(dir_value)
            elif '+' in dir_value:  # Manejo de arrays e índices
                array_name, index = dir_value.split('+')
                if array_name not in data:
                    raise InvalidOperandError(f"Array no definido: {array_name}")
                base_address, size = data[array_name]
                index = ValueConverter.parse_numeric(index)
                if index >= size:
                    raise InvalidOperandError(f"Índice fuera de rango para {array_name}: {index}")
                address = base_address + index
            else:
                if dir_value not in data:
                    raise InvalidOperandError(f"Variable no definida: {dir_value}")
                address = data[dir_value] if isinstance(data[dir_value], int) else data[dir_value][0]

            if address > max_value:
                raise InvalidOperandError(f"Dirección fuera de rango: {address}. El máximo permitido es {max_value}")
            return format(address, f'0{lit_params["bits"]}b')
        
        elif param_type == 'lit':
            value = ValueConverter.parse_numeric(param)
            if value > max_value:
                raise InvalidOperandError(f"Literal fuera de rango: {value}. El máximo permitido es {max_value}")
            return format(value, f'0{lit_params["bits"]}b')
        
        raise InvalidOperandError(f"Tipo de parámetro no reconocido: {param}")