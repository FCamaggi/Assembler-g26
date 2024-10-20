from typing import List
from components.fileProcessor import FileProcessor
from components.codeProcessor import CodeProcessor
from components.dataProcessor import DataProcessor
from components.binaryGenerator import BinaryGenerator
from components.configuration import Configuration
from components.labelManager import LabelManager
from components.memory import Memory
from components.instructionProcessor import InstructionProcessor

class Assembler:
    def __init__(self, setup, verbose=False, load_data=False):
        self.config = Configuration(setup)
        self.verbose = verbose
        self.load_data = load_data
        self.memory = Memory()
        self.label_manager = LabelManager()
        self.instruction_processor = InstructionProcessor(self.config)
        
        self.file_processor = FileProcessor()
        self.data_processor = DataProcessor(self.memory, self.load_data, self.verbose)
        self.code_processor = CodeProcessor(self.label_manager, self.config)
        self.binary_generator = BinaryGenerator(
            self.instruction_processor, 
            self.label_manager, 
            self.memory, 
            self.config, 
            self.verbose
        )

    def assemble(self, instructions: str) -> List[str]:
        if self.verbose:
            print("Iniciando proceso de ensamblaje...")
        
        cleaned_instructions, data_lines, code_lines = self.file_processor.process(instructions)
        
        self.data_processor.process(data_lines)
        self.code_processor.process(code_lines)
        
        binary = self.binary_generator.generate(cleaned_instructions)
        
        if self.verbose:
            print("Ensamblaje completado.")
        
        return binary

    def write(self, binary: List[str], filename: str) -> None:
        with open(filename, 'w') as f:
            for instruction in binary:
                f.write(instruction + '\n')
        if self.verbose:
            print(f"Código de máquina escrito en {filename}")
