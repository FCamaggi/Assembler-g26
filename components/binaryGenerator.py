from typing import List
from components.instructionProcessor import InstructionProcessor
from components.labelManager import LabelManager
from components.memory import Memory
from components.configuration import Configuration

class BinaryGenerator:
    def __init__(self, instruction_processor, label_manager, memory, config, verbose):
        self.instruction_processor = instruction_processor
        self.label_manager = label_manager
        self.memory = memory
        self.config = config
        self.verbose = verbose
        # Actualizamos las instrucciones especiales
        self.double_instructions = {'POP', 'RET'}
        # Instrucciones que no necesitan resolver etiquetas
        self.non_label_instructions = {'NOP', 'RET1', 'RET2', 'POP1', 'POP2'}

    def _decode_instruction(self, opcode: str, original_instruction: str) -> str:
        """Decodifica una instrucción binaria a formato legible."""
        # Extraer partes de la instrucción
        instruction_bits = opcode[:self.config.instruction_params['bits']]
        params_bits = opcode[self.config.instruction_params['bits']:self.config.instruction_params['bits'] + self.config.types_params['bits']]
        literal_bits = opcode[-self.config.lit_params['bits']:]

        # Encontrar el nombre de la instrucción
        instruction_name = next((name for name, instr in self.config.instructions.items() 
                               if instr['opcode'] == instruction_bits), "Unknown")

        # Instrucciones sin operandos
        if instruction_name in ['NOP', 'RET']:
            return instruction_name

        # Instrucciones de salto
        if instruction_name in ['JMP', 'JEQ', 'JNE', 'JGT', 'JGE', 'JLT', 'JLE', 'JCR', 'CALL']:
            literal_value = int(literal_bits, 2)
            return f"{instruction_name} {literal_value}"

        # Instrucciones de un operando
        if instruction_name in ['DEC', 'INC', 'PUSH', 'POP']:
            reg_type = params_bits[:3]
            reg_name = self.config.types_inverse.get(reg_type, '?')
            return f"{instruction_name} {reg_name}"

        # Procesar operandos para instrucciones regulares
        param1_type = params_bits[:3]
        param2_type = params_bits[3:6] if len(params_bits) >= 6 else ''
        literal_value = int(literal_bits, 2) if literal_bits else 0

        # Obtener nombres de operandos
        param1 = self.config.types_inverse.get(param1_type, '?')
        param2 = self.config.types_inverse.get(param2_type, '') if param2_type else ''

        # Construir la descripción de la instrucción
        if param2_type == '':
            # Instrucciones con un operando
            if literal_value > 0:
                return f"{instruction_name} {param1} {literal_value}"
            return f"{instruction_name} {param1}"
        else:
            # Instrucciones con dos operandos
            if param2 == '(B)':
                return f"{instruction_name} {param1} {param2}"
            elif '(dir)' in [param1, param2]:
                return f"{instruction_name} {param1} {param2} {literal_value}"
            elif literal_value > 0:
                return f"{instruction_name} {param1} {param2} {literal_value}"
            else:
                return f"{instruction_name} {param1} {param2}"

    def _decode_param(self, param: str) -> str:
        return next((type_name for type_name, type_bits in self.config.types.items() if type_bits == param), "Unknown")
    
    def generate(self, instructions: List[str]) -> List[str]:
        binary = []
        current_position = 0
        instruction_positions = {}
        
        # Primera pasada: generar código binario inicial
        for instruction in instructions:
            if instruction.endswith(':'):
                # Es una etiqueta, registrar su posición en el código binario
                label_name = instruction[:-1]
                self.label_manager.labels[label_name] = len(binary)
                continue
            
            if instruction in ['DATA:', 'CODE:']:
                continue

            instruction_name = instruction.split()[0]
            instruction_positions[current_position] = len(binary)
            
            # Manejar instrucciones que generan dos instrucciones de máquina
            if instruction_name in self.double_instructions:
                result = self.instruction_processor.get_opcode(
                    instruction,
                    self.label_manager.labels,
                    self.memory.data,
                    self.memory,
                    current_position
                )
                binary.extend(result)  # result será una lista de dos instrucciones
                current_position += 2
                
                if self.verbose:
                    print(f"\nInstrucción {len(binary)-2} (parte 1 de 2):")
                    print(self._format_binary_parts(result[0], f"{instruction} (parte 1)"))
                    print(f"\nInstrucción {len(binary)-1} (parte 2 de 2):")
                    print(self._format_binary_parts(result[1], f"{instruction} (parte 2)"))
            else:
                result = self.instruction_processor.get_opcode(
                    instruction,
                    self.label_manager.labels,
                    self.memory.data,
                    self.memory,
                    current_position
                )
                binary.append(result)
                current_position += 1
                
                if self.verbose:
                    print(f"\nInstrucción {len(binary)-1}:")
                    print(self._format_binary_parts(result, instruction))

        # Segunda pasada: resolver referencias a etiquetas
        self._resolve_labels(binary)
        
        return binary

    def _resolve_labels(self, binary: List[str]) -> None:
        """Resuelve las referencias a etiquetas en el código binario"""
        jump_opcodes = {
            self.config.instructions[ins]['opcode']
            for ins in ['JMP', 'JEQ', 'JNE', 'JGT', 'JGE', 'JLT', 'JLE', 'JCR', 'CALL']
        }
        
        for i, instruction in enumerate(binary):
            opcode = instruction[:self.config.instruction_params['bits']]
            if opcode in jump_opcodes:
                # Extraer la dirección actual
                current_literal = int(instruction[-self.config.lit_params['bits']:], 2)
                
                # Mantener saltos a direcciones absolutas
                if current_literal in self.label_manager.labels.values():
                    continue
                
                # Procesar saltos relativos y a etiquetas
                instruction_prefix = instruction[:self.config.word_length - self.config.lit_params['bits']]
                if current_literal == i:  # Salto a sí mismo
                    binary[i] = instruction_prefix + format(i, f'0{self.config.lit_params["bits"]}b')
                else:
                    # Buscar la etiqueta correspondiente
                    for label, pos in self.label_manager.labels.items():
                        if pos == current_literal:
                            binary[i] = instruction_prefix + format(pos, f'0{self.config.lit_params["bits"]}b')
                            break

    def _format_binary_parts(self, binary: str, original_instruction: str) -> str:
        """Formatea una instrucción binaria en partes legibles."""
        opcode = binary[:self.config.instruction_params['bits']]
        params = binary[self.config.instruction_params['bits']:
                       self.config.instruction_params['bits'] + self.config.types_params['bits']]
        param1 = params[:3]
        param2 = params[3:6]
        literal = binary[-self.config.lit_params['bits']:]

        # Actualizado para manejar tipos específicos A/B
        param1_name = self.config.types_inverse.get(param1, 'None')
        param2_name = self.config.types_inverse.get(param2, 'None')

        instruction_name = next(
            (name for name, info in self.config.instructions.items() 
             if info['opcode'] == opcode), 
            'None'
        )

        formatted = (
            f"Instrucción: {original_instruction}\n"
            f"  [opcode: {opcode}] ({instruction_name})\n"
            f"  [param1: {param1}] ({param1_name})\n"
            f"  [param2: {param2}] ({param2_name})\n"
            f"  [literal: {literal}] ({int(literal, 2)})\n"
            f"  Binario completo: {binary}"
        )
        return formatted