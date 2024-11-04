import os
import sys
import glob
import re
import unittest
from typing import List, Dict, Tuple, Optional

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from components.assembler import Assembler
from components.configuration import Configuration
from utils.exceptions import AssemblerError
from test_assembler import AssemblerTester
import json

class TestAssembler(unittest.TestCase):
    def setUp(self):
        setup_path = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'utils/setup.json')
        with open(setup_path, 'r') as f:
            self.setup = json.load(f)
        self.config = Configuration(self.setup)
        self.assembler = Assembler(self.setup, verbose=False)
        self.tester = AssemblerTester()

    def test_extract_labels_and_variables(self):
        content = """
        DATA:
        a 0
        b 1
        CODE:
        ADD A,(a)
        ADD A,(b)
        JMP end
        end:
        """
        expected_labels = {3: 'end'}
        expected_variables = {'a': 0, 'b': 1}
        labels = self.tester.extract_labels(content)
        self.assertEqual(labels, expected_labels)

        # Verificar que las variables se están utilizando correctamente
        instructions = self.assembler.assemble(content)
        expected_instructions = [
            '000010001011000000000000000000000000',  # ADD A,(0)
            '000010001011000000000000000000000001',  # ADD A,(1)
            '010000000000000000000000000000000011'   # JMP 3
        ]
        self.assertEqual(instructions, expected_instructions)

if __name__ == '__main__':
    unittest.main()