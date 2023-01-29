# Extends the paginagion class to create a button menu

from naff.ext.paginators import Paginator
from naff import Button, ActionRow, ButtonStyles, ComponentContext
from naff import Extension
import asyncio


class LinkerMenu(Paginator):
    def create_components(self, disable=False, all=False) -> list[ActionRow]:
        rows = super().create_components(disable, all)

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

            quiz_scale: Extension = ctx.bot.get_extensions("quiz")[0]

            asyncio.create_task(
                quiz_scale.quiz.callback(ctx, sheet=name, gamemode="singleplayer"))

        else:
            await super()._on_button(ctx, *args, **kwargs)
