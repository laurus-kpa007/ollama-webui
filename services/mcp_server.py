"""
MCP Server - Provides tools to AI agents
"""
from mcp.server.fastmcp import FastMCP
import os
import json
import requests
from datetime import datetime

# Initialize MCP server
mcp = FastMCP("ollama-webui-tools")

# ========== BASIC TOOLS ==========

@mcp.tool()
def add_numbers(a: int, b: int) -> int:
    """Add two numbers together

    Args:
        a: First number
        b: Second number

    Returns:
        Sum of a and b
    """
    return a + b

@mcp.tool()
def multiply_numbers(a: float, b: float) -> float:
    """Multiply two numbers

    Args:
        a: First number
        b: Second number

    Returns:
        Product of a and b
    """
    return a * b

@mcp.tool()
def calculate(expression: str) -> str:
    """Evaluate a mathematical expression safely

    Args:
        expression: Mathematical expression to evaluate (e.g., "2 + 2 * 3")

    Returns:
        Result of the calculation
    """
    try:
        # Safe evaluation (limited to math operations)
        import ast
        import operator

        ops = {
            ast.Add: operator.add,
            ast.Sub: operator.sub,
            ast.Mult: operator.mul,
            ast.Div: operator.truediv,
            ast.Pow: operator.pow,
            ast.USub: operator.neg,
        }

        def eval_expr(node):
            if isinstance(node, ast.Num):
                return node.n
            elif isinstance(node, ast.BinOp):
                return ops[type(node.op)](eval_expr(node.left), eval_expr(node.right))
            elif isinstance(node, ast.UnaryOp):
                return ops[type(node.op)](eval_expr(node.operand))
            else:
                raise TypeError(node)

        result = eval_expr(ast.parse(expression, mode='eval').body)
        return str(result)
    except Exception as e:
        return f"Error: {str(e)}"

# ========== TEXT TOOLS ==========

@mcp.tool()
def count_words(text: str) -> int:
    """Count words in a text

    Args:
        text: Text to count words in

    Returns:
        Number of words
    """
    return len(text.split())

@mcp.tool()
def count_characters(text: str, include_spaces: bool = True) -> int:
    """Count characters in a text

    Args:
        text: Text to count characters in
        include_spaces: Whether to include spaces in the count

    Returns:
        Number of characters
    """
    if include_spaces:
        return len(text)
    else:
        return len(text.replace(' ', ''))

@mcp.tool()
def reverse_text(text: str) -> str:
    """Reverse a text string

    Args:
        text: Text to reverse

    Returns:
        Reversed text
    """
    return text[::-1]

@mcp.tool()
def to_uppercase(text: str) -> str:
    """Convert text to uppercase

    Args:
        text: Text to convert

    Returns:
        Uppercase text
    """
    return text.upper()

@mcp.tool()
def to_lowercase(text: str) -> str:
    """Convert text to lowercase

    Args:
        text: Text to convert

    Returns:
        Lowercase text
    """
    return text.lower()

# ========== DATE/TIME TOOLS ==========

@mcp.tool()
def get_current_time() -> str:
    """Get the current date and time

    Returns:
        Current date and time in ISO format
    """
    return datetime.now().isoformat()

@mcp.tool()
def get_current_date() -> str:
    """Get the current date

    Returns:
        Current date in YYYY-MM-DD format
    """
    return datetime.now().strftime('%Y-%m-%d')

@mcp.tool()
def get_day_of_week() -> str:
    """Get the current day of the week

    Returns:
        Day name (e.g., 'Monday')
    """
    return datetime.now().strftime('%A')

# ========== FILE TOOLS ==========

@mcp.tool()
def list_files(directory: str = ".") -> list:
    """List files in a directory

    Args:
        directory: Directory path to list files from

    Returns:
        List of filenames
    """
    try:
        files = os.listdir(directory)
        return [f for f in files if os.path.isfile(os.path.join(directory, f))]
    except Exception as e:
        return [f"Error: {str(e)}"]

@mcp.tool()
def read_file(file_path: str, max_lines: int = 100) -> str:
    """Read contents of a file

    Args:
        file_path: Path to the file
        max_lines: Maximum number of lines to read

    Returns:
        File contents (up to max_lines)
    """
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            lines = f.readlines()[:max_lines]
            return ''.join(lines)
    except Exception as e:
        return f"Error reading file: {str(e)}"

# ========== WEB TOOLS ==========

@mcp.tool()
def fetch_url(url: str) -> dict:
    """Fetch content from a URL

    Args:
        url: URL to fetch

    Returns:
        Dictionary with status_code and content
    """
    try:
        response = requests.get(url, timeout=10)
        return {
            "status_code": response.status_code,
            "content": response.text[:1000],  # First 1000 chars
            "headers": dict(response.headers)
        }
    except Exception as e:
        return {"error": str(e)}

@mcp.tool()
def search_web(query: str, max_results: int = 5) -> dict:
    """Search the web for information (simulated)

    Args:
        query: Search query
        max_results: Maximum number of results

    Returns:
        Search results
    """
    # This is a placeholder - integrate with a real search API
    return {
        "query": query,
        "results": [
            {
                "title": f"Result for: {query}",
                "snippet": "This is a simulated search result. Integrate with DuckDuckGo or Google API for real results.",
                "url": "https://example.com"
            }
        ],
        "note": "This is a simulated search. Configure a real search API for production use."
    }

# ========== IMAGE GENERATION TOOLS ==========

@mcp.tool()
def generate_image_with_comfyui(
    prompt: str,
    negative_prompt: str = "",
    width: int = 1024,
    height: int = 1024,
    steps: int = 20,
    cfg_scale: float = 7.0
) -> dict:
    """Generate an image using ComfyUI

    Args:
        prompt: Image generation prompt
        negative_prompt: Negative prompt
        width: Image width
        height: Image height
        steps: Number of inference steps
        cfg_scale: CFG scale

    Returns:
        Result with image URL
    """
    try:
        # This would integrate with your existing ComfyUI client
        # For now, return a placeholder
        return {
            "success": True,
            "prompt": prompt,
            "message": "Image generation tool - integrate with ComfyUI client",
            "note": "Call /api/generate_image endpoint for actual generation"
        }
    except Exception as e:
        return {
            "success": False,
            "error": str(e)
        }

# ========== RESOURCES ==========

@mcp.resource("config://settings")
def get_app_config() -> str:
    """Get application configuration"""
    return """
    Application: Ollama WebUI v2.0
    Features: Chat, Image Generation, Multi-agent, MCP Tools
    Status: Active
    """

@mcp.resource("tools://list")
def get_tools_list() -> str:
    """Get list of available tools"""
    tools = [
        "add_numbers", "multiply_numbers", "calculate",
        "count_words", "count_characters", "reverse_text",
        "to_uppercase", "to_lowercase",
        "get_current_time", "get_current_date", "get_day_of_week",
        "list_files", "read_file",
        "fetch_url", "search_web",
        "generate_image_with_comfyui"
    ]
    return "\n".join(f"- {tool}" for tool in tools)

# ========== PROMPTS ==========

@mcp.prompt()
def code_review_prompt() -> list:
    """Generate a code review prompt"""
    return [
        {
            "role": "user",
            "content": """Please review the following code for:
1. Code quality and best practices
2. Potential bugs or security issues
3. Performance optimizations
4. Readability improvements
5. Documentation completeness

Provide specific, actionable feedback."""
        }
    ]

@mcp.prompt()
def image_prompt_enhancer(user_prompt: str) -> list:
    """Enhance an image generation prompt

    Args:
        user_prompt: The user's original prompt
    """
    return [
        {
            "role": "system",
            "content": "You are an expert at creating detailed image generation prompts."
        },
        {
            "role": "user",
            "content": f"""Enhance this image generation prompt: "{user_prompt}"

Add details about:
- Artistic style (e.g., realistic, anime, oil painting)
- Lighting and atmosphere (e.g., golden hour, dramatic, soft)
- Colors and mood (e.g., vibrant, muted, warm tones)
- Composition (e.g., rule of thirds, centered)
- Technical details (e.g., 8K resolution, highly detailed)

Return only the enhanced prompt, nothing else."""
        }
    ]

@mcp.prompt()
def summarize_prompt() -> list:
    """Generate a text summarization prompt"""
    return [
        {
            "role": "user",
            "content": """Please summarize the following text in 3-5 bullet points,
focusing on the most important information."""
        }
    ]

# Run the server
if __name__ == "__main__":
    print("Starting MCP Server...")
    print(f"Available tools: {len([f for f in dir(mcp) if not f.startswith('_')])}")
    mcp.run()
