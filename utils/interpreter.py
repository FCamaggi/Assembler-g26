import json
from typing import List, Dict

class Interpreter:
    def __init__(self, setup_file: str):
        with open(setup_file, 'r') as f:
            self.setup = json.load(f)
        self.word_length = self.setup['config']['tamañoPalabra']
        self.instruction_bits = self.setup['config']['instrucciones']['bits']
        self.types_bits = self.setup['config']['tipos']['bits']
        self.literal_bits = self.setup['config']['literals']['bits']
        self.instructions = self.setup['instrucciones']
        self.types = self.setup['tipos']

    def read_binary_file(self, filename: str) -> List[str]:
        with open(filename, 'r') as f:
            return [line.strip() for line in f if line.strip()]

    def decode_instruction(self, binary: str) -> Dict:
        if len(binary) != self.word_length:
            raise ValueError(f"Longitud de instrucción inválida: {len(binary)} bits")

        opcode = binary[:self.instruction_bits]
        params = binary[self.instruction_bits:self.instruction_bits + self.types_bits]
        literal = binary[self.instruction_bits + self.types_bits:]

        instruction_name = self.get_instruction_name(opcode)
        param_types = self.decode_params(params)
        literal_value = int(literal, 2) if literal else None

        return {
            'instruction': instruction_name,
            'params': param_types,
            'literal': literal_value
        }

    def get_instruction_name(self, opcode: str) -> str:
        for name, info in self.instructions.items():
            if info['opcode'] == opcode:
                return name
        raise ValueError(f"Opcode desconocido: {opcode}")

    def decode_params(self, params: str) -> List[str]:
        decoded = []
        for i in range(0, len(params), 3):
            param = params[i:i+3]
            for name, code in self.types.items():
                if code == param:
                    decoded.append(name)
                    break
            else:
                if param != '000':  # Ignora los parámetros vacíos
                    decoded.append(f"Unknown({param})")
        return decoded

    def interpret_file(self, filename: str) -> List[Dict]:
        binary_instructions = self.read_binary_file(filename)
        return [self.decode_instruction(instruction) for instruction in binary_instructions]

def main():
    interpreter = Interpreter('utils/setup.json')
    interpreted_instructions = interpreter.interpret_file('output.txt')

    for i, instruction in enumerate(interpreted_instructions):
        print(f"Instrucción {i}:")        
        print(f"  Nombre: {instruction['instruction']}")
        print(f"  Parámetros: {', '.join(instruction['params'])}")
        if instruction['literal'] is not None:
            print(f"  Literal/Dirección: {instruction['literal']}")
        print()

if __name__ == "__main__":
    main()