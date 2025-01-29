from nicegui import ui
import json
import uuid
from typing import List, Dict


class TodoApp:
    def __init__(self):
        self.tasks: List[Dict] = []
        self.load_tasks()

        # Основной контейнер
        with ui.column().classes('w-full max-w-2xl mx-auto p-4 gap-4'):
            # Поле ввода новой задачи
            with ui.row().classes('w-full items-center gap-2'):
                self.new_task = ui.input('Новая задача', placeholder='Введите задачу...') \
                    .classes('flex-grow')
                ui.button('Добавить', on_click=self.add_task) \
                    .classes('bg-green-500 hover:bg-green-600 text-white')

            # Список задач
            self.task_list = ui.column().classes('w-full gap-1')
            self.refresh_task_list()

            # Кнопка очистки
            ui.button('Очистить все задачи', on_click=self.clear_all_tasks) \
                .classes('bg-red-500 hover:bg-red-600 text-white')

    def refresh_task_list(self):
        self.task_list.clear()
        with self.task_list:  # Важно использовать контекстный менеджер
            self.render_tasks(self.tasks)

    def render_tasks(self, tasks: List[Dict]):
        for task in tasks:
            with ui.card().classes('w-full p-2 gap-1'):
                with ui.row().classes('items-center gap-2 w-full'):
                    checkbox = ui.checkbox(value=task.get('checked', False)) \
                        .props('dense') \
                        .on('update:model-value', lambda e, t=task: self.toggle_task(t, e.args))
                    label = ui.label(task.get('text', ''))
                    checkbox.bind_value_to(label.classes,
                                           forward=lambda v: ['line-through'] if v else [])

                    with ui.row().classes('ml-auto gap-1'):
                        ui.button(icon='add', on_click=lambda t=task: self.add_subtask(t)) \
                            .props('round dense') \
                            .classes('bg-blue-100 hover:bg-blue-200')
                        ui.button(icon='delete', on_click=lambda t=task: self.delete_task(t)) \
                            .props('round dense') \
                            .classes('bg-red-100 hover:bg-red-200')

                # Рекурсивный рендер подзадач
                if task.get('subtasks'):
                    with ui.column().classes('ml-8 pl-4 border-l-2 border-gray-200'):
                        self.render_tasks(task['subtasks'])

    def add_task(self):
        text = self.new_task.value.strip()
        if text:
            self.tasks.append({
                'id': str(uuid.uuid4()),
                'text': text,
                'checked': False,
                'subtasks': []
            })
            self.new_task.value = ''
            self.refresh_task_list()
            self.save_tasks()

    def add_subtask(self, parent_task):
        with ui.dialog() as dialog, ui.card():
            subtask_input = ui.input('Новая подзадача')
            with ui.row():
                ui.button('Добавить', on_click=lambda: [
                    self._handle_add_subtask(parent_task, subtask_input.value),
                    dialog.close()
                ])
                ui.button('Отмена', on_click=dialog.close)
        dialog.open()

    def _handle_add_subtask(self, parent_task, text):
        text = text.strip()
        if text:
            parent_task['subtasks'].append({
                'id': f"{parent_task['id']}-{uuid.uuid4().hex[:4]}",
                'text': text,
                'checked': False,
                'subtasks': []
            })
            self.refresh_task_list()
            self.save_tasks()

    # Остальные методы остаются без изменений
    # ... (delete_task, toggle_task, clear_all_tasks, save_tasks, load_tasks и т.д.)


# Стилизация и запуск
ui.add_head_html('''
<style>
    body { background-color: #f8fafc; font-family: 'Inter', system-ui; }
    .line-through { text-decoration: line-through; opacity: 0.7; }
    .card { transition: all 0.2s ease; }
    .card:hover { transform: translateY(-2px); box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.1); }
</style>
''')

TodoApp()
ui.run(title='To-Do List', port=8080)