import argparse
import json
import sys

from components.assembler import Assembler
from utils.exceptions import AssemblerError
from utils.logger import log
from iic2343 import Basys3

def parse_arguments():
    parser = argparse.ArgumentParser(description='Assembler para el proyecto de Arquitectura de Computadores')
    parser.add_argument('input', help='Archivo de entrada con código assembly')
    parser.add_argument('--debug', action='store_true', help='Activar modo de depuración')
    parser.add_argument('--program-basys', action='store_true', help='Programar la ROM de la Basys3 después del ensamblaje')
    parser.add_argument('--port', default=None, help='Puerto serial para la conexión con Basys3')
    parser.add_argument('-v', '--verbose', action='store_true', help='Mostrar información detallada durante el proceso')
    return parser.parse_args()

def program_basys(binary, port=None, verbose=False):
    print("Iniciando programación de la Basys3...")
    rom_programmer = Basys3()
    rom_programmer.begin(port_number=1)
    for address, instruction in enumerate(binary):
        print(f"Programando dirección {address}: {instruction}")

        old_instruction_bytes = bytearray([int(instruction[i:i+8], 2) for i in range(0, len(instruction), 8)])
        new_instruction_bytes = bytearray(int(instruction, 2).to_bytes(5, "big"))
        tst_instruction_bytes = remove_first_4_bits(bytearray(int(instruction, 2).to_bytes(5, "big")))

        rom_programmer.write(address, new_instruction_bytes)

        # print("Obj bin:", instruction)

        # olb_bin_repre = ''.join(format(byte, '08b') for byte in old_instruction_bytes)
        # print(f"Old bin: {olb_bin_repre}")

        # new_bin_repre = ''.join(format(byte, '08b') for byte in new_instruction_bytes)
        # print(f"New bin: {new_bin_repre}")

        # tst_bin_repre = ''.join(format(byte, '08b') for byte in tst_instruction_bytes)
        # print(f"Tst bin: {tst_bin_repre}\n")

        if verbose:
            print(f"Programando dirección {address}: {instruction}")
    rom_programmer.end()
    print("Programación de la Basys3 completada.")

def remove_first_4_bits(byte_array):
    # Convert bytearray to integer
    original_int = int.from_bytes(byte_array, byteorder='big')
    
    # Shift left by 4 bits
    shifted_int = (original_int << 4) & ((1 << 36) - 1)
    
    # Convert back to bytearray (5 bytes for 36 bits)
    new_byte_array = shifted_int.to_bytes(5, byteorder='big')
    
    return new_byte_array

def main():
    args = parse_arguments()

    try:
        with open('utils/setup.json') as f:
            setup = json.load(f)
    except FileNotFoundError:
        print(f"Error: No se pudo encontrar el archivo de configuración 'utils/setup.json'")
        sys.exit(1)
    except json.JSONDecodeError:
        print(f"Error: El archivo de configuración 'utils/setup.json' no es un JSON válido")
        sys.exit(1)

    assembler = Assembler(setup, verbose=args.verbose)

    try:
        with open(args.input, 'r') as f:
            program = f.read()
        
        if args.verbose:
            print(f"Procesando archivo de entrada: {args.input}")
        
        binary = assembler.assemble(program)
        
        if args.verbose:
            print(f"Ensamblaje completado. Escribiendo salida en: output.txt")
        
        assembler.write(binary, 'output.txt')
        
        print(f"Ensamblaje exitoso. Resultado guardado en output.txt")

        if args.program_basys:
            program_basys(binary, args.port, args.verbose)
    
    except FileNotFoundError:
        print(f"Error: No se pudo encontrar el archivo de entrada '{args.input}'")
        sys.exit(1)
    except AssemblerError as e:
        print(f"Error de ensamblado: {e}")
        if args.debug:
            raise
        sys.exit(1)
    except Exception as e:
        print(f"Error inesperado: {e}")
        if args.debug:
            raise
        sys.exit(1)

if __name__ == '__main__':
    main()
