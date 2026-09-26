import unittest
from core.outputs import OUTPUT_FILE_DESCRIPTIONS

class OutputDescriptionTests(unittest.TestCase):
    def test_every_output_description_has_clear_title_and_ten_words(self):
        for filename, (title, description) in OUTPUT_FILE_DESCRIPTIONS.items():
            self.assertGreaterEqual(len(title.split()), 6, filename)
            self.assertGreaterEqual(len(description.split()), 10, filename)

if __name__ == '__main__':
    unittest.main()