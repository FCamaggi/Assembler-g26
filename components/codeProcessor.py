from typing import List, Tuple
from components.labelManager import LabelManager
from components.configuration import Configuration
from utils.exceptions import InvalidInstructionError, LabelError

class CodeProcessor:
    def __init__(self, label_manager: LabelManager, config: Configuration):
        self.label_manager = label_manager
        self.config = config
        self.special_instructions = {'POP', 'RET'}

    def process(self, code_lines: List[Tuple[str, int]]) -> None:
        # Primera pasada: calcular posiciones correctas para todas las etiquetas
        self.label_manager.calculate_label_positions(code_lines)

        # Segunda pasada: procesar instrucciones y registrar saltos no resueltos
        current_position = 0
        for line, line_number in code_lines:
            if not line.endswith(':') and line not in ['DATA:', 'CODE:']:
                instruction_parts = line.split()
                if self._is_jump_instruction(line):
                    jump_target = instruction_parts[1]
                    if not self._is_numeric(jump_target):
                        self.label_manager.add_unresolved_label(jump_target, current_position)
                
                # Actualizar la posición actual
                instruction_name = instruction_parts[0]
                if instruction_name in self.special_instructions:
                    current_position += 2
                else:
                    current_position += 1

    def _is_valid_instruction(self, line: str) -> bool:
        instruction_name = line.split()[0]
        return instruction_name in self.config.instructions or instruction_name in self.special_instructions

    def _is_jump_instruction(self, line: str) -> bool:
        instruction_name = line.split()[0]
        return instruction_name in ['JMP', 'JEQ', 'JNE', 'JGT', 'JGE', 'JLT', 'JLE', 'JCR', 'CALL']

    def _is_numeric(self, value: str) -> bool:
        return value.isdigit() or (value.endswith('h') and all(c in '0123456789ABCDEFabcdef' for c in value[:-1]))