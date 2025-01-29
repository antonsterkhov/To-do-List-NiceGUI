from nicegui import ui
import json
import uuid
from datetime import datetime
from typing import List, Dict, Optional
from functools import partial

class TodoApp:
    def __init__(self):
        self.tasks: List[Dict] = []
        self.load_tasks()
        
        with ui.column().classes('w-full max-w-2xl mx-auto p-4 gap-4'):
            with ui.row().classes('w-full items-center gap-2'):
                self.new_task = ui.input('Новая задача', placeholder='Введите задачу...').classes('flex-grow')
                ui.button('Добавить', on_click=self.add_task).classes('bg-green-500 hover:bg-green-600 text-white')
            
            self.task_list = ui.column().classes('w-full gap-1')
            self.refresh_task_list()
            
            self.stats = ui.label()
            self.update_stats()

    def add_task(self):
        text = self.new_task.value.strip()
        if text:
            self.tasks.append({
                'id': str(uuid.uuid4()),
                'text': text,
                'checked': False,
                'due_date': None,
                'subtasks': []
            })
            self.new_task.value = ''
            self.refresh_task_list()
            self.save_tasks()

    def add_subtask(self, parent_task: Dict):
        with ui.dialog() as dialog, ui.card():
            task_input = ui.input('Новая подзадача')
            due_date = ui.date().props('today-btn')
            
            with ui.row():
                ui.button('Добавить', on_click=lambda: [
                    self._handle_add_subtask(parent_task, task_input.value, due_date.value),
                    dialog.close()
                ])
                ui.button('Отмена', on_click=dialog.close)
        dialog.open()

    def _handle_add_subtask(self, parent_task: Dict, text: str, due_date_str: Optional[str]):
        text = text.strip()
        if text:
            due_date = None
            if due_date_str:
                try:
                    due_date = datetime.strptime(due_date_str, '%Y-%m-%d').date().isoformat()
                except (ValueError, TypeError):
                    pass
            
            parent_task['subtasks'].append({
                'id': str(uuid.uuid4()),
                'text': text,
                'checked': False,
                'due_date': due_date,
                'subtasks': []
            })
            self.refresh_task_list()
            self.save_tasks()

    def get_task_status(self, task: Dict) -> str:
        if task.get('checked', False):
            return 'done'
            
        due_date_str = task.get('due_date')
        if due_date_str:
            try:
                due_date = datetime.fromisoformat(due_date_str).date()
                if due_date < datetime.now().date():
                    return 'overdue'
            except (ValueError, TypeError):
                pass
                
        return 'pending'

    def update_stats(self):
        total = len(self.tasks)
        done = sum(1 for t in self.tasks if t.get('checked', False))
        self.stats.text = f"Всего задач: {total} • Выполнено: {done} ({done/total*100:.0f}%)" if total else "Нет задач"

    def load_tasks(self):
        try:
            with open('tasks.json', 'r') as f:
                tasks = json.load(f)
                self.tasks = self.migrate_tasks(tasks)
        except (FileNotFoundError, json.JSONDecodeError):
            self.tasks = []

    def migrate_tasks(self, tasks):
        for task in tasks:
            if 'due_date' not in task:
                task['due_date'] = None
            if 'subtasks' not in task:
                task['subtasks'] = []
            if 'checked' not in task:
                task['checked'] = False
            if task['subtasks']:
                self.migrate_tasks(task['subtasks'])
        return tasks

    def save_tasks(self):
        with open('tasks.json', 'w') as f:
            json.dump(self.tasks, f, default=str, indent=2)

    def refresh_task_list(self):
        self.task_list.clear()
        with self.task_list:
            self.render_tasks(self.tasks)

    def render_tasks(self, tasks: List[Dict], level: int = 0):
        for task in tasks:
            with ui.card().classes('w-full p-2 gap-1').style(f'margin-left: {level*2}rem'):
                with ui.row().classes('items-center gap-2 w-full'):
                    status = self.get_task_status(task)
                    color = {
                        'done': 'text-green-500',
                        'pending': 'text-yellow-500',
                        'overdue': 'text-red-500'
                    }[status]
                    ui.icon('circle').classes(color).props('size=sm')
                    
                    checkbox = ui.checkbox(value=task.get('checked', False)) \
                        .props('dense') \
                        .on('update:model-value', lambda e, t=task: self.toggle_task(t, e.args))
                    label = ui.label(task.get('text', ''))
                    checkbox.bind_value_to(label.classes, forward=lambda v: ['line-through'] if v else [])
                    
                    if task.get('due_date'):
                        due_date = datetime.fromisoformat(task['due_date']).strftime('%d.%m.%Y')
                        ui.label(f'📅 {due_date}').classes('text-sm text-gray-500')
                    
                    with ui.row().classes('ml-auto gap-1'):
                        ui.button(icon='add', on_click=partial(self.add_subtask, task)) \
                            .props('round dense flat') \
                            .classes('text-blue-500')
                        ui.button(icon='edit', on_click=partial(self.show_edit_dialog, task)) \
                            .props('round dense flat') \
                            .classes('text-blue-500')
                        ui.button(icon='delete', on_click=partial(self.delete_task, task)) \
                            .props('round dense flat') \
                            .classes('text-red-500')
                
                if task.get('subtasks'):
                    self.render_tasks(task['subtasks'], level + 1)

    def show_edit_dialog(self, task: Dict):
        with ui.dialog() as dialog, ui.card():
            task_input = ui.input('Текст задачи', value=task['text'])
            due_date = ui.date().props('today-btn')
            
            if task['due_date']:
                try:
                    due_date.value = datetime.fromisoformat(task['due_date']).strftime('%Y-%m-%d')
                except:
                    pass
            
            with ui.row():
                ui.button('Сохранить', on_click=lambda: [
                    self._handle_edit_task(task, task_input.value, due_date.value),
                    dialog.close()
                ])
                ui.button('Отмена', on_click=dialog.close)
        dialog.open()

    def _handle_edit_task(self, task: Dict, text: str, due_date_str: Optional[str]):
        text = text.strip()
        if text:
            task['text'] = text
            task['due_date'] = None
            if due_date_str:
                try:
                    task['due_date'] = datetime.strptime(due_date_str, '%Y-%m-%d').date().isoformat()
                except (ValueError, TypeError):
                    pass
            self.refresh_task_list()
            self.save_tasks()

    def toggle_task(self, task: Dict, checked: bool):
        task['checked'] = checked
        self.update_stats()
        self.save_tasks()

    def delete_task(self, task: Dict):
        self._remove_task(self.tasks, task['id'])
        self.refresh_task_list()
        self.update_stats()
        self.save_tasks()

    def _remove_task(self, tasks: List[Dict], task_id: str) -> bool:
        for i in reversed(range(len(tasks))):
            if tasks[i]['id'] == task_id:
                del tasks[i]
                return True
            if self._remove_task(tasks[i].get('subtasks', []), task_id):
                return True
        return False

ui.add_head_html('''
<style>
    body {
        background-color: #f8fafc;
        font-family: 'Inter', system-ui;
    }
    .card {
        transition: all 0.2s;
        background: white;
        border-radius: 0.5rem;
        box-shadow: 0 1px 3px rgba(0,0,0,0.1);
    }
    .card:hover {
        transform: translateY(-2px);
        box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.1);
    }
    .line-through {
        text-decoration: line-through;
        opacity: 0.7;
    }
</style>
''')

TodoApp()
ui.run(title='To-Do List с подзадачами', port=8080)

#generate deepseek 