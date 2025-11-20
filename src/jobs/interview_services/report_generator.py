import openai
import json
from django.conf import settings
class ReportGenerator:

    @staticmethod
    def generate_report(job_requirements, transcript):
        client = openai.OpenAI(api_key=settings.OPENAI_API_KEY)

        system_content = """
        You are now in REPORT MODE.
        Generate score, strengths, weaknesses, recommendation, and transcript analysis.
        Return JSON only.
        """

        messages = [
            {"role": "system", "content": system_content},
            {"role": "user", "content": f"Job Requirements: {job_requirements}"},
            {"role": "user", "content": f"Transcript:\n{transcript}"}
        ]

        response = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=messages,
            response_format={"type": "json_object"}
        )
        print("Report Generation Response:")
        print(response.choices[0])

        return json.loads(response.choices[0].message.content)