import unittest
from unittest.mock import MagicMock, patch
import io
from research_os.features.search import SearchService

class TestSearchService(unittest.TestCase):
    def setUp(self):
        self.service = SearchService(download_dir="/tmp/test_papers")

    @patch('urllib.request.urlopen')
    def test_search_arxiv_parsing(self, mock_urlopen):
        # Mock XML response
        xml_content = b"""
        <feed xmlns="http://www.w3.org/2005/Atom">
            <entry>
                <title>Test Title
                </title>
                <summary>Test Abstract</summary>
                <published>2024-01-01T00:00:00Z</published>
                <author><name>Author One</name></author>
                <link href="http://arxiv.org/abs/1234.5678" rel="alternate"/>
                <link title="pdf" href="http://arxiv.org/pdf/1234.5678" rel="related"/>
            </entry>
        </feed>
        """
        
        # Configure mock
        mock_response = MagicMock()
        mock_response.read.return_value = xml_content
        mock_response.__enter__.return_value = mock_response
        mock_urlopen.return_value = mock_response

        # Run search
        results = self.service.search_arxiv("quantum")
        
        # Verify
        self.assertEqual(len(results), 1)
        self.assertEqual(results[0]['title'], "Test Title")
        self.assertEqual(results[0]['authors'], ["Author One"])
        self.assertEqual(results[0]['pdf_url'], "http://arxiv.org/pdf/1234.5678")

    def test_filename_sanitization(self):
        # Wrapper to test internal logic if we extracted it, 
        # but here we can test the download_paper logic with a mock
        pass

if __name__ == '__main__':
    unittest.main()
