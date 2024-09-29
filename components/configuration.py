from typing import List, Dict

class Configuration:
    def __init__(self, setup: Dict):
        self.word_length = setup['config']['tamañoPalabra']
        self.instruction_params = setup['config']['instrucciones']
        self.types_params = setup['config']['tipos']
        self.lit_params = setup['config']['literals']
        self.instructions = setup['instrucciones']
        self.types = setup['tipos']
