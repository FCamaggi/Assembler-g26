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
        if param in types:
            return types[param]
        elif param.startswith('(') and param.endswith(')'):
            return types['(dir)']
        else:
            return types['lit']

    @staticmethod
    def process_dir(param: str, types: Dict) -> str:
        if param[1] in types:
            return types[param]
        return types['(dir)']
    
    @staticmethod
    def literal_or_direct_value(param: str, types: Dict, lit_params: Dict, labels: Dict, data: Dict, memory, instruction_address: int) -> str:
        param_type = ValueConverter.get_type(param, types)
        max_value = 2**lit_params['bits'] - 1

        if param_type == 'dir':
            dir_value = param[1:-1]
            
            if ValueConverter.is_numeric(dir_value):
                address = ValueConverter.parse_numeric(dir_value)
            elif dir_value in data:
                address = data[dir_value]
            else:
                raise InvalidOperandError(f"Variable no definida: {dir_value}")

            if address > max_value:
                raise InvalidOperandError(f"Dirección fuera de rango: {address}. El máximo permitido es {max_value}")
            return format(address, f'0{lit_params["bits"]}b')
        
        elif param_type == 'lit':
            if param in data:
                value = memory.get_value(param)
            elif param in labels:
                value = labels[param]
            else:
                value = ValueConverter.parse_numeric(param)
            
            if value > max_value:
                raise InvalidOperandError(f"Literal fuera de rango: {value}. El máximo permitido es {max_value}")
            return format(value, f'0{lit_params["bits"]}b')
        
        raise InvalidOperandError(f"Tipo de parámetro no reconocido: {param}")