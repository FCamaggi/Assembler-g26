from typing import Dict
from components.memory import Memory
from utils.exceptions import InvalidInstructionError, InvalidOperandError
from components.configuration import Configuration
from components.valueConverter import ValueConverter

class InstructionProcessor:
    def __init__(self, config: Configuration):
        self.config = config

    def get_opcode(self, instruction: str, labels: Dict[str, int], data: Dict[str, int], memory: Memory, instruction_address: int) -> str:
        instruction_params = instruction.replace(',', ' ').split()
        instruction_name = instruction_params.pop(0)
        
        if instruction_name not in self.config.instructions:
            raise InvalidInstructionError(f"Instrucción desconocida: {instruction_name}")

        binary = self.config.instructions[instruction_name]['opcode']

        if instruction_name in ['JMP', 'JEQ', 'JNE', 'JGT', 'JGE', 'JLT', 'JLE', 'JCR']:
            if len(instruction_params) != 1:
                raise InvalidOperandError(f"Instrucción de salto '{instruction_name}' requiere exactamente una etiqueta")
            label = instruction_params[0]
            if label in labels:
                jump_address = labels[label]
            else:
                # Si la etiqueta no está resuelta, usamos un valor temporal
                jump_address = 0xFFF  # Usamos el máximo valor de 12 bits
            # Aseguramos que el opcode tenga la longitud correcta
            binary = binary.ljust(self.config.word_length - self.config.lit_params['bits'], '0')
            binary += format(jump_address, f'0{self.config.lit_params["bits"]}b')
        else:
            param_binary = ''
            literal_or_direct = ''
            for param in instruction_params:
                param_type = ValueConverter.get_type(param, self.config.types)
                if param_type == 'reg':
                    param_binary += ValueConverter.param_to_binary(param, self.config.types, self.config.types_params)
                elif param_type in ['dir', 'lit']:
                    if literal_or_direct:
                        raise InvalidOperandError(f"No se pueden usar direccionamiento directo y literal simultáneamente: {instruction}")
                    param_binary += ValueConverter.param_to_binary(param, self.config.types, self.config.types_params)
                    literal_or_direct = ValueConverter.literal_or_direct_value(param, self.config.types, self.config.lit_params, labels, data, memory, instruction_address)

            param_binary = param_binary.ljust(self.config.types_params['bits'], '0')
            binary += param_binary + literal_or_direct.ljust(self.config.lit_params['bits'], '0')

        if len(binary) != self.config.word_length:
            raise InvalidOperandError(f"Instrucción de longitud incorrecta: {instruction}. Esperado {self.config.word_length} bits, obtenido {len(binary)} bits.")

        return binary