import os
import sys

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import unittest
import json
import os
from components.assembler import Assembler
from utils.exceptions import AssemblerError, InvalidInstructionError, InvalidOperandError, SyntaxError

class TestAssembler(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        # Cargar configuración para todas las pruebas
        with open('utils/setup.json', 'r') as f:
            cls.setup = json.load(f)
        cls.assembler = Assembler(cls.setup)
        
    def test_basic_structure(self):
        """Prueba la estructura básica del código assembly"""
        test_cases = [
            {
                "name": "Estructura mínima válida",
                "input": "CODE:\nMOV A,1",
                "should_pass": True,
                "expected_exception": None
            },
            {
                "name": "Sin sección CODE",
                "input": "MOV A,1",
                "should_pass": False,
                "expected_exception": SyntaxError
            },
            {
                "name": "DATA antes de CODE",
                "input": "DATA:\nvar1 1\nCODE:\nMOV A,1",
                "should_pass": True,
                "expected_exception": None
            },
            {
                "name": "CODE antes de DATA (inválido)",
                "input": "CODE:\nMOV A,1\nDATA:\nvar1 1",
                "should_pass": False,
                "expected_exception": SyntaxError
            }
        ]
        
        for test in test_cases:
            with self.subTest(msg=test["name"]):
                if test["should_pass"]:
                    try:
                        self.assembler.assemble(test["input"])
                    except Exception as e:
                        self.fail(f"{test['name']} debería pasar pero falló con: {str(e)}")
                else:
                    with self.assertRaises(test["expected_exception"]):
                        self.assembler.assemble(test["input"])

    def test_instructions(self):
        """Prueba las instrucciones básicas"""
        test_cases = [
            {
                "name": "MOV registro a registro",
                "input": "CODE:\nMOV A,B",
                "should_pass": True,
                "expected_exception": None
            },
            {
                "name": "MOV literal a registro",
                "input": "CODE:\nMOV A,5",
                "should_pass": True,
                "expected_exception": None
            },
            {
                "name": "MOV con dirección",
                "input": "CODE:\nMOV A,(0)",
                "should_pass": True,
                "expected_exception": None
            },
            {
                "name": "Instrucción inválida",
                "input": "CODE:\nINVALID A,B",
                "should_pass": False,
                "expected_exception": InvalidInstructionError
            }
        ]
        
        for test in test_cases:
            with self.subTest(msg=test["name"]):
                if test["should_pass"]:
                    try:
                        self.assembler.assemble(test["input"])
                    except Exception as e:
                        self.fail(f"{test['name']} debería pasar pero falló con: {str(e)}")
                else:
                    with self.assertRaises(test["expected_exception"]):
                        self.assembler.assemble(test["input"])

    def test_data_section(self):
        """Prueba la sección de datos"""
        test_cases = [
            {
                "name": "Variable simple",
                "input": "DATA:\nvar1 5\nCODE:\nMOV A,(var1)",
                "should_pass": True,
                "expected_exception": None
            },
            {
                "name": "Array simple",
                "input": "DATA:\narr 1\n2\n3\nCODE:\nMOV A,(arr)",
                "should_pass": True,
                "expected_exception": None
            },
            {
                "name": "Variable sin valor",
                "input": "DATA:\nvar1\nCODE:\nMOV A,1",
                "should_pass": False,
                "expected_exception": SyntaxError
            },
            {
                "name": "Variable con valor hexadecimal",
                "input": "DATA:\nvar1 FFh\nCODE:\nMOV A,(var1)",
                "should_pass": True,
                "expected_exception": None
            }
        ]
        
        for test in test_cases:
            with self.subTest(msg=test["name"]):
                if test["should_pass"]:
                    try:
                        self.assembler.assemble(test["input"])
                    except Exception as e:
                        self.fail(f"{test['name']} debería pasar pero falló con: {str(e)}")
                else:
                    with self.assertRaises(test["expected_exception"]):
                        self.assembler.assemble(test["input"])

    def test_labels(self):
        """Prueba el manejo de etiquetas"""
        test_cases = [
            {
                "name": "Salto simple",
                "input": "CODE:\nstart:\nMOV A,1\nJMP start",
                "should_pass": True,
                "expected_exception": None
            },
            {
                "name": "Etiqueta duplicada",
                "input": "CODE:\nloop:\nMOV A,1\nloop:\nJMP loop",
                "should_pass": False,
                "expected_exception": LabelError
            },
            {
                "name": "Salto a etiqueta indefinida",
                "input": "CODE:\nJMP undefined",
                "should_pass": False,
                "expected_exception": LabelError
            },
            {
                "name": "Múltiples saltos válidos",
                "input": "CODE:\nstart:\nMOV A,1\nmid:\nMOV B,2\nJMP start\nJMP mid",
                "should_pass": True,
                "expected_exception": None
            }
        ]
        
        for test in test_cases:
            with self.subTest(msg=test["name"]):
                if test["should_pass"]:
                    try:
                        self.assembler.assemble(test["input"])
                    except Exception as e:
                        self.fail(f"{test['name']} debería pasar pero falló con: {str(e)}")
                else:
                    with self.assertRaises(test["expected_exception"]):
                        self.assembler.assemble(test["input"])

    def test_numeric_formats(self):
        """Prueba diferentes formatos numéricos"""
        test_cases = [
            {
                "name": "Decimal",
                "input": "CODE:\nMOV A,42",
                "should_pass": True,
                "expected_exception": None
            },
            {
                "name": "Hexadecimal",
                "input": "CODE:\nMOV A,FFh",
                "should_pass": True,
                "expected_exception": None
            },
            {
                "name": "Binario",
                "input": "CODE:\nMOV A,1010b",
                "should_pass": True,
                "expected_exception": None
            },
            {
                "name": "Hexadecimal inválido",
                "input": "CODE:\nMOV A,GGh",
                "should_pass": False,
                "expected_exception": InvalidOperandError
            }
        ]
        
        for test in test_cases:
            with self.subTest(msg=test["name"]):
                if test["should_pass"]:
                    try:
                        self.assembler.assemble(test["input"])
                    except Exception as e:
                        self.fail(f"{test['name']} debería pasar pero falló con: {str(e)}")
                else:
                    with self.assertRaises(test["expected_exception"]):
                        self.assembler.assemble(test["input"])

    def test_complex_programs(self):
        """Prueba programas más complejos"""
        test_cases = [
            {
                "name": "Suma con variables",
                "input": """DATA:
var1 5
var2 3
CODE:
MOV A,(var1)
ADD A,(var2)
MOV (var1),A""",
                "should_pass": True,
                "expected_exception": None
            },
            {
                "name": "Loop con array",
                "input": """DATA:
arr 1
2
3
4
CODE:
MOV B,arr
loop:
MOV A,(B)
INC B
JMP loop""",
                "should_pass": True,
                "expected_exception": None
            }
        ]
        
        for test in test_cases:
            with self.subTest(msg=test["name"]):
                if test["should_pass"]:
                    try:
                        self.assembler.assemble(test["input"])
                    except Exception as e:
                        self.fail(f"{test['name']} debería pasar pero falló con: {str(e)}")
                else:
                    with self.assertRaises(test["expected_exception"]):
                        self.assembler.assemble(test["input"])

if __name__ == '__main__':
    # Configurar el formato de salida para que sea más legible
    unittest.main(verbosity=2, failfast=False)