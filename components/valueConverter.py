from typing import Dict, List
from utils.exceptions import InvalidOperandError

class ValueConverter:
    @staticmethod
    def get_type(param: str, types: Dict) -> str:
        if param == 'A' or param == 'B':
            return param
        elif param.startswith('(') and param.endswith(')'):
            inner = param[1:-1].strip()
            if inner == 'A' or inner == 'B':
                return f'({inner})'
            # Si el contenido dentro de los paréntesis es un número (incluyendo con sufijos), es una dirección
            if ValueConverter.is_numeric(inner):
                return '(dir)'
            return 'dir'
        elif ValueConverter.is_numeric(param):
            return 'lit'
        elif ValueConverter.is_string(param):
            return 'string'
        return 'var'

    @staticmethod
    def is_string(value: str) -> bool:
        """Determina si un valor es un string"""
        value = value.strip()
        return value.startswith('"') and value.endswith('"')

    @staticmethod
    def is_numeric(value: str) -> bool:
        """Determina si un valor es numérico"""
        if not value or ValueConverter.is_string(value):
            return False
        
        value = value.strip()
        
        # Verificar caracteres
        if value.startswith("'") and value.endswith("'") and len(value) == 3:
            return True
            
        # Verificar números decimales con sufijo 'd' o sin sufijo
        if value.endswith('d'):
            return value[:-1].isdigit()
        if value.isdigit():
            return True
            
        # Verificar números binarios
        if value.endswith('b'):
            binary_part = value[:-1]
            return all(bit in '01' for bit in binary_part)
            
        # Verificar números hexadecimales
        if value.endswith('h'):
            hex_part = value[:-1]
            return all(c in '0123456789ABCDEFabcdef' for c in hex_part)
            
        return False

    @staticmethod
    def parse_numeric(value: str) -> int:
        """Convierte un valor numérico a entero"""
        if ValueConverter.is_string(value):
            raise InvalidOperandError("No se puede convertir un string a número")
            
        value = value.strip()
        
        try:
            if value.endswith('d'):
                return int(value[:-1])
            elif value.endswith('b'):
                return int(value[:-1], 2)
            elif value.endswith('h'):
                return int(value[:-1], 16)
            elif value.startswith("'") and value.endswith("'") and len(value) == 3:
                return ord(value[1])
            else:
                return int(value)
        except ValueError:
            raise InvalidOperandError(f"Valor numérico inválido: {value}")

    @staticmethod
    def parse_string(value: str) -> List[int]:
        """Convierte un string a una lista de valores ASCII"""
        if not ValueConverter.is_string(value):
            raise InvalidOperandError("No es un string válido")
        
        content = value[1:-1]  # Remover comillas
        return [ord(c) for c in content] + [0]  # Incluir null terminator

    @staticmethod
    def param_to_binary(param: str, types: Dict, types_params: Dict) -> str:
        """Convierte un parámetro a su representación binaria"""
        if param == 'A' or param == 'B':
            return types[param]
        elif param.startswith('(') and param.endswith(')'):
            inner = param[1:-1].strip()
            if inner == 'A' or inner == 'B':
                return types[f'({inner})']
            return types['(dir)']
        elif ValueConverter.is_numeric(param):
            return types['lit']
        elif ValueConverter.is_string(param):
            return types['(dir)']  # Los strings se almacenan en memoria
        else:
            return types['(dir)']

    @staticmethod
    def literal_or_direct_value(param: str, types: Dict, lit_params: Dict, labels: Dict, data: Dict, memory, instruction_address: int) -> str:
        max_value = 2**lit_params['bits'] - 1
        
        try:
            # Caso especial para strings
            if ValueConverter.is_string(param):
                return '0' * lit_params['bits']  # String length o dirección base
                
            # Caso especial para variables
            if param in data:
                address = memory.get_address(param)
                return format(address, f'0{lit_params["bits"]}b')
            
            # Direccionamiento directo
            if param.startswith('(') and param.endswith(')'):
                inner = param[1:-1].strip()
                if inner in ['A', 'B']:
                    return '0' * lit_params['bits']
                elif inner in data:
                    address = memory.get_address(inner)
                    return format(address, f'0{lit_params["bits"]}b')
                elif ValueConverter.is_numeric(inner):
                    value = ValueConverter.parse_numeric(inner)
                    if value > max_value:
                        raise InvalidOperandError(f"Dirección fuera de rango: {value}")
                    return format(value, f'0{lit_params["bits"]}b')
                else:
                    raise InvalidOperandError(f"Variable no definida: {inner}")
            
            # Literales directos
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
        if param_type == 'reg':
            return value
        elif param_type == 'dir':
            return '(dir)'
        elif param_type == 'lit':
            return 'lit'
        elif param_type.startswith('('):
            return param_type
        elif param_type == 'string':
            return 'string'
        elif param_type == 'var':
            return 'var'
        return param_type