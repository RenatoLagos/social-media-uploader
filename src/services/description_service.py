"""Servicio de generacion de descripciones con GPT-4"""

from typing import Optional

from openai import OpenAI
from tenacity import retry, stop_after_attempt, wait_exponential

from src.config.settings import settings
from src.models.video_metadata import PlatformDescriptions
from src.utils.exceptions import DescriptionGenerationError
from src.utils.logger import get_logger


class DescriptionService:
    """Servicio para generar descripciones optimizadas para cada red social"""

    # Limites de caracteres por plataforma
    LIMITS = {
        'youtube_title': 100,
        'youtube': 5000,
        'instagram': 2200,
        'tiktok': 2200
    }

    def __init__(self, model: str = "gpt-4"):
        """
        Inicializar servicio de descripcion

        Args:
            model: Modelo de OpenAI a usar (default: gpt-4)
        """
        self.logger = get_logger("description")
        self.model = model

        if not settings.openai_api_key:
            raise DescriptionGenerationError(
                "OPENAI_API_KEY no configurada. Agregar a archivo .env"
            )

        self.client = OpenAI(api_key=settings.openai_api_key)

    def generate_all(self, transcription: str) -> PlatformDescriptions:
        """
        Generar descripciones para todas las plataformas

        Args:
            transcription: Transcripcion del video

        Returns:
            PlatformDescriptions con descripciones optimizadas
        """
        self.logger.info("Generando descripciones para todas las plataformas")

        try:
            youtube_title, youtube_desc = self._generate_youtube(transcription)
            instagram_desc = self._generate_instagram(transcription)
            tiktok_desc = self._generate_tiktok(transcription)

            descriptions = PlatformDescriptions(
                youtube_title=youtube_title,
                youtube=youtube_desc,
                instagram=instagram_desc,
                tiktok=tiktok_desc
            )

            self.logger.info(
                "Descripciones generadas",
                youtube_title_len=len(youtube_title),
                youtube_len=len(youtube_desc),
                instagram_len=len(instagram_desc),
                tiktok_len=len(tiktok_desc)
            )

            return descriptions

        except DescriptionGenerationError:
            raise
        except Exception as e:
            raise DescriptionGenerationError(f"Error generando descripciones: {e}")

    def _generate_youtube(self, transcription: str) -> tuple:
        """Generar titulo y descripcion optimizada para YouTube Shorts"""
        prompt = f"""Based on this Spanish teaching video transcription, create a YouTube Shorts TITLE and DESCRIPTION.

TRANSCRIPTION:
"{transcription}"

STYLE GUIDE (follow this format exactly):

TITLE FORMAT:
- Start with a relevant emoji
- Short, catchy, max {self.LIMITS['youtube_title']} characters
- Hook that makes people want to watch
- Example: "📝 Where does the adjective go in Spanish? After the noun! 👇"

DESCRIPTION FORMAT:
- Start with a clear explanation of the topic
- Use 👉 for examples: "👉 casa grande (big house)"
- Use 🔹 for tips or rules
- Use ❌ for common mistakes
- Use 💡 for fun facts or tips
- End with ✅ CTA: "✅ Save this Short & share it with someone learning Spanish!"
- End with hashtags: #ferrealspanish #learnspanish #spanishgrammar #spanishforbeginners #spanishtips

IMPORTANT:
- Write in ENGLISH (the audience learns Spanish but reads English)
- Keep it educational and engaging
- Max description length: {self.LIMITS['youtube']} characters

RESPOND IN THIS EXACT FORMAT:
TITLE: [your title here]
DESCRIPTION: [your description here]"""

        response = self._call_gpt(prompt, self.LIMITS['youtube'])

        # Parsear titulo y descripcion
        lines = response.split('\n', 2)
        title = ""
        description = ""

        for line in lines:
            if line.startswith('TITLE:'):
                title = line.replace('TITLE:', '').strip()
            elif line.startswith('DESCRIPTION:'):
                description = line.replace('DESCRIPTION:', '').strip()

        # Si no se parseó bien, intentar dividir de otra forma
        if not title or not description:
            if 'TITLE:' in response and 'DESCRIPTION:' in response:
                parts = response.split('DESCRIPTION:')
                title = parts[0].replace('TITLE:', '').strip()
                description = parts[1].strip() if len(parts) > 1 else ""
            else:
                # Fallback: usar primera linea como titulo
                lines = response.strip().split('\n')
                title = lines[0][:self.LIMITS['youtube_title']]
                description = '\n'.join(lines[1:]) if len(lines) > 1 else response

        return title[:self.LIMITS['youtube_title']], description[:self.LIMITS['youtube']]

    def _generate_instagram(self, transcription: str) -> str:
        """Generar descripcion optimizada para Instagram Reels"""
        prompt = f"""Based on this Spanish teaching video transcription, create an Instagram Reels caption.

TRANSCRIPTION:
"{transcription}"

STYLE GUIDE (follow this format exactly):

- Start with emoji + catchy hook: "🔤 L vs LL — They sound COMPLETELY different in Spanish! 👇"
- Brief explanation of the topic
- Examples with 👉 or 🔹 bullet points
- Use 💡 for fun facts
- Use ⚠️ for important notes or regional variations
- End with ✅ CTA: "✅ Save this & share it with someone learning Spanish!"
- End with 5-10 hashtags on new line:
  #FerRealSpanish #ferrealspanish_ #LearnSpanish #SpanishPronunciation #SpanishTips #SpanishForBeginners

EXAMPLE FORMAT:
🔤 [HOOK with topic] 👇

[Brief explanation]

👉 [Example 1]
🔹 [Example 2]
🔹 [Example 3]

💡 Fun fact: [interesting detail]

⚠️ [Important note or variation]

✅ Save this & share it with someone learning Spanish!

#FerRealSpanish #ferrealspanish_ #LearnSpanish #SpanishTips #SpanishForBeginners

IMPORTANT:
- Write in ENGLISH (audience learns Spanish but reads English)
- Max {self.LIMITS['instagram']} characters
- Make it engaging and educational

Respond ONLY with the caption, no explanations."""

        return self._call_gpt(prompt, self.LIMITS['instagram'])

    def _generate_tiktok(self, transcription: str) -> str:
        """Generar descripcion optimizada para TikTok"""
        prompt = f"""Based on this Spanish teaching video transcription, create a TikTok caption.

TRANSCRIPTION:
"{transcription}"

STYLE GUIDE (follow this format exactly):

- Start with emoji + personal/emotional hook
- Use bullet points with emojis (👉, 💡, 🔹) for key points
- Keep it conversational and relatable
- Include practical tips the viewer can use
- End with ✅ CTA: "✅ Save this TikTok if you're learning Spanish!"
- End with 3-5 trending hashtags

EXAMPLE FORMAT:
🌍 [Personal hook about learning Spanish]

[Relatable struggle or insight]

👉 [Tip 1]
👉 [Tip 2]
👉 [Tip 3]

💡 [Key advice or takeaway]

✅ Save this TikTok if you're learning Spanish — I get you!

#FerRealSpanish #LearnSpanish #SpanishTips #SpanishMotivation #SpanishForBeginners

IMPORTANT:
- Write in ENGLISH
- Be brief and punchy - TikTok prefers shorter captions
- Max {self.LIMITS['tiktok']} characters
- Make it feel personal and authentic

Respond ONLY with the caption, no explanations."""

        return self._call_gpt(prompt, self.LIMITS['tiktok'])

    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=4, max=10)
    )
    def _call_gpt(self, prompt: str, max_chars: int) -> str:
        """
        Llamar a GPT-4 con reintentos

        Args:
            prompt: Prompt para GPT
            max_chars: Maximo de caracteres esperados

        Returns:
            Respuesta de GPT
        """
        try:
            self.logger.debug("Llamando a GPT", model=self.model)

            response = self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {
                        "role": "system",
                        "content": "You are a social media expert for FerRealSpanish, a Spanish language teaching account. You create engaging, educational content that helps English speakers learn Spanish. Your tone is friendly, encouraging, and authentic. You use emojis strategically and format content for maximum engagement."
                    },
                    {
                        "role": "user",
                        "content": prompt
                    }
                ],
                temperature=0.7,
                max_tokens=1500
            )

            content = response.choices[0].message.content.strip()

            # Truncar si excede el limite
            if len(content) > max_chars:
                self.logger.warning(
                    "Descripcion truncada",
                    original_len=len(content),
                    max_chars=max_chars
                )
                content = content[:max_chars-3] + "..."

            return content

        except Exception as e:
            error_msg = str(e)
            if "rate_limit" in error_msg.lower():
                self.logger.warning("Rate limit alcanzado, reintentando...")
                raise  # Permitir reintento
            raise DescriptionGenerationError(f"Error en GPT API: {e}")

    def generate_single(
        self,
        transcription: str,
        platform: str
    ) -> str:
        """
        Generar descripcion para una plataforma especifica

        Args:
            transcription: Transcripcion del video
            platform: Plataforma destino (youtube, instagram, tiktok)

        Returns:
            Descripcion optimizada
        """
        platform = platform.lower()

        if platform == 'youtube':
            title, desc = self._generate_youtube(transcription)
            return f"TITLE: {title}\n\nDESCRIPTION: {desc}"
        elif platform == 'instagram':
            return self._generate_instagram(transcription)
        elif platform == 'tiktok':
            return self._generate_tiktok(transcription)
        else:
            raise DescriptionGenerationError(
                f"Plataforma no soportada: {platform}. "
                f"Opciones: youtube, instagram, tiktok"
            )
