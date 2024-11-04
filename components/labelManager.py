from typing import Dict, List, Tuple
from utils.exceptions import LabelError

class LabelManager:
    def __init__(self):
        self.labels = {}
        self.unresolved_labels = {}

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
        Recalcula las posiciones de las etiquetas teniendo en cuenta instrucciones especiales.
        """
        current_position = 0
        for line, line_number in code_lines:
            if line.endswith(':'):  # Es una etiqueta
                self.labels[line[:-1]] = current_position
            elif line not in ['DATA:', 'CODE:']:
                instruction_parts = line.split()
                instruction_name = instruction_parts[0]
                # Verificar si es una instrucción que genera dos instrucciones máquina
                if instruction_name in ['POP', 'RET']:
                    current_position += 2
                else:
                    current_position += 1