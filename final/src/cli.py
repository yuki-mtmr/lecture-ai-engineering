import click
import asyncio
import os
import json
from typing import Optional
import logging

from .core.analyzer import SlideAnalyzer
from .utils.logger import setup_logger
from .utils.formatter import format_analysis_result

@click.group()
@click.option('--debug', is_flag=True, help='デバッグモードで実行')
@click.option('--api-key', help='Google Gemini API Key')
@click.pass_context
def cli(ctx, debug: bool, api_key: Optional[str]):
    """講義スライド作成をサポートするCopilot"""
    ctx.ensure_object(dict)
    ctx.obj['debug'] = debug
    ctx.obj['api_key'] = api_key
    
    # ロガー設定
    log_level = logging.DEBUG if debug else logging.INFO
    setup_logger(log_level)

@cli.command()
@click.argument('file_path', type=click.Path(exists=True))
@click.option('--output', '-o', help='結果を保存するファイルパス')
@click.option('--format', 'output_format', default='console', 
              type=click.Choice(['console', 'json', 'markdown']), 
              help='出力形式')
@click.pass_context
def analyze(ctx, file_path: str, output: Optional[str], output_format: str):
    """PowerPointファイルを分析し、質問と補足情報を生成"""
    
    if not file_path.lower().endswith('.pptx'):
        click.echo("エラー: PowerPointファイル（.pptx）のみサポートされています。", err=True)
        return
    
    try:
        analyzer = SlideAnalyzer(api_key=ctx.obj.get('api_key'))
        
        with click.progressbar(length=100, label='プレゼンテーションを解析中...') as bar:
            async def run_analysis():
                result = await analyzer.analyze_presentation(file_path)
                bar.update(100)
                return result
            
            result = asyncio.run(run_analysis())
        
        # 結果の出力
        if output_format == 'json':
            output_text = _format_json_output(result)
        elif output_format == 'markdown':
            output_text = _format_markdown_output(result)
        else:
            output_text = format_analysis_result(result)
        
        if output:
            with open(output, 'w', encoding='utf-8') as f:
                f.write(output_text)
            click.echo(f"結果を {output} に保存しました。")
        else:
            click.echo(output_text)
    
    except Exception as e:
        click.echo(f"エラー: {e}", err=True)
        if ctx.obj.get('debug'):
            import traceback
            click.echo(traceback.format_exc(), err=True)

@cli.command()
@click.argument('file_path', type=click.Path(exists=True))
@click.argument('slide_number', type=int)
@click.option('--format', 'output_format', default='console', 
              type=click.Choice(['console', 'json']), 
              help='出力形式')
@click.pass_context
def analyze_slide(ctx, file_path: str, slide_number: int, output_format: str):
    """特定のスライドのみを分析"""
    
    try:
        analyzer = SlideAnalyzer(api_key=ctx.obj.get('api_key'))
        
        async def run_analysis():
            return await analyzer.analyze_single_slide(file_path, slide_number)
        
        result = asyncio.run(run_analysis())
        
        if output_format == 'json':
            click.echo(json.dumps(_slide_to_dict(result), ensure_ascii=False, indent=2))
        else:
            _display_slide_analysis(result)
    
    except Exception as e:
        click.echo(f"エラー: {e}", err=True)
        if ctx.obj.get('debug'):
            import traceback
            click.echo(traceback.format_exc(), err=True)

@cli.command()
@click.argument('directory', type=click.Path(exists=True))
@click.option('--output-dir', '-o', help='結果を保存するディレクトリ')
@click.pass_context
def batch_analyze(ctx, directory: str, output_dir: Optional[str]):
    """ディレクトリ内の全PowerPointファイルを一括解析"""
    
    pptx_files = []
    for root, dirs, files in os.walk(directory):
        for file in files:
            if file.lower().endswith('.pptx'):
                pptx_files.append(os.path.join(root, file))
    
    if not pptx_files:
        click.echo("PowerPointファイルが見つかりませんでした。")
        return
    
    click.echo(f"{len(pptx_files)} 個のファイルを解析します...")
    
    analyzer = SlideAnalyzer(api_key=ctx.obj.get('api_key'))
    
    if output_dir:
        os.makedirs(output_dir, exist_ok=True)
    
    for file_path in pptx_files:
        click.echo(f"\n解析中: {os.path.basename(file_path)}")
        
        try:
            async def run_analysis():
                return await analyzer.analyze_presentation(file_path)
            
            result = asyncio.run(run_analysis())
            
            if output_dir:
                base_name = os.path.splitext(os.path.basename(file_path))[0]
                output_file = os.path.join(output_dir, f"{base_name}_analysis.md")
                
                with open(output_file, 'w', encoding='utf-8') as f:
                    f.write(_format_markdown_output(result))
                
                click.echo(f"  結果を {output_file} に保存しました。")
            else:
                click.echo(format_analysis_result(result))
        
        except Exception as e:
            click.echo(f"  エラー: {e}", err=True)

@cli.command()
@click.pass_context
def test_connection(ctx):
    """Google Gemini APIへの接続をテスト"""
    
    try:
        analyzer = SlideAnalyzer(api_key=ctx.obj.get('api_key'))
        
        async def test():
            response = await analyzer.gemini_client._generate_content("こんにちは、動作テストです。")
            return response
        
        response = asyncio.run(test())
        click.echo("✓ Google Gemini API接続成功")
        click.echo(f"レスポンス: {response[:100]}...")
    
    except Exception as e:
        click.echo(f"✗ API接続エラー: {e}", err=True)

def _format_json_output(result) -> str:
    """JSON形式で結果をフォーマット"""
    data = {
        "presentation": {
            "title": result.presentation.title,
            "total_slides": result.presentation.total_slides,
            "metadata": result.presentation.metadata
        },
        "summary": result.summary,
        "suggestions": [
            {
                "type": s.type,
                "content": s.content,
                "slide_number": s.slide_number,
                "relevance_score": s.relevance_score,
                "reasoning": s.reasoning
            } for s in result.suggestions
        ],
        "citations": result.citations
    }
    return json.dumps(data, ensure_ascii=False, indent=2)

def _format_markdown_output(result) -> str:
    """Markdown形式で結果をフォーマット"""
    lines = [
        f"# {result.presentation.title} - 分析結果",
        "",
        "## 概要",
        f"- 総スライド数: {result.presentation.total_slides}",
        f"- 作成者: {result.presentation.metadata.get('author', '不明')}",
        "",
        "## 要約",
        result.summary,
        "",
        "## 質問・補足情報の提案",
        ""
    ]
    
    current_slide = None
    for suggestion in sorted(result.suggestions, key=lambda x: x.slide_number):
        if current_slide != suggestion.slide_number:
            current_slide = suggestion.slide_number
            lines.append(f"### スライド {current_slide}")
            lines.append("")
        
        icon = "❓" if suggestion.type == "question" else "💡"
        lines.append(f"{icon} **{suggestion.type.title()}**: {suggestion.content}")
        lines.append(f"   - 関連度: {suggestion.relevance_score:.1f}")
        lines.append(f"   - 理由: {suggestion.reasoning}")
        lines.append("")
    
    if result.citations:
        lines.extend([
            "## 出典情報",
            ""
        ])
        for citation in result.citations:
            lines.append(f"- {citation.get('source', '出典不明')}")
            if 'apa' in citation:
                lines.append(f"  - APA: {citation['apa']}")
            if 'url' in citation:
                lines.append(f"  - URL: {citation['url']}")
            lines.append("")
    
    return '\n'.join(lines)

def _display_slide_analysis(result):
    """単一スライド分析結果を表示"""
    slide = result['slide']
    analysis = result['analysis']
    
    click.echo(f"=== スライド {slide.slide_number}: {slide.title} ===")
    click.echo(f"タイプ: {slide.slide_type.value}")
    click.echo("")
    
    if analysis['suggestions']:
        click.echo("📝 提案:")
        for suggestion in analysis['suggestions']:
            icon = "❓" if suggestion.type == "question" else "💡"
            click.echo(f"  {icon} {suggestion.content}")
        click.echo("")
    
    if analysis['citations']:
        click.echo("📚 出典情報:")
        for citation in analysis['citations']:
            click.echo(f"  - {citation.get('source', '出典不明')}")

def _slide_to_dict(result):
    """スライド分析結果を辞書に変換"""
    slide = result['slide']
    analysis = result['analysis']
    
    return {
        "slide": {
            "number": slide.slide_number,
            "title": slide.title,
            "type": slide.slide_type.value,
            "content": slide.text_content,
            "images": slide.images,
            "notes": slide.notes
        },
        "suggestions": [
            {
                "type": s.type,
                "content": s.content,
                "relevance_score": s.relevance_score,
                "reasoning": s.reasoning
            } for s in analysis['suggestions']
        ],
        "citations": analysis['citations']
    }

if __name__ == '__main__':
    cli()