import unittest
import asyncio
from unittest.mock import Mock, patch, AsyncMock
from src.services.gemini_client import GeminiClient

class TestGeminiClient(unittest.TestCase):
    
    def setUp(self):
        with patch.dict('os.environ', {'GOOGLE_API_KEY': 'test_key'}):
            self.client = GeminiClient()
    
    def test_init_with_api_key(self):
        """API Keyを指定した初期化のテスト"""
        client = GeminiClient(api_key="test_key")
        self.assertEqual(client.api_key, "test_key")
    
    def test_init_without_api_key(self):
        """API Keyなしの初期化のテスト（エラーになるべき）"""
        with patch.dict('os.environ', {}, clear=True):
            with self.assertRaises(ValueError):
                GeminiClient()
    
    @patch('src.services.gemini_client.GeminiClient._generate_content')
    async def test_suggest_questions(self, mock_generate):
        """質問生成のテスト"""
        mock_generate.return_value = "Q1: テスト質問1\nQ2: テスト質問2"
        
        questions = await self.client.suggest_questions("テストスライド内容")
        
        self.assertIsInstance(questions, list)
        mock_generate.assert_called_once()
    
    @patch('src.services.gemini_client.GeminiClient._generate_content')
    async def test_suggest_supplements(self, mock_generate):
        """補足情報生成のテスト"""
        mock_generate.return_value = "補足1: テスト補足1\n補足2: テスト補足2"
        
        supplements = await self.client.suggest_supplements("テストスライド内容")
        
        self.assertIsInstance(supplements, list)
        mock_generate.assert_called_once()
    
    def test_extract_questions(self):
        """質問抽出のテスト"""
        response = "Q1: 質問1\nQ2: 質問2\n他のテキスト"
        questions = self.client._extract_questions(response)
        
        self.assertEqual(len(questions), 2)
        self.assertTrue(questions[0].startswith("Q1:"))
        self.assertTrue(questions[1].startswith("Q2:"))
    
    def test_extract_supplements(self):
        """補足情報抽出のテスト"""
        response = "補足1: 補足情報1\n補足2: 補足情報2\n他のテキスト"
        supplements = self.client._extract_supplements(response)
        
        self.assertEqual(len(supplements), 2)
        self.assertTrue(supplements[0].startswith("補足1:"))
        self.assertTrue(supplements[1].startswith("補足2:"))

if __name__ == '__main__':
    unittest.main()