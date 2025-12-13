import unittest
import shutil
import tempfile
import os
from pathlib import Path
from research_os.foundation.graph import GraphEngine
from research_os.config import settings

class TestGraphEngine(unittest.TestCase):
    def setUp(self):
        # Create a temporary directory for the test database
        self.test_dir = tempfile.mkdtemp()
        self.db_path = Path(self.test_dir) / "test_kuzu"
        
        # Override settings to use test DB
        settings.KUZU_DB_PATH = self.db_path
        
        # Initialize GraphEngine with test DB
        self.engine = GraphEngine()

    def tearDown(self):
        # Close connection (if possible/needed) and remove temp dir
        # Kuzu doesn't have a strict close() on connection object in python bindings usually, 
        # but we should ensure we release resources.
        del self.engine
        shutil.rmtree(self.test_dir)

    def test_add_and_get_paper(self):
        success = self.engine.add_paper("Test Paper", "/tmp/test.pdf", "Abstract here")
        self.assertTrue(success)
        
        papers = self.engine.get_all_papers()
        self.assertEqual(len(papers), 1)
        self.assertEqual(papers[0]['title'], "Test Paper")
        self.assertEqual(papers[0]['path'], "/tmp/test.pdf")

    def test_citation_graph(self):
        # Add two papers
        self.engine.add_paper("Paper A", "path_a")
        self.engine.add_paper("Paper B", "path_b")
        
        # Add citation
        self.engine.add_citation("Paper A", "Paper B")
        
        # Get Graph
        data = self.engine.get_citation_graph()
        
        # Verify Nodes
        self.assertEqual(len(data['nodes']), 2)
        node_ids = {n['id'] for n in data['nodes']}
        self.assertIn("Paper A", node_ids)
        self.assertIn("Paper B", node_ids)
        
        # Verify Links
        self.assertEqual(len(data['links']), 1)
        self.assertEqual(data['links'][0]['source'], "Paper A")
        self.assertEqual(data['links'][0]['target'], "Paper B")

if __name__ == '__main__':
    unittest.main()
