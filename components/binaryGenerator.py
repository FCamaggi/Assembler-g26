# binaryGenerator.py
from typing import List
from components.instructionProcessor import InstructionProcessor
from components.labelManager import LabelManager
from components.memory import Memory
from components.configuration import Configuration

class BinaryGenerator:
    def __init__(self, instruction_processor: InstructionProcessor, 
                 label_manager: LabelManager, memory: Memory, 
                 config: Configuration, verbose: bool):
        self.instruction_processor = instruction_processor
        self.label_manager = label_manager
        self.memory = memory
        self.config = config
        self.verbose = verbose

    def generate(self, instructions: List[str]) -> List[str]:
        binary = []
        
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
                    print(f"  Desglose: {self._decode_instruction(opcode, len(binary)-1)}")

        # Resolver etiquetas
        resolved_labels = self.label_manager.resolve_labels()
        for address, label_address in resolved_labels.items():
            binary[address] = binary[address][:self.config.word_length - self.config.lit_params['bits']] + format(label_address, f'0{self.config.lit_params["bits"]}b')

        return binary

    def _decode_instruction(self, opcode: str, instruction_address: int) -> str:
        instruction_opcode = opcode[:self.config.instruction_params['bits']]
        params = opcode[self.config.instruction_params['bits']:self.config.instruction_params['bits'] + self.config.types_params['bits']]
        literal = opcode[self.config.instruction_params['bits'] + self.config.types_params['bits']:]

        # Buscar la instrucción correspondiente al opcode
        instruction_name = next((name for name, instr in self.config.instructions.items() if instr['opcode'] == instruction_opcode), "Unknown")

        # Decodificar parámetros
        param1 = self._decode_param(params[:3])
        param2 = self._decode_param(params[3:])

        # Convertir literal a decimal
        literal_value = int(literal, 2)

        # Formar la representación de la instrucción
        if instruction_name in ['JMP', 'JEQ', 'JNE', 'JGT', 'JGE', 'JLT', 'JLE', 'JCR']:
            return f"{instruction_name} {literal_value}"
        elif instruction_name in ['PUSH', 'POP', 'RET']:
            return f"{instruction_name} {param1}"
        elif instruction_name == 'NOP':
            return "NOP"
        else:
            if literal_value != 0:
                return f"{instruction_name} {param1}, {param2}, {literal_value}"
            else:
                return f"{instruction_name} {param1}, {param2}"

    def _decode_param(self, param: str) -> str:
        return next((type_name for type_name, type_bits in self.config.types.items() if type_bits == param), "Unknown")