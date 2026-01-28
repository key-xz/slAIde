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
1. You can ONLY use layouts explicitly listed in "Available Layouts"
2. For each slide, you MUST ONLY use placeholder indices (idx) that exist in the chosen layout
3. You MUST match placeholder types EXACTLY:
   - TEXT placeholders accept ONLY text
   - IMAGE placeholders accept ONLY images
   - NEVER put text in image placeholders or images in text placeholders
4. Each layout is a RIGID template - you cannot modify positions, sizes, or styling
5. **EVERY placeholder MUST be filled** - you cannot leave any placeholder empty
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
                
                matching_layout = None
                for layout in layouts:
                    if layout['name'] == layout_name:
                        matching_layout = layout
                        break
                
                if not matching_layout:
                    available_names = [l['name'] for l in layouts]
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
    
    def _format_layouts_for_prompt(self, layouts):
        descriptions = []
        for i, layout in enumerate(layouts):
            desc = f"\n{'='*60}"
            desc += f"\nLayout {i+1}: \"{layout['name']}\""
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
                
                if ph_type == 'text':
                    text_count += 1
                    desc += f"\n  ▸ idx={ph_idx}: TEXT | name=\"{ph_name}\""
                elif ph_type == 'image':
                    has_image = True
                    desc += f"\n  ▸ idx={ph_idx}: IMAGE | name=\"{ph_name}\""
            
            desc += f"\n\nCONSTRAINTS:"
            desc += f"\n  • ONLY use idx values: {[ph['idx'] for ph in layout['placeholders']]}"
            text_idxs = [ph['idx'] for ph in layout['placeholders'] if ph['type'] == 'text']
            if text_idxs:
                desc += f"\n  • Text placeholders: {text_idxs}"
            image_idxs = [ph['idx'] for ph in layout['placeholders'] if ph['type'] == 'image']
            if image_idxs:
                desc += f"\n  • Image placeholders: {image_idxs}"
            
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
        desc_text += f"\nREMINDER: USE DIFFERENT LAYOUTS for variety! Don't repeat the same layout."
        desc_text += f"\n{'='*60}"
        
        return desc_text
