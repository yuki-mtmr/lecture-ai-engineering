import os
import asyncio
from typing import List, Dict, Any, Optional
import google.generativeai as genai
from dotenv import load_dotenv
import logging
from ..utils.decorator.limiter import RateLimiter

load_dotenv()


class GeminiClient:
    def __init__(self, api_key: Optional[str] = None, model_name: str = "gemma-3-27b-it"):
        self.api_key = api_key or os.getenv("GOOGLE_API_KEY")
        if not self.api_key:
            raise ValueError("Google API key is required")
        
        genai.configure(api_key=self.api_key)
        self.model = genai.GenerativeModel(model_name)
        self.logger = logging.getLogger(__name__)
    
    async def analyze_slide_content(self, slide_content: str, slide_context: str = "") -> Dict[str, Any]:
        """スライド内容を解析し、質問と補足情報を生成"""
        prompt = self._create_analysis_prompt(slide_content, slide_context)
        
        try:
            response = await self._generate_content(prompt)
            return self._parse_analysis_response(response)
        except Exception as e:
            self.logger.error(f"Error analyzing slide content: {e}")
            return {"questions": [], "supplements": [], "error": str(e)}
    
    async def suggest_questions(self, slide_content: str, presentation_context: str = "") -> List[str]:
        """スライド内容に基づいて想定質問を生成"""
        prompt = f"""
        以下のスライド内容について、受講生から寄せられる可能性の高い質問を3-5個生成してください。
        質問は具体的で、講義の理解を深めるものにしてください。

        スライド内容:
        {slide_content}

        プレゼンテーション文脈:
        {presentation_context}

        回答は以下の形式で出力してください:
        Q1: [質問内容]
        Q2: [質問内容]
        ...
        """
        
        try:
            response = await self._generate_content(prompt)
            return self._extract_questions(response)
        except Exception as e:
            self.logger.error(f"Error generating questions: {e}")
            return []
    
    async def suggest_supplements(self, slide_content: str, presentation_context: str = "") -> List[str]:
        """スライド内容に基づいて補足情報を生成"""
        prompt = f"""
        以下のスライド内容について、理解を深めるために追加すべき補足情報を3-5個提案してください。
        補足情報は簡潔で、スライドの視認性を損なわない程度にしてください。

        スライド内容:
        {slide_content}

        プレゼンテーション文脈:
        {presentation_context}

        回答は以下の形式で出力してください:
        補足1: [補足内容]
        補足2: [補足内容]
        ...
        """
        
        try:
            response = await self._generate_content(prompt)
            return self._extract_supplements(response)
        except Exception as e:
            self.logger.error(f"Error generating supplements: {e}")
            return []
    
    async def find_citations(self, image_description: str, content_context: str = "") -> List[Dict[str, str]]:
        """画像や図表の出典を検索・提案"""
        prompt = f"""
        以下の画像・図表について、可能性の高い出典を提案してください。
        学術的な信頼性を重視し、APAスタイルでの引用形式も含めてください。

        画像・図表の説明:
        {image_description}

        コンテンツ文脈:
        {content_context}

        回答は以下の形式で出力してください:
        出典1: [著者名], [発行年]. [タイトル]. [出版社/ジャーナル]
        APA: [APA形式での引用]
        URL: [可能であればURL]

        出典2: ...
        """
        
        try:
            response = await self._generate_content(prompt)
            return self._extract_citations(response)
        except Exception as e:
            self.logger.error(f"Error finding citations: {e}")
            return []
    
    def _create_analysis_prompt(self, slide_content: str, slide_context: str) -> str:
        return f"""
        講義スライドの内容を分析し、以下の観点から提案を行ってください:

        1. 受講生から想定される質問（3-5個）
        2. 理解を深めるための補足情報（3-5個）

        スライド内容:
        {slide_content}

        スライド文脈:
        {slide_context}

        回答はJSON形式で以下のように出力してください:
        {{
            "questions": [
                {{"content": "質問内容", "reasoning": "なぜこの質問が出ると考えられるか"}},
                ...
            ],
            "supplements": [
                {{"content": "補足内容", "reasoning": "なぜこの補足が必要か"}},
                ...
            ]
        }}
        """
    
    limiter = RateLimiter(limit_per_minute=15)
    
    @limiter
    async def _generate_content(self, prompt: str) -> str:
        """Gemini APIを使用してコンテンツを生成"""
        try:
            response = self.model.generate_content(prompt)
            return response.text
        except Exception as e:
            self.logger.error(f"Error generating content with Gemini: {e}")
            raise
    
    def _parse_analysis_response(self, response: str) -> Dict[str, Any]:
        """解析レスポンスをパース"""
        try:
            import json
            return json.loads(response)
        except json.JSONDecodeError:
            return self._fallback_parse(response)
    
    def _fallback_parse(self, response: str) -> Dict[str, Any]:
        """JSONパースに失敗した場合のフォールバック"""
        questions = self._extract_questions(response)
        supplements = self._extract_supplements(response)
        return {"questions": questions, "supplements": supplements}
    
    def _extract_questions(self, response: str) -> List[str]:
        """レスポンスから質問を抽出"""
        questions = []
        lines = response.split('\n')
        for line in lines:
            if line.strip().startswith('Q') or line.strip().startswith('質問'):
                questions.append(line.strip())
        return questions
    
    def _extract_supplements(self, response: str) -> List[str]:
        """レスポンスから補足情報を抽出"""
        supplements = []
        lines = response.split('\n')
        for line in lines:
            if line.strip().startswith('補足') or line.strip().startswith('S'):
                supplements.append(line.strip())
        return supplements
    
    def _extract_citations(self, response: str) -> List[Dict[str, str]]:
        """レスポンスから出典情報を抽出"""
        citations = []
        lines = response.split('\n')
        current_citation = {}
        
        for line in lines:
            line = line.strip()
            if line.startswith('出典'):
                if current_citation:
                    citations.append(current_citation)
                current_citation = {"source": line}
            elif line.startswith('APA:'):
                current_citation["apa"] = line[4:].strip()
            elif line.startswith('URL:'):
                current_citation["url"] = line[4:].strip()
        
        if current_citation:
            citations.append(current_citation)
        
        return citations