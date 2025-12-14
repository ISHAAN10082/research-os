import os
from datetime import datetime
from typing import Dict, List, Any

class ResearchReporter:
    """
    Generates high-quality Markdown reports and syncs them to an Obsidian Vault.
    Handles LaTeX formatting, frontmatter, and cross-linking.
    """
    
    def __init__(self, vault_path: str = "data/obsidian_vault"):
        self.vault_path = vault_path
        os.makedirs(self.vault_path, exist_ok=True)
        os.makedirs(os.path.join(self.vault_path, "Papers"), exist_ok=True)
        os.makedirs(os.path.join(self.vault_path, "Debates"), exist_ok=True)
        os.makedirs(os.path.join(self.vault_path, "Hypotheses"), exist_ok=True)
        
    def generate_paper_report(self, paper: Dict, claims: List[Dict], debates: List[Dict]) -> str:
        """
        Creates a comprehensive analysis report for a single paper.
        """
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M")
        
        # 1. Frontmatter
        md = f"""---
title: "{paper.get('title', 'Unknown Paper')}"
type: paper_analysis
date: {timestamp}
tags: [research_os, analysis]
status: processed
---

# 📄 {paper.get('title', 'Unknown Paper')}

**Authors:** {paper.get('authors', 'Unknown')}
**Processed:** {timestamp}

## 🔍 Executive Summary
*Extracted {len(claims)} claims and facilitated {len(debates)} automated debates.*

---

## 💡 Key Claims Extracted
"""
        
        # 2. Claims Section
        for i, claim in enumerate(claims):
            conf_icon = "🟢" if claim.get('confidence', 0) > 0.8 else "🟡"
            md += f"### Claim {i+1}: {claim.get('claim_type', 'General').title()} {conf_icon}\n"
            md += f"> {claim.get('text')}\n\n"
            if claim.get('section'):
                md += f"*Source: Section {claim['section']}*\n\n"
            
        # 3. Debate Section
        md += "---\n## ⚔️ AI Debate Synthesis\n"
        if not debates:
            md += "*No contradictions or significant debates triggered for this paper.*\n"
        
        for debate in debates:
            verdict = debate.get('verdict', 'unknown')
            icon = {"refutes": "🔴", "supports": "🟢", "extends": "🔵", "orthogonal": "⚪"}.get(verdict, "⚪")
            
            md += f"### {icon} Relation: {verdict.upper()}\n"
            md += f"**Versus:** [[{debate.get('claim_b_id', 'Unknown Claim')}]]\n\n"
            md += f"**Confidence:** {int(debate.get('confidence', 0)*100)}%\n\n"
            md += f"**Synthesis:**\n{debate.get('explanation')}\n\n"
            
            md += "<details><summary>View Full Debate Log</summary>\n\n"
            for entry in debate.get('log', []):
                md += f"- {entry}\n"
            md += "</details>\n\n"

        return md

    def generate_hypothesis_report(self, hypotheses: List[Dict]) -> str:
        """
        Creates a 'Future Research' report based on generated hypotheses.
        """
        timestamp = datetime.now().strftime("%Y-%m-%d")
        md = f"""---
title: "Research Hypotheses - {timestamp}"
type: hypothesis_log
date: {timestamp}
---

# 🚀 Research Opportunities ({timestamp})

## High Priority: Contradictions
"""
        for h in hypotheses:
            if h.get('priority') == 'high':
                md += f"### 🔴 {h['description']}\n"
                md += f"**Proposed Action:** {h['proposed_action']}\n"
                md += f"**Involved:** {', '.join(h.get('claims_involved', []))}\n\n"
                
        md += "## Medium Priority: Validation Needed\n"
        for h in hypotheses:
            if h.get('priority') == 'medium':
                md += f"### 🟡 {h['description']}\n"
                md += f"**Action:** {h['proposed_action']}\n\n"
                
        return md

    def save_to_vault(self, filename: str, content: str, folder: str = ""):
        """Writes the markdown file to the Obsidian vault."""
        # Sanitize filename
        safe_name = "".join([c for c in filename if c.isalpha() or c.isdigit() or c==' ' or c=='-']).strip()
        path = os.path.join(self.vault_path, folder, f"{safe_name}.md")
        
        with open(path, "w", encoding="utf-8") as f:
            f.write(content)
        print(f"📝 Saved report to {path}")
