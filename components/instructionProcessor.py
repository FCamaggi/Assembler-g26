from typing import Dict
from utils.exceptions import InvalidInstructionError, InvalidOperandError
from components.configuration import Configuration
from components.valueConverter import ValueConverter

class InstructionProcessor:
    def __init__(self, config: Configuration):
        self.config = config

    def get_opcode(self, instruction: str, labels: Dict[str, int], data: Dict[str, int], memory: Dict[int, int], instruction_address: int) -> str:
        instruction_params = instruction.replace(',', ' ').split()
        instruction_name = instruction_params.pop(0)
        
        if instruction_name not in self.config.instructions:
            raise InvalidInstructionError(f"Instrucción desconocida: {instruction_name}")

        binary = self.config.instructions[instruction_name]['opcode']

        # Procesar parámetros
        param_binary = ''
        literal_or_direct = ''
        for param in instruction_params:
            param_type = ValueConverter.get_type(param, self.config.types)
            if param_type == 'reg':
                param_binary += ValueConverter.param_to_binary(param, self.config.types, self.config.types_params)
            elif param_type in ['dir', 'lit']:
                if instruction_name in ['JMP', 'JEQ', 'JNE', 'JGT', 'JGE', 'JLT', 'JLE', 'JCR', 'CALL']:
                    if param in labels:
                        literal_or_direct = format(labels[param], f'0{self.config.lit_params["bits"]}b')
                    elif param.isdigit():
                        literal_or_direct = format(int(param), f'0{self.config.lit_params["bits"]}b')
                    else:
                        literal_or_direct = 'U' * self.config.lit_params['bits']  # Marcador para etiqueta no resuelta
                        self.label_manager.add_unresolved_label(param, instruction_address)
                else:
                    try:
                        literal_or_direct = ValueConverter.literal_or_direct_value(param, self.config.types, self.config.lit_params, labels, data, memory)
                    except ValueError as e:
                        raise InvalidOperandError(str(e))

        # Asegurar que la parte de los parámetros tenga la longitud correcta
        param_binary = param_binary.ljust(self.config.types_params['bits'], '0')
        
        binary += param_binary + literal_or_direct.ljust(self.config.lit_params['bits'], '0')

        # Asegurarse de que la instrucción tenga la longitud correcta
        if len(binary) != self.config.word_length:
            raise InvalidOperandError(f"Instrucción de longitud incorrecta: {instruction}. Esperado {self.config.word_length} bits, obtenido {len(binary)} bits.")

        return binary

    