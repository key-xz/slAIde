import json
from openai import OpenAI
from config import Config


class AIService:
    def __init__(self):
        api_key = Config.OPENAI_API_KEY
        if not api_key:
            raise ValueError('OPENAI_API_KEY not found in environment variables')
        self.client = OpenAI(api_key=api_key)
        self.model = Config.AI_MODEL
    
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
  * A layout marked "⚠️  NEGATIVE SPACE: 65%" is TOO SPARSE - avoid it!
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
            response = self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": text_prompt}
                ],
                response_format={"type": "json_object"}
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
            
            # Validate and warn about aesthetic issues
            self._validate_aesthetic_choices(result.get('structure', []), layouts, slide_size)
            
            return result
            
        except json.JSONDecodeError as e:
            raise ValueError(f"Failed to parse AI response as JSON: {str(e)}")
        except Exception as e:
            raise ValueError(f"AI preprocessing error: {str(e)}")
    
    def preprocess_with_chunks_and_links(self, content_chunks, images, layouts, slide_size=None):
        """
        preprocess content chunks with linked images into structured slide outlines.
        ai selects layouts, content placement, and deck structure.
        """
        print(f"\n🖼️  PREPROCESSING WITH {len(images)} IMAGES")
        for i, img in enumerate(images):
            img_id = img.get('id', 'NO_ID')
            filename = img.get('filename', 'NO_NAME')
            has_data = bool(img.get('data'))
            tags = img.get('tags', [])
            print(f"   Image {i}: {filename} (ID: {img_id}, has_data: {has_data}, tags: {tags})")
        
        print(f"\n📝 CONTENT CHUNKS:")
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
                print(f"⚠️  misleading layout detected: {layout['name']} → shown as {display_name}")
            else:
                layout_display_names[layout['name']] = layout['name']
        
        layouts_by_category = {}
        for layout in layouts:
            cat = layout.get('category') or 'content_standard'
            layouts_by_category.setdefault(cat, []).append(layout)
        
        print(f"\n📋 PREPROCESSING WITH {len(layouts)} LAYOUTS:")
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
            print(f"\n❌ CRITICAL: {len(images)} images provided but NO layouts support images!")
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
  * A layout marked "⚠️  NEGATIVE SPACE: 65%" is TOO SPARSE - avoid it!
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
10. Each chunk's linked images MUST appear on slides containing that chunk's text.

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
            response = self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": text_prompt}
                ],
                response_format={"type": "json_object"}
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
            
            # Validate and warn about aesthetic issues
            self._validate_aesthetic_choices(result.get('structure', []), layouts, slide_size)
            
            # debug: count images in generated structure
            total_image_placeholders = 0
            for slide in result.get('structure', []):
                for ph in slide.get('placeholders', []):
                    if ph.get('type') == 'image':
                        total_image_placeholders += 1
            
            print(f"\n✅ AI GENERATED STRUCTURE:")
            print(f"   Total slides: {len(result.get('structure', []))}")
            print(f"   Total image placeholders: {total_image_placeholders}")
            print(f"   Images provided to AI: {len(images)}")
            
            if len(images) > 0 and total_image_placeholders == 0:
                print(f"\n⚠️  WARNING: {len(images)} images were provided but AI generated 0 image placeholders!")
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
            pos = placeholder_props.get('position', {})
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
        
        # Calculate total content area (all placeholders)
        content_area = 0
        for placeholder in layout.get('placeholders', []):
            ph_props = placeholder.get('properties', {})
            content_area += self._calculate_placeholder_area(ph_props)
        
        # Also include static shapes if present (design elements)
        for shape in layout.get('shapes', []):
            if shape.get('is_design_image') or shape.get('type') in ['PICTURE', 'TEXT_BOX', 'AUTO_SHAPE']:
                shape_props = shape.get('properties', {})
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
        Estimate text capacity for a placeholder based on dimensions and font size.
        Returns estimated character and word capacity.
        STRICT MODE: Raises ValueError if required properties are missing.
        """
        try:
            pos = placeholder_props.get('position')
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
            
            # Rough estimation: 
            # - Average character width ≈ 0.6 * font_size in points
            # - Convert EMUs to inches (914400 EMUs = 1 inch)
            # - 1 inch = 72 points
            width_inches = width / 914400.0
            height_inches = height / 914400.0
            
            width_points = width_inches * 72
            height_points = height_inches * 72
            
            # Account for margins (typically 0.1 inch on each side)
            usable_width = width_points - (2 * 0.1 * 72)
            usable_height = height_points - (2 * 0.1 * 72)
            
            # Estimate characters per line
            char_width = font_size * 0.5  # Conservative estimate
            chars_per_line = int(usable_width / char_width)
            
            # Estimate number of lines (with line spacing of ~1.2)
            line_height = font_size * 1.2
            num_lines = int(usable_height / line_height)
            
            # Total capacity
            total_chars = chars_per_line * num_lines
            total_words = total_chars // 5  # Average word length + space
            
            # Clamp to reasonable values
            total_chars = max(50, min(total_chars, 5000))
            total_words = max(10, min(total_words, 1000))
            
            # Categorize by size
            if total_chars < 300:
                size_category = "SMALL"
            elif total_chars < 800:
                size_category = "MEDIUM"
            else:
                size_category = "LARGE"
            
            return {
                'chars': total_chars,
                'words': total_words,
                'size': size_category
            }
        except Exception as e:
            # STRICT MODE: Don't use fallbacks, raise the error
            raise ValueError(f"Failed to calculate text capacity for placeholder: {str(e)}")
    
    def _format_layouts_with_categories(self, layouts, layouts_by_category, display_names=None, slide_size=None):
        """format layouts organized by category for AI prompt with capacity estimates and space utilization"""
        
        if display_names is None:
            display_names = {layout['name']: layout['name'] for layout in layouts}
        
        # Get slide dimensions
        slide_width = 9144000  # Default: 10 inches
        slide_height = 6858000  # Default: 7.5 inches
        if slide_size:
            slide_width = slide_size.get('width', slide_width)
            slide_height = slide_size.get('height', slide_height)
        
        output = []
        
        output.append("\n" + "="*80)
        output.append("VALID LAYOUT NAMES (use these EXACT names in layout_name field):")
        output.append("="*80)
        all_layout_names = [f'"{display_names[layout["name"]]}"' for layout in layouts]
        output.append(", ".join(all_layout_names))
        output.append("="*80)
        
        for category, cat_layouts in layouts_by_category.items():
            category_display = category if category else "uncategorized"
            output.append(f"\n## {category_display.replace('_', ' ').title()} ({len(cat_layouts)} layouts)")
            
            for layout in cat_layouts:
                text_phs = [p for p in layout['placeholders'] if p['type'] == 'text']
                img_phs = [p for p in layout['placeholders'] if p['type'] == 'image']
                text_indices = [p['idx'] for p in text_phs]
                img_indices = [p['idx'] for p in img_phs]
                all_indices = [p['idx'] for p in layout['placeholders']]
                
                # Calculate space utilization
                space_util = self._calculate_layout_space_utilization(layout, slide_width, slide_height)
                
                display_name = display_names[layout['name']]
                output.append(f"\n  - \"{display_name}\"")
                output.append(f"    STRUCTURE: {len(text_phs)}T+{len(img_phs)}I")
                output.append(f"    VALID idx: {all_indices}")
                
                # Add space utilization warning
                negative_space = space_util['negative_space_percent']
                if negative_space > 50:
                    output.append(f"    ⚠️  NEGATIVE SPACE: {negative_space:.0f}% (content covers only {space_util['content_percent']:.0f}%)")
                    output.append(f"       → This layout is SPARSE - use only for minimal content!")
                else:
                    output.append(f"    ✓ Space utilization: {space_util['content_percent']:.0f}% content, {negative_space:.0f}% negative")
                
                # Add text capacity information
                if text_indices:
                    output.append(f"      TEXT placeholders: {text_indices}")
                    for ph in text_phs:
                        capacity = self._estimate_text_capacity(ph.get('properties', {}))
                        ph_name = ph.get('name', 'Unknown')
                        is_title = 'title' in ph_name.lower()
                        ph_type = "Title" if is_title else "Body"
                        output.append(f"        • idx {ph['idx']} ({ph_type}): ~{capacity['chars']} chars (~{capacity['words']} words) [{capacity['size']}]")
                
                if img_indices:
                    output.append(f"      IMAGE: {img_indices}")
                else:
                    output.append(f"      IMAGE: NONE - cannot use for slides with images!")
                
                # Calculate total text capacity for the layout
                if text_phs:
                    total_capacity = sum(self._estimate_text_capacity(ph.get('properties', {}))['chars'] for ph in text_phs)
                    output.append(f"    💡 Total text capacity: ~{total_capacity} chars")
                
                if layout.get('category_confidence'):
                    output.append(f"    AI confidence: {layout['category_confidence']:.0%}")
                if layout.get('category_rationale'):
                    output.append(f"    rationale: {layout['category_rationale']}")
        
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
            response = self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": text_prompt}
                ],
                response_format={"type": "json_object"}
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
    
    def categorize_layouts(self, layouts, predefined_categories):
        """
        use AI to categorize extracted layouts into semantic groups.
        can assign to predefined categories or suggest new ones for unusual layouts.
        """
        
        layout_descriptions = []
        for i, layout in enumerate(layouts):
            desc = f"\nLayout {i+1}: {layout['name']}"
            desc += f"\n  Text placeholders: {len([p for p in layout['placeholders'] if p['type'] == 'text'])}"
            desc += f"\n  Image placeholders: {len([p for p in layout['placeholders'] if p['type'] == 'image'])}"
            
            for ph in layout['placeholders']:
                pos = ph['position']
                desc += f"\n  - {ph['type']} at ({pos['left']}, {pos['top']}) size ({pos['width']}x{pos['height']})"
            
            layout_descriptions.append(desc)
        
        category_list = "\n".join([
            f"- {cat['id']}: {cat['name']} - {cat['description']}"
            for cat in predefined_categories
        ])
        
        system_prompt = f"""You are a presentation layout analyst. Categorize slide layouts into semantic groups.

PREDEFINED CATEGORIES:
{category_list}

For each layout, either:
1. assign to a predefined category if it clearly matches
2. suggest a new category name if the layout is unusual

Consider:
- number and arrangement of placeholders
- typical use cases (title slides usually at top, large text areas, etc.)
- spatial layout (side-by-side suggests comparison, grid suggests multi-image)
- text-to-image ratio

Return JSON with "layouts" array containing one entry per layout:
{{
  "layouts": [
    {{
      "layout_index": 0,
      "category_id": "existing_category_id OR new_custom_name",
      "is_new_category": false,
      "confidence": 0.95,
      "rationale": "why this category fits"
    }}
  ]
}}

For new categories, use snake_case IDs like "custom_triple_column"."""

        user_prompt = f"""Categorize these {len(layouts)} layouts:
{chr(10).join(layout_descriptions)}

Return ONLY valid JSON."""

        try:
            response = self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt}
                ],
                response_format={"type": "json_object"}
            )
            
            result = json.loads(response.choices[0].message.content)
            
            categorizations = result.get('layouts', [])
            new_categories = []
            
            for cat in categorizations:
                idx = cat['layout_index']
                if 0 <= idx < len(layouts):
                    layouts[idx]['category'] = cat['category_id']
                    layouts[idx]['category_confidence'] = cat.get('confidence', 0.5)
                    layouts[idx]['category_rationale'] = cat.get('rationale', '')
                    
                    if cat.get('is_new_category'):
                        new_categories.append({
                            'id': cat['category_id'],
                            'name': cat['category_id'].replace('_', ' ').title(),
                            'isPredefined': False
                        })
            
            print(f"\n✓ categorized {len(categorizations)} layouts")
            for cat in categorizations:
                idx = cat['layout_index']
                if 0 <= idx < len(layouts):
                    print(f"  {layouts[idx]['name']}: {cat['category_id']} ({cat.get('confidence', 0.5):.0%})")
            
            return {
                'layouts': layouts,
                'new_categories': new_categories
            }
            
        except Exception as e:
            print(f"layout categorization failed: {e}")
            for layout in layouts:
                layout['category'] = 'content_standard'
                layout['category_confidence'] = 0.3
            return {'layouts': layouts, 'new_categories': []}
    
    def analyze_image_content(self, image_data_base64):
        """
        use vision AI to understand image content for intelligent layout matching.
        returns description and detected labels.
        """
        
        try:
            response = self.client.chat.completions.create(
                model="gpt-4o",
                messages=[
                    {
                        "role": "user",
                        "content": [
                            {
                                "type": "text",
                                "text": """analyze this image for presentation layout matching.

provide:
1. brief description (1-2 sentences)
2. image type (graph, chart, photo, diagram, screenshot, icon, logo, illustration)
3. key characteristics (has_text, has_data_points, is_portrait, is_landscape, is_complex)
4. recommended layout type (large_image, side_by_side, grid, corner_accent)

return JSON:
{
  "description": "...",
  "type": "...",
  "characteristics": [...],
  "recommended_layout_style": "...",
  "confidence": 0.0-1.0
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
                max_tokens=300
            )
            
            result = json.loads(response.choices[0].message.content)
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
            
            response = self.client.chat.completions.create(
                model=self.model,
                messages=messages,
                response_format={"type": "json_object"}
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
                    print(f"\n❌ ERROR: AI generated invalid layout name")
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
        if line_spacing is None:
            line_spacing = 1.0
        
        # calculate text metrics
        # average character width is approximately 0.5-0.6 times font size
        # average character height with line spacing is font_size * line_spacing
        char_width_factor = 0.55  # conservative estimate
        
        # ensure we don't divide by zero
        if font_size > 0 and usable_width_in > 0:
            chars_per_line = max(1, int((usable_width_in * 72) / (font_size * char_width_factor)))  # 72 points per inch
        else:
            chars_per_line = 0
        
        # calculate number of lines that fit
        line_height_pt = font_size * float(line_spacing)
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
    
    def _validate_aesthetic_choices(self, slides, layouts, slide_size=None):
        """
        Validate slide aesthetic choices and warn about potential issues.
        Checks for:
        - Text overflow (too much content for placeholder capacity)
        - Excessive white space (too little content for layout capacity)
        - Excessive negative space (>50% of slide is empty based on geometric area)
        - Poor layout matching
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
        
        issues_found = False
        
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
                print(f"⚠️  Slide {slide_num} ({layout_name}):")
                print(f"   EXCESSIVE NEGATIVE SPACE: {negative_space:.0f}% of slide is empty!")
                print(f"   Content covers only {space_util['content_percent']:.0f}% of slide area")
                print(f"   → This layout is TOO SPARSE for the content - use a denser layout!")
                issues_found = True
            
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
                
                # Estimate capacity
                capacity = self._estimate_text_capacity(layout_ph.get('properties', {}))
                max_chars = capacity['chars']
                ph_name = layout_ph.get('name', 'Unknown')
                
                # Check for overflow
                if content_len > max_chars * 1.1:  # 10% buffer
                    print(f"⚠️  Slide {slide_num} ({layout_name}):")
                    print(f"   TEXT OVERFLOW risk - idx {ph_idx} ('{ph_name}')")
                    print(f"   Content: {content_len} chars | Capacity: ~{max_chars} chars")
                    print(f"   Exceeds by: {content_len - max_chars} chars ({((content_len/max_chars - 1) * 100):.0f}% over)")
                    issues_found = True
                
                # Check for excessive white space within individual placeholders (less than 30% filled on large placeholders)
                elif max_chars > 500 and content_len < max_chars * 0.3:
                    fill_percent = (content_len / max_chars) * 100
                    print(f"⚠️  Slide {slide_num} ({layout_name}):")
                    print(f"   PLACEHOLDER UNDER-FILLED - idx {ph_idx} ('{ph_name}')")
                    print(f"   Content: {content_len} chars | Capacity: ~{max_chars} chars")
                    print(f"   Only {fill_percent:.0f}% filled - consider more content or smaller layout")
                    issues_found = True
        
        if not issues_found:
            print("✅ No aesthetic issues detected - all slides look well-balanced!")
        
        print("="*80 + "\n")
    
    def _format_layouts_for_prompt(self, layouts):
        descriptions = []
        
        # create display names with warnings for misleading layouts
        display_names = {}
        for layout in layouts:
            text_phs = [p for p in layout['placeholders'] if p['type'] == 'text']
            img_phs = [p for p in layout['placeholders'] if p['type'] == 'image']
            
            has_image_in_name = any(word in layout['name'].lower() for word in ['picture', 'image', 'photo'])
            has_no_image_placeholder = len(img_phs) == 0
            
            if has_image_in_name and has_no_image_placeholder:
                display_names[layout['name']] = f"{layout['name']} [TEXT-ONLY: {len(text_phs)}T+0I]"
            else:
                display_names[layout['name']] = layout['name']
        
        descriptions.append("\n" + "="*80)
        descriptions.append("VALID LAYOUT NAMES (use these EXACT names in layout_name field):")
        descriptions.append("="*80)
        all_layout_names = [f'"{display_names[layout["name"]]}"' for layout in layouts]
        descriptions.append(", ".join(all_layout_names))
        descriptions.append("="*80)
        
        for i, layout in enumerate(layouts):
            display_name = display_names[layout['name']]
            desc = f"\n{'='*60}"
            desc += f"\nLayout {i+1}: \"{display_name}\""
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
                    desc += f"\n  ▸ idx={ph_idx}: TEXT"
                    desc += f"\n     name: \"{ph_name}\""
                    desc += f"\n     dimensions: {capacity_info['width_in']:.1f}\" × {capacity_info['height_in']:.1f}\" (after margins)"
                    desc += f"\n     font: {capacity_info['font_name']} {capacity_info['font_size']}pt"
                    desc += f"\n     maximum capacity: {capacity_info['max_chars']} chars ({capacity_info['max_words']} words)"
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
