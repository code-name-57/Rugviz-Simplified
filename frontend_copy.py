from fastapi import FastAPI
from nicegui import app, ui
from backend import create_hero, read_hero, update_hero, delete_hero, list_heroes
from models import Hero

class HeroApp:
    def __init__(self, fastapi_app: FastAPI) -> None:
        self.fastapi_app = fastapi_app

        # state properties
        self.heroes = {}
        self.hero_id_counter = 1
        self.editing_id = None
        self.hero_list = None
        self.name_input = None
        self.power_input = None

        self.setup_ui()

        ui.run_with(
            self.fastapi_app,
            mount_path='/gui',  # Optional: if omitted then @ui.page paths are at the root
            storage_secret='pick your private secret here',
        )

    def setup_ui(self):
        @ui.page('/')
        def show():
            ui.label('Hello, FastAPI!')

            # persist dark mode across tabs / restarts
            ui.dark_mode().bind_value(app.storage.user, 'dark_mode')
            ui.checkbox('dark mode').bind_value(app.storage.user, 'dark_mode')

            with ui.card().classes('p-4'):
                ui.label('Hero Form').classes('text-h5')
                self.name_input = ui.input(label='Name')
                self.power_input = ui.input(label='Power')
                ui.button('Submit', on_click=self.submit_hero)

            ui.separator()

            ui.label('Heroes List').classes('text-h5 mb-2')
            self.hero_list = ui.column()

            self.refresh_hero_list()

    def refresh_hero_list(self):
        self.hero_list.clear()
        self.heroes = list_heroes()
        print(self.heroes)
        for hero in self.heroes:
            with self.hero_list:
                with ui.row().classes('items-center'):
                    ui.label(f"{hero.id}: {hero.name} - {hero.secret_name}")
                    ui.button('Edit', on_click=lambda hero_id=hero.id: self.edit_hero(hero_id)).classes('ml-2')
                    ui.button('Delete', on_click=lambda hero_id=hero.id: self.delete_hero(hero_id)).classes('ml-2')

    def submit_hero(self):
        if self.editing_id is None:
            # Create new hero
            new_hero_dict = {
                'id': self.hero_id_counter,
                'name': self.name_input.value,
                'secret_name': self.power_input.value,
            }
            new_hero = Hero.model_validate(new_hero_dict)
            create_hero(new_hero)
            self.hero_id_counter += 1
        else:
            # Update existing hero
            self.heroes[self.editing_id]['name'] = self.name_input.value
            self.heroes[self.editing_id]['power'] = self.power_input.value
            self.editing_id = None

        self.name_input.value = ''
        self.power_input.value = ''
        self.refresh_hero_list()

    def edit_hero(self, hid: int):
        self.editing_id = hid
        hero = self.heroes[hid]
        self.name_input.value = hero['name']
        self.power_input.value = hero['power']

    def delete_hero(self, hid: int):
        if hid in self.heroes:
            del self.heroes[hid]
        if self.editing_id == hid:
            self.editing_id = None
            self.name_input.value = ''
            self.power_input.value = ''
        self.refresh_hero_list()


# Usage/initialization example:
# fastapi_app must be an instance of FastAPI.
def init(fastapi_app: FastAPI) -> None:
    HeroApp(fastapi_app)