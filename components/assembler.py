import re
from typing import List, Dict, Tuple
from utils.exceptions import InvalidInstructionError, InvalidOperandError, LabelError
from components.labelManager import LabelManager
from components.configuration import Configuration
from components.memory import Memory
from components.instructionProcessor import InstructionProcessor

class Assembler:
    def __init__(self, setup, verbose=False, load_data=False):
        self.setup = setup
        self.verbose = verbose
        self.load_data = load_data
        self.config = Configuration(setup)
        self.memory = Memory()
        self.label_manager = LabelManager()
        self.instruction_processor = InstructionProcessor(self.config)
        self.data_lines = []
        self.data_init_code = []

    def process_file(self, instructions: str) -> List[str]:
        instructions = self._remove_multiline_comments(instructions)
        lines = instructions.split('\n')
        
        cleaned_instructions, self.data_lines, code_lines = self._separate_sections(lines)
        
        self._process_data_section()
        self._process_code_section(code_lines)
        
        return cleaned_instructions
    
    def _separate_sections(self, lines: List[str]) -> Tuple[List[str], List[str], List[str]]:
        cleaned_instructions = []
        data_lines = []
        code_lines = []
        current_section = None

        for line_number, line in enumerate(lines, 1):
            line = self._remove_inline_comments(line).strip()
            if not line:
                continue

            if line in ['DATA:', 'CODE:']:
                if line == 'DATA:' and current_section == 'CODE':
                    raise SyntaxError(f"Línea {line_number}: Sección DATA después de CODE")
                current_section = 'DATA' if line == 'DATA:' else 'CODE'
                cleaned_instructions.append(line)
            elif current_section == 'DATA':
                data_lines.append((line, line_number))
                cleaned_instructions.append(line)
            elif current_section == 'CODE':
                code_lines.append((line, line_number))
                cleaned_instructions.append(line)
            else:
                raise SyntaxError(f"Línea {line_number}: Instrucción fuera de las secciones DATA o CODE")

        if not code_lines:
            raise SyntaxError("Falta la sección CODE en el archivo")

        return cleaned_instructions, data_lines, code_lines
    
    def _process_data_section(self) -> None:
        self.data_init_code = []
        for line, line_number in self.data_lines:
            try:
                name, value = re.split(r'\s+', line, 1)
                if name in self.memory.data:
                    raise MemoryError(f"Variable '{name}' ya definida")
                self.memory.store_value(name, value)
                
                if self.load_data:
                    # Generate initialization code only if load_data is True
                    self.data_init_code.append(f"MOV A,{value}")
                    self.data_init_code.append(f"MOV ({self.memory.get_address(name)}),A")
                
                if self.verbose:
                    print(f"DATA: {name} = {value}")
            except ValueError as e:
                raise MemoryError(f"Línea {line_number}: {str(e)}")
    
    def _process_code_section(self, code_lines: List[Tuple[str, int]]) -> None:
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
                    label = instruction_parts[1]
                    if label not in self.label_manager.labels:
                        self.label_manager.add_unresolved_label(label, instruction_counter)
                instruction_counter += 1
            else:
                raise InvalidInstructionError(f"Línea {line_number}: Instrucción no reconocida: {line}")

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
        return line.endswith(':') and not line[:-1].isnumeric()

    def _is_valid_instruction(self, line: str) -> bool:
        return line.split()[0] in self.config.instructions

    def assemble(self, instructions):
        if self.verbose:
            print("Iniciando proceso de ensamblaje...")
        
        instructions = self.process_file(instructions)
        
        if self.verbose:
            print(f"Procesadas {len(instructions)} líneas de código.")
            print("Variables en DATA:")
            for name, address in self.memory.data.items():
                value = self.memory.memory[address]
                print(f"  {name}: dirección {address}, valor {value}")
        
        binary = []
        
        # First, assemble the data initialization code if load_data is True
        if self.load_data:
            for init_instruction in self.data_init_code:
                opcode = self.instruction_processor.get_opcode(
                    init_instruction,
                    self.label_manager.labels,
                    self.memory.data,
                    self.memory,
                    len(binary)
                )
                binary.append(opcode)
                if self.verbose:
                    print(f"Instrucción de inicialización: {init_instruction} -> {opcode}")
                    print(f"  Desglose: {self.decode_instruction(opcode, len(binary)-1)}")
        
        # Then, assemble the main code
        for i, instruction in enumerate(instructions):
            if not (instruction.endswith(':') or
                    instruction.split()[0] in self.memory.data or
                    instruction in ['DATA:', 'CODE:']):
                opcode = self.instruction_processor.get_opcode(
                    instruction,
                    self.label_manager.labels,
                    self.memory.data,
                    self.memory,
                    len(binary)
                )
                binary.append(opcode)
                if self.verbose:
                    print(f"Instrucción {i}: {instruction} -> {opcode}")
                    print(f"  Desglose: {self.decode_instruction(opcode, len(binary)-1)}")

        # Resolver etiquetas
        resolved_labels = self.label_manager.resolve_labels()
        for address, label_address in resolved_labels.items():
            binary[address] = binary[address][:self.config.word_length - self.config.lit_params['bits']] + format(label_address, f'0{self.config.lit_params["bits"]}b')

        if self.verbose:
            print("Ensamblaje completado.")
        
        return binary
    
    def decode_instruction(self, opcode: str, instruction_address: int) -> str:
        instruction_opcode = opcode[:6]
        for name, instr in self.config.instructions.items():
            if instr['opcode'] == instruction_opcode:
                if name in ['JMP', 'JEQ', 'JNE', 'JGT', 'JGE', 'JLT', 'JLE', 'JCR']:
                    # Para instrucciones de salto, decodificamos el literal como dirección absoluta
                    absolute_address = int(opcode[6:], 2)
                    return f"{name} {absolute_address}"
                else:
                    param1 = self.decode_param(opcode[6:9])
                    param2 = self.decode_param(opcode[9:12])
                    literal = int(opcode[12:], 2)
                    if literal != 0:
                        return f"{name} {param1}, {param2}, {literal}"
                    else:
                        return f"{name} {param1}, {param2}"
        return f"Unknown instruction: {instruction_opcode}"

    def decode_param(self, param: str) -> str:
        if param in self.config.types_inverse:
            return self.config.types_inverse[param]
        return f"Unknown({param})"

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