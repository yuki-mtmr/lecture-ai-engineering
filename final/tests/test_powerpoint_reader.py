import unittest
import os
from unittest.mock import Mock, patch
from src.services.powerpoint_reader import PowerPointReader
from src.types.models import SlideType

class TestPowerPointReader(unittest.TestCase):
    
    def setUp(self):
        self.reader = PowerPointReader()
    
    def test_init(self):
        """PowerPointReaderの初期化テスト"""
        reader = PowerPointReader()
        self.assertIsNotNone(reader.logger)
    
    @patch('src.services.powerpoint_reader.Presentation')
    def test_read_presentation_file_not_found(self, mock_presentation):
        """存在しないファイルのテスト"""
        with self.assertRaises(FileNotFoundError):
            self.reader.read_presentation("nonexistent.pptx")
    
    def test_determine_slide_type_title(self):
        """タイトルスライドの判定テスト"""
        mock_slide = Mock()
        mock_slide.shapes.title.text = "タイトル"
        
        with patch.object(self.reader, '_extract_slide_title', return_value="タイトル"):
            slide_type = self.reader._determine_slide_type(mock_slide, 1)
            self.assertEqual(slide_type, SlideType.TITLE)
    
    def test_determine_slide_type_conclusion(self):
        """まとめスライドの判定テスト"""
        mock_slide = Mock()
        
        with patch.object(self.reader, '_extract_slide_title', return_value="まとめ"):
            slide_type = self.reader._determine_slide_type(mock_slide, 5)
            self.assertEqual(slide_type, SlideType.CONCLUSION)
    
    def test_determine_slide_type_content(self):
        """コンテンツスライドの判定テスト"""
        mock_slide = Mock()
        
        with patch.object(self.reader, '_extract_slide_title', return_value="内容"):
            slide_type = self.reader._determine_slide_type(mock_slide, 3)
            self.assertEqual(slide_type, SlideType.CONTENT)

if __name__ == '__main__':
    unittest.main()