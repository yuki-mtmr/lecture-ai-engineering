import asyncio
from typing import List, Dict, Any
import logging

from ..types.models import PresentationData, AnalysisResult, SuggestionItem
from ..services.gemini_client import GeminiClient
from ..services.powerpoint_reader import PowerPointReader


class SlideAnalyzer:
    def __init__(self, api_key: str = None):
        self.gemini_client = GeminiClient(api_key)
        self.powerpoint_reader = PowerPointReader()
        self.logger = logging.getLogger(__name__)
    
    async def analyze_presentation(self, file_path: str) -> AnalysisResult:
        """プレゼンテーション全体を分析"""
        try:
            # PowerPointファイルを読み込み
            presentation = self.powerpoint_reader.read_presentation(file_path)
            self.logger.info(f"Loaded presentation: {presentation.title} ({presentation.total_slides} slides)")
            
            # 各スライドを並列で解析
            analysis_tasks = []
            for slide in presentation.slides:
                task = self._analyze_slide(slide, presentation)
                analysis_tasks.append(task)
            
            # 並列実行
            slide_analyses = await asyncio.gather(*analysis_tasks, return_exceptions=True)
            
            # 結果をまとめる
            all_suggestions = []
            all_citations = []
            
            for i, analysis in enumerate(slide_analyses):
                if isinstance(analysis, Exception):
                    self.logger.error(f"Error analyzing slide {i+1}: {analysis}")
                    continue
                
                if 'suggestions' in analysis:
                    all_suggestions.extend(analysis['suggestions'])
                if 'citations' in analysis:
                    all_citations.extend(analysis['citations'])
            
            # プレゼンテーション全体の要約を生成
            summary = await self._generate_summary(presentation)
            
            return AnalysisResult(
                presentation=presentation,
                suggestions=all_suggestions,
                citations=all_citations,
                summary=summary
            )
        
        except Exception as e:
            self.logger.error(f"Error analyzing presentation: {e}")
            raise
    
    async def _analyze_slide(self, slide, presentation: PresentationData) -> Dict[str, Any]:
        """個別スライドを解析"""
        try:
            # プレゼンテーション全体の文脈を作成
            presentation_context = self._create_presentation_context(presentation)
            
            # スライド内容を結合
            slide_content = f"タイトル: {slide.title}\n\n{slide.text_content}"
            if slide.notes:
                slide_content += f"\n\nノート: {slide.notes}"
            
            # 並列で質問と補足情報を生成
            questions_task = self.gemini_client.suggest_questions(slide_content, presentation_context)
            supplements_task = self.gemini_client.suggest_supplements(slide_content, presentation_context)
            
            # 画像の出典検索（画像がある場合）
            citations_tasks = []
            for image_desc in slide.images:
                task = self.gemini_client.find_citations(image_desc, slide_content)
                citations_tasks.append(task)
            
            # 全てのタスクを並列実行
            results = await asyncio.gather(
                questions_task,
                supplements_task,
                *citations_tasks,
                return_exceptions=True
            )
            
            questions = results[0] if not isinstance(results[0], Exception) else []
            supplements = results[1] if not isinstance(results[1], Exception) else []
            citations = []
            
            # 出典情報をまとめる
            for i, citation_result in enumerate(results[2:]):
                if not isinstance(citation_result, Exception):
                    citations.extend(citation_result)
            
            # SuggestionItemに変換
            suggestions = []
            
            # 質問を追加
            for i, question in enumerate(questions):
                suggestions.append(SuggestionItem(
                    type="question",
                    content=question,
                    relevance_score=0.8,  # 基本スコア
                    slide_number=slide.slide_number,
                    reasoning=f"スライド{slide.slide_number}の内容に基づいた想定質問"
                ))
            
            # 補足情報を追加
            for i, supplement in enumerate(supplements):
                suggestions.append(SuggestionItem(
                    type="supplement",
                    content=supplement,
                    relevance_score=0.7,  # 基本スコア
                    slide_number=slide.slide_number,
                    reasoning=f"スライド{slide.slide_number}の理解を深めるための補足情報"
                ))
            
            return {
                'suggestions': suggestions,
                'citations': citations
            }
        
        except Exception as e:
            self.logger.error(f"Error analyzing slide {slide.slide_number}: {e}")
            return {'suggestions': [], 'citations': []}
    
    def _create_presentation_context(self, presentation: PresentationData) -> str:
        """プレゼンテーション全体の文脈を作成"""
        context_parts = [
            f"プレゼンテーションタイトル: {presentation.title}",
            f"総スライド数: {presentation.total_slides}",
            f"作成者: {presentation.metadata.get('author', '不明')}",
        ]
        
        # スライド構成の概要
        if presentation.slides:
            context_parts.append("\nスライド構成:")
            for slide in presentation.slides[:5]:  # 最初の5スライドのみ
                context_parts.append(f"  {slide.slide_number}. {slide.title}")
            
            if len(presentation.slides) > 5:
                context_parts.append(f"  ... (他 {len(presentation.slides) - 5} スライド)")
        
        return '\n'.join(context_parts)
    
    async def _generate_summary(self, presentation: PresentationData) -> str:
        """プレゼンテーション全体の要約を生成"""
        try:
            # 全スライドの内容を結合
            all_content = []
            for slide in presentation.slides:
                slide_summary = f"スライド{slide.slide_number}: {slide.title}"
                if slide.text_content:
                    # 長すぎる場合は切り詰める
                    content = slide.text_content[:200] + "..." if len(slide.text_content) > 200 else slide.text_content
                    slide_summary += f"\n{content}"
                all_content.append(slide_summary)
            
            content_text = '\n\n'.join(all_content)
            
            # Gemini APIで要約生成
            prompt = f"""
以下のプレゼンテーション内容を日本語で要約してください。
主要なトピック、構成、対象読者を含めて3-5文で簡潔にまとめてください。

プレゼンテーション: {presentation.title}
スライド数: {presentation.total_slides}

内容:
{content_text}
"""
            
            summary = await self.gemini_client._generate_content(prompt)
            return summary.strip()
        
        except Exception as e:
            self.logger.error(f"Error generating summary: {e}")
            return f"プレゼンテーション '{presentation.title}' ({presentation.total_slides}スライド) の要約生成に失敗しました。"
    
    async def analyze_single_slide(self, file_path: str, slide_number: int) -> Dict[str, Any]:
        """特定のスライドのみを解析"""
        try:
            presentation = self.powerpoint_reader.read_presentation(file_path)
            
            if slide_number < 1 or slide_number > len(presentation.slides):
                raise ValueError(f"Invalid slide number: {slide_number}")
            
            target_slide = presentation.slides[slide_number - 1]
            analysis = await self._analyze_slide(target_slide, presentation)
            
            return {
                'slide': target_slide,
                'analysis': analysis
            }
        
        except Exception as e:
            self.logger.error(f"Error analyzing slide {slide_number}: {e}")
            raise