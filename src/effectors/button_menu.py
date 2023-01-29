# Extends the paginagion class to create a button menu

import asyncio

from naff import (ActionRow, Button, ButtonStyles, ComponentCommand,
                  ComponentContext, Extension)
from naff.ext.paginators import Paginator


class LinkerMenu(Paginator):

    def __attrs_post_init__(self) -> None:
        self.client.add_component_callback(
            ComponentCommand(
                name=f"Paginator:{self._uuid}_buttons",
                callback=self._on_button,
                listeners=[
                    f"{self._uuid}|{field.name}" for field in self.pages[self.page_index].fields
                ],
            )
        )
        super().__attrs_post_init__()

    def create_components(self, disable=False) -> list[ActionRow]:
        rows = super().create_components(disable)

        additional_row = ActionRow(
            *[Button(
                label=field.name,
                custom_id=f"{self._uuid}|{field.name}",
                style=ButtonStyles.GRAY) for field in self.pages[self.page_index].fields]
        )

        return rows + [additional_row]

    async def _on_button(self, ctx: ComponentContext, *args, **kwargs):

        field_names = [
            field.name for field in self.pages[self.page_index].fields]

        if (name := ctx.custom_id.split("|")[1]) in field_names:
            if self._timeout_task:
                self._timeout_task.ping.set()

            quiz_scale: Extension = ctx.bot.get_ext("Quizzes")

            asyncio.create_task(
                quiz_scale.quiz.callback(ctx, sheet=name, gamemode="singleplayer"))

        else:
            await super()._on_button(ctx, *args, **kwargs)
