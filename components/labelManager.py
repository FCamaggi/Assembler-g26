from typing import Dict, List, Tuple
from utils.exceptions import LabelError

class LabelManager:
    def __init__(self):
        self.labels = {}
        self.unresolved_labels = {}
        # Instrucciones que generan dos instrucciones máquina
        self.double_instructions = {'POP', 'RET'}

    def add_label(self, name: str, address: int) -> None:
        if name in self.labels:
            raise LabelError(f"Etiqueta '{name}' ya definida")
        self.labels[name] = address

    def add_unresolved_label(self, name: str, instruction_address: int) -> None:
        if name not in self.unresolved_labels:
            self.unresolved_labels[name] = []
        self.unresolved_labels[name].append(instruction_address)

    def resolve_labels(self) -> Dict[int, int]:
        resolved = {}
        for label, addresses in self.unresolved_labels.items():
            if label not in self.labels:
                raise LabelError(f"Etiqueta no definida: {label}")
            target_address = self.labels[label]
            for address in addresses:
                resolved[address] = target_address
        return resolved

    def get_label_address(self, name: str) -> int:
        try:
            return self.labels[name]
        except KeyError:
            raise LabelError(f"Etiqueta no definida: {name}")

    def calculate_label_positions(self, code_lines: List[Tuple[str, int]]) -> None:
        """
        Recalcula las posiciones de las etiquetas considerando instrucciones que generan
        múltiples instrucciones máquina.
        """
        position_counter = 0
        binary_position = 0  # Posición real en el código binario

        # Primera pasada: calcular posiciones de etiquetas
        for line, _ in code_lines:
            if line.endswith(':'):  # Es una etiqueta
                label_name = line[:-1]
                self.labels[label_name] = binary_position
            elif line not in ['DATA:', 'CODE:']:
                instruction_name = line.split()[0]
                # Incrementar contador según el tipo de instrucción
                if instruction_name in self.double_instructions:
                    binary_position += 2
                else:
                    binary_position += 1
            position_counter += 1

        # Segunda pasada: procesar referencias a etiquetas
        binary_position = 0
        for line, _ in code_lines:
            if not line.endswith(':') and line not in ['DATA:', 'CODE:']:
                instruction_parts = line.split()
                instruction_name = instruction_parts[0]
                
                # Procesar instrucciones de salto
                if instruction_name in ['JMP', 'JEQ', 'JNE', 'JGT', 'JGE', 'JLT', 'JLE', 'JCR', 'CALL']:
                    if len(instruction_parts) > 1:
                        label_name = instruction_parts[1]
                        if label_name in self.labels:
                            self.add_unresolved_label(label_name, binary_position)
                
                # Actualizar posición según el tipo de instrucción
                if instruction_name in self.double_instructions:
                    binary_position += 2
                else:
                    binary_position += 1