import re
from typing import List, Dict
from utils.exceptions import InvalidInstructionError, InvalidOperandError, LabelError
from components.labelManager import LabelManager
from components.configuration import Configuration
from components.memory import Memory
from components.instructionProcessor import InstructionProcessor

class Assembler:
    def __init__(self, setup, verbose=False):
        self.setup = setup
        self.verbose = verbose
        self.config = Configuration(setup)
        self.memory = Memory()
        self.label_manager = LabelManager()
        self.instruction_processor = InstructionProcessor(self.config)

    def process_file(self, instructions: str) -> List[str]:
        instructions = self._remove_multiline_comments(instructions)
        lines = instructions.split('\n')
        
        valid_data_keywords = ['DATA:', 'CODE:']
        cleaned_instructions = []
        data_section = False
        code_section = False
        instruction_counter = 0

        for line_number, line in enumerate(lines, 1):
            line = self._remove_inline_comments(line)
            line = line.strip()  # Elimina espacios y tabulaciones al inicio y final
            if not line:
                continue
            
            if line in valid_data_keywords:
                if line == 'DATA:' and data_section:
                    raise SyntaxError(f"Línea {line_number}: Sección DATA duplicada")
                if line == 'CODE:' and code_section:
                    raise SyntaxError(f"Línea {line_number}: Sección CODE duplicada")
                if line == 'DATA:' and code_section:
                    raise SyntaxError(f"Línea {line_number}: Sección CODE antes de DATA")
                
                cleaned_instructions.append(line)
                data_section = (line == 'DATA:')
                code_section = (line == 'CODE:')
                continue
            
            if not (data_section or code_section):
                raise SyntaxError(f"Línea {line_number}: Instrucción fuera de las secciones DATA o CODE")
            
            if data_section:
                try:
                    self._process_data_line(line, line_number)
                except ValueError as e:
                    raise MemoryError(f"Línea {line_number}: {str(e)}")
                cleaned_instructions.append(line)
            else:
                try:
                    instruction_counter = self._process_code_line(line, cleaned_instructions, instruction_counter, line_number)
                except (InvalidInstructionError, InvalidOperandError, LabelError) as e:
                    raise type(e)(f"Línea {line_number}: {str(e)}")

        if not code_section:
            raise SyntaxError("Falta la sección CODE en el archivo")

        return cleaned_instructions

    def _remove_multiline_comments(self, text: str) -> str:
        return re.sub(r'/\*.*?\*/', '', text, flags=re.DOTALL)

    def _remove_inline_comments(self, line: str) -> str:
        return re.split(r'\s*//\s*', line)[0].strip()

    def _process_data_line(self, line: str, line_number: int) -> None:
        parts = re.split(r'\s+', line, 1)
        if len(parts) != 2:
            raise SyntaxError(f"Línea {line_number}: Formato inválido en la línea de datos")
        
        name, value = parts
        if name in self.memory.data:
            raise MemoryError(f"Línea {line_number}: Variable '{name}' ya definida")

        if value.startswith('[') and value.endswith(']'):
            # Es un array
            array_values = [v.strip() for v in value[1:-1].split(',')]
            self.memory.store_value(name, array_values)
        else:
            self.memory.store_value(name, value)

    def _process_code_line(self, line: str, cleaned_instructions: List[str], instruction_counter: int, line_number: int) -> int:
        if self._is_label(line):
            if line[:-1] in self.label_manager.labels:
                raise LabelError(f"Etiqueta '{line[:-1]}' ya definida")
            self.label_manager.add_label(line[:-1], instruction_counter)
            cleaned_instructions.append(line)
        elif self._is_valid_instruction(line):
            # Normaliza los espacios en la instrucción
            normalized_line = re.sub(r'\s+', ' ', line)
            cleaned_instructions.append(normalized_line)
            instruction_counter += 1
        else:
            raise InvalidInstructionError(f"Instrucción no reconocida: {line}")
        return instruction_counter

    def _is_label(self, line: str) -> bool:
        return line.endswith(':') and line[:-1].isalpha()

    def _is_valid_instruction(self, line: str) -> bool:
        return line.split()[0] in self.config.instructions

    def assemble(self, instructions):
        if self.verbose:
            print("Iniciando proceso de ensamblaje...")
        
        instructions = self.process_file(instructions)
        
        if self.verbose:
            print(f"Procesadas {len(instructions)} líneas de código.")
        
        binary = []
        for i, instruction in enumerate(instructions):
            if not (instruction.endswith(':') or
                    instruction.split()[0] in self.memory.data or
                    instruction in ['DATA:', 'CODE:']):
                opcode = self.instruction_processor.get_opcode(
                    instruction,
                    self.label_manager.labels,
                    self.memory.data,
                    self.memory.memory,
                    i
                )
                binary.append(opcode)
                if self.verbose:
                    print(f"Instrucción {i}: {instruction} -> {opcode}")

        if self.verbose:
            print("Ensamblaje completado.")
        
        return binary

    def _resolve_labels(self, binary: List[str]) -> List[str]:
        resolved_addresses = self.label_manager.resolve_labels()
        for address, label_address in resolved_addresses.items():
            binary[address] = binary[address][:12] + format(label_address, '024b')
        return binary

    def run(self, instructions):
        if isinstance(instructions, list):
            instructions = '\n'.join(instructions)
        elif not isinstance(instructions, str):
            raise TypeError("Las instrucciones deben ser una cadena o una lista de cadenas")
        
        binary = self.assemble(instructions)
        self._write(binary, 'output.txt')

    def write(self, binary, filename):
        with open(filename, 'w') as f:
            for instruction in binary:
                f.write(instruction + '\n')
        if self.verbose:
            print(f"Código de máquina escrito en {filename}")