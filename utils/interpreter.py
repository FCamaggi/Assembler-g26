import json

class EnhancedInterpreter:
    def __init__(self, setup_file):
        with open(setup_file, 'r') as f:
            self.setup = json.load(f)
        self.instructions = self.setup['instrucciones']
        self.types = self.setup['tipos']
        self.config = self.setup['config']

    def interpret(self, filename):
        with open(filename, 'r') as f:
            lines = f.readlines()

        for i, line in enumerate(lines):
            binary = line.strip()
            if len(binary) != self.config['tamanoPalabra']:
                print(f"Error: La línea {i+1} no tiene la longitud correcta.")
                continue

            opcode = binary[:self.config['instrucciones']['bits']]
            params = binary[self.config['instrucciones']['bits']:self.config['instrucciones']['bits']+self.config['tipos']['bits']]
            literal = binary[self.config['instrucciones']['bits']+self.config['tipos']['bits']:]

            instruction_info = self.decode_instruction(opcode, params, literal)
            self.print_instruction_info(i+1, binary, instruction_info)

    def decode_instruction(self, opcode, params, literal):
        instruction_name = next((name for name, info in self.instructions.items() if info['opcode'] == opcode), "Unknown")
        param1_type = self.decode_param_type(params[:3])
        param2_type = self.decode_param_type(params[3:])
        literal_value = int(literal, 2) if literal else None

        return {
            'name': instruction_name,
            'opcode': opcode,
            'param1': param1_type,
            'param2': param2_type,
            'literal': literal_value,
            'format': self.determine_format(instruction_name, param1_type, param2_type, literal_value)
        }

    def decode_param_type(self, param_bits):
        return next((type_name for type_name, type_bits in self.types.items() if type_bits == param_bits), "Unknown")

    def determine_format(self, instruction_name, param1_type, param2_type, literal_value):
        if instruction_name not in self.instructions:
            return "Unknown format"

        possible_formats = self.instructions[instruction_name]['formato']
        
        for format in possible_formats:
            format_parts = format.replace(',', '').split()
            if len(format_parts) == 1 and format_parts[0] == 'Ins' and literal_value is not None:
                return format
            elif len(format_parts) == 1 and format_parts[0] == 'REG' and param1_type in ['A', 'B']:
                return format
            elif len(format_parts) == 2:
                if (format_parts[0] == 'REG' and param1_type in ['A', 'B']) and \
                   (format_parts[1] == 'REG' and param2_type in ['A', 'B']) or \
                   (format_parts[1] == 'Lit' and literal_value is not None) or \
                   (format_parts[1] == '(Dir)' and param2_type == '(dir)'):
                    return format

        return "Unknown format"

    def print_instruction_info(self, line_number, binary, info):
        print(f"Línea {line_number}:")
        print(f"  Binario completo: {binary}")
        print(f"  Instrucción: {info['name']}")
        print(f"  Formato: {info['format']}")
        print(f"  Desglose:")
        print(f"    [opcode: {info['opcode']}] [param1: {info['param1']}] [param2: {info['param2']}] [literal: {info['literal']}]")
        print()

if __name__ == "__main__":
    interpreter = EnhancedInterpreter("utils/setup.json")
    interpreter.interpret("output.txt")