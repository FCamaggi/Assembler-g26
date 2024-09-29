from typing import Dict
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
            if label in self.labels:
                for address in addresses:
                    resolved[address] = self.labels[label]
            else:
                raise LabelError(f"Etiqueta no definida: {label}")
        return resolved

    def get_label_address(self, name: str) -> int:
        if name in self.labels:
            return self.labels[name]
        raise ValueError(f"Undefined label: {name}")
