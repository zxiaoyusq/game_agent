import json
import os
from pathlib import Path
import unittest


class ToolCounterRoles(unittest.TestCase):
    def test_candidate_layout_declares_expected_counter_roles(self):
        game = Path(os.environ['ONECONNECT_CANDIDATE'])
        project = json.loads((game / 'data.js').read_text(encoding='utf8'))['project']
        self.assertEqual(project[3][25][0], 't25')
        self.assertEqual(len(project[3][25][3]), 1, 'counter type has one instance variable')
        instances = []
        for layer in project[5][0][6]:
            for value in layer:
                if isinstance(value, list) and value and isinstance(value[0], list):
                    instances.extend(item for item in value if len(item) > 3 and item[1] == 25)
        roles = {item[2]: item[3][0][0] for item in instances if item[2] in (2, 46)}
        self.assertEqual(roles, {2: 3, 46: 4})


if __name__ == '__main__':
    unittest.main()
