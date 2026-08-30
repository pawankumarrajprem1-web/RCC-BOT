import os
import asyncio
import re
import copy
import subprocess
from aiohttp import web
from aiogram import Bot, Dispatcher, types
from aiogram.filters import CommandStart, Command
from aiogram.fsm.storage.memory import MemoryStorage
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.client.default import DefaultBotProperties
from aiogram.enums import ParseMode, ChatAction
from pptx import Presentation

# Telegram Bot Token (Render Environment Variable se read hoga)
API_TOKEN = os.getenv("BOT_TOKEN", "8705690496:AAG7yX9v97D-WoHK6ZfC4gAAB5vCEMLVuUA")

# Relative PPT Template Path (Sahi folder path)
TEMPLATE_PATH = os.path.join(os.path.dirname(__file__), "template.pptx")

# Bot Initialization
bot = Bot(token=API_TOKEN, default=DefaultBotProperties(parse_mode=ParseMode.HTML))
dp = Dispatcher(storage=MemoryStorage())

# FSM States
class QuizForm(StatesGroup):
    waiting_for_topic = State()
    waiting_for_q_count = State()
    collecting_questions = State()

# Convert PPTX to PDF using LibreOffice (Linux Compatible)
def convert_pptx_to_pdf(input_pptx, output_dir="."):
    cmd = ["libreoffice", "--headless", "--convert-to", "pdf", input_pptx, "--outdir", output_dir]
    subprocess.run(cmd, check=True)

# Duplicate Template Slide
def duplicate_slide(prs, source_slide):
    blank_layout = prs.slide_layouts[6]
    target_slide = prs.slides.add_slide(blank_layout)
    try:
        target_slide.background.fill.copy(source_slide.background.fill)
    except Exception:
        pass
        
    for shape in source_slide.shapes:
        new_el = copy.deepcopy(shape.element)
        target_slide.shapes._spTree.insert_element_before(new_el, 'p:extLst')
    return target_slide

# Smart Parser for Questions
def parse_raw_text(text):
    clean_text = text.replace('```text', '').replace('```', '').strip()
    lines = [line.strip() for line in clean_text.split('\n') if line.strip()]
    
    questions = []
    current_q = None
    
    for line in lines:
        if re.match(r'^(Q\d*[\.\:]?|\d+[\.\:\)])\s*', line, re.IGNORECASE):
            if current_q and current_q.get('question') and current_q.get('opt_a'):
                questions.append(current_q)
            q_text = re.sub(r'^(Q\d*[\.\:]?|\d+[\.\:\)])\s*', '', line, flags=re.IGNORECASE).strip()
            current_q = {'question': q_text, 'opt_a': '', 'opt_b': '', 'opt_c': '', 'opt_d': ''}
        
        elif current_q is not None:
            if re.match(r'^[A][\)\.]\s*', line, re.IGNORECASE):
                current_q['opt_a'] = re.sub(r'^[A][\)\.]\s*', '', line, flags=re.IGNORECASE).strip()
            elif re.match(r'^[B][\)\.]\s*', line, re.IGNORECASE):
                current_q['opt_b'] = re.sub(r'^[B][\)\.]\s*', '', line, flags=re.IGNORECASE).strip()
            elif re.match(r'^[C][\)\.]\s*', line, re.IGNORECASE):
                current_q['opt_c'] = re.sub(r'^[C][\)\.]\s*', '', line, flags=re.IGNORECASE).strip()
            elif re.match(r'^[D][\)\.]\s*', line, re.IGNORECASE):
                current_q['opt_d'] = re.sub(r'^[D][\)\.]\s*', '', line, flags=re.IGNORECASE).strip()

    if current_q and current_q.get('question') and current_q.get('opt_a'):
        questions.append(current_q)
        
    return questions

def replace_text_in_slide(slide, replacements):
    for shape in slide.shapes:
        if shape.has_text_frame:
            for p in shape.text_frame.paragraphs:
                full_p_text = "".join(r.text for r in p.runs)
                for key, val in replacements.items():
                    if key in full_p_text or key in p.text:
                        if len(p.runs) > 0:
                            p.runs[0].text = p.text.replace(key, val)
                            for r in p.runs[1:]:
                                r.text = ""
                        else:
                            p.text = p.text.replace(key, val)

@dp.message(CommandStart())
async def cmd_start(message: types.Message, state: FSMContext):
    await state.clear()
    await state.set_state(QuizForm.waiting_for_topic)
    await message.reply("<b>📚 Enter the Topic or Subject Name</b>")

@dp.message(Command("cancel"))
async def cmd_cancel(message: types.Message, state: FSMContext):
    current_state = await state.get_state()
    if current_state is None:
        await message.reply("<b>⚠️ No active session found.</b>")
        return
    await state.clear()
    await message.reply("<b>❌ Session Cancelled.</b> Type /start to Reset.")

@dp.message(QuizForm.waiting_for_topic)
async def process_topic(message: types.Message, state: FSMContext):
    topic_name = message.text.strip()
    await state.update_data(topic=topic_name, questions=[])
    await state.set_state(QuizForm.waiting_for_q_count)
    await message.reply("<b>🔢 Enter Total Number of Questions</b>")

@dp.message(QuizForm.waiting_for_q_count)
async def process_q_count(message: types.Message, state: FSMContext):
    count_text = message.text.strip()
    if not count_text.isdigit():
        await message.reply("⚠️ <b>Please Enter a Valid Number.</b>")
        return
        
    q_count = int(count_text)
    user_data = await state.get_data()
    topic_name = user_data.get('topic')
    
    await state.update_data(target_count=q_count)
    await state.set_state(QuizForm.collecting_questions)
    
    prompt_text = (
        f"Generate {q_count} Multiple Choice Questions (MCQs) in Hindi for the Topic: \"{topic_name}\".\n\n"
        "STRICT FORMAT:\n1. Question text?\nA) Option 1\nB) Option 2\nC) Option 3\nD) Option 4\n\n"
        "RULES:\n- Leave 1 Blank line space after each Question.\n"
        "- Do not include any Introduction, Explanations, or Closing Notes.\n"
        "- Please Provide the Entire output inside a Code Box.\n"
        "- Provide only Questions and Options."
    )

    msg = (
        "<b>📋 Copy this Prompt Using for ChatGPT/Gemini:</b>\n\n"
        f"<code>{prompt_text}</code>\n\n"
        "<b>📋 Paste Questions here and Type /done.</b>"
    )
    await message.reply(msg)

@dp.message(Command("help"))
async def send_help(message: types.Message):
    help_text = (
        "🤖 <b>RCC PPT BOT - Help Menu</b>\n\n"
        "• 📝 <b>/start</b> - Create Test Paper\n"
        "• 📄 <b>/done</b> - Generate PDF\n"
        "• ❌ <b>/cancel</b> - Cancel Session\n"
    )
    await message.reply(help_text, parse_mode="HTML")

@dp.message(QuizForm.collecting_questions)
async def process_questions(message: types.Message, state: FSMContext):
    text = message.text.strip()
    
    if text.lower() == '/done':
        user_data = await state.get_data()
        questions_list = user_data.get('questions', [])
        topic_name = user_data.get('topic', 'General Test')
        
        if not questions_list:
            await message.reply("<b>⚠️ No Questions found.</b> Please paste Questions First")
            return

        total_q = len(questions_list)
        await message.reply(f"<b>⏳ Received {total_q} Questions. Generating PDF...</b>")

        output_ppt_path = "Generated_Test.pptx"
        output_pdf_path = "Generated_Test.pdf"
        final_pdf_name = f"{topic_name.replace(' ', '_')}_Test.pdf"
        
        try:
            if not os.path.exists(TEMPLATE_PATH):
                await message.reply("<b>❌ Template File not Found.</b> Check project root.")
                return

            for index, q in enumerate(questions_list, 1):
                temp_prs = Presentation(TEMPLATE_PATH)
                slide = temp_prs.slides[0]

                replacements = {
                    '{{TOPIC}}': str(topic_name),
                    '{{QUESTION}}': f"Q{index}. {q['question']}",
                    '{{OPTION_A}}': f"A) {q['opt_a']}",
                    '{{OPTION_B}}': f"B) {q['opt_b']}",
                    '{{OPTION_C}}': f"C) {q['opt_c']}",
                    '{{OPTION_D}}': f"D) {q['opt_d']}"
                }
                
                replace_text_in_slide(slide, replacements)

                if index == 1:
                    final_prs = temp_prs
                else:
                    duplicate_slide(final_prs, slide)

            final_prs.save(output_ppt_path)
            
            loop = asyncio.get_running_loop()
            await loop.run_in_executor(None, convert_pptx_to_pdf, output_ppt_path, ".")

            if os.path.exists(output_pdf_path):
                os.rename(output_pdf_path, final_pdf_name)

            pdf_file = types.FSInputFile(final_pdf_name)
            await message.reply_document(
                pdf_file, 
                caption=f"<b>📄 Your {topic_name} Test PDF is Ready!</b>\n📌 <b>Topic:</b> {topic_name}\n📊 <b>Total Questions:</b> {total_q}"
            )

            for f in (output_ppt_path, final_pdf_name):
                if os.path.exists(f):
                    os.remove(f)

            await state.clear()

        except Exception as e:
            await message.reply(f"<b>❌ PDF Generation Error:</b> {str(e)}")
        return

    parsed_q = parse_raw_text(text)
    if parsed_q:
        user_data = await state.get_data()
        questions = user_data.get('questions', [])
        questions.extend(parsed_q)
        await state.update_data(questions=questions)

        target = user_data.get('target_count', 0)
        current = len(questions)
        await message.reply(f"<b>✅ Questions Added ({current}/{target}).</b> Send more or Type /done.")
    else:
        await message.reply("<b>⚠️ Invalid Format.</b> Please Check and send Again")

# Dummy Web Server for Render Port Check
async def handle_ping(request):
    return web.Response(text="Bot is Running!")

async def start_web_server():
    app = web.Application()
    app.router.add_get('/', handle_ping)
    app.router.add_get('/health', handle_ping)
    runner = web.AppRunner(app)
    await runner.setup()
    port = int(os.environ.get("PORT", 8080))
    site = web.TCPSite(runner, '0.0.0.0', port)
    await site.start()

async def main():
    await start_web_server()
    await dp.start_polling(bot)

if __name__ == '__main__':
    asyncio.run(main())
