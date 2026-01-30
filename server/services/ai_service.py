import json
from openai import OpenAI
from config import Config


class AIService:
    def __init__(self):
        api_key = Config.OPENROUTER_API_KEY
        if not api_key:
            raise ValueError('OPENROUTER_API_KEY not found in environment variables')

        default_headers = {}
        if Config.OPENROUTER_SITE_URL:
            default_headers['HTTP-Referer'] = Config.OPENROUTER_SITE_URL
        if Config.OPENROUTER_APP_NAME:
            default_headers['X-Title'] = Config.OPENROUTER_APP_NAME

        self.openrouter_client = OpenAI(
            api_key=api_key,
            base_url=Config.OPENROUTER_BASE_URL,
            default_headers=default_headers or None,
            timeout=180.0  # 3 minute timeout for kimi
        )
        
        # also initialize openai client if key is available
        self.openai_client = None
        if Config.OPENAI_API_KEY:
            self.openai_client = OpenAI(
                api_key=Config.OPENAI_API_KEY,
                timeout=120.0  # 2 minute timeout for openai
            )
        
        self.model = Config.AI_MODEL
        self.current_provider = 'openrouter'  # or 'openai'
        self.client = self.openrouter_client

    def set_model(self, model_name: str):
        """switch between openai and kimi models"""
        if model_name == 'openai':
            if not self.openai_client:
                raise ValueError('OpenAI API key not configured')
            self.client = self.openai_client
            self.model = 'gpt-4o-mini'
            self.current_provider = 'openai'
            print(f"switched to OpenAI (gpt-4o-mini)")
        else:  # kimi or default
            self.client = self.openrouter_client
            self.model = 'moonshotai/kimi-k2.5'
            self.current_provider = 'openrouter'
            print(f"switched to Kimi (moonshotai/kimi-k2.5)")

    def _chat(self, messages, response_format_json=True, **kwargs):
        params = {
            'model': self.model,
            'messages': messages,
            **kwargs,
        }

        if response_format_json:
            params['response_format'] = {"type": "json_object"}

        try:
            return self.client.chat.completions.create(**params)
        except Exception as e:
            message = str(e)
            
            # check for timeout
            if 'timeout' in message.lower() or 'timed out' in message.lower():
                raise Exception(f"AI request timed out after {self.client.timeout}s using {self.current_provider}. Try using OpenAI instead or simplifying your content.")
            
            # openrouter/model may not support response_format; retry without it
            if response_format_json and ('response_format' in message or 'Unknown parameter' in message):
                params.pop('response_format', None)
                return self.client.chat.completions.create(**params)
            
            raise
    
    def preprocess_content_structure(self, content_text, layouts, num_images=0, slide_size=None):
        """
        Preprocess raw content into structured slide outlines with comprehensive information organization.
        AI analyzes both content and layouts to determine the best structure ensuring all content is preserved.
        """
        # filter out highly specialized/complex layouts for initial generation
        preferred_categories = [
            'title_slide', 'section_divider', 'table_of_contents', 
            'content_standard', 'content_with_image', 'image_focused',
            'two_column', 'comparison', 'closing_slide'
        ]
        
        general_layouts = [
            l for l in layouts 
            if l.get('category') in preferred_categories or not l.get('category')
        ]
        
        if not general_layouts:
            general_layouts = layouts
        
        # note: _format_layouts_for_prompt will add [TEXT-ONLY] suffixes for display
        layout_descriptions = self._format_layouts_for_prompt(general_layouts)
        
        system_prompt = """You are a presentation architect specializing in comprehensive information organization.

IMPORTANT: You are working with general-purpose layouts only. These layouts are designed 
for standard content patterns (1-3 text sections, 0-2 images). Focus on clear, predictable 
structures. More complex or specialized layouts will be available during manual editing if needed.

Your PRIMARY GOAL: Ensure ALL content is preserved and conveyed meaningfully - NO INFORMATION should be lost.

Your task is to:
1. Analyze the raw content and identify all key points, arguments, and supporting details.
2. Analyze the available slide layouts to understand the visual and structural possibilities.
3. Architect a slide deck that conveys all information using appropriate layouts.

PRESENTATION ORGANIZATION STRATEGY:
1. USE all provided content - every important point must be included
2. If title_slide layout exists: START with it (company name, main topic, tagline)
3. If table_of_contents layout exists: USE it early (slide 2 or 3) to overview the structure
4. Organize content into logical sections based on natural information flow
5. Use section_divider layouts to separate major topics when available
6. If closing_slide layout exists: END with it (summary, takeaway, call-to-action, thank you)
7. Match content to appropriate layout types based on information density and visual needs
8. Ensure smooth narrative flow from slide to slide

LAYOUT MAPPING STRATEGY - TEXT CAPACITY:
- CRITICAL: Each text placeholder shows "maximum capacity: X chars (Y words)". 
  This is the MAXIMUM amount of text that will physically fit in that placeholder.
- You MUST stay within these character/word limits. Going over will cause text overflow.
- When calculating text length, count ALL characters including spaces and punctuation.
- If your content exceeds a placeholder's capacity, you have 3 options:
  1. Choose a different layout with higher capacity placeholders
  2. Split the content across multiple slides
  3. Condense/summarize the text to fit within the limit
- NEVER exceed the stated character/word limits. It is better to create additional slides than to overflow.
- For titles: aim for 20-60 chars (3-10 words), max 100 chars
- For body text: aim for at least 100 chars minimum, ideally 200-800 chars for substantive content

AESTHETIC LAYOUT PRINCIPLES - AVOID WHITE SPACE WASTE:
- **CRITICAL: Negative space limit**: Each layout shows its "negative space" percentage. 
  * NEVER use layouts with >50% negative space unless absolutely necessary
  * Prefer layouts with 30-50% negative space (well-balanced)
  * Layouts with <30% negative space are dense/full (good for content-heavy slides)
  * A layout marked "NEGATIVE SPACE: 65%" is TOO SPARSE - avoid it!
- **Balance is key**: Don't put 2 sentences in a layout designed for 5 paragraphs
- **Text density guidelines**: 
  * Small placeholders (< 500 chars capacity) = concise bullets or short statements only (100-400 chars)
  * Medium placeholders (500-1500 chars) = 2-4 substantial bullet points or 1-2 paragraphs (400-1200 chars)
  * Large placeholders (> 1500 chars) = detailed explanations, multiple paragraphs (1000+ chars)
- **Target 50-90% fill**: Aim to use 50-90% of each placeholder's capacity for optimal aesthetics
- **Visual hierarchy**: Use layouts that create natural reading flow (title → key points → details)
- **Content length recommendations**:
  * One key point: 50-150 chars
  * Bullet list (3-5 items): 200-500 chars
  * Short paragraph: 300-600 chars
  * Detailed explanation: 600-1500 chars
  * Multiple paragraphs: 1000-2500 chars
- **Don't waste space**: If you have substantial content, use layouts that can showcase it properly
- **Match content to container**: Short content → compact layouts; Detailed content → spacious layouts
- Use multi-placeholder layouts for comparisons or complex groupings.
- Use image-capable layouts where visual support enhances the message.
- Match expository content to layouts with clear title/body regions.
- Match visual/abstract content to image-focused layouts.

CRITICAL CONSTRAINTS:
1. You can ONLY use the exact 'layout_name' values from the "VALID LAYOUT NAMES" list above.
2. DO NOT invent layout names - use the EXACT names provided (they will be in quotes).
3. For each slide, you MUST populate EVERY placeholder index (idx) defined in that layout.
4. Match types exactly: TEXT placeholders get text, IMAGE placeholders get an image_index.
5. If images are provided (indices 0 to N-1), you MUST use all of them exactly once across the deck.

Return a JSON object with:
{
  "structure": [
    {
      "slide_number": 1,
      "slide_type": "title|key_message|section_divider|content|conclusion",
      "layout_name": "EXACT layout name from the list",
      "placeholders": [
        {
          "idx": number,
          "type": "text|image",
          "content": "string (for text)",
          "image_index": number (for image)
        }
      ],
      "notes": "speaker notes",
      "rationale": "why this layout was chosen for this specific content chunk"
    }
  ],
  "deck_summary": {
    "total_slides": number,
    "flow_description": "description of how content is organized and flows",
    "key_message": "the core takeaway"
  }
}"""

        text_prompt = f"""Available Layouts:
{layout_descriptions}

Raw Content to Process:
{content_text}

Number of Images Available: {num_images}
{f"Image indices to use: 0 to {num_images-1}" if num_images > 0 else ""}

Organize ALL this information into a well-structured presentation using the available layouts.
Ensure no content is lost - include all important points.
Use special slides (title, TOC, section dividers, closing) appropriately if available.
Return ONLY valid JSON."""

        try:
            response = self._chat(
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": text_prompt}
                ],
                response_format_json=True,
            )
            
            raw_content = response.choices[0].message.content
            print("\n" + "="*80)
            print("CONTENT STRUCTURE PREPROCESSING:")
            print("="*80)
            print(raw_content)
            print("="*80 + "\n")
            
            result = json.loads(raw_content)
            
            if 'structure' not in result:
                raise ValueError("AI response missing 'structure' field")
            
            # Validate and warn about aesthetic issues and diversity
            slides = result.get('structure', [])
            self._validate_aesthetic_choices(slides, layouts, slide_size)
            self._validate_layout_diversity(slides)
            
            return result
            
        except json.JSONDecodeError as e:
            raise ValueError(f"Failed to parse AI response as JSON: {str(e)}")
        except Exception as e:
            raise ValueError(f"AI preprocessing error: {str(e)}")
    
    def intelligent_chunk_with_layouts(self, raw_text, images, layouts, slide_size=None):
        """
        ai-driven intelligent chunking: analyzes raw text + images + layouts together
        to create slide-ready chunks where each chunk already knows its layout and content pairing.
        """
        print(f"\nAI INTELLIGENT CHUNKING (using {self.current_provider})")
        print(f"   raw text: {len(raw_text)} chars")
        print(f"   images: {len(images)}")
        print(f"   layouts: {len(layouts)}")
        
        # organize layouts by category
        layouts_by_category = {}
        for layout in layouts:
            cat = layout.get('category') or 'content_standard'
            layouts_by_category.setdefault(cat, []).append(layout)
        
        layout_display_names = {layout['name']: layout['name'] for layout in layouts}
        layout_descriptions = self._format_layouts_with_categories(layouts, layouts_by_category, layout_display_names, slide_size)
        
        image_descriptions = self._format_images_with_vision(images)
        
        print(f"   layout descriptions: {len(layout_descriptions)} chars")
        print(f"   image descriptions: {len(image_descriptions)} chars")
        
        system_prompt = f"""You are an expert presentation designer. Create slides with OPTIMAL AESTHETIC BALANCE.

AVAILABLE LAYOUTS (RANKED BY QUALITY):
{layout_descriptions}

AVAILABLE IMAGES:
{image_descriptions}

IMAGE USAGE REQUIREMENTS:
{f"- You have {len(images)} image(s) available (image_index: 0 to {len(images)-1})" if len(images) > 0 else "- No images provided for this deck"}
{f"- CRITICAL: You MUST use ALL {len(images)} images exactly once in the deck" if len(images) > 0 else ""}
{f"- For IMAGE placeholders, use: {{'idx': X, 'type': 'image', 'image_index': N}}" if len(images) > 0 else ""}
{f"- Each image_index (0-{len(images)-1}) must appear EXACTLY ONCE across all slides" if len(images) > 0 else ""}
{f"- Choose layouts with IMAGE placeholders to accommodate these {len(images)} image(s)" if len(images) > 0 else ""}

LAYOUT SELECTION STRATEGY:

The layouts are organized by CAPACITY-BASED CATEGORIES showing what fits on each slide:
- Category names like "2 text (1 large, 1 small) + 1 image" tell you EXACTLY what fits
- "large text" = high capacity (>800 chars) or large font (>36pt)
- "medium text" = medium capacity (400-800 chars) or medium font (24-36pt)
- "small text" = lower capacity (<400 chars) or small font (<24pt)

Layouts are divided into TWO sections:

1. RECOMMENDED LAYOUTS - USE THESE!
   - Good space utilization (<50% negative space)
   - Professional appearance
   - ALWAYS try to use layouts from this section first
   - Grouped by capacity categories for easy matching

2. AVOID LAYOUTS - DO NOT USE!
   - >50% negative space = mostly empty slide
   - Looks unprofessional and wastes space
   - ONLY use if creating a minimalist title slide with <80 chars total

## SLIDE TYPE HIERARCHY (CRITICAL!)

Your deck should follow this structure when appropriate:

1. **TITLE SLIDE** (if available and content warrants it):
   - Use: Layouts with "title_slide" category or minimal capacity (<200 chars)
   - Content: Company name, main topic (2-5 words each placeholder)
   - Total content: <100 chars across ALL placeholders
   - Example: Title: "Company Overview" (17 chars) | Subtitle: "Q4 2024 Results" (15 chars)
   
2. **SECTION DIVIDER** (for major topic changes):
   - Use: Layouts with "section_divider" in name/category or minimal layouts (<200 chars)
   - Content: Section name ONLY (2-5 words, one short phrase)
   - Total content: <80 chars
   - When: Between distinct topics (Problem → Solution, Overview → Details, Q1 → Q2)
   - Example: "Market Analysis" or "Growth Strategy"
   
3. **CONTENT SLIDES** (main information):
   - Use: content_standard, content_with_image, two_column, high-capacity layouts (400-1000 chars)
   - Content: Bullet lists (plain text with \\n separators, NO • or - markers)
   - Each bullet: 3-7 words maximum
   - Title: Short label (2-5 words)
   - Body: All information as plain bullet points
   - Example Title: "Revenue Growth"
   - Example Body: "Q4 revenue: $2.3M\\nYear-over-year: +23%\\nEnterprise segment leading\\nNew markets: 3"
   
4. **CLOSING SLIDE** (if available):
   - Use: Layouts with "closing" in name/category or minimal layouts (<200 chars)
   - Content: Summary, call-to-action, thank you (2-5 words each)
   - Total content: <100 chars
   - Example: Title: "Thank You" | Body: "Questions welcome"

## SLIDE TYPE SELECTION RULES

For EACH slide, determine its TYPE first, then choose appropriate layout:

- **title_slide**: Minimal capacity layouts, <100 chars total, no detailed information
- **section_divider**: Minimal layouts with SINGLE title placeholder, <80 chars, section name only
- **content**: Standard/high capacity layouts (400-1000 chars), full information with bullets
- **closing_slide**: Minimal capacity layouts, <100 chars total, brief closing message

CRITICAL: Do NOT put detailed information on structural slides (title/divider/closing)!
CRITICAL: Content slides should have SUBSTANTIAL information (>200 chars), not just titles!

YOUR PROCESS - CONTENT-DRIVEN APPROACH:
1. Total text: {len(raw_text)} chars
2. Break content into NATURAL TOPICAL SECTIONS (1 section = 1+ slides)
3. For EACH section:
   a) Determine how much content this section contains
   b) Look at capacity categories to find suitable layouts
   c) If section has 800+ chars, SPLIT IT ACROSS MULTIPLE SLIDES
   d) Create AS MANY SLIDES AS NEEDED - don't force content to fit
   e) Each slide should be 70-85% full - comfortable, not cramped
   f) NEVER shorten or truncate content - just use more slides

SLIDE COUNT PHILOSOPHY:
- More slides with comfortable spacing > fewer slides with cramped text
- If you have 2000 chars to convey, use 3 slides @ 70% full each
- DON'T try to cram 2000 chars into 1 slide @ 120% capacity
- Let content breathe naturally

LAYOUT DIVERSITY (CRITICAL FOR VISUAL APPEAL):
- AVOID using the same layout repeatedly - it makes presentations boring and unprofessional
- AIM for visual variety: if you use a layout, try to use a DIFFERENT layout for the next slide
- GUIDELINE: Don't use the same layout more than 2-3 times in a 10-slide deck
- EXCEPTION: Title/section divider slides can be consistent (intentional branding)
- STRATEGY: 
  * Alternate between text-only and text+image layouts
  * Vary the number of content boxes (1-column → 2-column → 1-column)
  * Mix different capacity layouts even for similar content amounts
- THINK: "Would this presentation look repetitive if printed?" → If yes, diversify!
- Example good variety for 6 content slides:
  Slide 1: "Content with Picture" (1T+1I+1C)
  Slide 2: "Two Content" (1T+2C)  
  Slide 3: "Content 7" (1T+1C, different capacity)
  Slide 4: "Content with Picture" (can reuse, but not adjacent)
  Slide 5: "Statement" (1T+1C, different style)
  Slide 6: "Two Content" (can reuse from slide 2)
- Example bad (monotonous):
  All 6 slides use "Content with Picture" → looks like copy-paste

CRITICAL RULES:

0. BULLET POINTS ONLY - NO PARAGRAPHS! (MOST CRITICAL!)
   EVERY PIECE OF CONTENT MUST BE BULLET POINTS
   - **NEVER WRITE PARAGRAPHS OR LONG SENTENCES**
   - **ALWAYS USE CONCISE BULLET POINTS**: 3-7 words per bullet (max 10 words)
   - **ONE IDEA PER BULLET**: Each bullet = one clear, simple point
   - **FORMAT**: Plain text with \\n between bullets (NO • or - markers! PowerPoint auto-bullets will add them)
   - **Example PERFECT**:
     "Key market drivers\\nMobile-first strategy\\n65% growth rate\\nQ4 expansion complete"
   - **Example BAD (NEVER DO THIS)**:
     "Our market research shows that consumer behavior has shifted significantly towards online shopping with mobile devices becoming the primary channel and accounting for 65% of all purchases."
   
   FOR TITLES: Short phrases only (2-5 words)
   FOR CONTENT: Bulleted lists only (3-7 words per bullet, plain text with \\n separators, 5-8 bullets max per slide)

1. PREFER RECOMMENDED LAYOUTS
   - Start every layout choice by looking at the RECOMMENDED section
   - The AVOID section is there to warn you what to avoid

2. RESPECT PLACEHOLDER PURPOSE (CRITICAL!)
   MULTI-PLACEHOLDER SLIDES: Different text boxes serve DIFFERENT purposes!
   
   Each placeholder is labeled either TITLE or CONTENT:
   
   TITLE placeholders (large font >32pt):
     LARGE FONT = LABEL ONLY - NO INFORMATION!
     • STRICT LIMIT: 20-60 chars ONLY (2-5 WORDS)
     • Use for: LABELS, HEADERS, TITLES - that's it!
     • Think: "What would I write on a section divider?"
     • Examples: 
       "Market Overview" (15 chars)
       "Q4 Results" (10 chars)
       "Team Structure" (14 chars)
       "Growth Strategy" (15 chars)
     • NEVER EVER put:
       - Any information or details
       - Complete sentences
       - Bullet point lists
       - Data or numbers (unless it's a stat highlight like "23% Growth")
       - Multiple lines of text
       - Anything longer than 5 words
     • RULE: If font size > 32pt, it's a LABEL ONLY - zero information content!
     • If you put 100+ chars in a TITLE placeholder, the slide WILL BREAK!
   
   CONTENT placeholders (regular font <24pt):
     • THIS IS WHERE ALL INFORMATION GOES
     • Use 70-85% of stated capacity
     • Format: BULLET POINTS ONLY (3-7 words per bullet)
     • Use for: All actual information, data, details
     • This is the ONLY place for content - titles get NOTHING
   
   THE GOLDEN RULE - FONT SIZE DETERMINES PURPOSE:
   
   **LARGE FONT (>32pt) = ZERO INFORMATION**
   - Title is a LABEL: 2-5 words max
   - Example: "Growth Strategy" - that's it, nothing more
   - NO details, NO sentences, NO lists
   
   **SMALL FONT (<24pt) = ALL INFORMATION**
   - Content boxes get 100% of information as bullet points
   - Example: "Revenue up 23%\nNew markets: APAC, EU\nQ4 targets met"
   
   - On a slide with 1 TITLE + 1 CONTENT placeholder:
     → Title (44pt): "Growth Strategy" (15 chars, just a label)
     → Content (18pt): "Revenue: $2.3M (+23%)\nEnterprise: $1.2M\nSMB: $1.1M\nNew markets: 3\nQ4 performance strong" (all the info)
   
   - On a slide with 1 TITLE + 2 CONTENT placeholders:
     → Title (40pt): "Market Analysis" (15 chars, just a label)
     → Content box 1 (20pt): "Market size: $50B\nGrowth: 15% YoY\nOur share: 4.2%" (first half)
     → Content box 2 (20pt): "Competition: 3 major players\nOur advantage: pricing\nTarget: 6% share" (second half)
   
   COMMON MISTAKES TO AVOID:
   WRONG: Title (44pt): "Here are the key findings from our market research across Q3 and Q4 showing significant growth" (88 chars)
   RIGHT: Title (44pt): "Key Findings" (12 chars) + Content (18pt): "Q3 growth: 23%\nQ4 growth: 31%\nMarket research complete\nSignificant expansion"
   
   WRONG: Title (40pt): "Our revenue increased significantly this quarter with strong enterprise performance" (84 chars)
   RIGHT: Title (40pt): "Revenue Growth" (14 chars) + Content (18pt): "Total: $2.3M (+23%)\nEnterprise: +45%\nStrong Q4 results"

3. CAPACITY MATCHING - SPLIT, DON'T SQUEEZE
   - Layout shows "Capacity: ~800 chars" → write 560-680 chars (70-85% fill)
   - NEVER exceed 85% of stated capacity
   - If you have 1500 chars → use TWO slides @ 750 chars each
   - If you have 3000 chars → use FOUR slides @ 750 chars each
   - More slides with good spacing > fewer slides with tight cramming

4. FILL ALL PLACEHOLDERS
   - If layout has idx 0, 1, 2 → your response MUST have all three
   - Match content TYPE to placeholder PURPOSE

5. IMAGE SLOTS
   - Only use layouts with "IMAGE" if you're placing an image
   - Match counts: 1 image slot = use 1 image

6. EXACT NAMES
   - Copy layout names from "VALID LAYOUT NAMES" exactly

EXAMPLE 1 - LARGE FONT = LABEL ONLY!
Layout: idx 0 TITLE (44pt font, 60 char max) + idx 1 CONTENT (18pt font, 600 char max)
Content to convey: Market research findings about consumer behavior trends

BAD APPROACH - Treating large font as information container (WILL BREAK!):
{{
  "placeholders": [
    {{"idx": 0, "type": "text", "content": "Our market research shows that consumer behavior has shifted significantly towards online shopping with mobile devices becoming the primary channel"}},  // 154 chars in 44pt TITLE = DISASTER! Text will overflow off the slide!
    {{"idx": 1, "type": "text", "content": "More details here..."}}
  ]
}}
FONT SIZE 44PT = THIS IS A LABEL, NOT INFORMATION!

GOOD APPROACH - Large font = label, small font = bullet points (NO markers):
{{
  "placeholders": [
    {{"idx": 0, "type": "text", "content": "Consumer Behavior"}},  // 18 chars, 3 words - LABEL ONLY!
    {{"idx": 1, "type": "text", "content": "Online shopping dominates\\nMobile purchases: 65%\\nDesktop declining\\nKey drivers:\\nConvenience\\nPrice comparison\\nSeamless checkout\\nSocial commerce rising"}}  // ALL information, plain text!
  ]
}}
44pt font gets 3 words (label), 18pt font gets all the information (plain bullet points)!

EXAMPLE 2 - Layout with Multiple Content Boxes:
Layout: idx 0 TITLE (40pt, 55 char max) + idx 1 CONTENT (20pt, 400 char max) + idx 2 CONTENT (20pt, 400 char max)

BAD - Putting information in large font placeholder:
idx 0 (40pt): "Key findings include revenue growth of 23% year-over-year and expansion into three new markets" (95 chars) ← WRONG! 40pt = LABEL ONLY!
idx 1 (20pt): "Revenue: $2.3M" (14 chars) ← Under-filled
idx 2 (20pt): "Markets: APAC, EU, LATAM" (24 chars) ← Under-filled
This treats 40pt font like it can hold information - it CANNOT!

GOOD - 40pt = label (2 words), 20pt = all information (plain bullets):
idx 0 (40pt): "Growth Highlights" (18 chars, 2 words) ← LABEL ONLY!
idx 1 (20pt): "Revenue: $2.3M (+23%)\\nEnterprise: $1.2M (+45%)\\nSMB: $1.1M (stable)\\nQ4: Strong performance\\nNew clients: +30%" ← ALL revenue info!
idx 2 (20pt): "APAC launch: Q2\\nEU launch: Q3\\nLATAM: Pilot phase\\nAll: 15%+ MoM growth\\nTeams hired\\nLocalization done" ← ALL market info!
The 40pt large font gets ZERO information, just a 2-word label!

EXAMPLE 3 - Large Content (SPLIT IT!):
You have: "Market Analysis" section + 1800 chars of detailed analysis
Available layout capacity: ~900 chars total (1 title @ 50 chars + 1 content @ 850 chars)

BAD: Try to cram 1800 chars into one 900-char layout = 200% overflow!
GOOD: Split across THREE slides:
   - Slide 1: Title "Market Size" (11 chars) + 650 chars content
   - Slide 2: Title "Market Trends" (13 chars) + 600 chars content  
   - Slide 3: Title "Opportunities" (13 chars) + 550 chars content
   Result: Same content, naturally flowing, comfortable spacing

Return JSON:
{{
  "slides": [
    {{
      "slide_number": 1,
      "slide_type": "content",
      "layout_name": "EXACT name from RECOMMENDED section if possible",
      "placeholders": [
        {{"idx": 0, "type": "text", "content": "title"}},
        {{"idx": 1, "type": "text", "content": "body text"}},
        {{"idx": 2, "type": "image", "image_index": 0}}
      ],
      "notes": "rationale: chose from RECOMMENDED, capacity matches, 60% filled, image 0 placed"
    }}
  ],
  "deck_summary": {{
    "total_slides": N,
    "flow_description": "how slides flow from intro → body → conclusion",
    "key_message": "main takeaway from the presentation"
  }}
}}

REMEMBER: If images were provided, EVERY image_index (0 to N-1) MUST appear exactly once!

CRITICAL REMINDERS BEFORE YOU START:
0. ALL CONTENT MUST BE BULLET POINTS! NO PARAGRAPHS!
   - Each bullet: 3-7 words (max 10 words)
   - Use \\n between bullets
   - Example: "Mobile growth: 65%\\nDesktop declining\\nQ4 targets achieved"
1. Check EVERY layout you plan to use - look at the placeholder details
2. For EACH text placeholder, check if it says "TITLE" or "CONTENT"
3. TITLE = max 60 chars (short headline only!)
4. CONTENT = 70-85% of stated capacity using BULLET POINTS
5. Count your characters BEFORE assigning content to placeholders
6. If your title is >60 chars, it's NOT a title - it's content that needs shortening
7. NEVER exceed character limits - if content doesn't fit, SPLIT across MORE SLIDES
8. FINAL CHECK: Are ALL content placeholders using concise bullet points?

Return ONLY valid JSON. Remember: Prefer RECOMMENDED layouts!"""

        user_prompt = f"""Raw Text Content:
{raw_text}

Create intelligent slide-ready chunks considering the available layouts and images.
Each chunk should already know which layout to use and which images to pair with its text."""

        try:
            response = self._chat(
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt}
                ],
                response_format_json=True,
            )
            
            result = json.loads(response.choices[0].message.content)
            
            if 'slides' not in result:
                raise ValueError("AI response missing 'slides' field")
            
            slides = result['slides']
            
            # ensure all required fields are present
            for i, slide in enumerate(slides):
                if 'slide_type' not in slide:
                    slide['slide_type'] = 'content'
                if 'notes' not in slide and 'rationale' in slide:
                    slide['notes'] = slide['rationale']
                elif 'notes' not in slide:
                    slide['notes'] = ''
            
            # ensure deck_summary has all required fields
            deck_summary = result.get('deck_summary', {})
            if 'flow_description' not in deck_summary:
                deck_summary['flow_description'] = deck_summary.get('structure_overview', 'Presentation flow')
            if 'key_message' not in deck_summary:
                deck_summary['key_message'] = 'Main presentation takeaway'
            result['deck_summary'] = deck_summary
            
            print(f"\nAI INTELLIGENT CHUNKING complete: {len(slides)} slides")
            for i, slide in enumerate(slides):
                layout = slide.get('layout_name', 'unknown')
                num_text = len([ph for ph in slide.get('placeholders', []) if ph.get('type') == 'text'])
                num_img = len([ph for ph in slide.get('placeholders', []) if ph.get('type') == 'image'])
                print(f"   slide {i+1}: {layout} ({num_text}T + {num_img}I)")
            
            # validate aesthetic choices and collect warnings
            warnings = self._validate_aesthetic_choices(slides, layouts, slide_size)
            
            # validate slide type hierarchy and content allocation
            slide_type_warnings = self._validate_slide_types(slides, layouts)
            warnings.extend(slide_type_warnings)
            
            # validate layout diversity
            diversity_warnings = self._validate_layout_diversity(slides)
            warnings.extend(diversity_warnings)
            
            # count critical issues (excessive negative space or major overflow)
            critical_issues = []
            for warning in warnings:
                if 'EXCESSIVE NEGATIVE SPACE' in warning or 'Exceeds by:' in warning:
                    critical_issues.append(warning)
            
            print(f"\nValidation summary: {len(warnings)} total warnings, {len(critical_issues)} critical")
            
            # if there are critical overflow issues OR title violations OR diversity issues, try one retry with feedback
            overflow_issues = [w for w in warnings if 'Exceeds by:' in w or 'overflow' in w.lower()]
            title_violations = [w for w in warnings if 'TITLE/HEADER' in w or ('idx' in w and 'chars' in w)]
            diversity_issues = [w for w in warnings if 'overused' in w.lower() or 'same layout' in w.lower() or 'diversity' in w.lower()]
            
            critical_issues = overflow_issues + title_violations + diversity_issues
            
            if critical_issues and len(critical_issues) >= 1:
                print(f"\n{len(critical_issues)} critical issues detected ({len(overflow_issues)} overflow, {len(title_violations)} title, {len(diversity_issues)} diversity)")
                
                feedback_prompt = f"""Your previous attempt had CRITICAL issues:

{chr(10).join(critical_issues[:8])}

CRITICAL FIXES REQUIRED:

1. TITLE PLACEHOLDERS (large font >32pt):
   - These are HEADERS, not content boxes!
   - STRICT LIMIT: 20-60 chars ONLY
   - Use for: "Market Overview" (15 chars), "Q4 Results" (10 chars), "Key Findings" (12 chars)
   - DO NOT put: paragraphs, sentences, bullet points, detailed data
   - DO NOT put: "Here are the key findings from our analysis showing..." (57 chars but still too wordy!)
   - DO put: "Analysis Findings" (18 chars) in TITLE, then put detailed text in CONTENT placeholder
   
   HOW TO FIX TITLE VIOLATIONS:
   - Look at what you wrote in the title placeholder
   - Is it more than 60 chars? → Extract a SHORT headline (5-8 words max)
   - Move the detailed information to the CONTENT placeholder below it
   - Example: Title had "Our comprehensive market research findings indicate strong growth potential" (76 chars)
     → Fix: Title becomes "Market Research Summary" (24 chars), content gets the detailed sentence

2. OVERFLOW ISSUES:
   - DO NOT shorten content
   - DO NOT truncate information
   - SPLIT content across MORE SLIDES instead
   - Example: 1200 chars in 800-char CONTENT placeholder → use TWO slides @ 600 chars each
   - The TITLE placeholder on each slide stays short (20-60 chars)

3. MULTI-PLACEHOLDER BALANCE:
   - If slide has 1 TITLE + 2 CONTENT placeholders:
     → TITLE gets ~30 chars (e.g., "Growth Strategy")
     → CONTENT 1 gets ~400 chars (first half of information)
     → CONTENT 2 gets ~400 chars (second half of information)
   - Don't spread content evenly across all boxes - TITLE is for headlines only!

4. LAYOUT DIVERSITY:
   - AVOID using the same layout repeatedly - vary your layout choices!
   - DON'T use the same layout for consecutive slides
   - Alternate between different layouts even if content is similar
   - Example: Use "Content with Picture" → "Two Content" → "Content 7" instead of all "Content with Picture"

Please regenerate with MORE SLIDES, SHORT TITLES, and DIVERSE LAYOUTS!

Original text (use ALL of it, split across more slides):
{raw_text[:500]}... ({len(raw_text)} total chars)

Return corrected JSON with MORE SLIDES."""

                try:
                    retry_response = self._chat(
                        messages=[
                            {"role": "system", "content": system_prompt},
                            {"role": "user", "content": user_prompt},
                            {"role": "assistant", "content": response.choices[0].message.content},
                            {"role": "user", "content": feedback_prompt}
                        ],
                        response_format_json=True,
                    )
                    
                    retry_result = json.loads(retry_response.choices[0].message.content)
                    
                    if 'slides' in retry_result:
                        slides = retry_result['slides']
                        
                        # ensure all required fields in retry
                        for i, slide in enumerate(slides):
                            if 'slide_type' not in slide:
                                slide['slide_type'] = 'content'
                            if 'notes' not in slide and 'rationale' in slide:
                                slide['notes'] = slide['rationale']
                            elif 'notes' not in slide:
                                slide['notes'] = ''
                        
                        # ensure deck_summary has all required fields
                        retry_deck_summary = retry_result.get('deck_summary', result.get('deck_summary', {}))
                        if 'flow_description' not in retry_deck_summary:
                            retry_deck_summary['flow_description'] = retry_deck_summary.get('structure_overview', 'Presentation flow')
                        if 'key_message' not in retry_deck_summary:
                            retry_deck_summary['key_message'] = 'Main presentation takeaway'
                        
                        original_slide_count = len(result.get('slides', []))
                        print(f"content split successful: expanded from {original_slide_count} to {len(slides)} slides")
                        
                        # re-validate (including diversity)
                        warnings = self._validate_aesthetic_choices(slides, layouts, slide_size)
                        diversity_warnings = self._validate_layout_diversity(slides)
                        warnings.extend(diversity_warnings)
                        
                        return {
                            'structure': slides,
                            'deck_summary': retry_deck_summary
                        }
                except Exception as e:
                    print(f"   retry failed: {e}, using original result")
            
            # final enforcement: zero overflow by splitting content into more slides
            slides = self._enforce_zero_overflow_by_splitting(slides, layouts, slide_size)
            
            # validate: ensure all images were used
            if len(images) > 0:
                used_image_indices = set()
                for i, slide in enumerate(slides):
                    for ph in slide.get('placeholders', []):
                        if ph.get('type') == 'image' and 'image_index' in ph:
                            used_image_indices.add(ph['image_index'])
                
                expected_indices = set(range(len(images)))
                missing_indices = expected_indices - used_image_indices
                extra_indices = used_image_indices - expected_indices
                
                if missing_indices:
                    raise ValueError(
                        f"AI did not use all images in the presentation. "
                        f"Missing image indices: {sorted(missing_indices)}. "
                        f"All {len(images)} uploaded images must be placed in the deck. "
                        f"Please check that layouts with IMAGE placeholders are available."
                    )
                
                if extra_indices:
                    raise ValueError(
                        f"AI used invalid image indices: {sorted(extra_indices)}. "
                        f"Only image indices 0-{len(images)-1} are available."
                    )
                
                print(f"✅ Image validation passed: all {len(images)} images used")
            
            return {
                'structure': slides,
                'deck_summary': result.get('deck_summary', {})
            }
            
        except json.JSONDecodeError as e:
            raise ValueError(f"Failed to parse AI response as JSON: {str(e)}")
        except Exception as e:
            raise ValueError(f"AI intelligent chunking error: {str(e)}")
    
    def _convert_chunks_to_slides(self, intelligent_chunks, images, layouts):
        """
        convert ai-generated intelligent chunks into full slide specifications.
        delegates back to ai to properly assign text and images to specific placeholders.
        """
        layout_map = {layout['name']: layout for layout in layouts}
        image_id_to_index = {img['id']: i for i, img in enumerate(images)}
        
        # ask ai to create detailed placeholder assignments for each chunk
        conversion_prompt = f"""You have created intelligent chunks. Now assign each chunk\'s content to specific placeholders.

For each chunk, you provided:
- suggested_layout: which layout to use
- text_content: the text for this slide
- suggested_images: which images to use

Now create the detailed placeholder assignments:

CHUNKS TO CONVERT:
{json.dumps(intelligent_chunks, indent=2)}

AVAILABLE IMAGES:
{json.dumps([{{'id': img['id'], 'filename': img['filename'], 'tags': img.get('tags', [])}} for img in images], indent=2)}

For each chunk, assign its text_content and suggested_images to the specific placeholder indices.
Review the layout structure and intelligently distribute content:
- Title text → title placeholders (typically idx 0)
- Body text → body placeholders (typically idx 1+)
- Images → image placeholders in order

Return JSON:
{{
  "slides": [
    {{
      "slide_number": 1,
      "layout_name": "exact layout name",
      "placeholders": [
        {{"idx": 0, "type": "text", "content": "title text"}},
        {{"idx": 1, "type": "text", "content": "body text"}},
        {{"idx": 2, "type": "image", "image_id": "img-xxx", "image_index": 0}}
      ]
    }}
  ]
}}"""

        try:
            response = self._chat(
                messages=[
                    {"role": "user", "content": conversion_prompt}
                ],
                response_format_json=True,
            )
            
            result = json.loads(response.choices[0].message.content)
            slides = result.get('slides', [])
            
            # add missing fields
            for i, slide in enumerate(slides):
                slide['slide_type'] = 'content'
                slide['source_chunk_ids'] = [intelligent_chunks[i].get('id', f'chunk-{i}')]
                slide['notes'] = intelligent_chunks[i].get('rationale', '')
                slide['rationale'] = intelligent_chunks[i].get('rationale', '')
            
            return slides
            
        except Exception as e:
            print(f"   conversion failed, using simple mapping: {e}")
            # fallback to simple mapping
            slides = []
            
            for i, chunk in enumerate(intelligent_chunks):
                layout_name = chunk.get('suggested_layout')
                text_content = chunk.get('text_content', '')
                suggested_image_ids = chunk.get('suggested_images', [])
                
                if not layout_name or layout_name not in layout_map:
                    print(f"   chunk {i+1}: invalid layout '{layout_name}', skipping")
                    continue
                
                layout = layout_map[layout_name]
                placeholders = []
                
                text_phs = [ph for ph in layout['placeholders'] if ph['type'] == 'text']
                img_phs = [ph for ph in layout['placeholders'] if ph['type'] == 'image']
                
                # assign text to first text placeholder
                if text_phs:
                    text_ph = text_phs[0]
                    ph_dict = {
                        'idx': text_ph['idx'],
                        'type': 'text',
                        'content': text_content
                    }
                    # CRITICAL: Add font size for enforcement
                    font_size = self._get_placeholder_font_size(text_ph)
                    if font_size:
                        ph_dict['font_size'] = font_size
                    placeholders.append(ph_dict)
                
                # assign images to image placeholders
                for j, img_ph in enumerate(img_phs):
                    if j < len(suggested_image_ids):
                        img_id = suggested_image_ids[j]
                        if img_id in image_id_to_index:
                            placeholders.append({
                                'idx': img_ph['idx'],
                                'type': 'image',
                                'image_id': img_id,
                                'image_index': image_id_to_index[img_id]
                            })
                
                slides.append({
                    'slide_number': i + 1,
                    'slide_type': 'content',
                    'layout_name': layout_name,
                    'source_chunk_ids': [chunk.get('id', f'chunk-{i}')],
                    'placeholders': placeholders,
                    'notes': chunk.get('rationale', ''),
                    'rationale': chunk.get('rationale', '')
                })
            
            return slides
    
    def preprocess_with_chunks_and_links(self, content_chunks, images, layouts, slide_size=None):
        """
        preprocess content chunks with linked images into structured slide outlines.
        ai selects layouts, content placement, and deck structure.
        """
        print(f"\nPREPROCESSING WITH {len(images)} IMAGES")
        for i, img in enumerate(images):
            img_id = img.get('id', 'NO_ID')
            filename = img.get('filename', 'NO_NAME')
            has_data = bool(img.get('data'))
            tags = img.get('tags', [])
            print(f"   Image {i}: {filename} (ID: {img_id}, has_data: {has_data}, tags: {tags})")
        
        print(f"\nCONTENT CHUNKS:")
        for i, chunk in enumerate(content_chunks):
            chunk_id = chunk.get('id', 'NO_ID')
            text_preview = chunk.get('text', '')[:50]
            linked_ids = chunk.get('linked_image_ids', [])
            print(f"   Chunk {i} (ID: {chunk_id}): \"{text_preview}...\" → linked to images: {linked_ids}")
        
        # create display names for misleading layouts (don't modify original names)
        layout_display_names = {}
        for layout in layouts:
            text_phs = [p for p in layout['placeholders'] if p['type'] == 'text']
            img_phs = [p for p in layout['placeholders'] if p['type'] == 'image']
            
            has_image_in_name = any(word in layout['name'].lower() for word in ['picture', 'image', 'photo'])
            has_no_image_placeholder = len(img_phs) == 0
            
            # create display name with warning suffix
            if has_image_in_name and has_no_image_placeholder:
                display_name = f"{layout['name']} [TEXT-ONLY: {len(text_phs)}T+0I]"
                layout_display_names[layout['name']] = display_name
                print(f"misleading layout detected: {layout['name']} → shown as {display_name}")
            else:
                layout_display_names[layout['name']] = layout['name']
        
        layouts_by_category = {}
        for layout in layouts:
            cat = layout.get('category') or 'content_standard'
            layouts_by_category.setdefault(cat, []).append(layout)
        
        print(f"\nPREPROCESSING WITH {len(layouts)} LAYOUTS:")
        layouts_with_images = 0
        for layout in layouts:
            valid_indices = [ph['idx'] for ph in layout['placeholders']]
            text_count = len([p for p in layout['placeholders'] if p['type'] == 'text'])
            img_count = len([p for p in layout['placeholders'] if p['type'] == 'image'])
            if img_count > 0:
                layouts_with_images += 1
            print(f"  - {layout['name']}: {text_count}T+{img_count}I, indices {valid_indices}")
        
        print(f"\n📊 LAYOUT SUMMARY:")
        print(f"   Total layouts: {len(layouts)}")
        print(f"   Layouts with image support: {layouts_with_images}")
        print(f"   Text-only layouts: {len(layouts) - layouts_with_images}")
        
        if len(images) > 0 and layouts_with_images == 0:
            print(f"\nCRITICAL: {len(images)} images provided but NO layouts support images!")
            print(f"   The AI will not be able to place images anywhere.")
        
        layout_descriptions = self._format_layouts_with_categories(layouts, layouts_by_category, layout_display_names, slide_size)
        
        image_id_to_index = {img['id']: i for i, img in enumerate(images)}
        image_tag_map = {}
        for img in images:
            for tag in img.get('tags', []):
                image_tag_map.setdefault(tag, []).append(img['id'])
        
        chunks_description = self._format_chunks_for_prompt(content_chunks, images, image_id_to_index)
        tag_guidelines = self._format_tag_guidelines(image_tag_map, images)
        image_descriptions = self._format_images_with_vision(images)
        
        system_prompt = f"""You are a presentation architect with access to categorized layouts.

Your task is to map user-provided text chunks and their linked images to appropriate slide layouts.
Your PRIMARY GOAL: Convey ALL information meaningfully - NO CONTENT should be lost.

PRESENTATION ORGANIZATION STRATEGY:
1. USE all provided content - every chunk must be included
2. If title_slide layout exists: START with it (company name, main topic)
3. If table_of_contents layout exists: USE it as slide 2 or 3 to overview sections
4. Use section_divider layouts to separate major topics/sections
5. If closing_slide layout exists: END with it (summary, call-to-action, thank you)
6. Organize content logically based on the natural flow of information
7. MATCH image content to appropriate layout categories:
   - Graphs/charts → content_with_image or image_focused
   - Multiple images → multi_image_grid
   - Logos → corner/small image layouts or title slide
8. Ensure smooth narrative flow from slide to slide

LAYOUT MAPPING STRATEGY - TEXT CAPACITY:
- CRITICAL: Each text placeholder shows "maximum capacity: X chars (Y words)". 
  This is the MAXIMUM amount of text that will physically fit in that placeholder.
- You MUST stay within these character/word limits. Going over will cause text overflow.
- When calculating text length, count ALL characters including spaces and punctuation.
- For titles: aim for 20-60 chars (3-10 words), max 100 chars
- For body text: aim for at least 100 chars minimum, ideally 200-800 chars for substantive content
- If your content exceeds limits: choose larger layout, split content, or condense text

AESTHETIC LAYOUT PRINCIPLES - AVOID WHITE SPACE WASTE:
- **CRITICAL: Negative space limit**: Each layout shows its "negative space" percentage. 
  * NEVER use layouts with >50% negative space unless absolutely necessary
  * Prefer layouts with 30-50% negative space (well-balanced)
  * Layouts with <30% negative space are dense/full (good for content-heavy slides)
  * A layout marked "NEGATIVE SPACE: 65%" is TOO SPARSE - avoid it!
- **Balance is key**: Don't put 2 sentences in a layout designed for 5 paragraphs
- **Text density guidelines**: 
  * Small placeholders (< 500 chars capacity) = concise bullets or short statements only (100-400 chars)
  * Medium placeholders (500-1500 chars) = 2-4 substantial bullet points or 1-2 paragraphs (400-1200 chars)
  * Large placeholders (> 1500 chars) = detailed explanations, multiple paragraphs (1000+ chars)
- **Target 50-90% fill**: Aim to use 50-90% of each placeholder's capacity for optimal aesthetics
- **Visual hierarchy**: Use layouts that create natural reading flow (title → key points → details)
- **Content length recommendations**:
  * One key point: 50-150 chars
  * Bullet list (3-5 items): 200-500 chars
  * Short paragraph: 300-600 chars
  * Detailed explanation: 600-1500 chars
  * Multiple paragraphs: 1000-2500 chars
- **Don't waste space**: If you have substantial content, use layouts that can showcase it properly
- **Match content to container**: Short content → compact layouts; Detailed content → spacious layouts

IMAGES WITH VISION ANALYSIS:
{image_descriptions}

{tag_guidelines}

STRICT LINKING CONSTRAINTS:
{chunks_description}

You MUST ensure all linked images appear on the same slide(s) as their associated text chunk.
If a layout cannot fit all linked images for a chunk, you must split the chunk across multiple slides 
while keeping each piece with its linked images intact.

CRITICAL CONSTRAINTS:
1. You can ONLY use the exact 'layout_name' values from the "VALID LAYOUT NAMES" list above.
2. DO NOT invent layout names - use the EXACT names as shown (including any [TEXT-ONLY] markers).
3. READ the STRUCTURE line: "2T+0I" means 2 text, 0 images. "1T+1I" means 1 text, 1 image.
4. If a layout shows "IMAGE: NONE", you CANNOT use it for slides that need images!
5. For each slide, you MUST use ONLY the VALID idx values listed for that specific layout.
6. DO NOT invent placeholder indices - each layout shows its "VALID idx: [...]"
7. You MUST populate EVERY placeholder index defined in the chosen layout (no missing indices).
8. Match types exactly: TEXT idx gets text content, IMAGE idx gets image_id/image_index.
9. ALL images MUST be used exactly once across the deck.
10. Each chunk\'s linked images MUST appear on slides containing that chunk\'s text.

Return a JSON object with:
{{
  "structure": [
    {{
      "slide_number": 1,
      "slide_type": "title|key_message|section_divider|content|conclusion",
      "layout_name": "EXACT layout name from VALID LAYOUT NAMES list (in quotes)",
      "source_chunk_ids": ["chunk-1"],
      "placeholders": [
        {{
          "idx": number,
          "type": "text|image",
          "content": "string (for text)",
          "image_id": "string (for image)",
          "image_index": number (for image, from provided mapping)
        }}
      ],
      "notes": "speaker notes",
      "rationale": "why this layout was chosen"
    }}
  ],
  "deck_summary": {{
    "total_slides": number,
    "flow_description": "description of how content is organized and flows",
    "key_message": "the core takeaway"
  }}
}}"""

        text_prompt = f"""Available Layouts:
{layout_descriptions}

Process ALL content chunks with their linked images and create a well-organized presentation.
CRITICAL: Include every chunk - no content should be lost.
Use special slides (title, TOC, section dividers, closing) appropriately if available.
Ensure smooth narrative flow while maintaining all text-image bindings.
Return ONLY valid JSON."""

        try:
            response = self._chat(
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": text_prompt}
                ],
                response_format_json=True,
            )
            
            raw_content = response.choices[0].message.content
            print("\n" + "="*80)
            print("CONTENT STRUCTURE PREPROCESSING WITH LINKS:")
            print("="*80)
            print(raw_content)
            print("="*80 + "\n")
            
            result = json.loads(raw_content)
            
            if 'structure' not in result:
                raise ValueError("AI response missing 'structure' field")
            
            # Validate and warn about aesthetic issues and diversity
            slides = result.get('structure', [])
            self._validate_aesthetic_choices(slides, layouts, slide_size)
            self._validate_layout_diversity(slides)
            
            # debug: count images in generated structure
            total_image_placeholders = 0
            for slide in result.get('structure', []):
                for ph in slide.get('placeholders', []):
                    if ph.get('type') == 'image':
                        total_image_placeholders += 1
            
            print(f"\nAI GENERATED STRUCTURE:")
            print(f"   Total slides: {len(result.get('structure', []))}")
            print(f"   Total image placeholders: {total_image_placeholders}")
            print(f"   Images provided to AI: {len(images)}")
            
            if len(images) > 0 and total_image_placeholders == 0:
                print(f"\nWARNING: {len(images)} images were provided but AI generated 0 image placeholders!")
                print(f"   This likely means the AI didn't find layouts with image support or chose not to use them.")
            
            return result
            
        except json.JSONDecodeError as e:
            raise ValueError(f"Failed to parse AI response as JSON: {str(e)}")
        except Exception as e:
            raise ValueError(f"AI preprocessing error with links: {str(e)}")
    
    def _format_chunks_for_prompt(self, content_chunks, images, image_id_to_index):
        """format content chunks with their linked images for AI prompt"""
        descriptions = []
        for i, chunk in enumerate(content_chunks):
            desc = f"\nChunk {i+1} (ID: {chunk['id']}):"
            desc += f"\nText: \"{chunk['text'][:200]}{'...' if len(chunk['text']) > 200 else ''}\""
            desc += f"\nFull length: {len(chunk['text'])} characters"
            
            if chunk['linked_image_ids']:
                desc += f"\nMUST include these images on same slide(s):"
                for img_id in chunk['linked_image_ids']:
                    img_index = image_id_to_index.get(img_id)
                    img = next((im for im in images if im['id'] == img_id), None)
                    if img:
                        tags_str = f" (tags: {', '.join(img['tags'])})" if img.get('tags') else ""
                        desc += f"\n  - Image ID: {img_id}, Index: {img_index}, File: {img['filename']}{tags_str}"
            else:
                desc += f"\nNo linked images"
            
            descriptions.append(desc)
        
        return "\n".join(descriptions)
    
    def _format_tag_guidelines(self, image_tag_map, images):
        """format image tag placement guidelines for AI prompt"""
        if not image_tag_map:
            return ""
        
        guidelines = "\nIMAGE TAG PLACEMENT GUIDELINES:"
        guidelines += "\nUse these preferences when selecting layouts and positions for images:"
        guidelines += "\n- 'logo', 'brand': prefer top-left or title slide positions, small size"
        guidelines += "\n- 'graph', 'chart', 'data': prefer center-right with text on left, needs space"
        guidelines += "\n- 'profile', 'headshot': prefer top-right or side positions"
        guidelines += "\n- 'icon': flexible positioning, can be small accents"
        guidelines += "\n- 'screenshot', 'diagram': prefer center position, needs full view space"
        
        guidelines += "\n\nTagged images in this deck:"
        for tag, img_ids in sorted(image_tag_map.items()):
            count = len(img_ids)
            guidelines += f"\n  - '{tag}': {count} image(s)"
        
        return guidelines
    
    def _calculate_placeholder_area(self, placeholder_props):
        """
        Calculate the physical area of a placeholder in square EMUs.
        EMUs (English Metric Units) are PowerPoint's internal unit.
        """
        try:
            # accept either {position:{...}} or a bare {left,top,width,height}
            pos = placeholder_props.get('position') or placeholder_props
            width = pos.get('width', 0)
            height = pos.get('height', 0)
            return width * height
        except:
            return 0
    
    def _calculate_layout_space_utilization(self, layout, slide_width=9144000, slide_height=6858000):
        """
        Calculate the space utilization for a layout.
        Returns:
        - content_area: total area covered by placeholders
        - slide_area: total slide area
        - content_percent: percentage of slide covered by content
        - negative_space_percent: percentage of slide that is empty
        """
        slide_area = slide_width * slide_height
        
        # calculate total content area (all placeholders)
        content_area = 0
        for placeholder in layout.get('placeholders', []):
            # layouts coming from DB may store geometry at placeholder.position
            ph_props = placeholder.get('properties') or placeholder
            content_area += self._calculate_placeholder_area(ph_props)
        
        # Also include static shapes if present (design elements)
        for shape in layout.get('shapes', []):
            if shape.get('is_design_image') or shape.get('type') in ['PICTURE', 'TEXT_BOX', 'AUTO_SHAPE']:
                shape_props = shape.get('properties') or shape
                content_area += self._calculate_placeholder_area(shape_props)
        
        content_percent = (content_area / slide_area * 100) if slide_area > 0 else 0
        negative_space_percent = 100 - content_percent
        
        return {
            'content_area': content_area,
            'slide_area': slide_area,
            'content_percent': content_percent,
            'negative_space_percent': negative_space_percent
        }
    
    def _estimate_text_capacity(self, placeholder_props):
        """
        Estimate text capacity for a placeholder based on *per-textbox geometry* and font size.
        This is intentionally conservative to prevent overflow.

        Returns:
        - chars, words, size (SMALL/MEDIUM/LARGE)
        - chars_per_line, lines_available (for granular per-box guidance)

        STRICT MODE: Raises ValueError if required properties are missing.
        """
        try:
            # allow simplified placeholder payloads (from DB) by normalizing props
            normalized = dict(placeholder_props or {})
            if 'position' not in normalized and isinstance(placeholder_props, dict) and 'position' in placeholder_props:
                normalized['position'] = placeholder_props.get('position')
            metrics = self._textbox_metrics_from_props(normalized)

            total_chars = max(0, metrics['chars_per_line'] * metrics['lines_available'])
            total_words = max(0, total_chars // 6)

            # clamp to reasonable values for prompt readability
            total_chars = max(20, min(total_chars, 5000))
            total_words = max(5, min(total_words, 1000))
            
            # Categorize by size
            if total_chars < 250:
                size_category = "SMALL"
            elif total_chars < 700:
                size_category = "MEDIUM"
            else:
                size_category = "LARGE"
            
            return {
                'chars': total_chars,
                'words': total_words,
                'size': size_category,
                'chars_per_line': metrics['chars_per_line'],
                'lines_available': metrics['lines_available'],
            }
        except Exception:
            # fallback for DB-saved layouts where font/style metadata isn't present
            # choose conservative capacities so prompts still work
            pos = (placeholder_props or {}).get('position') if isinstance(placeholder_props, dict) else None
            width = (pos or {}).get('width') if isinstance(pos, dict) else None
            height = (pos or {}).get('height') if isinstance(pos, dict) else None

            # if we have geometry, scale a rough estimate; otherwise default small
            if isinstance(width, (int, float)) and isinstance(height, (int, float)) and width > 0 and height > 0:
                area = width * height
                # tuned so typical body boxes land ~400-1200 chars
                approx_chars = int(max(120, min(2500, area / 20000000)))
            else:
                approx_chars = 300

            approx_words = max(20, approx_chars // 6)
            if approx_chars < 250:
                size_category = "SMALL"
            elif approx_chars < 700:
                size_category = "MEDIUM"
            else:
                size_category = "LARGE"

            return {
                'chars': approx_chars,
                'words': approx_words,
                'size': size_category,
                'chars_per_line': max(20, approx_chars // 10),
                'lines_available': 10,
            }

    def _textbox_metrics_from_props(self, placeholder_props):
        """
        Compute conservative textbox metrics (per-textbox, not per-slide).
        Uses:
        - position.width/height (EMUs)
        - text_frame_props margins (if present)
        - font size
        - paragraph line spacing (if present)
        """
        pos = placeholder_props.get('position') or placeholder_props
        if not pos:
            raise ValueError("Missing position data for placeholder")

        width = pos.get('width')
        height = pos.get('height')
        if width is None or height is None:
            raise ValueError(f"Missing width or height in position data: width={width}, height={height}")

        font_props = placeholder_props.get('font_props')
        if not font_props:
            raise ValueError("Missing font_props for text placeholder")

        font_size = font_props.get('size')
        if not font_size:
            raise ValueError(f"Missing font size in font_props: {font_props}")

        # margins (EMU) if available
        tf = placeholder_props.get('text_frame_props') or {}
        margin_left = tf.get('margin_left') or 91440   # 0.1"
        margin_right = tf.get('margin_right') or 91440
        margin_top = tf.get('margin_top') or 45720     # 0.05"
        margin_bottom = tf.get('margin_bottom') or 45720

        usable_width_emu = max(0, width - margin_left - margin_right)
        usable_height_emu = max(0, height - margin_top - margin_bottom)

        usable_width_pt = (usable_width_emu / 914400.0) * 72.0
        usable_height_pt = (usable_height_emu / 914400.0) * 72.0

        # paragraph spacing
        para = placeholder_props.get('paragraph_props') or {}
        raw_line_spacing = para.get('line_spacing')
        try:
            line_spacing = float(raw_line_spacing) if raw_line_spacing else 1.3
        except Exception:
            line_spacing = 1.3

        # ULTRA-CONSERVATIVE safety factors to prevent overflow:
        # Even with post-processing enforcement, we want AI to aim low to minimize truncation.
        # - Treat average char width as 1.2em (wider than actual to be safe)
        # - Treat line height as 1.6em (taller than actual to be safe)
        # this intentionally underestimates capacity so AI creates more slides instead of overflow.
        char_width_pt = float(font_size) * 1.2
        line_height_pt = max(float(font_size) * max(line_spacing, 1.3) * 1.3, float(font_size) * 1.6)

        chars_per_line = max(5, int(usable_width_pt / char_width_pt)) if char_width_pt > 0 else 5
        lines_available = max(1, int(usable_height_pt / line_height_pt)) if line_height_pt > 0 else 1

        return {
            'font_size': float(font_size),
            'usable_width_pt': usable_width_pt,
            'usable_height_pt': usable_height_pt,
            'chars_per_line': chars_per_line,
            'lines_available': lines_available,
        }

    def _wrap_text_into_lines(self, text, chars_per_line):
        """Wrap text into visual lines for a given chars_per_line."""
        import textwrap

        if text is None:
            return []

        s = str(text).strip()
        if not s:
            return []

        lines_out = []
        for raw in s.splitlines():
            line = raw.rstrip()
            if not line.strip():
                continue

            stripped = line.lstrip()
            is_bullet = stripped.startswith(("- ", "• ", "* "))
            if is_bullet:
                bullet_prefix = stripped[:2]
                bullet_body = stripped[2:].strip()
                wrapped = textwrap.wrap(
                    bullet_body,
                    width=max(8, chars_per_line - 2),
                    break_long_words=False,
                    break_on_hyphens=False,
                )
                if not wrapped:
                    lines_out.append(bullet_prefix.strip())
                else:
                    lines_out.append(f"{bullet_prefix}{wrapped[0]}")
                    for cont in wrapped[1:]:
                        lines_out.append(f"  {cont}")
            else:
                wrapped = textwrap.wrap(
                    stripped,
                    width=max(8, chars_per_line),
                    break_long_words=False,
                    break_on_hyphens=False,
                )
                lines_out.extend(wrapped if wrapped else [stripped])

        return lines_out

    def _split_text_to_fit_box(self, text, placeholder_props):
        """Split text into (fits, remainder) based on per-box line constraints."""
        metrics = self._textbox_metrics_from_props(placeholder_props)
        lines = self._wrap_text_into_lines(text, metrics['chars_per_line'])
        if len(lines) <= metrics['lines_available']:
            return str(text).strip(), ""

        fit_lines = lines[: metrics['lines_available']]
        rem_lines = lines[metrics['lines_available'] :]
        return "\n".join(fit_lines).strip(), "\n".join(rem_lines).strip()

    def _pick_best_text_continuation_layout(self, layouts, slide_size=None):
        """
        Pick a robust text-only layout for overflow continuation slides:
        - 0 image placeholders
        - at least one CONTENT (non-title) placeholder
        - prefer <= 70% negative space
        - maximize total content capacity
        """
        slide_width = 9144000
        slide_height = 6858000
        if slide_size:
            slide_width = slide_size.get('width', slide_width)
            slide_height = slide_size.get('height', slide_height)

        best = None
        best_score = -1

        for layout in layouts:
            text_phs = [p for p in layout.get('placeholders', []) if p.get('type') == 'text']
            img_phs = [p for p in layout.get('placeholders', []) if p.get('type') == 'image']
            if img_phs or not text_phs:
                continue

            space_util = self._calculate_layout_space_utilization(layout, slide_width, slide_height)
            negative_space = space_util['negative_space_percent']
            if negative_space > 70:
                continue

            # capacity of CONTENT placeholders only
            content_cap = 0
            has_content = False
            for ph in text_phs:
                props = ph.get('properties', {})
                cap = self._estimate_text_capacity(props)
                font_size = (props.get('font_props') or {}).get('size', 18)
                is_title = font_size > 32 or (cap['chars'] < 150 and font_size > 24)
                if not is_title:
                    has_content = True
                    content_cap += cap['chars']

            if not has_content:
                continue

            score = content_cap - int(max(0, negative_space - 50) * 50)
            if score > best_score:
                best_score = score
                best = layout

        return best

    def _enforce_zero_overflow_by_splitting(self, slides, layouts, slide_size=None):
        """
        Zero-overflow enforcement by SPLITTING content across more slides (no information loss).
        Title placeholders are treated as headers only; any overflow moves into content boxes or new slides.
        """
        layout_map = {layout['name']: layout for layout in layouts}
        continuation_layout = self._pick_best_text_continuation_layout(layouts, slide_size)
        if not continuation_layout:
            return slides

        def short_title(s):
            s = " ".join(str(s).strip().split())
            if len(s) <= 60:
                return s
            words = s.split()
            head = " ".join(words[:8])
            return head[:60].rstrip()

        def is_title_box(layout_ph):
            props = layout_ph.get('properties', {})
            cap = self._estimate_text_capacity(props)
            font_size = (props.get('font_props') or {}).get('size', 18)
            return font_size > 32 or (cap['chars'] < 150 and font_size > 24)

        print("\n" + "="*80)
        print("ZERO-OVERFLOW ENFORCEMENT (SPLIT, DON'T TRUNCATE):")
        print("="*80)

        out = []
        inserted = 0

        for slide in slides:
            out.append(slide)

            layout = layout_map.get(slide.get('layout_name', ''))
            if not layout:
                continue

            # classify placeholders in current layout
            layout_text_phs = [p for p in layout.get('placeholders', []) if p.get('type') == 'text']
            if not layout_text_phs:
                continue

            title_lp = next((lp for lp in layout_text_phs if is_title_box(lp)), None)
            content_lps = [lp for lp in layout_text_phs if not is_title_box(lp)]

            slide_text_ph = {p.get('idx'): p for p in slide.get('placeholders', []) if p.get('type') == 'text'}

            carry = []

            # title enforcement: keep short headline, move excess into carry
            if title_lp:
                t_idx = title_lp.get('idx')
                t_ph = slide_text_ph.get(t_idx)
                if t_ph:
                    original = str(t_ph.get('content', '')).strip()
                    st = short_title(original)
                    if original and st != original:
                        extra = original[len(st):].strip()
                        t_ph['content'] = st
                        if extra:
                            carry.append(extra)

                    # also enforce line-fit for title box
                    try:
                        fit, rem = self._split_text_to_fit_box(t_ph.get('content', ''), title_lp.get('properties', {}))
                        t_ph['content'] = fit
                        if rem:
                            carry.append(rem)
                    except Exception:
                        pass

            # split overflowing content boxes into carry
            for lp in content_lps:
                idx = lp.get('idx')
                sp = slide_text_ph.get(idx)
                if not sp:
                    continue
                txt = str(sp.get('content', '')).strip()
                if not txt:
                    continue
                try:
                    fit, rem = self._split_text_to_fit_box(txt, lp.get('properties', {}))
                    sp['content'] = fit
                    if rem:
                        carry.append(rem)
                except Exception:
                    continue

            remaining = "\n".join([c for c in carry if c and str(c).strip()]).strip()
            if not remaining:
                continue

            # build continuation title
            base_title = ""
            if title_lp:
                t_idx = title_lp.get('idx')
                base_title = str((slide_text_ph.get(t_idx) or {}).get('content', '')).strip()
            cont_title = short_title((base_title + " (cont.)").strip() if base_title else "Continued")

            safety_loops = 0
            while remaining and safety_loops < 12:
                safety_loops += 1
                inserted += 1

                cont_slide = {
                    'slide_number': None,
                    'slide_type': slide.get('slide_type', 'content'),
                    'layout_name': continuation_layout['name'],
                    'placeholders': [],
                    'notes': slide.get('notes', ''),
                }

                cont_text_phs = [p for p in continuation_layout.get('placeholders', []) if p.get('type') == 'text']
                cont_title_lp = next((lp for lp in cont_text_phs if is_title_box(lp)), None)
                cont_content_lps = [lp for lp in cont_text_phs if not is_title_box(lp)]

                if cont_title_lp:
                    title_ph = {'idx': cont_title_lp['idx'], 'type': 'text', 'content': cont_title}
                    # Add font size for enforcement
                    font_size = self._get_placeholder_font_size(cont_title_lp)
                    if font_size:
                        title_ph['font_size'] = font_size
                    cont_slide['placeholders'].append(title_ph)

                # initialize all content boxes empty
                for lp in cont_content_lps:
                    content_ph = {'idx': lp['idx'], 'type': 'text', 'content': ''}
                    # add font size for enforcement
                    font_size = self._get_placeholder_font_size(lp)
                    if font_size:
                        content_ph['font_size'] = font_size
                    cont_slide['placeholders'].append(content_ph)

                for lp in cont_content_lps:
                    if not remaining:
                        break
                    fit, rem = self._split_text_to_fit_box(remaining, lp.get('properties', {}))
                    # structure overflow content as clean bullets (no markers)
                    fit_structured = self._structure_as_bullets(fit)
                    for ph in cont_slide['placeholders']:
                        if ph['type'] == 'text' and ph['idx'] == lp['idx']:
                            ph['content'] = fit_structured
                            break
                    remaining = rem.strip()

                out.append(cont_slide)

        # renumber slides sequentially
        for i, s in enumerate(out):
            s['slide_number'] = i + 1

        print(f"✅ Inserted {inserted} continuation slide(s) to eliminate overflow")
        print("="*80 + "\n")
        return out
    
    def _structure_as_bullets(self, text):
        """
        Convert text into bullet format WITHOUT bullet markers.
        Format: "Point one\nPoint two\nPoint three"
        PowerPoint's auto-bullet feature will add the markers.
        """
        if not text or not text.strip():
            return text
        
        # Split on existing newlines or sentences
        points = self._split_into_points(text)
        
        # Join with newlines (no • or - markers)
        return '\n'.join(points)
    
    def _split_into_points(self, text):
        """
        Intelligently split text into bullet-sized points.
        Each point should be 3-10 words.
        """
        if not text:
            return []
        
        # remove existing bullet markers if any
        text = text.replace('• ', '').replace('- ', '').replace('* ', '')
        
        # split on newlines first
        lines = text.split('\n')
        
        points = []
        for line in lines:
            line = line.strip()
            if not line:
                continue
            
            # If line is short enough (<= 10 words), keep as is
            words = line.split()
            if len(words) <= 10:
                points.append(line)
            else:
                # Split long lines at natural breaks
                sub_points = self._split_long_line(line)
                points.extend(sub_points)
        
        return points
    
    def _split_long_line(self, line):
        """
        Split a long line (>10 words) into multiple bullet points.
        Looks for natural break points: commas, semicolons, conjunctions.
        """
        points = []
        
        # First try splitting on semicolons
        if ';' in line:
            parts = line.split(';')
            for part in parts:
                part = part.strip()
                if part:
                    words = part.split()
                    if len(words) <= 10:
                        points.append(part)
                    else:
                        # Still too long, try commas
                        points.extend(self._split_by_commas(part))
            return points
        
        # Try splitting on commas
        if ',' in line:
            return self._split_by_commas(line)
        
        # Try splitting on conjunctions (and, or, but, while, with)
        conjunctions = [' and ', ' or ', ' but ', ' while ', ' with ']
        for conj in conjunctions:
            if conj in line.lower():
                parts = line.split(conj, 1)  # Split only on first occurrence
                if len(parts) == 2:
                    part1, part2 = parts
                    part1 = part1.strip()
                    part2 = part2.strip()
                    
                    if part1:
                        points.append(part1)
                    if part2 and len(part2.split()) > 10:
                        # Part 2 still too long, recursively split
                        points.extend(self._split_long_line(part2))
                    elif part2:
                        points.append(part2)
                    
                    return points
        
        # No good break points found - split at word boundary near middle
        words = line.split()
        mid = len(words) // 2
        part1 = ' '.join(words[:mid])
        part2 = ' '.join(words[mid:])
        if part1:
            points.append(part1)
        if part2:
            points.append(part2)
        
        return points
    
    def _split_by_commas(self, text):
        """Split text by commas, combining if needed to meet min length."""
        parts = text.split(',')
        points = []
        current = ""
        
        for part in parts:
            part = part.strip()
            if not part:
                continue
            
            words_in_part = len(part.split())
            words_in_current = len(current.split()) if current else 0
            
            # If adding this part would still be under 10 words, accumulate
            if words_in_current > 0 and words_in_current + words_in_part <= 10:
                current += ", " + part
            else:
                # Save current if exists
                if current:
                    points.append(current)
                # Start new point
                if words_in_part <= 10:
                    current = part
                else:
                    # This part alone is too long, add it anyway
                    points.append(part)
                    current = ""
        
        # Add any remaining
        if current:
            points.append(current)
        
        return points if points else [text]
    
    def _format_layouts_with_categories(self, layouts, layouts_by_category, display_names=None, slide_size=None):
        """format layouts RANKED by aesthetic suitability for AI selection"""
        
        if display_names is None:
            display_names = {layout['name']: layout['name'] for layout in layouts}
        
        slide_width = 9144000
        slide_height = 6858000
        if slide_size:
            slide_width = slide_size.get('width', slide_width)
            slide_height = slide_size.get('height', slide_height)
        
        # calculate metrics for all layouts
        layouts_with_metrics = []
        for layout in layouts:
            space_util = self._calculate_layout_space_utilization(layout, slide_width, slide_height)
            text_phs = [p for p in layout['placeholders'] if p['type'] == 'text']
            img_phs = [p for p in layout['placeholders'] if p['type'] == 'image']
            total_capacity = sum(self._estimate_text_capacity(ph.get('properties', {}))['chars'] for ph in text_phs)
            
            layouts_with_metrics.append({
                'layout': layout,
                'negative_space': space_util['negative_space_percent'],
                'content_percent': space_util['content_percent'],
                'total_capacity': total_capacity,
                'text_count': len(text_phs),
                'image_count': len(img_phs),
                'text_phs': text_phs,
                'img_phs': img_phs
            })
        
        # separate into RECOMMENDED vs AVOID
        recommended = [lm for lm in layouts_with_metrics if lm['negative_space'] <= 50]
        avoid = [lm for lm in layouts_with_metrics if lm['negative_space'] > 50]
        
        # group recommended by category
        recommended_by_category = {}
        for lm in recommended:
            category = lm['layout'].get('category', 'uncategorized')
            if category not in recommended_by_category:
                recommended_by_category[category] = []
            recommended_by_category[category].append(lm)
        
        # sort each category group by negative space
        for category in recommended_by_category:
            recommended_by_category[category].sort(key=lambda x: x['negative_space'])
        
        # sort avoid by negative space
        avoid.sort(key=lambda x: x['negative_space'])
        
        output = []
        
        output.append("\n" + "="*80)
        output.append("RECOMMENDED LAYOUTS (Good space utilization, <50% negative space)")
        output.append("="*80)
        output.append(f"USE THESE {len(recommended)} LAYOUTS - They have good aesthetic balance:\n")
        
        # display grouped by category
        for category in sorted(recommended_by_category.keys()):
            layouts_in_category = recommended_by_category[category]
            output.append(f"📁 {category.upper()} ({len(layouts_in_category)} layouts)")
            output.append("-" * 80)
            
            for lm in layouts_in_category:
                layout = lm['layout']
                display_name = display_names[layout['name']]
                output.append(f"\"{display_name}\"")
                output.append(f"   Space: {lm['content_percent']:.0f}% content | {lm['negative_space']:.0f}% empty (GOOD)")
                output.append(f"   Capacity: ~{lm['total_capacity']} chars total")
                output.append(f"   Structure: {lm['text_count']}T + {lm['image_count']}I")
                
                if lm['text_phs']:
                    output.append(f"   Placeholders:")
                    for ph in lm['text_phs']:
                        cap = self._estimate_text_capacity(ph.get('properties', {}))
                        font_size = ph.get('properties', {}).get('font_props', {}).get('size', 18)
                        
                        # determine purpose
                        if font_size > 32 or (cap['chars'] < 150 and font_size > 24):
                            purpose = "TITLE"
                            output.append(f"     idx {ph['idx']}: {purpose} - 20-60 chars only (font: {font_size}pt)")
                        else:
                            purpose = "CONTENT"
                            output.append(f"     idx {ph['idx']}: {purpose} - ~{cap['chars']} chars max (font: {font_size}pt)")
                    
                    for ph in lm['img_phs']:
                        output.append(f"     idx {ph['idx']}: IMAGE")
                
                output.append("")
            
            output.append("")
        
        if avoid:
            output.append("\n" + "="*80)
            output.append(f"AVOID THESE {len(avoid)} LAYOUTS (>50% negative space = TOO SPARSE)")
            output.append("="*80)
            output.append("DO NOT USE unless it's a title slide with very minimal text (<80 chars):\n")
            
            # group avoid by category
            avoid_by_category = {}
            for lm in avoid:
                category = lm['layout'].get('category', 'uncategorized')
                if category not in avoid_by_category:
                    avoid_by_category[category] = []
                avoid_by_category[category].append(lm)
            
            for category in sorted(avoid_by_category.keys()):
                layouts_in_category = avoid_by_category[category]
                output.append(f"📁 {category.upper()} ({len(layouts_in_category)} layouts - TOO SPARSE)")
                
                for lm in layouts_in_category:
                    layout = lm['layout']
                    display_name = display_names[layout['name']]
                    output.append(f"\"{display_name}\" - {lm['negative_space']:.0f}% EMPTY!")
                    output.append(f"   Why avoid: Only {lm['content_percent']:.0f}% of slide has content")
                    output.append(f"   Capacity: ~{lm['total_capacity']} chars")
                    output.append("")
                
                output.append("")
        
        output.append("\n" + "="*80)
        output.append("VALID LAYOUT NAMES (copy exactly):")
        output.append("="*80)
        all_layout_names = [f'"{display_names[layout["name"]]}"' for layout in layouts]
        output.append(", ".join(all_layout_names))
        output.append("="*80)
        
        return "\n".join(output)

    def _format_images_with_vision(self, images):
        """format images with vision analysis for AI prompt"""
        
        output = []
        for i, img in enumerate(images):
            output.append(f"\nImage {i}: {img['filename']}")
            
            if img.get('visionDescription'):
                output.append(f"  vision: {img['visionDescription']}")
            
            if img.get('visionLabels'):
                output.append(f"  labels: {', '.join(img['visionLabels'])}")
            
            if img.get('tags'):
                output.append(f"  user tags: {', '.join(img['tags'])}")
            
            if img.get('recommendedLayoutStyle'):
                output.append(f"  suggested style: {img['recommendedLayoutStyle']}")
        
        return "\n".join(output) if output else "no images provided"
    
    def regenerate_single_slide(self, slide, images, layouts, context_slides=None):
        """
        regenerate a single slide with access to all layouts (including special).
        optionally considers surrounding slides for context.
        """
        layout_descriptions = self._format_layouts_for_prompt(layouts)
        
        image_id_to_index = {img['id']: i for i, img in enumerate(images)} if images else {}
        image_tag_map = {}
        for img in images:
            for tag in img.get('tags', []):
                image_tag_map.setdefault(tag, []).append(img['id'])
        
        tag_guidelines = self._format_tag_guidelines(image_tag_map, images) if images else ""
        
        current_text = []
        current_images = []
        for ph in slide.get('placeholders', []):
            if ph.get('type') == 'text' and ph.get('content'):
                current_text.append(ph['content'])
            elif ph.get('type') == 'image' and 'image_id' in ph:
                img = next((im for im in images if im['id'] == ph['image_id']), None)
                if img:
                    current_images.append(img)
        
        system_prompt = f"""You are refining a single slide in a presentation.

You have access to ALL available layouts, including specialized complex layouts.
Consider the slide's content and choose the most appropriate layout.

{layout_descriptions}

{tag_guidelines}

CRITICAL CONSTRAINTS:
1. You can ONLY use the exact 'layout_name' values from the "VALID LAYOUT NAMES" list above.
2. DO NOT invent layout names - use the EXACT names provided.
3. IGNORE misleading layout names - check the "STRUCTURE" line for actual placeholder counts!
4. You MUST use ONLY the VALID idx values listed for the chosen layout.
5. DO NOT invent placeholder indices - check the layout's "VALID idx: [...]"
6. For the slide, you MUST populate EVERY placeholder index (idx) defined in that layout.
7. Match types exactly: TEXT placeholders get text, IMAGE placeholders get an image_id.
8. Maintain the core message and content from the original slide.

Return a JSON object with:
{{
  "layout_name": "EXACT layout name from the list",
  "placeholders": [
    {{
      "idx": number,
      "type": "text|image",
      "content": "string (for text)",
      "image_id": "string (for image)",
      "image_index": number (for image)
    }}
  ],
  "rationale": "why this layout was chosen"
}}"""

        text_content = "\n\n".join(current_text) if current_text else "No text content"
        image_info = ""
        if current_images:
            image_info = "\n\nImages in this slide:"
            for img in current_images:
                tags_str = f" (tags: {', '.join(img['tags'])})" if img.get('tags') else ""
                image_info += f"\n- {img['filename']}{tags_str}"
        
        text_prompt = f"""Current slide content:
{text_content}
{image_info}

Current layout: {slide.get('layout_name', 'unknown')}

Optimize this slide by choosing the best layout. Return ONLY valid JSON."""

        try:
            response = self._chat(
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": text_prompt}
                ],
                response_format_json=True,
            )
            
            raw_content = response.choices[0].message.content
            print("\n" + "="*80)
            print(f"REGENERATED SLIDE:")
            print("="*80)
            print(raw_content)
            print("="*80 + "\n")
            
            result = json.loads(raw_content)
            return result
            
        except json.JSONDecodeError as e:
            raise ValueError(f"Failed to parse AI response as JSON: {str(e)}")
        except Exception as e:
            raise ValueError(f"AI slide regeneration error: {str(e)}")
    
    def categorize_layouts(self, layouts, predefined_categories=None):
        """
        categorize layouts by content capacity, type, and PURPOSE.
        distinguishes between title/header placeholders vs content/data placeholders.
        """
        
        for layout in layouts:
            # count placeholders by type
            text_placeholders = [p for p in layout['placeholders'] if p['type'] == 'text']
            image_placeholders = [p for p in layout['placeholders'] if p['type'] == 'image']
            
            num_text = len(text_placeholders)
            num_images = len(image_placeholders)
            
            # analyze text placeholders by PURPOSE and capacity
            title_placeholders = []
            content_placeholders = []
            
            for ph in text_placeholders:
                # extract font properties from the correct path
                props = ph.get('properties', {})
                font_props = props.get('font_props', {})
                font_size = font_props.get('size', 18)
                
                # calculate capacity
                capacity_info = self._estimate_text_capacity(props)
                capacity = capacity_info['chars']
                
                # store capacity for easy access
                ph['estimated_capacity'] = capacity
                ph['font_size'] = font_size
                
                # determine PURPOSE based on font size and capacity
                if font_size > 32 or (capacity < 150 and font_size > 24):
                    # large font or small capacity with large font = title/header
                    purpose = 'title'
                    title_placeholders.append(ph)
                else:
                    # regular font = content/data
                    purpose = 'content'
                    content_placeholders.append(ph)
                
                # store purpose in placeholder for later reference
                ph['purpose'] = purpose
                
                # categorize size for display
                if capacity > 800 or font_size > 36:
                    ph['size_category'] = 'large'
                elif capacity > 400 or font_size > 24:
                    ph['size_category'] = 'medium'
                else:
                    ph['size_category'] = 'small'
            
            # build detailed category description
            category_parts = []
            
            # describe titles
            if title_placeholders:
                if len(title_placeholders) == 1:
                    category_parts.append("1 title")
                else:
                    category_parts.append(f"{len(title_placeholders)} titles")
            
            # describe content placeholders with size
            if content_placeholders:
                size_counts = {}
                for ph in content_placeholders:
                    size = ph.get('size_category', 'medium')
                    size_counts[size] = size_counts.get(size, 0) + 1
                
                size_desc = []
                for size in ['large', 'medium', 'small']:
                    if size in size_counts:
                        count = size_counts[size]
                        size_desc.append(f"{count} {size}")
                
                if size_desc:
                    category_parts.append(f"{len(content_placeholders)} content ({', '.join(size_desc)})")
                else:
                    category_parts.append(f"{len(content_placeholders)} content")
            
            # describe image placeholders
            if num_images > 0:
                category_parts.append(f"{num_images} image{'s' if num_images > 1 else ''}")
            
            # combine into category
            if category_parts:
                category = " + ".join(category_parts)
            else:
                category = "blank"
            
            # calculate capacities
            title_capacity = sum(p.get('estimated_capacity', 0) for p in title_placeholders)
            content_capacity = sum(p.get('estimated_capacity', 0) for p in content_placeholders)
            total_capacity = title_capacity + content_capacity
            
            # store category and metadata
            layout['category'] = category
            layout['category_confidence'] = 1.0
            layout['total_text_capacity'] = total_capacity
            layout['title_capacity'] = title_capacity
            layout['content_capacity'] = content_capacity
            layout['num_title_placeholders'] = len(title_placeholders)
            layout['num_content_placeholders'] = len(content_placeholders)
            layout['num_image_placeholders'] = num_images
            
            # generate human-readable rationale
            rationale_parts = []
            if title_placeholders:
                rationale_parts.append(f"{len(title_placeholders)} title (≤150 chars each)")
            if content_placeholders:
                rationale_parts.append(f"{len(content_placeholders)} content (~{content_capacity} chars)")
            if num_images > 0:
                rationale_parts.append(f"{num_images} image{'s' if num_images > 1 else ''}")
            
            layout['category_rationale'] = ", ".join(rationale_parts)
        
        print(f"\n✓ categorized {len(layouts)} layouts by capacity")
        for layout in layouts:
            print(f"  {layout['name']}: {layout['category']}")
        
        return {
            'layouts': layouts,
            'new_categories': []
        }
    
    def analyze_image_content(self, image_data_base64):
        """
        use vision AI to understand image content for intelligent layout matching.
        returns description and detected labels.
        """
        
        try:
            response = self._chat(
                messages=[
                    {
                        "role": "system",
                        "content": "analyze images for presentation layout matching. return ONLY valid JSON."
                    },
                    {
                        "role": "user",
                        "content": [
                            {
                                "type": "text",
                                "text": """analyze this image:
1. description (1-2 sentences)
2. type: graph, chart, photo, diagram, screenshot, icon, logo, illustration
3. characteristics: has_text, has_data_points, is_portrait, is_landscape, is_complex
4. recommended_layout_style: large_image, side_by_side, grid, corner_accent

return JSON only:
{
  "description": "...",
  "type": "...",
  "characteristics": [...],
  "recommended_layout_style": "...",
  "confidence": 0.9
}"""
                            },
                            {
                                "type": "image_url",
                                "image_url": {
                                    "url": f"data:image/jpeg;base64,{image_data_base64}"
                                }
                            }
                        ]
                    }
                ],
                model=Config.AI_VISION_MODEL,
                max_tokens=300,
                response_format_json=True,
            )
            
            content = response.choices[0].message.content
            if not content or not content.strip():
                raise ValueError("empty response from AI")
            
            result = json.loads(content)
            return {
                'visionDescription': result.get('description', ''),
                'visionLabels': [result.get('type')] + result.get('characteristics', []),
                'recommendedLayoutStyle': result.get('recommended_layout_style'),
                'confidence': result.get('confidence', 0.5)
            }
            
        except Exception as e:
            print(f"image analysis failed: {e}")
            return {
                'visionDescription': 'analysis unavailable',
                'visionLabels': [],
                'recommendedLayoutStyle': None,
                'confidence': 0
            }
    
    def organize_content_into_slides(self, content_text, image_filenames, layouts, image_data_list=None, slides_specification=None):
        layout_descriptions = self._format_layouts_for_prompt(layouts)
        has_images = image_data_list and len(image_data_list) > 0
        has_spec = slides_specification and len(slides_specification) > 0
        
        system_prompt = """You are a presentation designer expert. Your task is to organize content into a well-structured slide deck, working with varying levels of user specification.

Given:
1. Raw text content (may be topic, notes, or pre-written content)
2. Images (if provided, you can see their content)
3. Available slide layouts - RIGID templates where ONLY content changes
4. User slide specifications (if provided) - varying levels of detail per slide

CRITICAL CONSTRAINTS - THESE ARE ABSOLUTE:
1. You can ONLY use the exact layout names from the "VALID LAYOUT NAMES" list
2. DO NOT invent generic names like "TITLE", "CONTENT" - use the EXACT names provided
3. IGNORE misleading layout names - check the "STRUCTURE" line for actual placeholders!
4. For each slide, you MUST ONLY use the VALID idx values listed for that specific layout
5. DO NOT invent placeholder indices - each layout shows its "VALID idx: [...]"
6. You MUST match placeholder types EXACTLY:
   - TEXT placeholders accept ONLY text
   - IMAGE placeholders accept ONLY images
   - NEVER put text in image placeholders or images in text placeholders
7. Each layout is a RIGID template - you cannot modify positions, sizes, or styling
8. **EVERY placeholder MUST be filled** - you cannot leave any placeholder empty
6. **MANDATORY IMAGE USAGE**: If images are provided, you MUST use ALL of them:
   - Image indices: 0 to N-1 (where N = number of images)
   - Each image_index must appear EXACTLY ONCE
   - Choose/use layouts that have image placeholders to accommodate all images
7. **USER SPECIFICATIONS**: If user provides slide specifications, you must respect them:
   - If layout_name is specified, you MUST use that exact layout
   - If placeholder content is specified, you MUST use that exact content
   - If placeholders are missing, you MUST generate content to fill them
   - If layout is not specified, you MUST choose an appropriate layout
   - Adapt your content generation to fit the specified constraints
8. **TEXT CAPACITY LIMITS**: Each text placeholder shows capacity (chars/words):
   - You MUST stay within the stated character/word limits
   - Count ALL characters including spaces and punctuation
   - If content exceeds capacity, condense it or use a different layout
   - NEVER overflow text - it will break the presentation

Your workflow:
1. **Analyze user specifications** (if provided):
   - Check which slides have layouts specified vs need layout selection
   - Check which placeholders have content vs need content generation
   - Identify which images are already assigned vs need assignment
2. **Analyze content**:
   - IF topic/command: generate comprehensive content
   - IF pre-written: use verbatim and organize appropriately
   - Look at images and understand what each shows
3. **Plan slide structure**:
   - For specified slides: respect the layout and fill missing content
   - For unspecified slides: choose appropriate layouts
   - Ensure all images will be used across all slides
   - Plan coherent narrative flow
4. **For EACH slide**:
   - IF layout specified: use that exact layout and fill ALL its placeholders
   - IF layout not specified: choose layout that fits your content plan
   - IF placeholder content specified: use it exactly as provided
   - IF placeholder content missing: generate appropriate content
   - Ensure EVERY placeholder is filled (text or image)
   - Track which image_index values have been used
5. **Final validation**:
   - Every slide uses a valid layout
   - Every placeholder in every slide is filled
   - All image indices (0 to N-1) used exactly once
   - Logical narrative flow across slides

VALIDATION CHECKLIST (verify before returning):
- ✓ Every layout_name exists in the provided layouts list
- ✓ Every placeholder idx exists in its chosen layout  
- ✓ Every placeholder in every slide is filled (no empty placeholders)
- ✓ Text content only goes to text placeholders
- ✓ Image content only goes to image placeholders
- ✓ If images provided: EVERY image index (0 to N-1) used exactly once
- ✓ Using DIFFERENT layouts for variety (not repeating same layout excessively)
- ✓ All content is clear, concise, and relevant to the topic

Return ONLY a JSON object with a "slides" array. Each slide in the array must have:
- layout_name (string): which layout to use
- placeholders (array): list of placeholder assignments, each with:
  - idx (number): the placeholder index
  - type (string): either "text" or "image"
  - content (string): the text content (only for text type)
  - image_index (number): the image array index (only for image type)

Example format:
{
  "slides": [
    {
      "layout_name": "Title Slide",
      "placeholders": [
        {"idx": 0, "type": "text", "content": "My Title"},
        {"idx": 1, "type": "text", "content": "Subtitle text"}
      ]
    },
    {
      "layout_name": "Content with Picture",
      "placeholders": [
        {"idx": 0, "type": "text", "content": "About Our Product"},
        {"idx": 1, "type": "image", "image_index": 0}
      ]
    }
  ]
}
"""

        num_images = len(image_data_list) if image_data_list else 0
        
        spec_description = ""
        if has_spec:
            spec_description = f"\n\nUser Slide Specifications:\n{json.dumps(slides_specification, indent=2)}\n\nIMPORTANT: Respect user specifications where provided. Fill in missing layouts and content where not specified."
        
        text_prompt = f"""Available Layouts:
{layout_descriptions}

Content/Topic:
{content_text if content_text else "No base content - generate based on specifications"}

Number of Images: {num_images}
{f"You MUST use all {num_images} images (indices 0-{num_images-1}) in your slide deck." if num_images > 0 else "No images provided."}{spec_description}

Generate a complete slide deck. Return ONLY valid JSON (no markdown, no explanation)."""

        try:
            if has_images:
                user_message_content = [
                    {"type": "text", "text": text_prompt}
                ]
                
                for i, img_data in enumerate(image_data_list):
                    if ',' in img_data:
                        img_data = img_data.split(',')[1]
                    
                    user_message_content.append({
                        "type": "image_url",
                        "image_url": {
                            "url": f"data:image/jpeg;base64,{img_data}",
                            "detail": "high"
                        }
                    })
                
                messages = [
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_message_content}
                ]
            else:
                messages = [
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": text_prompt}
                ]
            
            response = self._chat(
                messages=messages,
                response_format_json=True,
            )
            
            raw_content = response.choices[0].message.content
            print("\n" + "="*80)
            print("AI RESPONSE:")
            print("="*80)
            print(raw_content)
            print("="*80 + "\n")
            
            result = json.loads(raw_content)
            
            if 'slides' not in result:
                if isinstance(result, list):
                    result = {'slides': result}
                elif isinstance(result, dict):
                    for key in ['presentation', 'deck', 'slide_deck', 'content']:
                        if key in result and isinstance(result[key], list):
                            result = {'slides': result[key]}
                            break
                    else:
                        result = {'slides': [result]}
            
            slides = result['slides']
            
            if not isinstance(slides, list):
                raise ValueError(f"Expected slides to be a list, got {type(slides)}")
            
            for i, slide in enumerate(slides):
                if not isinstance(slide, dict):
                    raise ValueError(f"Expected slide {i} to be a dict, got {type(slide)}: {slide}")
                
                if 'layout_name' not in slide:
                    raise ValueError(f"Slide {i} missing 'layout_name'")
                
                layout_name = slide['layout_name']
                
                # strip [TEXT-ONLY: ...] suffix if present (we added this for AI clarity)
                if '[TEXT-ONLY:' in layout_name:
                    original_name = layout_name.split(' [TEXT-ONLY:')[0]
                    print(f"   stripping suffix: {layout_name} → {original_name}")
                    layout_name = original_name
                
                matching_layout = None
                for layout in layouts:
                    if layout['name'] == layout_name:
                        matching_layout = layout
                        break
                
                if not matching_layout:
                    available_names = [l['name'] for l in layouts]
                    print(f"\nERROR: AI generated invalid layout name")
                    print(f"   Requested: '{layout_name}'")
                    print(f"   Available layouts:")
                    for name in available_names:
                        print(f"     - \"{name}\"")
                    raise ValueError(f"Slide {i}: Layout '{layout_name}' not found. Available: {available_names}")
                
                if 'placeholders' not in slide:
                    slide['placeholders'] = []
                
                placeholders = slide['placeholders']
                if not isinstance(placeholders, list):
                    raise ValueError(f"Slide {i} placeholders must be a list, got {type(placeholders)}")
                
                available_phs = {ph['idx']: ph for ph in matching_layout['placeholders']}
                
                for j, ph in enumerate(placeholders):
                    if not isinstance(ph, dict):
                        raise ValueError(f"Slide {i} placeholder {j} must be a dict, got {type(ph)}: {ph}")
                    
                    if 'idx' not in ph:
                        raise ValueError(f"Slide {i} placeholder {j} missing 'idx'")
                    
                    if 'type' not in ph:
                        raise ValueError(f"Slide {i} placeholder {j} missing 'type'")
                    
                    ph_idx = ph['idx']
                    ph_type = ph['type']
                    
                    if ph_idx not in available_phs:
                        available_idxs = list(available_phs.keys())
                        raise ValueError(
                            f"slide {i} placeholder {j}: idx {ph_idx} not found in layout '{layout_name}'. "
                            f"available indices: {available_idxs}"
                        )
                    
                    layout_ph = available_phs[ph_idx]
                    layout_ph_type = layout_ph['type']
                    
                    if ph_type != layout_ph_type:
                        raise ValueError(
                            f"slide {i} placeholder {j}: type mismatch for idx {ph_idx}. "
                            f"trying to insert '{ph_type}' but placeholder expects '{layout_ph_type}'"
                        )
                
                used_indices = {ph['idx'] for ph in placeholders}
                required_indices = set(available_phs.keys())
                missing_indices = required_indices - used_indices
                
                if missing_indices:
                    raise ValueError(
                        f"slide {i} ('{layout_name}'): not all placeholders filled. "
                        f"layout requires placeholders {sorted(required_indices)}, "
                        f"but missing: {sorted(missing_indices)}. "
                        f"every placeholder in a layout must be populated."
                    )
            
            if num_images > 0:
                used_image_indices = set()
                for i, slide in enumerate(slides):
                    for ph in slide.get('placeholders', []):
                        if ph.get('type') == 'image' and 'image_index' in ph:
                            used_image_indices.add(ph['image_index'])
                
                expected_indices = set(range(num_images))
                missing_indices = expected_indices - used_image_indices
                extra_indices = used_image_indices - expected_indices
                
                if missing_indices:
                    raise ValueError(
                        f"not all images were used in the presentation. "
                        f"missing image indices: {sorted(missing_indices)}. "
                        f"all {num_images} uploaded images must be placed in the deck."
                    )
                
                if extra_indices:
                    raise ValueError(
                        f"invalid image indices used: {sorted(extra_indices)}. "
                        f"only image indices 0-{num_images-1} are available."
                    )
            
            return slides
            
        except json.JSONDecodeError as e:
            raise ValueError(f"Failed to parse AI response as JSON: {str(e)}")
        except Exception as e:
            raise ValueError(f"AI service error: {str(e)}")
    
    def _calculate_text_capacity(self, placeholder):
        """
        calculate accurate text capacity based on placeholder dimensions, font size, and margins.
        returns character and word estimates.
        """
        pos = placeholder.get('position', {})
        props = placeholder.get('properties', {})
        
        # get dimensions in EMUs (914400 EMUs = 1 inch)
        EMU_PER_INCH = 914400
        width_emu = pos.get('width', 0) or 0
        height_emu = pos.get('height', 0) or 0
        
        # get margins from text_frame_props (in EMUs)
        text_frame_props = props.get('text_frame_props', {})
        margin_left = text_frame_props.get('margin_left') or 91440  # default 0.1"
        margin_right = text_frame_props.get('margin_right') or 91440
        margin_top = text_frame_props.get('margin_top') or 45720  # default 0.05"
        margin_bottom = text_frame_props.get('margin_bottom') or 45720
        
        # calculate usable area after margins
        usable_width_emu = max(0, width_emu - margin_left - margin_right)
        usable_height_emu = max(0, height_emu - margin_top - margin_bottom)
        
        # convert to inches for readability
        usable_width_in = usable_width_emu / EMU_PER_INCH
        usable_height_in = usable_height_emu / EMU_PER_INCH
        
        # get font properties
        font_props = props.get('font_props', {})
        font_size = font_props.get('size') or 18
        font_name = font_props.get('name') or 'Calibri'
        
        # get paragraph properties
        para_props = props.get('paragraph_props', {})
        line_spacing = para_props.get('line_spacing')
        try:
            line_spacing = float(line_spacing) if line_spacing else 1.3
        except Exception:
            line_spacing = 1.3
        
        # calculate text metrics (ULTRA-CONSERVATIVE to prevent overflow)
        # Since we have post-processing enforcement, aim low so AI creates more slides.
        # Use 1.2em per character and padded line height to underestimate capacity.
        char_width_factor = 1.2
        
        # ensure we don't divide by zero
        if font_size > 0 and usable_width_in > 0:
            chars_per_line = max(1, int((usable_width_in * 72) / (font_size * char_width_factor)))  # 72 points per inch
        else:
            chars_per_line = 0
        
        # calculate number of lines that fit (conservative line height)
        line_height_pt = max(font_size * float(line_spacing) * 1.3, font_size * 1.6)
        if line_height_pt > 0 and usable_height_in > 0:
            lines_available = max(1, int((usable_height_in * 72) / line_height_pt))
        else:
            lines_available = 0
        
        max_chars = max(0, chars_per_line * lines_available)
        max_words = max(0, max_chars // 6)
        
        return {
            'width_in': usable_width_in,
            'height_in': usable_height_in,
            'font_name': font_name,
            'font_size': font_size,
            'chars_per_line': chars_per_line,
            'lines_available': lines_available,
            'max_chars': max_chars,
            'max_words': max_words
        }
    
    def _multipass_text_fitting(self, slides, layouts, slide_size, max_passes=3):
        """
        iteratively shorten overflowing text until it fits.
        thinking model approach: analyze → identify overflow → shorten → re-validate.
        """
        layout_map = {layout['name']: layout for layout in layouts}
        
        for pass_num in range(max_passes):
            # detect text overflow
            overflow_items = []
            
            for slide in slides:
                layout_name = slide.get('layout_name', 'Unknown')
                if layout_name not in layout_map:
                    continue
                
                layout = layout_map[layout_name]
                placeholders = slide.get('placeholders', [])
                
                for ph in placeholders:
                    if ph.get('type') != 'text':
                        continue
                    
                    content = ph.get('content', '')
                    content_len = len(content)
                    ph_idx = ph.get('idx')
                    
                    layout_ph = next((p for p in layout['placeholders'] if p['idx'] == ph_idx and p['type'] == 'text'), None)
                    
                    if not layout_ph:
                        continue
                    
                    capacity = self._estimate_text_capacity(layout_ph.get('properties', {}))
                    max_chars = capacity['chars']
                    
                    # check for overflow (with 5% buffer for safety)
                    if content_len > max_chars * 0.95:
                        overflow_amount = content_len - int(max_chars * 0.85)  # target 85% fill
                        overflow_items.append({
                            'slide_number': slide.get('slide_number'),
                            'placeholder_idx': ph_idx,
                            'current_length': content_len,
                            'max_capacity': max_chars,
                            'target_length': int(max_chars * 0.85),
                            'overflow_by': overflow_amount,
                            'current_content': content
                        })
            
            if not overflow_items:
                print(f"\n✅ Pass {pass_num + 1}: No text overflow detected")
                break
            
            print(f"\nPass {pass_num + 1}/{max_passes}: Found {len(overflow_items)} overflowing text placeholders")
            for item in overflow_items:
                print(f"   Slide {item['slide_number']} idx {item['placeholder_idx']}: {item['current_length']} → {item['target_length']} chars")
            
            # ask ai to shorten overflowing text
            try:
                shorten_prompt = f"""You created slide content, but some text is too long and will overflow.

Please shorten ONLY the specified text items to fit their capacity limits.

OVERFLOW ITEMS TO FIX:
{chr(10).join([f"- Slide {item['slide_number']}, placeholder {item['placeholder_idx']}: Currently {item['current_length']} chars, must be ≤{item['target_length']} chars (reduce by {item['overflow_by']})" for item in overflow_items])}

ORIGINAL CONTENT TO SHORTEN:
{chr(10).join([f"Slide {item['slide_number']}, idx {item['placeholder_idx']}:\n\"{item['current_content']}\"\n" for item in overflow_items])}

INSTRUCTIONS:
1. Keep the same meaning and key points
2. Remove filler words, redundancy, and verbose phrasing
3. Be more concise while preserving essential information
4. Target 70-85% of max capacity for good aesthetics

Return JSON with ONLY the slides that need changes:
{{
  "slides_to_update": [
    {{
      "slide_number": N,
      "placeholder_idx": N,
      "shortened_content": "concise version that fits"
    }}
  ]
}}

Return ONLY valid JSON."""

                response = self._chat(
                    messages=[
                        {"role": "user", "content": shorten_prompt}
                    ],
                    response_format_json=True,
                )
                
                result = json.loads(response.choices[0].message.content)
                updates = result.get('slides_to_update', [])
                
                # apply updates
                for update in updates:
                    slide_num = update['slide_number']
                    ph_idx = update['placeholder_idx']
                    new_content = update['shortened_content']
                    
                    for slide in slides:
                        if slide.get('slide_number') == slide_num:
                            for ph in slide.get('placeholders', []):
                                if ph.get('idx') == ph_idx:
                                    old_len = len(ph.get('content', ''))
                                    ph['content'] = new_content
                                    new_len = len(new_content)
                                    print(f"   ✓ Slide {slide_num} idx {ph_idx}: {old_len} → {new_len} chars")
                
                print(f"   ✅ Applied {len(updates)} text shortenings")
                
            except Exception as e:
                print(f"   text shortening failed: {e}, keeping original")
                break
        
        return slides
    
    def _validate_aesthetic_choices(self, slides, layouts, slide_size=None):
        """
        validate slide aesthetic choices and return warnings.
        returns list of warning strings for retry mechanism.
        """
        layout_map = {layout['name']: layout for layout in layouts}
        
        # Get slide dimensions
        slide_width = 9144000  # Default: 10 inches
        slide_height = 6858000  # Default: 7.5 inches
        if slide_size:
            slide_width = slide_size.get('width', slide_width)
            slide_height = slide_size.get('height', slide_height)
        
        print("\n" + "="*80)
        print("AESTHETIC VALIDATION:")
        print("="*80)
        
        warnings = []
        
        for slide in slides:
            slide_num = slide.get('slide_number', '?')
            layout_name = slide.get('layout_name', 'Unknown')
            
            if layout_name not in layout_map:
                continue
            
            layout = layout_map[layout_name]
            placeholders = slide.get('placeholders', [])
            
            # Calculate geometric space utilization for this layout
            space_util = self._calculate_layout_space_utilization(layout, slide_width, slide_height)
            negative_space = space_util['negative_space_percent']
            
            # Check for excessive negative space (>50%)
            if negative_space > 50:
                warning = (f"Slide {slide_num} ({layout_name}): "
                          f"EXCESSIVE NEGATIVE SPACE: {negative_space:.0f}% empty, "
                          f"only {space_util['content_percent']:.0f}% content coverage")
                warnings.append(warning)
                print(f"⚠️  {warning}")
            
            # Check each text placeholder
            for ph in placeholders:
                if ph.get('type') != 'text':
                    continue
                
                content = ph.get('content', '')
                content_len = len(content)
                ph_idx = ph.get('idx')
                
                # Find corresponding layout placeholder
                layout_ph = next((p for p in layout['placeholders'] if p['idx'] == ph_idx and p['type'] == 'text'), None)
                
                if not layout_ph:
                    continue
                
                # Get font size and capacity
                props = layout_ph.get('properties', {})
                font_props = props.get('font_props', {})
                font_size = font_props.get('size', 18)
                capacity = self._estimate_text_capacity(props)
                max_chars = capacity['chars']
                ph_name = layout_ph.get('name', 'Unknown')
                
                # Check if this is a TITLE placeholder
                is_title = font_size > 32 or (max_chars < 150 and font_size > 24)
                
                if is_title and content_len > 60:
                    # CRITICAL: Title placeholder violation
                    warning = (f"Slide {slide_num} ({layout_name}): "
                              f"🚫 TITLE/HEADER VIOLATION idx {ph_idx} ({font_size}pt font): "
                              f"{content_len} chars in TITLE placeholder (MAX 60 chars!)."
                              f"Content: \"{content[:50]}...\"")
                    warnings.append(warning)
                    print(f"🚫 {warning}")
                
                # Check for overflow using per-textbox line wrapping (STRONGER than char-count)
                elif content:
                    try:
                        fit, rem = self._split_text_to_fit_box(content, props)
                        if rem:
                            warning = (f"Slide {slide_num} ({layout_name}): "
                                      f"TEXT OVERFLOW idx {ph_idx}: content does not fit "
                                      f"(~{capacity.get('chars_per_line')} chars/line × {capacity.get('lines_available')} lines). "
                                      f"Exceeds by: {len(rem)} chars")
                            warnings.append(warning)
                            print(f"⚠️  {warning}")
                    except Exception:
                        # fall back to conservative char count check
                        if content_len > max_chars * 0.70:
                            warning = (f"Slide {slide_num} ({layout_name}): "
                                      f"TEXT MAY OVERFLOW idx {ph_idx}: {content_len} chars vs ~{int(max_chars * 0.70)} safe max")
                            warnings.append(warning)
                            print(f"⚠️  {warning}")
                
                # Check for excessive white space within individual placeholders (less than 30% filled on large placeholders)
                elif max_chars > 500 and content_len < max_chars * 0.3:
                    fill_percent = (content_len / max_chars) * 100
                    warning = (f"Slide {slide_num} ({layout_name}): "
                              f"UNDER-FILLED idx {ph_idx}: {content_len} chars in {max_chars} capacity "
                              f"({fill_percent:.0f}% filled)")
                    warnings.append(warning)
                    print(f"⚠️  {warning}")
        
        if not warnings:
            print("no aesthetic issues detected - all slides look well-balanced!")
        
        print("="*80 + "\n")
        
        return warnings
    
    def _validate_layout_diversity(self, slides):
        """
        validate that layouts are diverse and not overused.
        returns list of warning strings.
        """
        if len(slides) < 3:
            return []  # too few slides to check diversity
        
        print("\n" + "="*80)
        print("LAYOUT DIVERSITY VALIDATION:")
        print("="*80)
        
        warnings = []
        layout_usage = {}
        
        # count usage of each layout (excluding title/section slides)
        content_slides = []
        for slide in slides:
            layout_name = slide.get('layout_name', 'Unknown')
            slide_type = slide.get('slide_type', 'content')
            
            # track all layouts
            layout_usage[layout_name] = layout_usage.get(layout_name, 0) + 1
            
            # track content slides separately (exclude titles/dividers)
            if slide_type not in ['title', 'section_divider']:
                content_slides.append(slide)
        
        total_slides = len(slides)
        total_content_slides = len(content_slides)
        unique_layouts = len(layout_usage)
        
        print(f"Total slides: {total_slides}")
        print(f"Content slides: {total_content_slides}")
        print(f"Unique layouts used: {unique_layouts}")
        print(f"\nLayout usage breakdown:")
        for layout_name, count in sorted(layout_usage.items(), key=lambda x: -x[1]):
            pct = (count / total_slides) * 100
            print(f"  '{layout_name}': {count}× ({pct:.0f}%)")
        
        # check for overuse of any single layout
        for layout_name, count in layout_usage.items():
            usage_pct = (count / total_slides) * 100
            
            # warn if a layout is used more than 40% of the time (excluding very small decks)
            if total_slides >= 5 and usage_pct > 40:
                warning = (f"Layout '{layout_name}' is overused: {count}/{total_slides} slides ({usage_pct:.0f}%). "
                          f"Recommendation: Use more diverse layouts for visual interest.")
                warnings.append(warning)
                print(f"⚠️  {warning}")
        
        # check for consecutive reuse (adjacent slides with same layout)
        consecutive_count = 0
        for i in range(1, len(slides)):
            prev_layout = slides[i-1].get('layout_name', '')
            curr_layout = slides[i].get('layout_name', '')
            prev_type = slides[i-1].get('slide_type', 'content')
            curr_type = slides[i].get('slide_type', 'content')
            
            # only warn if both are content slides (not title/divider)
            if (prev_layout == curr_layout and 
                prev_type not in ['title', 'section_divider'] and 
                curr_type not in ['title', 'section_divider']):
                consecutive_count += 1
                if consecutive_count == 1:  # only warn once per sequence
                    warning = (f"Slides {i} and {i+1} use the same layout ('{curr_layout}'). "
                              f"Consider alternating layouts for better visual variety.")
                    warnings.append(warning)
                    print(f"⚠️  {warning}")
            else:
                consecutive_count = 0
        
        # check overall diversity ratio
        if total_content_slides >= 6:
            diversity_ratio = unique_layouts / total_slides
            if diversity_ratio < 0.4:  # less than 40% unique layouts
                warning = (f"Low layout diversity: only {unique_layouts} unique layouts for {total_slides} slides. "
                          f"Recommendation: Use more varied layouts to avoid monotonous presentation.")
                warnings.append(warning)
                print(f"⚠️  {warning}")
            elif diversity_ratio >= 0.5:
                print(f"✅ Good layout diversity: {unique_layouts} unique layouts for {total_slides} slides")
        
        if not warnings:
            print("layout diversity looks good!")
        
        print("="*80 + "\n")
        
        return warnings
    
    def _enforce_strict_capacity_limits(self, slides, layouts):
        """
        programmatically enforce text capacity limits.
        HARD ENFORCEMENT:
        - title placeholders (>32pt): MAX 60 chars
        - content placeholders: MAX 85% of capacity
        """
        layout_map = {layout['name']: layout for layout in layouts}
        
        print("\n" + "="*80)
        print("STRICT CAPACITY ENFORCEMENT:")
        print("="*80)
        
        truncated_count = 0
        title_violations = 0
        
        for slide in slides:
            slide_num = slide.get('slide_number', '?')
            layout_name = slide.get('layout_name', 'Unknown')
            
            if layout_name not in layout_map:
                continue
            
            layout = layout_map[layout_name]
            placeholders = slide.get('placeholders', [])
            
            for ph in placeholders:
                if ph.get('type') != 'text':
                    continue
                
                content = ph.get('content', '')
                content_len = len(content)
                ph_idx = ph.get('idx')
                
                # find corresponding layout placeholder
                layout_ph = next((p for p in layout['placeholders'] if p['idx'] == ph_idx and p['type'] == 'text'), None)
                
                if not layout_ph:
                    continue
                
                # get font size and capacity
                props = layout_ph.get('properties', {})
                font_props = props.get('font_props', {})
                font_size = font_props.get('size', 18)
                capacity = self._estimate_text_capacity(props)
                
                # determine if this is a title placeholder
                is_title = font_size > 32 or (capacity['chars'] < 150 and font_size > 24)
                
                if is_title:
                    # HARD LIMIT for titles: 60 chars max
                    strict_max = 60
                    if content_len > strict_max:
                        title_violations += 1
                        truncated_count += 1
                        original_len = content_len
                        
                        # truncate at word boundary
                        truncated = content[:strict_max]
                        last_space = truncated.rfind(' ')
                        if last_space > strict_max * 0.8:
                            truncated = truncated[:last_space]
                        
                        truncated = truncated.rstrip()
                        
                        ph['content'] = truncated
                        print(f"🚫 TITLE VIOLATION - Slide {slide_num} idx {ph_idx} (font: {font_size}pt): truncated {original_len} → {len(truncated)} chars (TITLE MAX: 60)")
                else:
                    # content placeholder: 85% of capacity
                    strict_max = int(capacity['chars'] * 0.85)
                    if content_len > strict_max:
                        truncated_count += 1
                        original_len = content_len
                        
                        # truncate at word boundary
                        truncated = content[:strict_max]
                        last_space = truncated.rfind(' ')
                        if last_space > strict_max * 0.9:
                            truncated = truncated[:last_space]
                        
                        if len(truncated) < len(content):
                            truncated = truncated.rstrip() + '...'
                        
                        ph['content'] = truncated
                        print(f"✂️  Slide {slide_num} idx {ph_idx}: truncated {original_len} → {len(truncated)} chars (limit: {strict_max})")
        
        if truncated_count == 0:
            print("no truncation needed - all text within capacity limits")
        else:
            print(f"⚠️  {truncated_count} text placeholders were truncated ({title_violations} title violations)")
        
        print("="*80 + "\n")
        
        return slides
    
    def _validate_slide_types(self, slides, layouts):
        """
        Validate slides follow proper type hierarchy and content allocation.
        Ensures structural slides (title, divider, closing) have minimal content,
        and content slides have substantial information.
        """
        warnings = []
        layout_map = {l['name']: l for l in layouts}
        
        for i, slide in enumerate(slides):
            slide_num = i + 1
            layout_name = slide.get('layout_name')
            slide_type = slide.get('slide_type', 'content')
            
            if layout_name not in layout_map:
                continue
            
            layout = layout_map[layout_name]
            total_content_length = sum(
                len(ph.get('content', '')) 
                for ph in slide.get('placeholders', []) 
                if ph.get('type') == 'text'
            )
            
            # Check title slide (first slide or explicitly marked)
            if slide_type == 'title' or (i == 0 and total_content_length < 150):
                if total_content_length > 100:
                    warnings.append(
                        f"Slide {slide_num} (TITLE SLIDE): {total_content_length} chars - "
                        f"TITLE SLIDES should have <100 chars total (company name + tagline only)"
                    )
            
            # Check section divider
            elif 'divider' in layout_name.lower() or 'section' in slide_type.lower():
                if total_content_length > 80:
                    warnings.append(
                        f"Slide {slide_num} (SECTION DIVIDER): {total_content_length} chars - "
                        f"DIVIDERS should have <80 chars (section name only, e.g., 'Market Analysis')"
                    )
            
            # Check closing slide
            elif 'closing' in slide_type.lower() or 'closing' in layout_name.lower():
                if total_content_length > 100:
                    warnings.append(
                        f"Slide {slide_num} (CLOSING SLIDE): {total_content_length} chars - "
                        f"CLOSING SLIDES should have <100 chars (brief message only)"
                    )
            
            # Check content slides have sufficient content
            elif slide_type == 'content':
                layout_capacity = layout.get('total_text_capacity', 1000)
                
                # Content slides should use at least 30% of capacity
                if total_content_length < layout_capacity * 0.3 and layout_capacity > 300:
                    warnings.append(
                        f"Slide {slide_num} (CONTENT): Only {total_content_length} chars "
                        f"in {layout_capacity} char layout - UNDER-FILLED "
                        f"(consider using smaller layout or adding more information)"
                    )
                
                # Content slides should have substantial information (not just titles)
                if total_content_length < 50:
                    warnings.append(
                        f"Slide {slide_num} (CONTENT): Only {total_content_length} chars - "
                        f"CONTENT SLIDES should have substantial information (>100 chars)"
                    )
        
        if warnings:
            print(f"\nSLIDE TYPE VALIDATION:")
            for warning in warnings:
                print(f"  - {warning}")
        
        return warnings
    
    def _format_layouts_for_prompt(self, layouts):
        descriptions = []
        
        descriptions.append("\n" + "="*80)
        descriptions.append("VALID LAYOUT NAMES (use these EXACT names in layout_name field):")
        descriptions.append("="*80)
        all_layout_names = [f'"{layout["name"]}"' for layout in layouts]
        descriptions.append(", ".join(all_layout_names))
        descriptions.append("="*80)
        
        for i, layout in enumerate(layouts):
            # check for misleading names
            text_phs = [p for p in layout['placeholders'] if p['type'] == 'text']
            img_phs = [p for p in layout['placeholders'] if p['type'] == 'image']
            has_image_in_name = any(word in layout['name'].lower() for word in ['picture', 'image', 'photo'])
            has_no_image_placeholder = len(img_phs) == 0
            
            desc = f"\n{'='*60}"
            desc += f"\nLayout {i+1}: \"{layout['name']}\""
            
            # add warning as note, not in the name itself
            if has_image_in_name and has_no_image_placeholder:
                desc += f"\n!! WARNING: Name mentions image but layout has NO image placeholders ({len(text_phs)} text only)"
            if 'original_layout_name' in layout:
                desc += f" (based on: {layout['original_layout_name']})"
            desc += f"\n{'='*60}"
            desc += f"\nTotal Placeholders: {len(layout['placeholders'])}"
            desc += f"\n\nAVAILABLE PLACEHOLDERS (these are the ONLY valid idx values):"
            
            has_image = False
            text_count = 0
            
            for ph in layout['placeholders']:
                ph_type = ph['type']
                ph_idx = ph['idx']
                ph_name = ph['name']
                pos = ph.get('position', {})
                width = pos.get('width', 0)
                height = pos.get('height', 0)
                area = width * height
                
                # calculate text capacity with accurate metrics
                if ph_type == 'text':
                    text_count += 1
                    capacity_info = self._calculate_text_capacity(ph)
                    font_size = capacity_info['font_size']
                    max_chars = capacity_info['max_chars']
                    
                    # determine purpose
                    if font_size > 32 or (max_chars < 150 and font_size > 24):
                        purpose = "TITLE/HEADER"
                        purpose_note = "LARGE FONT - Use for titles/headers ONLY (20-60 chars)"
                    else:
                        purpose = "CONTENT/DATA"
                        purpose_note = f"✓ Content placeholder - suitable for paragraphs/data ({max_chars} chars max)"
                    
                    desc += f"\n  ▸ idx={ph_idx}: TEXT - {purpose}"
                    desc += f"\n     {purpose_note}"
                    desc += f"\n     name: \"{ph_name}\""
                    desc += f"\n     font: {capacity_info['font_name']} {font_size}pt"
                    desc += f"\n     dimensions: {capacity_info['width_in']:.1f}\" × {capacity_info['height_in']:.1f}\""
                    desc += f"\n     maximum capacity: {max_chars} chars ({capacity_info['max_words']} words)"
                elif ph_type == 'image':
                    has_image = True
                    desc += f"\n  ▸ idx={ph_idx}: IMAGE | name=\"{ph_name}\""
            
            desc += f"\n\nCONSTRAINTS:"
            all_idxs = [ph['idx'] for ph in layout['placeholders']]
            text_idxs = [ph['idx'] for ph in layout['placeholders'] if ph['type'] == 'text']
            image_idxs = [ph['idx'] for ph in layout['placeholders'] if ph['type'] == 'image']
            
            desc += f"\n  • STRUCTURE: {len(text_idxs)}T+{len(image_idxs)}I"
            desc += f"\n  • VALID idx: {all_idxs}"
            if text_idxs:
                desc += f"\n  • TEXT idx: {text_idxs}"
            if image_idxs:
                desc += f"\n  • IMAGE idx: {image_idxs}"
            else:
                desc += f"\n  • IMAGE idx: NONE - cannot use for slides with images!"
            
            use_cases = []
            if has_image and text_count > 0:
                use_cases.append("Text + Image combination")
            elif has_image:
                use_cases.append("Image-focused layout")
            elif text_count > 2:
                use_cases.append("Multiple text sections")
            elif text_count > 0:
                use_cases.append("Text-only layout")
            
            if use_cases:
                desc += f"\n\nBEST FOR: {' | '.join(use_cases)}"
            
            descriptions.append(desc)
        
        desc_text = '\n'.join(descriptions)
        desc_text += f"\n\n{'='*60}"
        desc_text += f"\nTOTAL: {len(layouts)} layouts available"
        desc_text += f"\n\nCRITICAL REMINDERS:"
        desc_text += f"\n• ALWAYS check the 'maximum capacity' (character/word count) for each placeholder"
        desc_text += f"\n• NEVER exceed the stated character or word limits"
        desc_text += f"\n• Count ALL characters including spaces and punctuation"
        desc_text += f"\n• If content doesn't fit, choose a different layout or create multiple slides"
        desc_text += f"\n• Text overflow will break the presentation - prevention is mandatory!"
        desc_text += f"\n{'='*60}"
        
        return desc_text
    
    def compress_overflowing_content(self, slide_specs, overflow_details, compression_ratio=0.70):
        """
        compress content in slides that overflow their text boxes.
        uses AI to intelligently reduce content while preserving key information.
        
        compression_ratio: target length as fraction of current (0.70 = reduce by 30%)
        """
        
        # group overflows by slide
        slides_to_fix = {}
        for overflow in overflow_details:
            slide_idx = overflow['slide_idx']
            if slide_idx not in slides_to_fix:
                slides_to_fix[slide_idx] = []
            slides_to_fix[slide_idx].append(overflow)
        
        # create compressed slide specs
        compressed_specs = []
        for i, spec in enumerate(slide_specs):
            if i in slides_to_fix:
                # this slide has overflows, compress it
                overflows = slides_to_fix[i]
                compressed_spec = self._compress_slide_content(spec, overflows, compression_ratio)
                compressed_specs.append(compressed_spec)
            else:
                # no overflow, keep as is
                compressed_specs.append(spec)
        
        return compressed_specs
    
    def _compress_slide_content(self, slide_spec, overflows, compression_ratio):
        """compress content in specific placeholders that overflow"""
        # build a map of which placeholder indices need compression
        overflow_map = {}
        for ovf in overflows:
            # try to match overflow to placeholder by content
            current_text = ovf['current_text']
            for ph in slide_spec['placeholders']:
                if ph.get('type') == 'text' and ph.get('content') == current_text:
                    target_length = max(50, int(ovf['char_count'] * compression_ratio))  # min 50 chars
                    overflow_map[ph['idx']] = {
                        'current_length': ovf['char_count'],
                        'target_length': target_length,
                        'current_content': current_text,
                    }
                    break
        
        if not overflow_map:
            return slide_spec
        
        # build compression prompt
        compression_tasks = []
        for idx, info in overflow_map.items():
            compression_tasks.append({
                'placeholder_idx': idx,
                'current_length': info['current_length'],
                'target_length': info['target_length'],
                'content': info['current_content'],
            })
        
        system_prompt = """you are a content compression expert. your task is to aggressively reduce text length to fit strict character limits while preserving the core message.

CRITICAL RULES:
- the compressed text MUST be under the target character limit (count every character including spaces)
- if needed, reduce to only the most essential points
- use extremely concise language
- remove redundant words and filler
- maintain bullet point structure if present
- be aggressive - fitting the limit is mandatory, even if it means significant reduction
- preserve clarity and grammar despite the compression"""

        user_prompt = f"""compress the following text content to fit within the specified character limits:

layout: {slide_spec['layout_name']}

compression tasks:
"""
        for task in compression_tasks:
            user_prompt += f"\n{'='*60}\n"
            user_prompt += f"placeholder index: {task['placeholder_idx']}\n"
            user_prompt += f"current length: {task['current_length']} characters\n"
            user_prompt += f"target length: {task['target_length']} characters (MUST NOT EXCEED)\n"
            user_prompt += f"current content:\n{task['content']}\n"
        
        user_prompt += f"\n{'='*60}\n"
        user_prompt += """\nreturn a JSON object with this structure:
{
  "compressed": [
    {
      "placeholder_idx": <number>,
      "content": "<compressed text that fits target length>",
      "actual_length": <character count>
    }
  ]
}"""
        
        try:
            response = self._chat(
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt}
                ],
                response_format_json=True,
                temperature=0.3,
            )
            
            result = json.loads(response.choices[0].message.content)
            
            # apply compressed content to slide spec
            compressed_slide = dict(slide_spec)
            compressed_placeholders = []
            
            compression_map = {item['placeholder_idx']: item['content'] for item in result['compressed']}
            
            for ph in slide_spec['placeholders']:
                new_ph = dict(ph)
                if ph['idx'] in compression_map:
                    new_ph['content'] = compression_map[ph['idx']]
                compressed_placeholders.append(new_ph)
            
            compressed_slide['placeholders'] = compressed_placeholders
            return compressed_slide
            
        except Exception as e:
            # fallback: smart truncation at word boundaries
            compressed_slide = dict(slide_spec)
            compressed_placeholders = []
            
            for ph in slide_spec['placeholders']:
                new_ph = dict(ph)
                if ph['idx'] in overflow_map:
                    target = overflow_map[ph['idx']]['target_length']
                    content = ph.get('content', '')
                    
                    if len(content) > target:
                        # truncate at word boundary
                        truncated = content[:target - 3]  # leave room for ellipsis
                        last_space = truncated.rfind(' ')
                        if last_space > target * 0.8:  # if space is reasonably close to end
                            truncated = truncated[:last_space]
                        new_ph['content'] = truncated + '...'
                
                compressed_placeholders.append(new_ph)
            
            compressed_slide['placeholders'] = compressed_placeholders
            return compressed_slide
