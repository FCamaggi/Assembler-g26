from typing import List, Tuple
from components.labelManager import LabelManager
from components.configuration import Configuration
from utils.exceptions import InvalidInstructionError, LabelError

class CodeProcessor:
    def __init__(self, label_manager: LabelManager, config: Configuration):
        self.label_manager = label_manager
        self.config = config

    def process(self, code_lines: List[Tuple[str, int]]) -> None:
        instruction_counter = 0
        for line, line_number in code_lines:
            if self._is_label(line):
                label = line[:-1]
                if label in self.label_manager.labels:
                    raise LabelError(f"Línea {line_number}: Etiqueta '{label}' ya definida")
                self.label_manager.add_label(label, instruction_counter)
            elif self._is_valid_instruction(line):
                instruction_parts = line.split()
                if instruction_parts[0] in ['JMP', 'JEQ', 'JNE', 'JGT', 'JGE', 'JLT', 'JLE', 'JCR']:
                    if len(instruction_parts) != 2:
                        raise InvalidInstructionError(f"Línea {line_number}: Formato inválido para instrucción de salto")
                    jump_target = instruction_parts[1]
                    if not self._is_numeric(jump_target) and jump_target not in self.label_manager.labels:
                        self.label_manager.add_unresolved_label(jump_target, instruction_counter)
                instruction_counter += 1
            else:
                raise InvalidInstructionError(f"Línea {line_number}: Instrucción no reconocida: {line}")

    def _is_label(self, line: str) -> bool:
        return line.endswith(':') and not line[:-1].isnumeric()

    def _is_valid_instruction(self, line: str) -> bool:
        return line.split()[0] in self.config.instructions

    def _is_numeric(self, value: str) -> bool:
        return value.isdigit() or (value.endswith('h') and all(c in '0123456789ABCDEFabcdef' for c in value[:-1]))

