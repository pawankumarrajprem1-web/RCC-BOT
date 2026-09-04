import os
import asyncio
import re
import copy
import subprocess
import tempfile
import uuid
import html
import certifi
from aiohttp import web
from aiogram import Bot, Dispatcher, types, F
from aiogram.filters import CommandStart, Command, StateFilter
from aiogram.fsm.storage.memory import MemoryStorage
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.client.default import DefaultBotProperties
from aiogram.enums import ParseMode, ChatAction
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton, CallbackQuery, BotCommand

from pptx import Presentation
from docxtpl import DocxTemplate, RichText
from pymongo import MongoClient

# ==================== CONFIGURATION ====================
API_TOKEN = os.getenv("BOT_TOKEN", "8941822350:AAF2H5oiIdvQ70t1TFhX8lhkvHlZLzHBkPc")
MONGO_URI = os.getenv(
    "MONGO_URI", 
    "mongodb+srv://mpcpawan:RswOqZ4uy3UQtM3Q@cluster0.edkvmpu.mongodb.net/"
)

# आपकी दी गई एडमिन आईडी (MPC PAWAN)
ADMIN_IDS = [826246110]

BASE_DIR = os.path.dirname(__file__)
PPT_TEMPLATE = os.path.join(BASE_DIR, "template.pptx")
DOCX_TEMPLATE = os.path.join(BASE_DIR, "template.docx")

client = MongoClient(MONGO_URI, tlsCAFile=certifi.where(), serverSelectionTimeoutMS=5000)
db = client["rcc_quiz_db"]
tests_col = db["test_papers"]

bot = Bot(token=API_TOKEN, default=DefaultBotProperties(parse_mode=ParseMode.HTML))
dp = Dispatcher(storage=MemoryStorage())

class QuizForm(StatesGroup):
    waiting_for_topic = State()
    waiting_for_format = State()
    collecting_questions = State()


# ==================== SET TELEGRAM MENU COMMANDS ====================

async def setup_bot_commands(bot_instance: Bot):
    commands = [
        BotCommand(command="start", description="🤖 बॉट शुरू करें"),
        BotCommand(command="create", description="📝 नया टेस्ट बनाएं"),
        BotCommand(command="mytests", description="📂 सभी टेस्ट देखें, डिलीट करें या PDF बनाएं"),
        BotCommand(command="prompt", description="✨ Gemini AI Prompt (फोटो/PDF से प्रश्न बनाएं)"),
        BotCommand(command="ppt", description="📊 PPT PDF बनाएं (/ppt ID)"),
        BotCommand(command="test", description="📄 Test PDF बनाएं (/test ID)"),
        BotCommand(command="answer", description="✅ Answer PDF बनाएं (/answer ID)"),
        BotCommand(command="cancel", description="❌ प्रक्रिया रद्द करें"),
        BotCommand(command="help", description="❓ सहायता एवं निर्देश"),
        BotCommand(command="stats", description="📈 कुल टेस्ट के आंकड़े"),
    ]
    await bot_instance.set_my_commands(commands)


# ==================== HELPER FUNCTIONS ====================

def convert_to_pdf(input_file, output_dir="."):
    abs_input = os.path.abspath(input_file)
    out_name = os.path.basename(input_file).rsplit('.', 1)[0] + '.pdf'
    abs_output = os.path.abspath(os.path.join(output_dir, out_name))

    if os.name == 'nt':
        libre_paths = [
            r"C:\Program Files\LibreOffice\program\soffice.exe",
            r"C:\Program Files (x86)\LibreOffice\program\soffice.exe",
            "soffice"
        ]
        for soffice_path in libre_paths:
            try:
                cmd = [soffice_path, "--headless", "--convert-to", "pdf", abs_input, "--outdir", output_dir]
                subprocess.run(cmd, check=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
                if os.path.exists(abs_output):
                    return
            except Exception:
                continue

        if input_file.endswith('.docx'):
            try:
                from docx2pdf import convert
                convert(abs_input, abs_output)
                return
            except Exception as e:
                raise Exception(f"DOCX to PDF Error: {str(e)}")

        raise Exception("PDF कनवर्टर फ़ाइल जनरेट करने में असमर्थ रहा।")
    else:
        cmd = ["libreoffice", "--headless", "--convert-to", "pdf", abs_input, "--outdir", output_dir]
        subprocess.run(cmd, check=True)

def parse_raw_text(raw_text):
    questions_list = []
    q_blocks = re.split(r'\n(?=\s*\d+[\.\)\-])', '\n' + raw_text.strip())
    
    for block in q_blocks:
        if not block.strip(): 
            continue
        lines = [line.strip() for line in block.split('\n') if line.strip()]
        if not lines: 
            continue
            
        q_text = re.sub(r'^\d+[\.\)\-]\s*', '', lines[0])
        full_text = "\n".join(lines[1:])
        
        opt_a = re.search(r'(?:^|\n|\s*)(?:\(a\)|a[\.\)\-])\s*(.*?)(?=(?:\(b\)|b[\.\)\-])|$)', full_text, re.DOTALL | re.IGNORECASE)
        opt_b = re.search(r'(?:^|\n|\s*)(?:\(b\)|b[\.\)\-])\s*(.*?)(?=(?:\(c\)|c[\.\)\-])|$)', full_text, re.DOTALL | re.IGNORECASE)
        opt_c = re.search(r'(?:^|\n|\s*)(?:\(c\)|c[\.\)\-])\s*(.*?)(?=(?:\(d\)|d[\.\)\-])|$)', full_text, re.DOTALL | re.IGNORECASE)
        opt_d = re.search(r'(?:^|\n|\s*)(?:\(d\)|d[\.\)\-])\s*(.*?)(?=$)', full_text, re.DOTALL | re.IGNORECASE)
        
        questions_list.append({
            'text': q_text.strip(),
            'a': opt_a.group(1).strip() if opt_a else '',
            'b': opt_b.group(1).strip() if opt_b else '',
            'c': opt_c.group(1).strip() if opt_c else '',
            'd': opt_d.group(1).strip() if opt_d else ''
        })
    return questions_list

def format_docx_option(label, opt_text, show_answer=False):
    if not opt_text: 
        return ""
    rt = RichText()
    is_answer = "✅" in opt_text or "*" in opt_text
    cleaned = opt_text.replace("✅", "").replace("*", "").strip()
    
    if show_answer and is_answer:
        rt.add(f"{label} {cleaned}", bold=True)
    else:
        rt.add(f"{label} {cleaned}", bold=False)
    return rt


# ==================== PDF GENERATION ENGINE ====================

async def generate_and_send(chat_id, doc_id, gen_type):
    try:
        row = tests_col.find_one({"_id": doc_id})
    except Exception as e:
        await bot.send_message(chat_id, f"❌ <b>Database Error:</b> {html.escape(str(e))}")
        return

    if not row:
        await bot.send_message(chat_id, "❌ <b>ID नहीं मिला!</b> कृपया सही ID दर्ज करें।")
        return

    topic = row["topic"]
    raw_text = row["raw_text"]
    parsed_qs = parse_raw_text(raw_text)
    
    await bot.send_chat_action(chat_id=chat_id, action=ChatAction.TYPING)
    msg = await bot.send_message(chat_id, f"⏳ <b>{gen_type}</b> जनरेट हो रहा है, कृपया प्रतीक्षा करें...")

    temp_dir = tempfile.gettempdir()
    output_pdf = os.path.join(temp_dir, f"{topic.replace(' ', '_')}_{gen_type}_{doc_id}.pdf")
    
    try:
        loop = asyncio.get_running_loop()

        if gen_type == "PPT":
            if not os.path.exists(PPT_TEMPLATE):
                await msg.edit_text("❌ <b>Template Missing:</b> `template.pptx` नहीं मिला!")
                return
                
            output_file = os.path.join(temp_dir, f"temp_{doc_id}.pptx")
            prs = Presentation(PPT_TEMPLATE)
            base_slide = prs.slides[0]
            base_shapes_elements = [copy.deepcopy(shape.element) for shape in base_slide.shapes]
            
            for index, q in enumerate(parsed_qs, 1):
                cl_a = q['a'].replace("✅", "").replace("*", "").strip()
                cl_b = q['b'].replace("✅", "").replace("*", "").strip()
                cl_c = q['c'].replace("✅", "").replace("*", "").strip()
                cl_d = q['d'].replace("✅", "").replace("*", "").strip()
                
                replacements = {
                    '{{TOPIC}}': topic, 
                    '{{QUESTION}}': f"Q{index}. {q['text']}",
                    '{{OPTION_A}}': f"a) {cl_a}", 
                    '{{OPTION_B}}': f"b) {cl_b}",
                    '{{OPTION_C}}': f"c) {cl_c}", 
                    '{{OPTION_D}}': f"d) {cl_d}"
                }
                
                target_slide = base_slide if index == 1 else prs.slides.add_slide(prs.slide_layouts[6])
                if index != 1:
                    for el in base_shapes_elements:
                        target_slide.shapes._spTree.insert_element_before(copy.deepcopy(el), 'p:extLst')
                
                for shape in target_slide.shapes:
                    if shape.has_text_frame:
                        for paragraph in shape.text_frame.paragraphs:
                            full_p_text = "".join(run.text for run in paragraph.runs)
                            changed = False
                            for key, val in replacements.items():
                                if key in full_p_text:
                                    full_p_text = full_p_text.replace(key, str(val))
                                    changed = True
                            if changed and paragraph.runs:
                                paragraph.runs[0].text = full_p_text
                                for run in paragraph.runs[1:]:
                                    run.text = ""

            prs.save(output_file)
            await loop.run_in_executor(None, convert_to_pdf, output_file, temp_dir)

        else: # DOCX Formats (Test PDF & Answer Test PDF)
            if not os.path.exists(DOCX_TEMPLATE):
                await msg.edit_text("❌ <b>Template Missing:</b> `template.docx` नहीं मिला!")
                return
                
            output_file = os.path.join(temp_dir, f"temp_{doc_id}.docx")
            doc = DocxTemplate(DOCX_TEMPLATE)
            show_answers = (gen_type == "Answer Test PDF")
            
            formatted_qs = []
            for i, q in enumerate(parsed_qs, 1):
                formatted_qs.append({
                    'id': i, 
                    'text': q['text'],
                    'a': format_docx_option("a)", q['a'], show_answers),
                    'b': format_docx_option("b)", q['b'], show_answers),
                    'c': format_docx_option("c)", q['c'], show_answers),
                    'd': format_docx_option("d)", q['d'], show_answers),
                })
            
            context = {'topic_name': topic, 'questions': formatted_qs}
            doc.render(context)
            doc.save(output_file)
            await loop.run_in_executor(None, convert_to_pdf, output_file, temp_dir)

        generated_pdf_path = output_file.rsplit('.', 1)[0] + ".pdf"
        if os.path.exists(generated_pdf_path):
            os.rename(generated_pdf_path, output_pdf)
            await bot.send_chat_action(chat_id=chat_id, action=ChatAction.UPLOAD_DOCUMENT)
            await bot.send_document(
                chat_id, types.FSInputFile(output_pdf),
                caption=f"📄 आपका <b>{gen_type}</b> तैयार है!\n🆔 <b>ID:</b> <code>{doc_id}</code>"
            )
        else:
            await msg.edit_text("❌ PDF जनरेट करने में विफलता हुई।")
        
        if os.path.exists(output_file): 
            os.remove(output_file)
        if os.path.exists(output_pdf): 
            os.remove(output_pdf)
        await msg.delete()

    except Exception as e:
        await msg.edit_text(f"❌ <b>Error:</b> {html.escape(str(e))}")


# ==================== GLOBAL COMMAND HANDLERS ====================

@dp.message(CommandStart(), StateFilter("*"))
async def cmd_start(message: types.Message, state: FSMContext):
    await state.clear()
    welcome_text = (
        "🤖 <b>Rajesh Competition Centre Bot में आपका स्वागत है!्</b>\n\n"
        "• /create - नया टेस्ट बनाएं\n"
        "• /mytests - सभी टेस्ट देखें, डिलीट करें या PDF बनाएं\n"
        "• /prompt - Gemini AI प्रॉम्प्ट\n"
        "• /help - मदद"
    )
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="📝 Create (नया टेस्ट)", callback_data="btn_create")],
        [InlineKeyboardButton(text="📂 My Tests & Admin Manager", callback_data="list_tests_0")],
        [InlineKeyboardButton(text="✨ AI Prompt", callback_data="btn_prompt")]
    ])
    await message.reply(welcome_text, reply_markup=keyboard)

@dp.message(Command("cancel"), StateFilter("*"))
async def cmd_cancel(message: types.Message, state: FSMContext):
    await state.clear()
    await message.reply("❌ प्रक्रिया रद्द कर दी गई है।")

@dp.message(Command("create"), StateFilter("*"))
async def cmd_create(message: types.Message, state: FSMContext):
    await state.clear()
    await state.set_state(QuizForm.waiting_for_topic)
    await message.reply("🎯 <b>कृपया अपने टेस्ट पेपर का नाम (Topic Name) दर्ज करें:</b>")


# ==================== PAGINATION & ADMIN MANAGER ====================

@dp.message(Command("mytests"), StateFilter("*"))
async def cmd_mytests(message: types.Message):
    await show_tests_list(message, page=0)

async def show_tests_list(target: types.Message | CallbackQuery, page: int = 0):
    limit = 8
    skip = page * limit
    
    try:
        total_count = tests_col.count_documents({})
        records = list(tests_col.find().sort("_id", -1).skip(skip).limit(limit))
    except Exception as e:
        err_msg = f"❌ Error: {str(e)}"
        if isinstance(target, CallbackQuery):
            await target.message.answer(err_msg)
        else:
            await target.reply(err_msg)
        return

    if not total_count:
        msg = "📂 डेटाबेस में अभी कोई टेस्ट पेपर मौजूद नहीं है।"
        if isinstance(target, CallbackQuery):
            await target.message.edit_text(msg)
        else:
            await target.reply(msg)
        return

    text = f"📂 <b>एडमिन डेटाबेस मैनेजर (कुल टेस्ट: {total_count})</b>\nपेज {page + 1} / {(total_count + limit - 1) // limit}\n\n"
    
    keyboard_buttons = []
    for r in records:
        doc_id = r["_id"]
        topic = r.get('topic', 'N/A')[:25]
        text += f"🆔 <code>{doc_id}</code> | 📌 {topic}\n"
        
        keyboard_buttons.append([
            InlineKeyboardButton(text=f"📌 {topic}", callback_data=f"view_t_{doc_id}"),
            InlineKeyboardButton(text="📄 Test", callback_data=f"gen_Test_{doc_id}"),
            InlineKeyboardButton(text="✅ Ans", callback_data=f"gen_Ans_{doc_id}"),
            InlineKeyboardButton(text="🗑️ Delete", callback_data=f"del_{doc_id}_{page}")
        ])

    nav_buttons = []
    if page > 0:
        nav_buttons.append(InlineKeyboardButton(text="⬅️ Previous", callback_data=f"list_tests_{page - 1}"))
    if skip + limit < total_count:
        nav_buttons.append(InlineKeyboardButton(text="Next ➡️", callback_data=f"list_tests_{page + 1}"))
    
    if nav_buttons:
        keyboard_buttons.append(nav_buttons)
    
    keyboard_buttons.append([InlineKeyboardButton(text="🔄 रिफ्रेश लिस्ट", callback_data=f"list_tests_{page}")])
    
    markup = InlineKeyboardMarkup(inline_keyboard=keyboard_buttons)
    
    if isinstance(target, CallbackQuery):
        try:
            await target.message.edit_text(text, reply_markup=markup)
        except Exception:
            await target.message.answer(text, reply_markup=markup)
        await target.answer()
    else:
        await target.reply(text, reply_markup=markup)


@dp.callback_query(F.data.startswith("list_tests_"))
async def pagination_callback(callback: CallbackQuery):
    page = int(callback.data.split("_")[2])
    await show_tests_list(callback, page=page)


@dp.callback_query(F.data.startswith("gen_"))
async def inline_generate_pdf(callback: CallbackQuery):
    parts = callback.data.split("_")
    gen_type_key = parts[1]
    doc_id = parts[2]
    
    gen_type = "Answer Test PDF" if gen_type_key == "Ans" else "Test PDF"
    await callback.answer(f"{gen_type} जनरेट हो रहा है...")
    await generate_and_send(callback.message.chat.id, doc_id, gen_type)


@dp.callback_query(F.data.startswith("del_"))
async def delete_test_callback(callback: CallbackQuery):
    parts = callback.data.split("_")
    doc_id = parts[1]
    page = int(parts[2])
    
    # एडमिन सिक्योरिटी चेक
    if callback.from_user.id not in ADMIN_IDS:
        await callback.answer("❌ आपके पास इसे डिलीट करने की अनुमति नहीं है!", show_alert=True)
        return
        
    try:
        tests_col.delete_one({"_id": doc_id})
        await callback.answer(f"🗑️ टेस्ट ID {doc_id} डिलीट हो गया!")
        await show_tests_list(callback, page=page)
    except Exception as e:
        await callback.answer(f"❌ त्रुटि: {str(e)}")


@dp.callback_query(F.data.startswith("view_t_"))
async def view_single_test(callback: CallbackQuery):
    doc_id = callback.data.replace("view_t_", "")
    row = tests_col.find_one({"_id": doc_id})
    if not row:
        await callback.answer("❌ टेस्ट नहीं मिला!")
        return
        
    info = (
        f"📌 <b>टेस्ट विवरण:</b>\n"
        f"🆔 ID: <code>{doc_id}</code>\n"
        f"🎯 Topic: {row.get('topic')}\n\n"
        f"यहाँ से आप डायरेक्ट PDF डाउनलोड कर सकते हैं या डिलीट कर सकते हैं।"
    )
    markup = InlineKeyboardMarkup(inline_keyboard=[
        [
            InlineKeyboardButton(text="📄 Test PDF", callback_data=f"gen_Test_{doc_id}"),
            InlineKeyboardButton(text="✅ Answer PDF", callback_data=f"gen_Ans_{doc_id}"),
            InlineKeyboardButton(text="📊 PPT", callback_data=f"gen_PPT_{doc_id}")
        ],
        [InlineKeyboardButton(text="🗑️ इस टेस्ट को डिलीट करें", callback_data=f"del_{doc_id}_0")],
        [InlineKeyboardButton(text="🔙 वापस लिस्ट पर जाएं", callback_data="list_tests_0")]
    ])
    await callback.message.edit_text(info, reply_markup=markup)
    await callback.answer()


# ==================== ID COMMAND HANDLERS ====================

@dp.message(Command("ppt"), StateFilter("*"))
async def cmd_ppt(message: types.Message):
    args = message.text.split()
    if len(args) < 2:
        await message.reply("⚠️ कृपया ID दर्ज करें। उदाहरण: <code>/ppt A1B2C3</code>")
        return
    await generate_and_send(message.chat.id, args[1].upper(), "PPT")

@dp.message(Command("test"), StateFilter("*"))
async def cmd_test(message: types.Message):
    args = message.text.split()
    if len(args) < 2:
        await message.reply("⚠️ कृपया ID दर्ज करें। उदाहरण: <code>/test A1B2C3</code>")
        return
    await generate_and_send(message.chat.id, args[1].upper(), "Test PDF")

@dp.message(Command("answer"), StateFilter("*"))
async def cmd_answer(message: types.Message):
    args = message.text.split()
    if len(args) < 2:
        await message.reply("⚠️ कृपया ID दर्ज करें। उदाहरण: <code>/answer A1B2C3</code>")
        return
    await generate_and_send(message.chat.id, args[1].upper(), "Answer Test PDF")


# ==================== OTHER COMMANDS & FLOW ====================

@dp.message(Command("prompt"), StateFilter("*"))
@dp.callback_query(F.data == "btn_prompt")
async def cmd_prompt(event: types.Message | CallbackQuery):
    prompt_text = (
        "✨ <b>Gemini AI क्विज़ मेकर प्रॉम्प्ट</b>\n\n"
        "<code>विषय (Topic): [टॉपिक का नाम]\n"
        "प्रश्नों की संख्या: [जैसे 30]\n\n"
        "कृपया इस फोटो/PDF से MCQs बनाएं और इस फॉर्मेट में दें:\n"
        "1. भारत की राजधानी क्या है?\n"
        "a) मुंबई\n"
        "b) नई दिल्ली ✅\n"
        "c) कोलकाता\n"
        "d) चेन्नई</code>"
    )
    if isinstance(event, CallbackQuery):
        await event.message.reply(prompt_text)
        await event.answer()
    else:
        await event.reply(prompt_text)

@dp.message(Command("help"), StateFilter("*"))
@dp.callback_query(F.data == "btn_help")
async def cmd_help(event: types.Message | CallbackQuery):
    text = (
        "📖 <b>गाइड:्</b>\n"
        "• /create से नया टेस्ट बनाएं।\n"
        "• /mytests से सारे टेस्ट देखें, पेज बदलें, पीडीएफ बनाएं या डिलीट करें।"
    )
    if isinstance(event, CallbackQuery):
        await event.message.reply(text)
        await event.answer()
    else:
        await event.reply(text)

@dp.message(Command("stats"), StateFilter("*"))
async def cmd_stats(message: types.Message):
    count = tests_col.count_documents({})
    await message.reply(f"📊 कुल डेटाबेस टेस्ट पेपर्स: <b>{count}</b>")

@dp.callback_query(F.data == "btn_create")
async def ask_topic(callback: CallbackQuery, state: FSMContext):
    await state.clear()
    await state.set_state(QuizForm.waiting_for_topic)
    await callback.message.edit_text("🎯 <b>कृपया अपने टेस्ट पेपर का नाम (Topic Name) दर्ज करें:</b>")

@dp.message(QuizForm.waiting_for_topic)
async def process_topic(message: types.Message, state: FSMContext):
    await state.update_data(topic=message.text.strip())
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="📊 PPT", callback_data="fmt_PPT")],
        [InlineKeyboardButton(text="📄 Test PDF", callback_data="fmt_Test PDF")],
        [InlineKeyboardButton(text="✅ Answer Test PDF", callback_data="fmt_Answer Test PDF")]
    ])
    await message.reply("📝 टॉपिक सेव हो गया! फॉर्मेट चुनें:", reply_markup=keyboard)
    await state.set_state(QuizForm.waiting_for_format)

@dp.callback_query(QuizForm.waiting_for_format)
async def ask_questions(callback: CallbackQuery, state: FSMContext):
    fmt = callback.data.replace("fmt_", "")
    await state.update_data(selected_format=fmt, raw_questions="")
    await callback.message.edit_text(
        f"✅ <b>{fmt}</b> चुना गया।\n\nअपने प्रश्न भेजें और अंत में <b>/done</b> टाइप करें।"
    )
    await state.set_state(QuizForm.collecting_questions)

@dp.message(QuizForm.collecting_questions)
async def collect_questions(message: types.Message, state: FSMContext):
    text = message.text.strip()
    if text.startswith('/') and text.lower() != '/done':
        return

    if text.lower() == '/done':
        data = await state.get_data()
        raw_text = data.get('raw_questions', '')
        topic = data.get('topic', 'Test')
        selected_format = data.get('selected_format', 'Test PDF')
        
        if not raw_text.strip():
            await message.reply("❌ कोई प्रश्न नहीं मिला!")
            return

        doc_id = uuid.uuid4().hex[:6].upper()
        tests_col.insert_one({"_id": doc_id, "topic": topic, "raw_text": raw_text})
        
        await message.reply(f"✅ <b>सेव हो गया! ID:</b> <code>{doc_id}</code>\nPDF जनरेट हो रहा है...")
        await state.clear()
        await generate_and_send(message.chat.id, doc_id, selected_format)
        return

    data = await state.get_data()
    curr = data.get('raw_questions', '')
    new_raw = curr + "\n\n" + text if curr else text
    await state.update_data(raw_questions=new_raw)
    parsed = parse_raw_text(new_raw)
    await message.reply(f"📥 प्रश्न जोड़े गए (कुल: {len(parsed)})। और भेजें या <b>/done</b> टाइप करें।")


# ==================== RENDER WEB SERVER ====================

async def handle_ping(request):
    return web.Response(text="RCC Bot Active!")

async def start_web_server():
    app = web.Application()
    app.router.add_get('/', handle_ping)
    runner = web.AppRunner(app)
    await runner.setup()
    site = web.TCPSite(runner, '0.0.0.0', int(os.environ.get("PORT", 8080)))
    await site.start()

async def main():
    await start_web_server()
    await setup_bot_commands(bot)
    await bot.delete_webhook(drop_pending_updates=True)
    print("🚀 BOT STARTED SUCCESSFULLY WITH ADMIN ID 826246110 & ALL FEATURES!")
    await dp.start_polling(bot)

if __name__ == '__main__':
    try:
        asyncio.run(main())
    except (KeyboardInterrupt, SystemExit):
        print("Stopped!")
