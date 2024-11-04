from typing import Dict
from utils.exceptions import InvalidOperandError

class ValueConverter:
    @staticmethod
    def get_type(param: str, types: Dict) -> str:
        if param in ['A', 'B']:
            return 'reg'
        elif param.startswith('(') and param.endswith(')'):
            inner = param[1:-1]
            if inner in ['A', 'B']:
                return f'({inner})'
            return 'dir'
        elif ValueConverter.is_numeric(param):
            return 'lit'
        return 'var'  # Nuevo tipo para variables

    @staticmethod
    def is_numeric(value: str) -> bool:
        if not value:
            return False
        if value.isdigit():
            return True
        if value.endswith('b') and set(value[:-1]).issubset('01'):
            return True
        if value.endswith('h') and all(c in '0123456789ABCDEFabcdef' for c in value[:-1]):
            return True
        if value.startswith("'") and value.endswith("'") and len(value) == 3:
            return True
        return False

    @staticmethod
    def parse_numeric(value: str) -> int:
        if not value:
            raise ValueError("No se puede convertir una cadena vacía a número")
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
        if param in ['A', 'B']:
            return types[param]
        elif param.startswith('(') and param.endswith(')'):
            inner = param[1:-1]
            if inner in ['A', 'B']:
                return types[f'({inner})']
            return types['(dir)']
        elif ValueConverter.is_numeric(param):
            return types['lit']
        else:
            # Para variables, usamos direccionamiento directo
            return types['(dir)']

    @staticmethod
    def literal_or_direct_value(param: str, types: Dict, lit_params: Dict, labels: Dict, data: Dict, memory, instruction_address: int) -> str:
        max_value = 2**lit_params['bits'] - 1
        
        try:
            # Caso especial para variables (incluyendo arrays)
            if param in data:
                address = memory.get_address(param)
                return format(address, f'0{lit_params["bits"]}b')
            
            # Direccionamiento directo
            if param.startswith('(') and param.endswith(')'):
                inner = param[1:-1]
                if inner in ['A', 'B']:
                    return '0' * lit_params['bits']
                elif inner in data:
                    address = memory.get_address(inner)
                    return format(address, f'0{lit_params["bits"]}b')
                elif ValueConverter.is_numeric(inner):
                    address = ValueConverter.parse_numeric(inner)
                    if address > max_value:
                        raise InvalidOperandError(f"Dirección fuera de rango: {address}")
                    return format(address, f'0{lit_params["bits"]}b')
                else:
                    raise InvalidOperandError(f"Variable no definida: {inner}")
            
            # Literales
            if ValueConverter.is_numeric(param):
                value = ValueConverter.parse_numeric(param)
                if value > max_value:
                    raise InvalidOperandError(f"Literal fuera de rango: {value}")
                return format(value, f'0{lit_params["bits"]}b')
            
            # Etiquetas
            if param in labels:
                address = labels[param]
                if address > max_value:
                    raise InvalidOperandError(f"Dirección de etiqueta fuera de rango: {address}")
                return format(address, f'0{lit_params["bits"]}b')
            
            raise InvalidOperandError(f"Operando no válido: {param}")
            
        except ValueError as e:
            raise InvalidOperandError(f"Error al procesar valor: {str(e)}")
            
    @staticmethod
    def get_param_description(param_type: str, value: str = '') -> str:
        """Retorna una descripción legible del tipo de parámetro."""
        if param_type == 'reg':
            return value
        elif param_type == 'dir':
            return '(dir)'
        elif param_type == 'lit':
            return 'lit'
        elif param_type.startswith('('):
            return param_type
        elif param_type == 'var':
            return 'var'
        return param_type