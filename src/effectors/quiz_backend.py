import asyncio
from collections import defaultdict
from dataclasses import dataclass

from interactions import (
    Button,
    ButtonStyle,
    ComponentContext,
    Embed,
    InteractionContext,
    MaterialColors,
    spread_to_rows,
)
from interactions.api.events.internal import Component

from utils import textToEmoji

REACTIONS = "abcdefghijklmnopqrstuvwxyz"


@dataclass
class QuizQuestion:
    mcq: bool
    correct_index: int
    answered_index: int
    options: list


@dataclass
class QuizSessionSP:
    current_score: int = 0
    current_mcq: int = 0
    question: QuizQuestion = None


@dataclass
class QuizSessionMP:
    current_score: defaultdict
    current_mcq: defaultdict
    question: QuizQuestion = None


def termination_embed_sp(
    ctx: InteractionContext, sesh: QuizSessionSP, message: str
) -> Embed:
    """
    Embed to terminate a quiz session
    """
    finalscore = (
        f"Final Score: {sesh.current_score}/{sesh.current_mcq} ="
        f" {round(sesh.current_score/sesh.current_mcq*100)}%"
        if sesh.current_mcq
        else None
    )

    end_embed = Embed(
        title=message,
        description=("\n" + finalscore) if finalscore else "",
        color=MaterialColors.RED,
    )
    end_embed.set_author(
        icon_url=ctx.author.avatar.url, name=f"Quiz for {ctx.author.display_name}"
    )
    return end_embed


def termination_embed_mp(sesh: QuizSessionMP, message: str) -> Embed:
    """
    Embed to terminate a quiz session
    """
    standings = Embed(title="Standings")
    standings.set_author(name=message)
    standings.description = "\n".join(
        [
            f"<@{id}>: {sesh.current_score[id]}/{sesh.current_mcq[id]} = "
            f"{round(sesh.current_score[id]/sesh.current_mcq[id]*100)}%"
            for id in sesh.current_mcq
        ]
    )
    return standings


def embed_result_sp(session: QuizSessionSP) -> Embed:
    """
    Generate Result embed of a user's response
    """
    question = session.question

    if question.mcq:
        # Determine whether MCQ answer is correct or not

        session.current_mcq += 1  # Add 1 to total MCQ
        if question.answered_index == question.correct_index:
            session.current_score += 1  # Add 1 to current score
            e = Embed(
                color=MaterialColors.GREEN,
                title="Correct",
                description=textToEmoji(REACTIONS[question.correct_index])
                + " "
                + question.options[question.correct_index],
            )
        else:
            e = Embed(
                color=MaterialColors.RED,
                title="Incorrect",
                description=textToEmoji(REACTIONS[question.correct_index])
                + " "
                + question.options[question.correct_index],
            )

        e.set_footer(
            text=f"You Answered: {REACTIONS[question.answered_index].upper()}\n"
            f"Current Score: {session.current_score}/{session.current_mcq} = "
            f"{round(session.current_score/session.current_mcq*100)}%"
        )

    else:
        # Show flashcard answer
        e = Embed(color=MaterialColors.GREEN)

        answers = "\n".join(question.options)

        e.set_author(
            name="Answer",
            icon_url="https://media.discordapp.net/attachments/724671574459940974/856634979001434142/unknown.png",
        )

        if question.options and len(answers) < 256:
            e.title = answers
        elif question.options:
            e.description = answers
        else:
            e.title = "(No Answer Found)"
    return e


def embed_result_mp(session: QuizSessionMP, user_id: int) -> Embed:
    """
    Generate Result embed of a user's response
    """
    question = session.question

    if question.mcq:
        # Determine whether MCQ answer is correct or not

        session.current_mcq[user_id] += 1  # Add 1 to total MCQ
        if question.answered_index == question.correct_index:
            session.current_score[user_id] += 1  # Add 1 to current score
            e = Embed(
                color=MaterialColors.GREEN,
                title="Correct",
                description=textToEmoji(REACTIONS[question.correct_index])
                + " "
                + question.options[question.correct_index],
            )
        else:
            e = Embed(
                color=MaterialColors.RED,
                title="Incorrect",
                description=textToEmoji(REACTIONS[question.correct_index])
                + " "
                + question.options[question.correct_index],
            )

        e.set_footer(
            text=f"You Answered: {REACTIONS[question.answered_index].upper()}\n"
            f"Current Score: {session.current_score[user_id]}/{session.current_mcq[user_id]} = "
            f"{round(session.current_score[user_id]/session.current_mcq[user_id]*100)}%"
        )

    else:
        # Show flashcard answer
        e = Embed(color=MaterialColors.GREEN)

        answers = "\n".join(question.options)

        e.set_author(
            name="Answer",
            icon_url="https://media.discordapp.net/attachments/724671574459940974/856634979001434142/unknown.png",
        )

        if question.options and len(answers) < 256:
            e.title = answers
        elif question.options:
            e.description = answers
        else:
            e.title = "(No Answer Found)"
    return e


async def listen_quiz(ctx: InteractionContext, quiz_name: str, questions: list):
    # Assume ctx has already been deferred

    sesh = QuizSessionSP()
    # Store current state of quiz

    result_embed: Embed = None

    for question_num in range(len(questions)):
        current_question = questions[question_num]
        prompt = current_question[0]

        question_embed = Embed(color=MaterialColors.BLUE)
        question_embed.set_footer("Press 🛑 to stop the quiz.")
        if image_url := current_question[1]:
            question_embed.set_image(url=image_url)

        desc_text = ""

        if len(prompt) < 252:
            question_embed.title = f"**{prompt}**"
        else:
            desc_text = f"**{prompt}**\n"

        options = [
            op.strip("\n") for op in current_question[2:-1] if op
        ]  # Take only non blank entries

        if mcq := bool(current_question[-1]):
            if len(options) > 24:
                await ctx.send(
                    f"Error, Question `{prompt}` has {len(options)} options, which exceeds the allowed maximum of 24."
                )
                continue

            correct_index: int = ord(current_question[-1][0].lower()) - 97

            if correct_index > len(current_question) - 1:
                await ctx.send(
                    f"Error, Question `{prompt}` has an invalid 'Correct Answer' label."
                    "Please make sure the correct answer is labelled as {A, B, C, D, etc.}"
                )
                continue

            question_embed.description = desc_text + "\n".join(
                f"{textToEmoji(REACTIONS[i])} {options[i]}" for i in range(len(options))
            )
            # Add the MCQ options to the description

            question_embed.set_author(
                name="Select the correct answer", icon_url=ctx.author.avatar.url
            )
        else:
            correct_index: int = 0  # Give it a default value

            question_embed.description = desc_text
            question_embed.set_author(
                name="Press ✅ to see the answer", icon_url=ctx.author.avatar.url
            )

        # Generate components
        if mcq:
            components = [
                Button(
                    label=REACTIONS[i].upper(), style=ButtonStyle.BLUE, custom_id=str(i)
                )
                for i in range(len(options))
            ]
        else:
            components = [Button(label="✅", style=ButtonStyle.GREEN, custom_id="0")]

        components = spread_to_rows(
            *(components + [Button(label="🛑", style=ButtonStyle.RED, custom_id="stop")])
        )

        sesh.question = QuizQuestion(True, correct_index, 0, options)

        # Handle embeds
        if result_embed:
            next_embed = Embed(
                title=f"Next Question ({question_num+1}/{len(questions)})",
                color=MaterialColors.BLUE,
            )
            embeds = [result_embed, next_embed, question_embed]

            msg = await component_ctx.send(
                embed=embeds, components=components, ephemeral=True
            )
        else:
            intro_embed = Embed(
                title=quiz_name,
                description=f"**Starting Quiz** -- {len(questions)} questions",
                color=MaterialColors.BLUE,
            )
            embeds = [intro_embed, question_embed]
            msg = await ctx.send(embeds=embeds, components=components)

        def check(component: Component):
            return component.ctx.author == ctx.author

        try:
            used_component: Component = await ctx.bot.wait_for_component(
                messages=[msg], timeout=120, check=check
            )

            component_ctx: ComponentContext = used_component.ctx

            if component_ctx.custom_id == "stop":
                stop_embed = termination_embed_sp(
                    ctx, sesh, "Quiz Terminated. Enter a new link to start again!"
                )
                await component_ctx.send(embed=stop_embed, ephemeral=True)
                return

            sesh.question.answered_index = int(component_ctx.custom_id)
            result_embed = embed_result_sp(sesh)

        except asyncio.TimeoutError:
            await ctx.send(
                content="**Quiz timed out after 120 seconds of inactivity.**",
                ephemeral=True,
            )
            return

    stop_embed = termination_embed_sp(
        ctx, sesh, "Question deck has been exhausted. Enter a new link to start again!"
    )
    await component_ctx.send(embeds=[result_embed, stop_embed], ephemeral=True)
    return


async def listen_quiz_mp(ctx: InteractionContext, quiz_name: str, questions: list):
    sesh = QuizSessionMP(defaultdict(int), defaultdict(int), None)
    # Store current state of quiz

    result_embed: Embed = None

    for question_num in range(len(questions)):
        current_question = questions[question_num]
        prompt = current_question[0]

        question_embed = Embed(color=MaterialColors.BLUE)
        question_embed.set_footer(
            "Press 🛑 to stop the quiz, or ⏭️ to skip to the next question."
        )
        if image_url := current_question[1]:
            question_embed.set_image(url=image_url)

        desc_text = ""

        if len(prompt) < 252:
            question_embed.title = f"**{prompt}**"
        else:
            desc_text = f"**{prompt}**\n"

        options = [
            op.strip("\n") for op in current_question[2:-1] if op
        ]  # Take only non blank entries

        if mcq := bool(current_question[-1]):
            if len(options) > 24:
                await ctx.send(
                    f"Error, Question `{prompt}` has {len(options)} options, which exceeds the allowed maximum of 24."
                )
                continue

            correct_index: int = ord(current_question[-1][0].lower()) - 97

            if correct_index > len(current_question) - 1:
                await ctx.send(
                    f"Error, Question `{prompt}` has an invalid 'Correct Answer' label."
                    "Please make sure the correct answer is labelled as {A, B, C, D, etc.}"
                )
                continue

            question_embed.description = desc_text + "\n".join(
                f"{textToEmoji(REACTIONS[i])} {options[i]}" for i in range(len(options))
            )
            # Add the MCQ options to the description

            question_embed.set_author(
                name="Select the correct answer within 30 seconds"
            )
        else:
            correct_index: int = 0  # Give it a default value

            question_embed.description = desc_text
            question_embed.set_author(
                name="Press ✅ to see the answer (30 seconds)",
                icon_url=ctx.author.avatar.url,
            )

        # Generate components
        if mcq:
            components = [
                Button(
                    label=REACTIONS[i].upper(), style=ButtonStyle.BLUE, custom_id=str(i)
                )
                for i in range(len(options))
            ]
        else:
            components = [Button(label="✅", style=ButtonStyle.GREEN, custom_id="0")]

        components = spread_to_rows(
            *(
                components
                + [
                    Button(label="🛑", style=ButtonStyle.RED, custom_id="stop"),
                    Button(label="⏭️", style=ButtonStyle.GRAY, custom_id="skip"),
                ]
            )
        )

        sesh.question = QuizQuestion(True, correct_index, 0, options)

        # Handle embeds
        if question_num > 0:
            next_embed = Embed(
                title=f"Next Question ({question_num+1}/{len(questions)})",
                color=MaterialColors.BLUE,
            )
            embeds = [next_embed, question_embed]
            msg = await ctx.send(embed=embeds, components=components)
        else:
            intro_embed = Embed(
                title=quiz_name,
                description=f"**Starting Multiplayer Quiz** -- {len(questions)} questions",
                color=MaterialColors.BLUE,
            )
            intro_embed.set_footer("Anyone can answer!")
            embeds = [intro_embed, question_embed]
            msg = await ctx.send(embeds=embeds, components=components)

        answered = []

        async def listen_button():
            while 1:
                used_component: Component = await ctx.bot.wait_for_component(
                    messages=[msg]
                )
                component_ctx = used_component.ctx

                if (
                    component_ctx.custom_id == "stop"
                    and component_ctx.author == ctx.author
                ):
                    await component_ctx.send("Stopping Quiz...", ephemeral=True)
                    return "stop"
                elif (
                    component_ctx.custom_id == "skip"
                    and component_ctx.author == ctx.author
                ):
                    await component_ctx.send("Skipping Question...", ephemeral=True)
                    return "skip"
                elif component_ctx.author.id not in answered:
                    sesh.question.answered_index = int(component_ctx.custom_id)
                    # send query to author privately
                    result_embed = embed_result_mp(sesh, component_ctx.author.id)
                    answered.append(component_ctx.author.id)
                    await component_ctx.send(embed=result_embed, ephemeral=True)

        t = asyncio.create_task(listen_button())
        try:
            result = await asyncio.wait_for(t, timeout=30)
            if result == "stop":
                stop_embed = termination_embed_mp(
                    sesh, "Quiz Terminated. Enter a new link to start again!"
                )
                await ctx.send(embed=stop_embed)
                return
        except asyncio.TimeoutError:
            pass
        except IndexError:
            pass

        standings = Embed(title="Standings")
        standings.description = "\n".join(
            [
                f"<@{id}>: {sesh.current_score[id]}/{sesh.current_mcq[id]} = "
                f"{round(sesh.current_score[id]/sesh.current_mcq[id]*100)}%"
                for id in sesh.current_mcq
            ]
        )
        await msg.edit(components=[])
        await ctx.send(embed=standings)

    stop_embed = termination_embed_mp(
        sesh, "Question deck has been exhausted. Enter a new link to start again!"
    )
    await ctx.send(embed=stop_embed)
    return
