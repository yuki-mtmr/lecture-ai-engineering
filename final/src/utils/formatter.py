from typing import List
from ..types.models import AnalysisResult, SuggestionItem

def format_analysis_result(result: AnalysisResult) -> str:
    """分析結果をコンソール表示用にフォーマット"""
    
    lines = []
    
    # ヘッダー
    lines.append("=" * 60)
    lines.append(f"📊 {result.presentation.title}")
    lines.append("=" * 60)
    
    # 基本情報
    lines.append(f"📁 総スライド数: {result.presentation.total_slides}")
    lines.append(f"👤 作成者: {result.presentation.metadata.get('author', '不明')}")
    lines.append("")
    
    # 要約
    lines.append("📝 要約:")
    lines.append("-" * 40)
    lines.append(result.summary)
    lines.append("")
    
    # 提案をスライド別にグループ化
    suggestions_by_slide = {}
    for suggestion in result.suggestions:
        slide_num = suggestion.slide_number
        if slide_num not in suggestions_by_slide:
            suggestions_by_slide[slide_num] = []
        suggestions_by_slide[slide_num].append(suggestion)
    
    # スライド別に提案を表示
    if suggestions_by_slide:
        lines.append("💡 質問・補足情報の提案:")
        lines.append("-" * 40)
        lines.append("")
        
        for slide_num in sorted(suggestions_by_slide.keys()):
            slide = next(s for s in result.presentation.slides if s.slide_number == slide_num)
            lines.append(f"🔸 スライド {slide_num}: {slide.title}")
            lines.append("")
            
            suggestions = suggestions_by_slide[slide_num]
            
            # 質問
            questions = [s for s in suggestions if s.type == "question"]
            if questions:
                lines.append("  ❓ 想定される質問:")
                for q in questions:
                    lines.append(f"    • {q.content}")
                    lines.append(f"      (関連度: {q.relevance_score:.1f})")
                lines.append("")
            
            # 補足情報
            supplements = [s for s in suggestions if s.type == "supplement"]
            if supplements:
                lines.append("  💡 補足情報:")
                for s in supplements:
                    lines.append(f"    • {s.content}")
                    lines.append(f"      (関連度: {s.relevance_score:.1f})")
                lines.append("")
            
            lines.append("")
    
    # 出典情報
    if result.citations:
        lines.append("📚 出典情報:")
        lines.append("-" * 40)
        for citation in result.citations:
            lines.append(f"• {citation.get('source', '出典不明')}")
            if 'apa' in citation:
                lines.append(f"  APA: {citation['apa']}")
            if 'url' in citation:
                lines.append(f"  URL: {citation['url']}")
            lines.append("")
    
    lines.append("=" * 60)
    
    return '\n'.join(lines)

def format_suggestion_summary(suggestions: List[SuggestionItem]) -> str:
    """提案の統計情報をフォーマット"""
    
    if not suggestions:
        return "提案はありません。"
    
    questions = [s for s in suggestions if s.type == "question"]
    supplements = [s for s in suggestions if s.type == "supplement"]
    
    lines = [
        f"📊 提案統計:",
        f"  • 質問: {len(questions)}個",
        f"  • 補足情報: {len(supplements)}個",
        f"  • 総計: {len(suggestions)}個"
    ]
    
    # 関連度の統計
    if suggestions:
        scores = [s.relevance_score for s in suggestions]
        avg_score = sum(scores) / len(scores)
        max_score = max(scores)
        min_score = min(scores)
        
        lines.extend([
            "",
            f"📈 関連度統計:",
            f"  • 平均: {avg_score:.2f}",
            f"  • 最高: {max_score:.2f}",
            f"  • 最低: {min_score:.2f}"
        ])
    
    return '\n'.join(lines)

def format_slide_summary(presentation_data) -> str:
    """スライド構成の要約をフォーマット"""
    
    lines = [
        "📑 スライド構成:",
        "-" * 30
    ]
    
    for slide in presentation_data.slides:
        type_icon = {
            "title": "🎯",
            "content": "📝",
            "section": "📂",
            "conclusion": "🎯"
        }.get(slide.slide_type.value, "📄")
        
        lines.append(f"{type_icon} {slide.slide_number:2d}. {slide.title}")
    
    return '\n'.join(lines)