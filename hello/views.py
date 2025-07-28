import os
import json
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_http_methods
from groq import Groq
from dotenv import load_dotenv

load_dotenv()

@csrf_exempt
@require_http_methods(["POST"])
def receive_essay(request):
    if request.content_type != 'application/json':
        return JsonResponse({'error': 'Invalid content type'}, status=415)

    try:
        data = json.loads(request.body.decode('utf-8'))
        essay_text = data.get('essay', '').strip()
        test_type = data.get('test_type', '').strip().upper()

        print("Received:", data)  # Debug

        if not essay_text:
            return JsonResponse({'error': 'No essay received'}, status=400)
        if test_type not in ['IELTS', 'SAT', 'GRE']:
            return JsonResponse({'error': 'Invalid or missing test type. Use IELTS, SAT, or GRE.'}, status=400)

        # Prompt templates
        if test_type == 'IELTS':
            system_prompt = (
                f"You are an IELTS examiner grading Task 2. Prompt:\n\n"
                f"{data.get('prompt', '').strip()}\n\n"
                "Check topic relevance strictly. Follow:\n"
                "1) Score out of 9 on:\n"
                "- Task Response\n"
                "- Coherence and Cohesion\n"
                "- Lexical Resource\n"
                "- Grammatical Range and Accuracy\n"
                "2) Average for Overall Band (1 decimal).\n"
                "3) Give brief feedback.\n"
                "4) Suggest 3 improvements.\n\n"
                "**Total output under 100 words. No score repetition.**\n\n"
                "Format:\n"
                "Task Response: <score>\n"
                "Coherence and Cohesion: <score>\n"
                "Lexical Resource: <score>\n"
                "Grammatical Range and Accuracy: <score>\n"
                "Overall Band Score: <score>\n\n"
                "Feedback:\n<paragraph>\n\n"
                "Suggestions for Improvement:\n<3 bullets>\n\n"
            )

        elif test_type == 'SAT':
            system_prompt = (
                f"You are an SAT essay scorer. Prompt:\n\n"
                f"{data.get('prompt', '').strip()}\n\n"
                "Evaluate strictly. Follow:\n"
                "1) Score out of 8 on:\n"
                "- Command of Evidence\n"
                "- Focus and Coherence\n"
                "- Style and Formal Tone\n"
                "- Grammar and Usage\n"
                "- Vocabulary & Sentence Variety\n"
                "2) Average for Total (1 decimal).\n"
                "3) Give concise feedback.\n"
                "4) Suggest 3 improvements.\n\n"
                "**Limit total output to 100 words. Avoid repetition.**\n\n"
                "Format:\n"
                "Command of Evidence: <score>\n"
                "Focus and Coherence: <score>\n"
                "Style and Formal Tone: <score>\n"
                "Grammar and Usage: <score>\n"
                "Vocabulary & Sentence Variety: <score>\n"
                "Total Score: <score>\n\n"
                "Feedback:\n<paragraph>\n\n"
                "Suggestions for Improvement:\n<3 bullets>\n\n"
            )

        elif test_type == 'GRE':
            system_prompt = (
                f"You are grading 2 GRE essays: Issue and Argument. Prompts:\n\n"
                f"{data.get('prompt', '').strip()}\n\n"
                "Evaluate both combined. I want only one evaluation for both essays out of 6. Follow:\n"
                "1) Score out of 6 on:\n"
                "- Clarity and Logic of Ideas\n"
                "- Use of Reasoning & Evidence\n"
                "- Organization and Coherence\n"
                "- Grammar and Vocabulary\n"
                "2) Average each essay, then average both out of 6 not 12(1 decimal).\n"
                "3) Give brief combined feedback.\n"
                "4) Suggest 3 improvements.\n\n"
                "**Output must be ≤100 words. No repeating.**\n\n"
                "Format:\n"
                "Clarity and Logic of Ideas: <score>\n"
                "Use of Reasoning & Evidence:  <score>\n"
                "Organization and Coherence: <score>\n"
                "Grammar and Vocabulary: <score>\n"
                "Total Score: <score>\n\n"
                "Feedback:\n<paragraph>\n\n"
                "Suggestions for Improvement:\n<3 bullets>\n\n"
            )

        # Replace Ollama with Groq call
        client = Groq(api_key=os.getenv("GROQ_API_KEY"))

        completion = client.chat.completions.create(
            model="llama-3.3-70b-versatile",
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": essay_text}
            ],
            temperature=1,
            max_tokens=1024,
            top_p=1,
            stream=False
        )

        reply = completion.choices[0].message.content.strip()

        return JsonResponse({'evaluation': reply}, status=200)

    except json.JSONDecodeError:
        return JsonResponse({'error': 'Invalid JSON'}, status=400)
    except Exception as e:
        return JsonResponse({'error': f'An error occurred: {str(e)}'}, status=500)


@csrf_exempt
@require_http_methods(["GET"])
def generate_prompt(request):
    test_type = request.GET.get('test_type', '').strip().upper()

    if test_type not in ['IELTS', 'SAT', 'GRE-ISSUE', 'GRE-ARGUMENT']:
        return JsonResponse({'error': 'Invalid or missing test type. Use IELTS, SAT, GRE-ISSUE, or GRE-ARGUMENT.'}, status=400)

    try:
        if test_type == 'GRE-ISSUE':
            prompt_text = (
                "You are an expert GRE exam writer. Give one GRE Issue Task Essay prompt only. "
                "No other text please. No instructions, headings, or extra info."
            )
        elif test_type == 'GRE-ARGUMENT':
            prompt_text = (
                "You are an expert GRE exam writer. Give one GRE Argument Essay Task prompt only. "
                "No other text please. No instructions, headings, or extra info."
            )
        else:
            prompt_texts = {
                'IELTS': (
                    "You are an expert IELTS exam writer. Give one Task 2 essay prompt only. "
                    "No instructions, headings, or extra info."
                ),
                'SAT': (
                    "You are an expert SAT exam writer. Give one SAT essay prompt only. "
                    "No instructions, headings, or extra info."
                )
            }
            prompt_text = prompt_texts[test_type]

        # Groq request instead of Ollama
        client = Groq(api_key=os.getenv("GROQ_API_KEY"))

        completion = client.chat.completions.create(
            model="llama-3.3-70b-versatile",
            messages=[
                {"role": "system", "content": prompt_text}
            ],
            temperature=1,
            max_tokens=512,
            top_p=1,
            stream=False
        )

        prompt = completion.choices[0].message.content.strip()

        return JsonResponse({'prompt': prompt}, status=200)

    except Exception as e:
        return JsonResponse({'error': f'An error occurred: {str(e)}'}, status=500)
