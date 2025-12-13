# Concept Crystallizer: Turn chaos into structure
"""
Takes a messy, exploratory conversation and crystallizes it into:
- Structured outline
- Key insights
- Open questions
- Next steps
"""

from dataclasses import dataclass
from typing import List
from datetime import datetime

@dataclass
class CrystallizedOutput:
    title: str
    insights: List[str]
    open_questions: List[str]
    next_steps: List[str]
    raw_markdown: str
    created_at: datetime

class Crystallizer:
    """Turn messy chats into structured documents."""
    
    PROMPT_TEMPLATE = """Crystallize this research conversation into a structured document:

{conversation}

Format:
# [Topic Title]

## Key Insights
- [Insight 1]
- [Insight 2]

## Open Questions
- [Question 1]

## Recommended Papers
- [Paper 1 with why]

## Next Steps
1. [Action item]"""

    def __init__(self, foundation):
        self.foundation = foundation
    
    async def crystallize(self, messages: List[dict]) -> CrystallizedOutput:
        """Convert conversation history to structured output."""
        # Format conversation
        conversation = "\n".join([
            f"{'User' if msg.get('role') == 'user' else 'AI'}: {msg.get('content', '')}"
            for msg in messages
        ])
        
        prompt = self.PROMPT_TEMPLATE.format(conversation=conversation)
        
        result = await self.foundation.generate_async(
            prompt=prompt,
            system="You are a research curator. Be concise and actionable.",
            max_tokens=800
        )
        
        return CrystallizedOutput(
            title=self._extract_title(result),
            insights=self._extract_section(result, "Key Insights"),
            open_questions=self._extract_section(result, "Open Questions"),
            next_steps=self._extract_section(result, "Next Steps"),
            raw_markdown=result,
            created_at=datetime.now()
        )
    
    def _extract_title(self, text: str) -> str:
        lines = text.strip().split('\n')
        for line in lines:
            if line.startswith('# '):
                return line[2:].strip()
        return "Untitled"
    
    def _extract_section(self, text: str, section_name: str) -> List[str]:
        lines = text.split('\n')
        in_section = False
        items = []
        
        for line in lines:
            if section_name in line:
                in_section = True
                continue
            if in_section:
                if line.startswith('## '):
                    break
                if line.startswith('- ') or line.startswith('1. '):
                    items.append(line[2:].strip())
        
        return items
    
    def export_markdown(self, output: CrystallizedOutput) -> str:
        """Export as Obsidian-compatible markdown."""
        return output.raw_markdown
