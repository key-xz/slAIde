import json
from openai import OpenAI
from config import Config


class AIService:
    def __init__(self):
        self.client = OpenAI(api_key=Config.OPENAI_API_KEY)
        self.model = Config.AI_MODEL
    
    def organize_content_into_slides(self, content_text, image_filenames, layouts):
        layout_descriptions = self._format_layouts_for_prompt(layouts)
        
        system_prompt = """You are a presentation designer expert. Your task is to organize unstructured content into a well-structured slide deck.

Given:
1. Raw text content (may be unorganized notes, bullet points, paragraphs)
2. Available images
3. Available slide layouts with their placeholders

You must:
1. Analyze the content and identify main topics/sections
2. Decide how many slides are needed
3. For each slide, choose the most appropriate layout
4. Assign specific content (text/images) to each placeholder
5. Ensure content flows logically across slides
6. Pair images with relevant text content
7. Follow good presentation design principles (not too much text, visual hierarchy)

Return a JSON array of slides. Each slide must specify:
- layout_name: which layout to use
- placeholders: object mapping placeholder idx to content
  - For text placeholders: {"idx": N, "type": "text", "content": "the text"}
  - For image placeholders: {"idx": N, "type": "image", "image_index": M} where M is the index in the image list

Be concise but clear. Focus on key points. Don't overcrowd slides."""

        user_prompt = f"""Available Layouts:
{layout_descriptions}

Available Images:
{json.dumps(image_filenames, indent=2)}

Raw Content:
{content_text}

Please organize this content into slides. Return ONLY valid JSON (no markdown, no explanation)."""

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
            
            return result['slides']
            
        except Exception as e:
            raise ValueError(f"AI service error: {str(e)}")
    
    def _format_layouts_for_prompt(self, layouts):
        descriptions = []
        for i, layout in enumerate(layouts):
            desc = f"\nLayout {i+1}: {layout['name']}"
            desc += f"\n  Placeholders ({len(layout['placeholders'])}):"
            
            for ph in layout['placeholders']:
                ph_type = ph['type']
                if 'TITLE' in ph_type:
                    ph_type = 'TITLE'
                elif 'BODY' in ph_type or 'OBJECT' in ph_type:
                    ph_type = 'CONTENT'
                elif 'PICTURE' in ph_type:
                    ph_type = 'IMAGE'
                
                desc += f"\n    - idx {ph['idx']}: {ph_type} ({ph['name']})"
            
            descriptions.append(desc)
        
        return '\n'.join(descriptions)
