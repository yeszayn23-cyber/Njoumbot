import json
import os
from telegram import InlineKeyboardButton, InlineKeyboardMarkup, Update
from telegram.ext import (
    ApplicationBuilder,
    CallbackQueryHandler,
    CommandHandler,
    ContextTypes,
    MessageHandler,
    filters,
)

# تم إدخال التوكن ومعرف المالك الذي أرسلته
TOKEN = "8892763034:AAFea81gOWJOk5Hy2jedAfizbv0Tg_oo-FQ"
OWNER_ID = 8421694319

# ملفات حفظ البيانات
DATA_FILE = "bot_data.json"


def load_data():
  if os.path.exists(DATA_FILE):
    with open(DATA_FILE, "r", encoding="utf-8") as f:
      return json.load(f)
  return {
      "welcome_message": "أهلاً بك في البوت!",
      "buttons": {},  # اسم الزر: محتواه
      "users": {},  # user_id: {"username": str, "stars_normal": int, "stars_advanced": int, "tasks": {}}
  }


def save_data(data):
  with open(DATA_FILE, "w", encoding="utf-8") as f:
    json.dump(data, f, ensure_ascii=False, indent=4)


data = load_data()


# أمر البدء والترحيب
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
  user = update.effective_user
  if str(user.id) not in data["users"]:
    data["users"][str(user.id)] = {
        "username": user.username or user.first_name,
        "stars_normal": 0,
        "stars_advanced": 0,
        "tasks": {},
    }
    save_data(data)

  await update.message.reply_text(data["welcome_message"])


# لوحة تحكم المالك لإدارة الأزرار والترحيب
async def panel(update: Update, context: ContextTypes.DEFAULT_TYPE):
  if update.effective_user.id != OWNER_ID:
    return

  keyboard = [
      [
          InlineKeyboardButton("➕ إضافة زر", callback_data="admin_add_btn"),
          InlineKeyboardButton("🗑️ حذف زر", callback_data="admin_del_btn"),
      ],
      [
          InlineKeyboardButton(
              "✏️ تعديل رسالة الترحيب", callback_data="admin_set_welcome"
          ),
          InlineKeyboardButton("📋 عرض الأزرار", callback_data="admin_list_btn"),
      ],
  ]
  reply_markup = InlineKeyboardMarkup(keyboard)
  await update.message.reply_text(
      "🛠️ لوحة تحكم المالك:", reply_markup=reply_markup
  )


# معالجة تفاعلات الأزرار للمالك أو المستخدمين
async def button_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
  query = update.callback_query
  await query.answer()
  user_id = str(query.from_user.id)

  if query.data.startswith("admin_"):
    if query.from_user.id != OWNER_ID:
      await query.edit_message_text("هذه اللوحة خاصة بمالك البوت فقط.")
      return

    if query.data == "admin_add_btn":
      await query.edit_message_text(
          "لإضافة زر، أرسل رسالة بالصيغة التالية:\n`/addbtn اسم_الزر | محتوى الزر`",
          parse_mode="Markdown",
      )
    elif query.data == "admin_del_btn":
      buttons = list(data["buttons"].keys())
      if not buttons:
        await query.edit_message_text("لا توجد أزرار مضافة حالياً.")
        return
      kb = [
          [InlineKeyboardButton(b, callback_data=f"del_{b}")] for b in buttons
      ]
      await query.edit_message_text(
          "اختر الزر للحذف:", reply_markup=InlineKeyboardMarkup(kb)
      )
    elif query.data == "admin_list_btn":
      btns = (
          "\n".join([f"- {k}" for k in data["buttons"].keys()])
          if data["buttons"]
          else "لا توجد أزرار."
      )
      await query.edit_message_text(f"الأزرار الحالية:\n{btns}")
    elif query.data == "admin_set_welcome":
      await query.edit_message_text(
          "لتغيير رسالة الترحيب، أرسل الأمر:\n`/setwelcome رسالتك هنا`",
          parse_mode="Markdown",
      )

  elif query.data.startswith("del_"):
    if query.from_user.id != OWNER_ID:
      return
    btn_name = query.data.replace("del_", "")
    if btn_name in data["buttons"]:
      del data["buttons"][btn_name]
      save_data(data)
      await query.edit_message_text(f"تم حذف الزر: {btn_name}")

  elif query.data.startswith("task_"):
    task_name = query.data.replace("task_", "")
    if user_id not in data["users"]:
      data["users"][user_id] = {
          "username": query.from_user.username,
          "stars_normal": 0,
          "stars_advanced": 0,
          "tasks": {},
      }

    current_status = data["users"][user_id]["tasks"].get(task_name, False)
    data["users"][user_id]["tasks"][task_name] = not current_status
    save_data(data)

    keyboard = []
    for t_name, status in data["users"][user_id]["tasks"].items():
      icon = "✅" if status else "❌"
      keyboard.append(
          [InlineKeyboardButton(f"{t_name} {icon}", callback_data=f"task_{t_name}")]
      )
    await query.edit_message_reply_markup(
        reply_markup=InlineKeyboardMarkup(keyboard)
    )

  else:
    if query.data in data["buttons"]:
      await query.answer(data["buttons"][query.data], show_alert=True)


# أمر إضافة زر من قبل المالك
async def add_btn_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
  if update.effective_user.id != OWNER_ID:
    return
  text = " ".join(context.args)
  if "|" not in text:
    await update.message.reply_text(
        "الصيغة خاطئة. استخدم: `/addbtn الاسم | المحتوى`", parse_mode="Markdown"
    )
    return
  name, content = text.split("|", 1)
  name = name.strip()
  content = content.strip()
  data["buttons"][name] = content
  save_data(data)
  await update.message.reply_text(f"تم إضافة الزر ({name}) بنجاح.")


# أمر تعيين رسالة الترحيب
async def set_welcome_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
  if update.effective_user.id != OWNER_ID:
    return
  new_welcome = " ".join(context.args)
  if not new_welcome:
    await update.message.reply_text("الرجاء كتابة رسالة الترحيب بعد الأمر.")
    return
  data["welcome_message"] = new_welcome
  save_data(data)
  await update.message.reply_text("تم تحديث رسالة الترحيب بنجاح.")


# أمر عرض قائمة النقاط العملية للمستخدم
async def tasks_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
  user_id = str(update.effective_user.id)
  if user_id not in data["users"]:
    data["users"][user_id] = {
        "username": update.effective_user.username,
        "stars_normal": 0,
        "stars_advanced": 0,
        "tasks": {"المهام اليومية": False, "متابعة القناة": False},
    }
    save_data(data)

  user_tasks = data["users"][user_id]["tasks"]
  keyboard = []
  for t_name, status in user_tasks.items():
    icon = "✅" if status else "❌"
    keyboard.append(
        [InlineKeyboardButton(f"{t_name} {icon}", callback_data=f"task_{t_name}")]
    )

  await update.message.reply_text(
      "📌 قائمة النقاط العملية الخاصة بك (اضغط لتغيير الحالة):",
      reply_markup=InlineKeyboardMarkup(keyboard),
  )


# معالجة الرسائل والمجموعات (النجوم، الردود، والتحويل التلقائي)
async def handle_messages(update: Update, context: ContextTypes.DEFAULT_TYPE):
  message = update.message
  if not message or not message.text:
    return

  text = message.text.strip()

  if text == "نجومي":
    user_id = str(update.effective_user.id)
    if user_id in data["users"]:
      u_data = data["users"][user_id]
      await message.reply_text(
          f"⭐ قائمة نجومك:\n- {u_data['stars_normal']} نجوم عادية. ⭐\n- {u_data['stars_advanced']} نجمة متطورة . 🌟"
      )
    else:
      await message.reply_text("ليس لديك أي نجوم حتى الآن.")
    return

  if message.reply_to_message:
    if update.effective_user.id != OWNER_ID:
      return

    target_user = message.reply_to_message.from_user
    target_id = str(target_user.id)
    target_name = target_user.username or target_user.first_name

    if target_id not in data["users"]:
      data["users"][target_id] = {
          "username": target_name,
          "stars_normal": 0,
          "stars_advanced": 0,
          "tasks": {},
      }

    if text == "+⭐":
      data["users"][target_id]["stars_normal"] += 1
      if data["users"][target_id]["stars_normal"] >= 3:
        div = data["users"][target_id]["stars_normal"] // 3
        data["users"][target_id]["stars_advanced"] += div
        data["users"][target_id]["stars_normal"] %= 3
      save_data(data)
      await message.reply_text(f"تمت إضافة نجمة لحساب @{target_name} ⭐")

    elif text == "+🌟":
      data["users"][target_id]["stars_advanced"] += 1
      save_data(data)
      await message.reply_text(f"تمت إضافة نجمة متطورة لحساب @{target_name} 🌟")

    elif text == "-⭐":
      if data["users"][target_id]["stars_normal"] > 0:
        data["users"][target_id]["stars_normal"] -= 1
        save_data(data)
        await message.reply_text(
            f"تم خصم نجمة من حساب @{target_name} (عادية)"
        )
      else:
        await message.reply_text(
            f"رصيد النجوم العادية لـ @{target_name} هو صفر بالفعل."
        )

    elif text == "-🌟":
      if data["users"][target_id]["stars_advanced"] > 0:
        data["users"][target_id]["stars_advanced"] -= 1
        save_data(data)
        await message.reply_text(
            f"تم خصم نجمة من حساب @{target_name} (متطورة)"
        )
      else:
        await message.reply_text(
            f"رصيد النجوم المتطورة لـ @{target_name} هو صفر بالفعل."
        )


def main():
  app = ApplicationBuilder().token(TOKEN).build()

  app.add_handler(CommandHandler("start", start))
  app.add_handler(CommandHandler("panel", panel))
  app.add_handler(CommandHandler("addbtn", add_btn_cmd))
  app.add_handler(CommandHandler("setwelcome", set_welcome_cmd))
  app.add_handler(CommandHandler("tasks", tasks_cmd))

  app.add_handler(CallbackQueryHandler(button_handler))
  app.add_handler(
      MessageHandler(filters.TEXT & ~filters.COMMAND, handle_messages)
  )

  print("البوت يعمل الآن بنجاح...")
  app.run_polling()


if __name__ == "__main__":
  main()
