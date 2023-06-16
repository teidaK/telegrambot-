import logging
from telegram import ReplyKeyboardMarkup, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Updater, CommandHandler, ConversationHandler, MessageHandler, Filters, CallbackQueryHandler

# Уровни разговора
START, CREATE_TASK, SET_DEADLINE, SET_DESCRIPTION, VIEW_TASKS, EDIT_TASK = range(6)

# Обработчик команды /start
def start(update, context):
    user = update.message.from_user
    context.user_data['tasks'] = []  # список задач пользователя
    reply_keyboard = [['Создать задачу', 'Просмотреть задачи']]
    markup = ReplyKeyboardMarkup(reply_keyboard, one_time_keyboard=True)
    update.message.reply_text(f"Привет, {user.first_name}! Я бот ежедневник. Чем я могу тебе помочь?", reply_markup=markup)

    return START

# Обработчик команды /create_task
def create_task(update, context):
    reply_keyboard = [['Добавить дедлайн', 'Создать задачу без дедлайна', 'Отмена']]
    markup = ReplyKeyboardMarkup(reply_keyboard, one_time_keyboard=True)
    update.message.reply_text("Как назовем задачу?", reply_markup=markup)

    return CREATE_TASK

# Обработчик названия задачи
def set_task_name(update, context):
    context.user_data['task_name'] = update.message.text
    reply_keyboard = [['Добавить дедлайн', 'Создать задачу без дедлайна', 'Отмена']]
    markup = ReplyKeyboardMarkup(reply_keyboard, one_time_keyboard=True)
    update.message.reply_text("Хотите добавить дедлайн к задаче?", reply_markup=markup)

    return SET_DEADLINE

# Обработчик выбора дедлайна
def set_deadline(update, context):
    choice = update.message.text
    if choice == 'Добавить дедлайн':
        reply_keyboard = [['Отмена']]
        markup = ReplyKeyboardMarkup(reply_keyboard, one_time_keyboard=True)
        update.message.reply_text("Введите дедлайн в формате ДД.ММ.ГГГГ:", reply_markup=markup)
        return SET_DEADLINE
    elif choice == 'Создать задачу без дедлайна':
        context.user_data['deadline'] = None
        reply_keyboard = [['Добавить описание', 'Создать задачу без описания', 'Отмена']]
        markup = ReplyKeyboardMarkup(reply_keyboard, one_time_keyboard=True)
        update.message.reply_text("Хотите добавить описание к задаче?", reply_markup=markup)
        return SET_DESCRIPTION
    elif choice == 'Отмена':
        reply_keyboard = [['Создать задачу', 'Просмотреть задачи']]
        markup = ReplyKeyboardMarkup(reply_keyboard, one_time_keyboard=True)
        update.message.reply_text("Создание задачи отменено. Чем ещё я могу помочь?", reply_markup=markup)
        return START

# Обработчик дедлайна
def set_task_deadline(update, context):
    context.user_data['deadline'] = update.message.text
    reply_keyboard = [['Добавить описание', 'Создать задачу без описания', 'Отмена']]
    markup = ReplyKeyboardMarkup(reply_keyboard, one_time_keyboard=True)
    update.message.reply_text("Хотите добавить описание к задаче?", reply_markup=markup)

    return SET_DESCRIPTION

# Обработчик выбора описания
def set_description(update, context):
    choice = update.message.text
    if choice == 'Добавить описание':
        reply_keyboard = [['Отмена']]
        markup = ReplyKeyboardMarkup(reply_keyboard, one_time_keyboard=True)
        update.message.reply_text("Введите описание задачи:", reply_markup=markup)
        return SET_DESCRIPTION
    elif choice == 'Создать задачу без описания':
        context.user_data['description'] = None
        save_task(update, context)
        reply_keyboard = [['Создать задачу', 'Просмотреть задачи']]
        markup = ReplyKeyboardMarkup(reply_keyboard, one_time_keyboard=True)
        update.message.reply_text("Задача успешно создана! Чем ещё я могу помочь?", reply_markup=markup)
        return START
    elif choice == 'Отмена':
        reply_keyboard = [['Создать задачу', 'Просмотреть задачи']]
        markup = ReplyKeyboardMarkup(reply_keyboard, one_time_keyboard=True)
        update.message.reply_text("Создание задачи отменено. Чем ещё я могу помочь?", reply_markup=markup)
        return START

# Обработчик описания задачи
def set_task_description(update, context):
    context.user_data['description'] = update.message.text
    save_task(update, context)
    reply_keyboard = [['Создать задачу', 'Просмотреть задачи']]
    markup = ReplyKeyboardMarkup(reply_keyboard, one_time_keyboard=True)
    update.message.reply_text("Задача успешно создана! Чем ещё я могу помочь?", reply_markup=markup)

    return START

# Сохранение задачи и завершение разговора
def save_task(update, context):
    task = {
        'name': context.user_data['task_name'],
        'deadline': context.user_data['deadline'],
        'description': context.user_data['description']
    }
    context.user_data['tasks'].append(task)
    context.user_data['task_name'] = None
    context.user_data['deadline'] = None
    context.user_data['description'] = None

# Обработчик команды /view_tasks
def view_tasks(update, context):
    if not context.user_data['tasks']:
        reply_keyboard = [['Создать задачу']]
        markup = ReplyKeyboardMarkup(reply_keyboard, one_time_keyboard=True)
        update.message.reply_text("Список задач пуст.", reply_markup=markup)
        return START

    buttons = []
    for i, task in enumerate(context.user_data['tasks']):
        button_text = f"{i + 1}. {task['name']}"
        buttons.append([InlineKeyboardButton(button_text, callback_data=str(i))])

    markup = InlineKeyboardMarkup(buttons)
    update.message.reply_text("Выберите задачу:", reply_markup=markup)

    return VIEW_TASKS

# Обработчик выбора задачи из списка
def select_task(update, context):
    query = update.callback_query
    task_index = int(query.data)
    task = context.user_data['tasks'][task_index]

    buttons = [
        [InlineKeyboardButton('Редактировать задачу', callback_data='edit')],
        [InlineKeyboardButton('Удалить задачу', callback_data='delete')],
        [InlineKeyboardButton('Вернуться к списку задач', callback_data='back')]
    ]
    markup = InlineKeyboardMarkup(buttons)

    task_info = f"Название задачи: {task['name']}\n"
    if task['deadline']:
        task_info += f"Дедлайн: {task['deadline']}\n"
    if task['description']:
        task_info += f"Описание: {task['description']}\n"

    query.message.reply_text(task_info, reply_markup=markup)

    return EDIT_TASK

# Обработчик редактирования задачи
def edit_task(update, context):
    query = update.callback_query
    task_index = int(query.data)
    task = context.user_data['tasks'][task_index]

    buttons = [
        [InlineKeyboardButton('Изменить название', callback_data='change_name')],
        [InlineKeyboardButton('Изменить дедлайн', callback_data='change_deadline')],
        [InlineKeyboardButton('Изменить описание', callback_data='change_description')],
        [InlineKeyboardButton('Вернуться к списку задач', callback_data='back')]
    ]
    markup = InlineKeyboardMarkup(buttons)

    query.message.reply_text("Выберите параметр для редактирования:", reply_markup=markup)

    return EDIT_TASK

# Обработчик неизвестных команд
def unknown_command(update, context):
    update.message.reply_text("Извините, я не понимаю эту команду.")

# Обработчик отмены
def cancel(update, context):
    reply_keyboard = [['Создать задачу', 'Просмотреть задачи']]
    markup = ReplyKeyboardMarkup(reply_keyboard, one_time_keyboard=True)
    update.message.reply_text("Операция отменена. Чем ещё я могу помочь?", reply_markup=markup)

    return START

# Создание и настройка бота
def main():
    logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO)
    updater = Updater(token='6213628923:AAHC_iqEKBhVZwEUbvoTK8VfTuuIxjhlMbQ', use_context=True)
    dispatcher = updater.dispatcher

    conv_handler = ConversationHandler(
        entry_points=[CommandHandler('start', start)],
        states={
            START: [MessageHandler(Filters.regex('^(Создать задачу)$'), create_task),
                    MessageHandler(Filters.regex('^(Просмотреть задачи)$'), view_tasks)],
            CREATE_TASK: [MessageHandler(Filters.text & ~Filters.regex('^(Отмена)$'), set_task_name)],
            SET_DEADLINE: [MessageHandler(Filters.regex('^(Добавить дедлайн|Создать задачу без дедлайна|Отмена)$'),
                                          set_deadline),
                            MessageHandler(Filters.text & ~Filters.regex('^(Отмена)$'), set_task_deadline)],
            SET_DESCRIPTION: [MessageHandler(Filters.regex('^(Добавить описание|Создать задачу без описания|Отмена)$'),
                                             set_description),
                              MessageHandler(Filters.text & ~Filters.regex('^(Отмена)$'), set_task_description)],
            VIEW_TASKS: [CallbackQueryHandler(select_task)],
            EDIT_TASK: [CallbackQueryHandler(edit_task)]
        },
        fallbacks=[CommandHandler('cancel', cancel)]
    )

    dispatcher.add_handler(conv_handler)
    dispatcher.add_handler(CommandHandler('start', start))
    dispatcher.add_handler(CommandHandler('view_tasks', view_tasks))
    dispatcher.add_handler(MessageHandler(Filters.command, unknown_command))

    updater.start_polling()
    updater.idle()

if __name__ == '__main__':
    main()
