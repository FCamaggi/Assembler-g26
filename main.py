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
    parser.add_argument('-o', '--output', default='output.txt', help='Archivo de salida para el código de máquina (por defecto: output.txt)')
    parser.add_argument('-s', '--setup', default='utils/setup.json', help='Archivo de configuración JSON (por defecto: utils/setup.json)')
    parser.add_argument('-v', '--verbose', action='store_true', help='Mostrar información detallada durante el proceso')
    parser.add_argument('--debug', action='store_true', help='Activar modo de depuración')
    parser.add_argument('--program-basys', action='store_true', help='Programar la ROM de la Basys3 después del ensamblaje')
    parser.add_argument('--port', default=None, help='Puerto serial para la conexión con Basys3')
    parser.add_argument('--load-data', action='store_true', help='Cargar datos iniciales como instrucciones')
    return parser.parse_args()

def program_basys(binary, port=None, verbose=False):
    rom_programmer = Basys3(port)
    if verbose:
        print("Iniciando programación de la Basys3...")
    rom_programmer.begin()
    for address, instruction in enumerate(binary):
        # Convertir la instrucción binaria a bytes
        instruction_bytes = bytearray([int(instruction[i:i+8], 2) for i in range(0, len(instruction), 8)])
        rom_programmer.write(address, instruction_bytes)
        if verbose:
            print(f"Programando dirección {address}: {instruction}")
    rom_programmer.end()
    if verbose:
        print("Programación de la Basys3 completada.")

def main():
    args = parse_arguments()

    try:
        with open(args.setup) as f:
            setup = json.load(f)
    except FileNotFoundError:
        print(f"Error: No se pudo encontrar el archivo de configuración '{args.setup}'")
        sys.exit(1)
    except json.JSONDecodeError:
        print(f"Error: El archivo de configuración '{args.setup}' no es un JSON válido")
        sys.exit(1)

    assembler = Assembler(setup, verbose=args.verbose, load_data=args.load_data)

    try:
        with open(args.input, 'r') as f:
            program = f.read()
        
        if args.verbose:
            print(f"Procesando archivo de entrada: {args.input}")
        
        binary = assembler.assemble(program)
        
        if args.verbose:
            print(f"Ensamblaje completado. Escribiendo salida en: {args.output}")
        
        assembler.write(binary, args.output)
        
        print(f"Ensamblaje exitoso. Resultado guardado en {args.output}")

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